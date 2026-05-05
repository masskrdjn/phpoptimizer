"""
Analyseur spécialisé pour la qualité de code
"""

import re
from pathlib import Path
from typing import List, Dict, Any

from .base_analyzer import BaseAnalyzer


class CodeQualityAnalyzer(BaseAnalyzer):
    """Analyseur spécialisé pour la qualité de code et les bonnes pratiques"""
    
    def analyze(self, content: str, file_path: Path, lines: List[str]) -> List[Dict[str, Any]]:
        """Analyser la qualité du code PHP"""
        issues = []
        
        # Détecter les problèmes de variables globales
        self._detect_unused_global_variables(content, file_path, lines, issues)
        
        # Analyser ligne par ligne
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Ignorer les commentaires et directives Blade
            if self._is_comment_line(line) or self._is_blade_directive(line):
                continue
            
            # Détecter les problèmes de style et bonnes pratiques
            self._detect_style_issues(line_stripped, line_num, file_path, line, issues)
            
            # Détecter les problèmes de nommage
            self._detect_naming_issues(line_stripped, line_num, file_path, line, issues)
            
            # Détecter la complexité excessive
            self._detect_complexity_issues(line_stripped, line_num, file_path, line, issues)
            
            # Détecter les problèmes de structure
            self._detect_structure_issues(line_stripped, line_num, file_path, line, lines, issues)
            
            # Détecter les problèmes de documentation
            self._detect_documentation_issues(line_stripped, line_num, file_path, line, lines, issues)
        
        return issues
    
    def _detect_unused_global_variables(self, content: str, file_path: Path, lines: List[str], 
                                      issues: List[Dict[str, Any]]) -> None:
        """Détecter les variables globales inutilisées ou qui pourraient être locales"""
        # Dictionnaires pour tracker les variables globales
        global_declarations = {}  # ligne -> {var_name, function_name}
        global_usages = {}        # var_name -> [lignes d'utilisation]
        variable_assignments = {} # var_name -> [lignes d'assignation]
        variable_usages = {}      # var_name -> [lignes d'utilisation]
        
        current_function = None
        function_boundaries = []
        brace_level = 0
        
        # Première passe : identifier les fonctions et leurs limites
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Détecter les fonctions
            func_match = re.search(r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', line_stripped)
            if func_match:
                function_boundaries.append({
                    'name': func_match.group(1),
                    'start_line': line_num,
                    'end_line': None
                })
                current_function = func_match.group(1)
            
            # Compter les accolades pour déterminer la fin de fonction
            brace_level += line_stripped.count('{') - line_stripped.count('}')
            
            # Si on revient au niveau 0 et qu'on était dans une fonction
            if brace_level == 0 and current_function and function_boundaries:
                function_boundaries[-1]['end_line'] = line_num
                current_function = None
        
        # Deuxième passe : analyser les variables globales
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Ignorer les commentaires
            if self._is_comment_line(line):
                continue
            
            # Déterminer dans quelle fonction on se trouve
            current_func = self._get_current_function(line_num, function_boundaries)
            
            # Détecter les déclarations global
            global_match = re.search(r'global\s+([^;]+);', line_stripped)
            if global_match:
                global_vars = global_match.group(1)
                # Extraire toutes les variables (format: $var1, $var2, etc.)
                var_matches = re.findall(r'\$([a-zA-Z_][a-zA-Z0-9_]*)', global_vars)
                for var_name in var_matches:
                    global_declarations[line_num] = {
                        'var_name': var_name,
                        'function_name': current_func
                    }
                    if var_name not in global_usages:
                        global_usages[var_name] = []
            
            # Détecter les utilisations de variables
            var_matches = re.findall(r'\$([a-zA-Z_][a-zA-Z0-9_]*)', line_stripped)
            for var_name in var_matches:
                # Ignorer les superglobales
                if var_name in ['_GET', '_POST', '_SESSION', '_COOKIE', '_SERVER', '_ENV', '_REQUEST', 'GLOBALS']:
                    continue
                
                # Tracker les utilisations générales
                if var_name not in variable_usages:
                    variable_usages[var_name] = []
                variable_usages[var_name].append(line_num)
                
                # Si c'est une variable déclarée globale
                if var_name in global_usages:
                    global_usages[var_name].append(line_num)
                
                # Détecter les assignations
                if re.search(rf'\${var_name}\s*=', line_stripped):
                    if var_name not in variable_assignments:
                        variable_assignments[var_name] = []
                    variable_assignments[var_name].append(line_num)
        
        # Analyser les problèmes
        for line_num, global_info in global_declarations.items():
            var_name = global_info['var_name']
            function_name = global_info['function_name']
            
            # Variables globales jamais utilisées
            usage_lines = global_usages.get(var_name, [])
            # Retirer la ligne de déclaration des usages
            actual_usage_lines = [l for l in usage_lines if l != line_num]
            
            if not actual_usage_lines:
                issues.append(self._create_issue(
                    'performance.unused_global_variable',
                    f'Variable globale ${var_name} déclarée mais jamais utilisée dans la fonction {function_name}',
                    file_path,
                    line_num,
                    'warning',
                    'performance',
                    f'Supprimer la déclaration "global ${var_name}" si elle n\'est pas utilisée',
                    lines[line_num - 1].strip()
                ))
            
            # Variables qui pourraient être locales
            elif self._could_be_local_variable(var_name, function_name, function_boundaries, 
                                              variable_assignments, variable_usages):
                issues.append(self._create_issue(
                    'performance.global_could_be_local',
                    f'Variable ${var_name} déclarée globale mais pourrait être locale dans {function_name}',
                    file_path,
                    line_num,
                    'info',
                    'performance',
                    f'Considérer faire de ${var_name} une variable locale si elle n\'est utilisée que dans {function_name}',
                    lines[line_num - 1].strip()
                ))
    
    def _detect_style_issues(self, line_stripped: str, line_num: int, file_path: Path, 
                           line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les problèmes de style de code"""
        # Lignes trop longues
        if len(line) > 120:
            # Générer une suggestion spécifique selon le contexte
            suggestion = self._get_line_length_suggestion(line, line_stripped)
            
            issues.append(self._create_issue(
                'best_practices.line_length',
                f'Ligne trop longue ({len(line)} caractères)',
                file_path,
                line_num,
                'info',
                'best_practices',
                suggestion,
                line[:80] + '...' if len(line) > 80 else line
            ))
        
        # Espaces vs tabs
        if line.startswith('\t') and '    ' in line:
            issues.append(self._create_issue(
                'best_practices.mixed_indentation',
                'Mélange de tabulations et d\'espaces pour l\'indentation',
                file_path,
                line_num,
                'warning',
                'best_practices',
                'Utiliser soit des espaces soit des tabulations de manière cohérente',
                line.strip()
            ))
    
    def _detect_naming_issues(self, line_stripped: str, line_num: int, file_path: Path, 
                            line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les problèmes de nommage"""
        # Variables avec noms non descriptifs
        non_descriptive_patterns = [
            (r'\$[a-z]{1,2}\d*\s*=', 'Variable avec nom trop court'),
            (r'\$(temp|tmp|test|foo|bar|baz)\d*\s*=', 'Variable avec nom non descriptif'),
            (r'\$(var|val|data|item)\d*\s*=', 'Variable avec nom générique')
        ]
        
        for pattern, description in non_descriptive_patterns:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                var_match = re.search(r'\$[a-zA-Z_][a-zA-Z0-9_]*', line_stripped)
                if var_match:
                    var_name = var_match.group(0)
                    
                    # Ignorer les variables de boucle for/foreach classiques
                    if self._is_loop_variable(var_name, line_stripped):
                        continue
                    
                    issues.append(self._create_issue(
                        'best_practices.naming',
                        f'{description}: {var_name}',
                        file_path,
                        line_num,
                        'info',
                        'best_practices',
                        'Utiliser des noms de variables descriptifs et explicites',
                        line.strip()
                    ))
                break
        
        # Fonctions avec noms non descriptifs
        func_match = re.search(r'function\s+(test|temp|foo|bar|baz|func)\d*\s*\(', line_stripped, re.IGNORECASE)
        if func_match:
            func_name = func_match.group(1)
            issues.append(self._create_issue(
                'best_practices.function_naming',
                f'Nom de fonction non descriptif: {func_name}',
                file_path,
                line_num,
                'info',
                'best_practices',
                'Utiliser des noms de fonctions descriptifs qui expliquent leur rôle',
                line.strip()
            ))
    
    def _detect_complexity_issues(self, line_stripped: str, line_num: int, file_path: Path, 
                                line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les problèmes de complexité excessive"""
        # Trop de paramètres dans une fonction
        func_match = re.search(r'function\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(([^)]*)\)', line_stripped)
        if func_match:
            params = func_match.group(1)
            if params.strip():
                param_count = len([p for p in params.split(',') if p.strip()])
                if param_count > 5:
                    issues.append(self._create_issue(
                        'best_practices.too_many_parameters',
                        f'Fonction avec trop de paramètres ({param_count})',
                        file_path,
                        line_num,
                        'warning',
                        'best_practices',
                        'Considérer regrouper les paramètres en objet ou diviser la fonction',
                        line.strip()
                    ))
        
        # Conditions trop complexes
        complex_condition_patterns = [
            r'if\s*\([^)]*&&[^)]*&&[^)]*&&',  # Plus de 3 &&
            r'if\s*\([^)]*\|\|[^)]*\|\|[^)]*\|\|',  # Plus de 3 ||
        ]
        
        for pattern in complex_condition_patterns:
            if re.search(pattern, line_stripped):
                issues.append(self._create_issue(
                    'best_practices.complex_condition',
                    'Condition trop complexe',
                    file_path,
                    line_num,
                    'warning',
                    'best_practices',
                    'Simplifier la condition ou utiliser des variables intermédiaires',
                    line.strip()
                ))
                break
    
    def _detect_structure_issues(self, line_stripped: str, line_num: int, file_path: Path, 
                               line: str, lines: List[str], issues: List[Dict[str, Any]]) -> None:
        """Détecter les problèmes de structure de code"""
        # Multiples instructions sur une ligne (amélioré pour ignorer les ; dans les chaînes)
        if ';' in line_stripped and not line_stripped.startswith('for'):
            # Compter seulement les ; qui sont réellement des terminateurs d'instruction
            statement_count = self._count_real_statements(line_stripped)
            if statement_count > 1:
                issues.append(self._create_issue(
                    'best_practices.multiple_statements',
                    'Multiples instructions sur une seule ligne',
                    file_path,
                    line_num,
                    'warning',
                    'best_practices',
                    'Séparer chaque instruction sur sa propre ligne',
                    line.strip()
                ))
        
        # Accolades mal placées (style K&R vs Allman) - Seulement pour les fonctions, pas les classes
        if re.search(r'^\s*{\s*$', line_stripped):
            # Vérifier si l'accolade précède une déclaration de classe/interface
            prev_line_context = ""
            if line_num > 1:
                prev_line_context = lines[line_num - 2].strip() if line_num - 2 < len(lines) else ""
            
            # Ne pas signaler les accolades de classe/interface car les deux styles sont acceptés
            if not re.search(r'(class|interface|trait)\s+\w+', prev_line_context):
                issues.append(self._create_issue(
                    'best_practices.brace_style',
                    'Accolade ouvrante sur ligne séparée',
                    file_path,
                    line_num,
                    'info',
                    'best_practices',
                    'Considérer placer l\'accolade ouvrante sur la même ligne (style K&R) pour les fonctions',
                    line.strip()
                ))
    
    def _detect_documentation_issues(self, line_stripped: str, line_num: int, file_path: Path, 
                                   line: str, lines: List[str], issues: List[Dict[str, Any]]) -> None:
        """Détecter les problèmes de documentation"""
        # Fonctions publiques sans docstring
        func_match = re.search(r'(public\s+)?function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', line_stripped)
        if func_match:
            func_name = func_match.group(2)
            
            # Vérifier s'il y a un commentaire de documentation avant
            has_docstring = False
            for i in range(max(0, line_num - 5), line_num):
                if i < len(lines):
                    prev_line = lines[i].strip()
                    if prev_line.startswith('/**') or prev_line.startswith('/*'):
                        has_docstring = True
                        break
            
            if not has_docstring and not func_name.startswith('_'):  # Ignorer les méthodes privées
                issues.append(self._create_issue(
                    'best_practices.missing_docstring',
                    f'Fonction publique {func_name} sans documentation',
                    file_path,
                    line_num,
                    'info',
                    'best_practices',
                    'Ajouter un commentaire de documentation pour les fonctions publiques',
                    line.strip()
                ))
    
    def _get_current_function(self, line_num: int, function_boundaries: List[Dict]) -> str:
        """Déterminer dans quelle fonction se trouve une ligne donnée"""
        for func in function_boundaries:
            if func['start_line'] <= line_num <= (func['end_line'] or float('inf')):
                return func['name']
        return 'unknown'
    
    def _could_be_local_variable(self, var_name: str, function_name: str, function_boundaries: List[Dict],
                                variable_assignments: Dict[str, List[int]], 
                                variable_usages: Dict[str, List[int]]) -> bool:
        """Déterminer si une variable globale pourrait être locale"""
        # Obtenir les limites de la fonction
        func_info = None
        for func in function_boundaries:
            if func['name'] == function_name:
                func_info = func
                break
        
        if not func_info or func_info['end_line'] is None:
            return False
        
        start_line = func_info['start_line']
        end_line = func_info['end_line']
        
        # Vérifier si toutes les utilisations sont dans cette fonction
        usages = variable_usages.get(var_name, [])
        assignments = variable_assignments.get(var_name, [])
        
        # Si la variable est assignée ET utilisée uniquement dans cette fonction
        usages_in_function = [l for l in usages if start_line <= l <= end_line]
        assignments_in_function = [l for l in assignments if start_line <= l <= end_line]
        
        # Conditions pour être locale :
        # 1. Au moins une assignation dans la fonction
        # 2. Toutes les utilisations sont dans la fonction  
        # 3. Au moins une utilisation (sinon ce serait unused)
        return (len(assignments_in_function) > 0 and 
                len(usages_in_function) == len(usages) and
                len(usages_in_function) > 1)  # > 1 car inclut la déclaration global
    
    def _is_loop_variable(self, var_name: str, line_stripped: str) -> bool:
        """Vérifier si une variable est un compteur de boucle for classique ou une variable de boucle foreach courante"""
        # Variables de compteur acceptées pour les boucles for : $i, $j, $k, $l, $m, $n, $x, $y, $z
        classic_counters = ['$i', '$j', '$k', '$l', '$m', '$n', '$x', '$y', '$z']
        
        # Variables courantes acceptées pour les boucles foreach
        common_foreach_vars = ['$item', '$file', '$dir', '$key', '$value', '$row', '$data', '$element']
        
        # Si c'est une variable de compteur classique, vérifier les boucles for
        if var_name in classic_counters:
            # Vérifier si la ligne contient une structure de boucle for
            for_patterns = [
                rf'for\s*\(\s*{re.escape(var_name)}\s*=',  # for ($i = ...)
                rf'for\s*\([^;]*;\s*{re.escape(var_name)}\s*[<>=!]',  # for (...; $i < ...)
                rf'for\s*\([^;]*;\s*[^;]*;\s*{re.escape(var_name)}[\+\-]',  # for (...; ...; $i++)
            ]
            
            for pattern in for_patterns:
                if re.search(pattern, line_stripped):
                    return True
        
        # Si c'est une variable foreach courante, vérifier les boucles foreach
        if var_name in common_foreach_vars:
            # Vérifier si la ligne contient une structure de boucle foreach
            foreach_patterns = [
                rf'foreach\s*\([^)]*as\s*{re.escape(var_name)}\b',  # foreach (...as $item)
                rf'foreach\s*\([^)]*=>\s*{re.escape(var_name)}\b',  # foreach (...=> $value)
            ]
            
            for pattern in foreach_patterns:
                if re.search(pattern, line_stripped):
                    return True
        
        return False

    def _count_real_statements(self, line_stripped: str) -> int:
        """Compter le nombre réel d'instructions dans une ligne (ignore les ; dans les chaînes)"""
        statement_count = 0
        in_string = False
        in_single_quote = False
        escape_next = False
        
        for i, char in enumerate(line_stripped):
            if escape_next:
                escape_next = False
                continue
                
            if char == '\\':
                escape_next = True
                continue
                
            if char == '"' and not in_single_quote:
                in_string = not in_string
            elif char == "'" and not in_string:
                in_single_quote = not in_single_quote
            elif char == ';' and not in_string and not in_single_quote:
                # Vérifier que ce n'est pas dans un commentaire
                comment_pos = line_stripped.find('//', max(0, i-50))
                if comment_pos == -1 or comment_pos > i:
                    statement_count += 1
                    
        return statement_count

    def _is_comment_line(self, line: str) -> bool:
        """Vérifier si une ligne est un commentaire"""
        line_stripped = line.strip()
        return (line_stripped.startswith('//') or 
                line_stripped.startswith('/*') or 
                line_stripped.startswith('*') or
                line_stripped.startswith('#') or
                line_stripped == '*/')

    def _is_blade_directive(self, line: str) -> bool:
        """Vérifier si une ligne contient une directive Blade Laravel"""
        line_stripped = line.strip()
        blade_patterns = [
            r'@[a-zA-Z_][a-zA-Z0-9_]*',  # @directive
            r'{{\s*.*\s*}}',             # {{ variable }}
            r'{!!\s*.*\s*!!}',           # {!! html !!}
            r'@php\b',                   # @php
            r'@endphp\b',               # @endphp
        ]
        
        for pattern in blade_patterns:
            if re.search(pattern, line_stripped):
                return True
        return False

    def _get_line_length_suggestion(self, line: str, line_stripped: str) -> str:
        """Générer une suggestion spécifique pour raccourcir une ligne trop longue"""
        
        # Cas spécifique: User-Agent HTTP
        if 'user-agent' in line_stripped.lower() or 'useragent' in line_stripped.lower():
            return ("Chaîne User-Agent très longue. Solutions possibles :\n"
                   "• Stocker dans une variable séparée : $userAgent = '...'; puis utiliser $userAgent\n"
                   "• Découper en plusieurs parties concaténées\n"
                   "• Utiliser une constante de classe pour les valeurs longues")
        
        # Cas spécifique: URL longue
        if 'http' in line_stripped and len([c for c in line_stripped if c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789']) > 80:
            return ("URL très longue. Solutions possibles :\n"
                   "• Stocker l'URL dans une variable ou constante\n"
                   "• Découper l'URL en base + paramètres\n"
                   "• Utiliser un constructeur d'URL si disponible")
        
        # Cas spécifique: Tableau avec de nombreuses clés
        if '=>' in line_stripped and '[' in line_stripped:
            return ("Ligne de tableau trop longue. Solutions possibles :\n"
                   "• Mettre chaque élément sur une ligne séparée\n"
                   "• Extraire les valeurs longues dans des variables\n"
                   "• Utiliser l'indentation pour améliorer la lisibilité")
        
        # Cas spécifique: Chaîne de caractères longue
        if "'" in line_stripped or '"' in line_stripped:
            return ("Chaîne de caractères trop longue. Solutions possibles :\n"
                   "• Découper en plusieurs chaînes concaténées avec le point (.)\n"
                   "• Utiliser des variables pour les parties répétées\n"
                   "• Considérer un heredoc ou nowdoc pour les textes très longs")
        
        # Cas spécifique: Condition complexe
        if any(op in line_stripped for op in ['&&', '||', 'and', 'or']) and ('if' in line_stripped or 'while' in line_stripped):
            return ("Condition trop complexe. Solutions possibles :\n"
                   "• Séparer en plusieurs conditions avec des variables booléennes\n"
                   "• Utiliser des méthodes pour encapsuler la logique complexe\n"
                   "• Découper sur plusieurs lignes avec une indentation claire")
        
        # Cas spécifique: Appel de méthode avec de nombreux paramètres
        if line_stripped.count(',') >= 3 and '(' in line_stripped:
            return ("Trop de paramètres sur une ligne. Solutions possibles :\n"
                   "• Mettre chaque paramètre sur une ligne séparée\n"
                   "• Regrouper les paramètres liés dans un tableau\n"
                   "• Utiliser des variables pour les paramètres complexes")
        
        # Cas général
        return ("Ligne trop longue (limite: 120 caractères). Solutions générales :\n"
               "• Découper en plusieurs lignes plus courtes\n"
               "• Extraire les expressions complexes dans des variables\n"
               "• Améliorer l'indentation et la structure du code")