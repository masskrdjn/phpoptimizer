"""
Analyseur spécialisé pour les problèmes de performance
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Tuple


from .base_analyzer import BaseAnalyzer


class PerformanceAnalyzer(BaseAnalyzer):
    """Analyseur spécialisé pour les problèmes de performance"""

    def analyze(self, content: str, file_path: Path, lines: List[str]) -> List[Dict[str, Any]]:
        """Analyser les problèmes de performance dans le code PHP"""
        issues = []

        # Détecter les opportunités de propagation de constantes
        self._detect_constant_propagation(lines, file_path, issues)

        # Détecter les calculs répétés
        self._detect_repeated_calculations(lines, file_path, issues)
        
        # Détecter les accès répétitifs aux tableaux (si activé)
        if self.config.is_rule_enabled('performance.repetitive_array_access'):
            self._detect_repetitive_array_access(lines, file_path, issues)
        
        # Analyser ligne par ligne
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Ignorer les commentaires et directives Blade
            if self._is_comment_line(line) or self._is_blade_directive(line):
                continue
            
            # Détecter les variables non utilisées
            self._detect_unused_variables(line_stripped, line_num, file_path, line, issues)
            
            # Détecter les fonctions coûteuses utilisées inutilement
            self._detect_expensive_function_calls(line_stripped, line_num, file_path, line, issues)
            
            # Détecter les opérations inefficaces sur les tableaux
            self._detect_inefficient_array_operations(line_stripped, line_num, file_path, line, issues)
            
            # Détecter les problèmes de chaînes de caractères
            self._detect_string_performance_issues(line_stripped, line_num, file_path, line, issues)
            
            # Détecter les problèmes de régularité d'expressions
            self._detect_regex_performance_issues(line_stripped, line_num, file_path, line, issues)
            
            # Détecter les problèmes d'I/O
            self._detect_io_performance_issues(line_stripped, line_num, file_path, line, issues)
        
        return issues
    
    def _detect_repeated_calculations(self, lines: List[str], file_path: Path, 
                                    issues: List[Dict[str, Any]]) -> None:
        """Détecter les calculs répétés dans le même contexte"""
        math_expressions = {}
        
        for line_num, line in enumerate(lines, 1):
            # Rechercher les expressions mathématiques du type $var = $a * $b + $c
            match = re.search(r'\$[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*(\$[a-zA-Z_][a-zA-Z0-9_]*\s*[\+\-\*\/]\s*\$[a-zA-Z_][a-zA-Z0-9_]*(?:\s*[\+\-\*\/]\s*\$[a-zA-Z_][a-zA-Z0-9_]*)*)', line)
            if match:
                expr = match.group(1)
                expr_clean = re.sub(r'\s+', ' ', expr.strip())
                
                # Ignorer les expressions contenant $this (référence d'objet)
                if '$this' in expr_clean:
                    continue
                
                # Ignorer les expressions trop simples
                if not re.search(r'[\+\-\*\/]', expr_clean):
                    continue
                
                if expr_clean not in math_expressions:
                    math_expressions[expr_clean] = []
                math_expressions[expr_clean].append((line_num, line.strip()))
        
        # Signaler les expressions répétées
        for expr, occurrences in math_expressions.items():
            if len(occurrences) >= 2:
                first_line, first_code = occurrences[0]
                issues.append(self._create_issue(
                    'performance.repeated_calculations',
                    f'Calcul répété détecté: {expr} (trouvé {len(occurrences)} fois)',
                    file_path,
                    first_line,
                    'info',
                    'performance',
                    f'Stocker le résultat de "{expr}" dans une variable réutilisable',
                    first_code
                ))
    
    def _detect_unused_variables(self, line_stripped: str, line_num: int, file_path: Path, 
                                line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les variables potentiellement non utilisées"""
        # Simple détection basée sur le nom (contient "unused" ou similaire)
        unused_patterns = [
            r'\$[a-zA-Z_][a-zA-Z0-9_]*unused[a-zA-Z0-9_]*\s*=',
            r'\$unused[a-zA-Z_][a-zA-Z0-9_]*\s*=',
            r'\$temp[0-9]*\s*=.*(?!temp)',  # variables temp non réutilisées
            r'\$dummy[a-zA-Z0-9_]*\s*='
        ]
        
        for pattern in unused_patterns:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                var_match = re.search(r'\$[a-zA-Z_][a-zA-Z0-9_]*', line_stripped)
                if var_match:
                    var_name = var_match.group(0)
                    issues.append(self._create_issue(
                        'performance.unused_variables',
                        f'Variable potentiellement non utilisée: {var_name}',
                        file_path,
                        line_num,
                        'info',
                        'performance',
                        f'Supprimer {var_name} si elle n\'est pas utilisée',
                        line.strip()
                    ))
                break
    
    def _detect_expensive_function_calls(self, line_stripped: str, line_num: int, file_path: Path, 
                                       line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les appels de fonctions coûteuses qui pourraient être optimisés"""
        expensive_functions = [
            ('array_unique', 'array_flip puis array_keys peut être plus rapide'),
            ('array_intersect', 'Considérer array_intersect_key si approprié'),
            ('array_diff', 'Considérer array_diff_key si approprié'),
            ('in_array.*true', 'Utiliser array_key_exists ou array_flip pour de gros tableaux'),
            ('preg_match.*\\.\\*', 'Expression régulière avec .* peut être lente'),
            ('file_get_contents.*http', 'Considérer cURL avec timeout pour les URL HTTP'),
            ('glob', 'Considérer opendir/readdir pour de gros répertoires'),
            ('scandir', 'Filtrer les résultats tôt si possible')
        ]
        
        for func_pattern, suggestion in expensive_functions:
            if re.search(rf'\b{func_pattern}\s*\(', line_stripped, re.IGNORECASE):
                func_name = func_pattern.split('\\.*')[0].split('\\.')[0]  # Nettoyer le nom
                issues.append(self._create_issue(
                    'performance.expensive_function',
                    f'Fonction potentiellement coûteuse: {func_name}()',
                    file_path,
                    line_num,
                    'info',
                    'performance',
                    suggestion,
                    line.strip()
                ))
                break
    
    def _detect_inefficient_array_operations(self, line_stripped: str, line_num: int, file_path: Path, 
                                           line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les opérations inefficaces sur les tableaux"""
        # array_push vs affectation directe
        if re.search(r'array_push\s*\(\s*\$[a-zA-Z_][a-zA-Z0-9_]*\s*,\s*[^,)]+\s*\)', line_stripped):
            issues.append(self._create_issue(
                'performance.array_push_single',
                'array_push() avec un seul élément est moins efficace que l\'affectation directe',
                file_path,
                line_num,
                'info',
                'performance',
                'Utiliser $array[] = $value au lieu de array_push($array, $value)',
                line.strip()
            ))
        
        # Utilisation de count() dans des conditions multiples
        if re.search(r'count\s*\([^)]+\)\s*[><=!]+\s*\d+', line_stripped):
            if re.search(r'count\s*\([^)]+\)\s*>\s*0', line_stripped):
                issues.append(self._create_issue(
                    'performance.count_vs_empty',
                    'count($array) > 0 est moins efficace que !empty($array)',
                    file_path,
                    line_num,
                    'info',
                    'performance',
                    'Utiliser !empty($array) au lieu de count($array) > 0',
                    line.strip()
                ))
        
        # Concatenation de tableaux inefficace
        if re.search(r'array_merge\s*\([^)]*\$[a-zA-Z_][a-zA-Z0-9_]*\s*,\s*array\s*\([^)]*\)\s*\)', line_stripped):
            issues.append(self._create_issue(
                'performance.array_merge_single',
                'array_merge() avec un petit tableau peut être inefficace',
                file_path,
                line_num,
                'info',
                'performance',
                'Considérer l\'opérateur + ou array_push() pour de meilleures performances',
                line.strip()
            ))
    
    def _detect_string_performance_issues(self, line_stripped: str, line_num: int, file_path: Path, 
                                        line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les problèmes de performance liés aux chaînes"""
        # Concaténation de chaînes en boucle (approximatif)
        if re.search(r'\$[a-zA-Z_][a-zA-Z0-9_]*\s*\.=', line_stripped):
            issues.append(self._create_issue(
                'performance.string_concatenation',
                'Concaténation de chaînes (.=) peut être inefficace en boucle',
                file_path,
                line_num,
                'info',
                'performance',
                'Considérer utiliser un tableau et implode() pour de nombreuses concaténations',
                line.strip()
            ))
        
        # substr vs array access
        if re.search(r'substr\s*\([^,]+,\s*0\s*,\s*1\s*\)', line_stripped):
            issues.append(self._create_issue(
                'performance.substr_first_char',
                'substr($str, 0, 1) est moins efficace que $str[0]',
                file_path,
                line_num,
                'info',
                'performance',
                'Utiliser $str[0] pour récupérer le premier caractère',
                line.strip()
            ))
        
        # strlen dans les conditions
        if re.search(r'strlen\s*\([^)]+\)\s*[><=!]+\s*0', line_stripped):
            issues.append(self._create_issue(
                'performance.strlen_vs_empty',
                'strlen() pour vérifier si une chaîne est vide est moins efficace',
                file_path,
                line_num,
                'info',
                'performance',
                'Utiliser empty($str) ou $str === \'\' pour vérifier si une chaîne est vide',
                line.strip()
            ))
    
    def _detect_regex_performance_issues(self, line_stripped: str, line_num: int, file_path: Path, 
                                       line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les problèmes de performance avec les expressions régulières"""
        # Regex avec quantificateurs gourmands
        regex_patterns_to_check = [
            (r'preg_match\s*\([^)]*\.\*\.\*', 'Expression régulière avec .*.* peut être très lente'),
            (r'preg_match\s*\([^)]*\.\+\.\+', 'Expression régulière avec .+.+ peut être très lente'),
            (r'preg_replace\s*\([^)]*\.\*', 'preg_replace avec .* peut être inefficace'),
            (r'preg_match_all\s*\([^)]*\.\*', 'preg_match_all avec .* peut consommer beaucoup de mémoire')
        ]
        
        for pattern, message in regex_patterns_to_check:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                issues.append(self._create_issue(
                    'performance.regex_performance',
                    message,
                    file_path,
                    line_num,
                    'warning',
                    'performance',
                    'Optimiser l\'expression régulière ou utiliser des fonctions de chaînes plus simples',
                    line.strip()
                ))
                break
        
        # Utilisation de regex pour des opérations simples
        simple_operations = [
            (r'preg_match\s*\([\'"][^\'"\[\]{}()*+?.\\|^$]*[\'"]', 'Expression régulière simple'),
            (r'preg_replace\s*\([\'"][^\'"\[\]{}()*+?.\\|^$]*[\'"].*[\'"][^\'"\[\]{}()*+?.\\|^$]*[\'"]', 'Remplacement simple')
        ]
        
        for pattern, description in simple_operations:
            if re.search(pattern, line_stripped):
                issues.append(self._create_issue(
                    'performance.regex_overkill',
                    f'{description} - regex peut être excessive',
                    file_path,
                    line_num,
                    'info',
                    'performance',
                    'Considérer str_replace(), strpos(), ou substr() pour des opérations de chaînes simples',
                    line.strip()
                ))
                break
    
    def _detect_io_performance_issues(self, line_stripped: str, line_num: int, file_path: Path, 
                                    line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les problèmes de performance liés aux I/O"""
        # Lecture de fichier ligne par ligne inefficace
        if re.search(r'fgets\s*\(.*fopen\s*\(', line_stripped):
            issues.append(self._create_issue(
                'performance.inefficient_file_reading',
                'Lecture de fichier ligne par ligne avec fopen/fgets peut être inefficace',
                file_path,
                line_num,
                'info',
                'performance',
                'Considérer file() ou file_get_contents() pour les petits fichiers',
                line.strip()
            ))
        
        # Vérifications d'existence de fichier répétées
        file_check_functions = ['file_exists', 'is_file', 'is_dir', 'is_readable', 'is_writable']
        for func in file_check_functions:
            if re.search(rf'\b{func}\s*\([^)]*\$[a-zA-Z_][a-zA-Z0-9_]*\)', line_stripped):
                issues.append(self._create_issue(
                    'performance.repeated_file_checks',
                    f'Vérification de fichier {func}() - considérer la mise en cache si répétée',
                    file_path,
                    line_num,
                    'info',
                    'performance',
                    f'Mettre en cache le résultat de {func}() si appelé plusieurs fois',
                    line.strip()
                ))
                break
        
        # Opérations de base de données sans préparation
        if re.search(r'mysql_query\s*\(.*\$', line_stripped):
            issues.append(self._create_issue(
                'performance.unprepared_query',
                'Requête SQL non préparée - peut être inefficace et dangereuse',
                file_path,
                line_num,
                'warning',
                'performance',
                'Utiliser des requêtes préparées pour de meilleures performances et sécurité',
                line.strip()
            ))
    
    def _detect_repetitive_array_access(self, lines: List[str], file_path: Path, 
                                      issues: List[Dict[str, Any]]) -> None:
        """Détecter les accès répétitifs aux tableaux et suggérer des variables temporaires"""
        # Dictionnaire pour stocker les accès trouvés par fonction/méthode
        function_scopes = {}
        current_function = None
        current_scope_start = 0
        
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Ignorer les commentaires et lignes vides
            if self._is_comment_line(line) or not line_stripped:
                continue
            
            # Détecter le début d'une fonction/méthode
            function_match = re.search(r'\b(?:function|public|private|protected|static)\s+(?:static\s+)?(?:function\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', line_stripped)
            if function_match:
                current_function = function_match.group(1)
                current_scope_start = line_num
                function_scopes[current_function] = {
                    'start': line_num,
                    'end': None,
                    'accesses': {}
                }
                continue
            
            # Détecter la fin d'une fonction (approximatif)
            if current_function and line_stripped == '}':
                # Vérifier si c'est probablement la fin de la fonction
                if line_num - current_scope_start > 2:  # Au moins quelques lignes dans la fonction
                    function_scopes[current_function]['end'] = line_num
                    self._analyze_function_array_accesses(function_scopes[current_function], file_path, lines, issues)
                    current_function = None
                continue
            
            # Dans le contexte global si pas de fonction courante
            if not current_function:
                current_function = '__global__'
                if current_function not in function_scopes:
                    function_scopes[current_function] = {
                        'start': 1,
                        'end': len(lines),
                        'accesses': {}
                    }
            
            # Extraire tous les accès aux tableaux/objets de la ligne
            array_accesses = self._extract_array_accesses(line_stripped)
            
            for access in array_accesses:
                # Ignorer les accès en assignation (côté gauche)
                if self._is_assignment_target(line_stripped, access):
                    continue
                
                # Ajouter l'accès à la liste pour cette fonction
                if access not in function_scopes[current_function]['accesses']:
                    function_scopes[current_function]['accesses'][access] = []
                
                function_scopes[current_function]['accesses'][access].append({
                    'line': line_num,
                    'code': line_stripped,
                    'full_line': line.strip()
                })
        
        # Analyser la fonction globale s'il y en a une
        if '__global__' in function_scopes:
            self._analyze_function_array_accesses(function_scopes['__global__'], file_path, lines, issues)
    
    def _extract_array_accesses(self, line: str) -> List[str]:
        """Extraire tous les accès aux tableaux et objets d'une ligne"""
        accesses = []
        
        # Pattern pour les accès aux tableaux simples et imbriqués
        # $array['key'] ou $array["key"] ou $array[$var]
        array_pattern = r'\$[a-zA-Z_][a-zA-Z0-9_]*(?:\[[^\]]+\])+(?:\[[^\]]+\])*'
        array_matches = re.findall(array_pattern, line)
        accesses.extend(array_matches)
        
        # Pattern pour les accès aux propriétés d'objets
        # $object->property->subproperty
        object_pattern = r'\$[a-zA-Z_][a-zA-Z0-9_]*(?:->[a-zA-Z_][a-zA-Z0-9_]*)+(?:->[a-zA-Z_][a-zA-Z0-9_]*)*'
        object_matches = re.findall(object_pattern, line)
        accesses.extend(object_matches)
        
        # Pattern pour les accès mixtes (objet puis tableau)
        # $object->property['key'] ou $object->property[$var]
        mixed_pattern = r'\$[a-zA-Z_][a-zA-Z0-9_]*(?:->[a-zA-Z_][a-zA-Z0-9_]*)+(?:\[[^\]]+\])+(?:\[[^\]]+\])*'
        mixed_matches = re.findall(mixed_pattern, line)
        accesses.extend(mixed_matches)
        
        return list(set(accesses))  # Éliminer les doublons
    
    def _is_assignment_target(self, line: str, access: str) -> bool:
        """Vérifier si l'accès est une cible d'assignation (côté gauche du =)"""
        # Chercher si l'accès apparaît avant un = qui n'est pas dans une comparaison
        escaped_access = re.escape(access)
        
        # Pattern pour détecter une assignation (pas ==, !=, <=, >=)
        assignment_pattern = rf'{escaped_access}\s*=(?!=|<|>|!)'
        if re.search(assignment_pattern, line):
            return True
        
        # Vérifier aussi les opérateurs d'assignation composés
        compound_assignment_pattern = rf'{escaped_access}\s*[+\-*/.%&|^]='
        if re.search(compound_assignment_pattern, line):
            return True
        
        # Vérifier unset()
        unset_pattern = rf'unset\s*\([^)]*{escaped_access}'
        if re.search(unset_pattern, line):
            return True
        
        return False
    
    def _analyze_function_array_accesses(self, function_info: Dict[str, Any], file_path: Path, 
                                       lines: List[str], issues: List[Dict[str, Any]]) -> None:
        """Analyser les accès aux tableaux dans une fonction et détecter les répétitions"""
        accesses = function_info['accesses']
        
        # Obtenir le seuil minimum depuis la configuration
        rule_config = self.config.get_rule_config('performance.repetitive_array_access')
        min_occurrences = rule_config.params.get('min_occurrences', 3)
        
        for access_expr, occurrences in accesses.items():
            # Seuil de détection configurable
            if len(occurrences) < min_occurrences:
                continue
            
            # Vérifier s'il y a des modifications de la variable/tableau entre les accès
            if self._has_modifications_between_accesses(access_expr, occurrences, lines):
                continue
            
            # Générer une alerte pour cet accès répétitif
            first_occurrence = occurrences[0]
            
            # Déterminer le type d'accès pour le message
            access_type = self._determine_access_type(access_expr)
            
            # Générer une suggestion de variable temporaire
            temp_var_name = self._generate_temp_variable_name(access_expr)
            
            issues.append(self._create_issue(
                'performance.repetitive_array_access',
                f'Accès répétitif détecté: {access_expr} (utilisé {len(occurrences)} fois)',
                file_path,
                first_occurrence['line'],
                'info',
                'performance',
                f'Stocker {access_expr} dans une variable temporaire ${temp_var_name} pour améliorer les performances.\n'
                f'Exemple: ${temp_var_name} = {access_expr}; puis utiliser ${temp_var_name}',
                first_occurrence['full_line']
            ))
    
    def _has_modifications_between_accesses(self, access_expr: str, occurrences: List[Dict[str, Any]], 
                                          lines: List[str]) -> bool:
        """Vérifier s'il y a des modifications de la variable/tableau entre les accès"""
        # Extraire la variable racine de l'expression d'accès
        root_var_match = re.match(r'(\$[a-zA-Z_][a-zA-Z0-9_]*)', access_expr)
        if not root_var_match:
            return False
        
        root_var = root_var_match.group(1)
        
        # Vérifier entre chaque paire d'accès consécutifs
        for i in range(len(occurrences) - 1):
            current_line = occurrences[i]['line']
            next_line = occurrences[i + 1]['line']
            
            # Vérifier les lignes entre les deux accès
            for line_num in range(current_line + 1, next_line):
                if line_num > len(lines):
                    break
                
                line = lines[line_num - 1].strip()  # -1 car les lignes sont indexées à partir de 0
                
                # Ignorer les commentaires
                if self._is_comment_line(lines[line_num - 1]):
                    continue
                
                # Vérifier les modifications de la variable racine
                if self._line_modifies_variable(line, root_var, access_expr):
                    return True
        
        return False
    
    def _line_modifies_variable(self, line: str, root_var: str, access_expr: str) -> bool:
        """Vérifier si une ligne modifie la variable ou l'expression d'accès"""
        # Échapper les caractères spéciaux pour regex
        escaped_root = re.escape(root_var)
        escaped_access = re.escape(access_expr)
        
        # Assignation directe à la variable racine
        if re.search(rf'{escaped_root}\s*=(?!=)', line):
            return True
        
        # Assignation à l'expression d'accès exacte
        if re.search(rf'{escaped_access}\s*=(?!=)', line):
            return True
        
        # Fonctions qui modifient les tableaux
        modifying_functions = [
            'unset', 'array_pop', 'array_push', 'array_shift', 'array_unshift',
            'array_splice', 'sort', 'rsort', 'asort', 'arsort', 'ksort', 'krsort',
            'shuffle', 'array_reverse', 'array_walk', 'array_walk_recursive'
        ]
        
        for func in modifying_functions:
            if re.search(rf'\b{func}\s*\([^)]*{escaped_root}', line):
                return True
        
        return False
    
    def _determine_access_type(self, access_expr: str) -> str:
        """Déterminer le type d'accès (tableau, objet, mixte)"""
        if '->' in access_expr and '[' in access_expr:
            return 'accès mixte objet/tableau'
        elif '->' in access_expr:
            return 'accès à propriété d\'objet'
        elif '[' in access_expr:
            return 'accès à tableau'
        else:
            return 'accès'
    
    def _generate_temp_variable_name(self, access_expr: str) -> str:
        """Générer un nom de variable temporaire basé sur l'expression d'accès"""
        # Extraire les éléments significatifs de l'expression
        parts = []
        
        # Extraire la variable racine
        root_match = re.match(r'\$([a-zA-Z_][a-zA-Z0-9_]*)', access_expr)
        if root_match:
            parts.append(root_match.group(1))
        
        # Extraire les clés de tableau littérales
        key_matches = re.findall(r"\['([^']+)'\]|\[\"([^\"]+)\"\]", access_expr)
        for match in key_matches:
            key = match[0] or match[1]  # Premier ou deuxième groupe non vide
            if key.isalnum():  # Seulement les clés alphanumériques
                parts.append(key)
        
        # Extraire les propriétés d'objet
        prop_matches = re.findall(r'->([a-zA-Z_][a-zA-Z0-9_]*)', access_expr)
        parts.extend(prop_matches)
        
        # Construire le nom de la variable temporaire
        if len(parts) > 1:
            # Utiliser camelCase pour combiner les parties
            var_name = parts[0]
            for part in parts[1:]:
                var_name += part.capitalize()
        else:
            var_name = parts[0] if parts else 'temp'
        
        # Ajouter un suffixe si nécessaire
        if len(var_name) > 20:
            var_name = var_name[:17] + 'Tmp'

        return var_name

    def _detect_constant_propagation(self, lines: List[str], file_path: Path,
                                     issues: List[Dict[str, Any]]) -> None:
        """Détecter les variables dont la valeur reste constante et qui pourraient
        être remplacées par leur littéral (propagation de constantes)."""
        const_assignments: Dict[str, Tuple[str, int]] = {}
        modified_vars: set = set()

        # 1ère passe : repérer les affectations vers une valeur littérale
        const_pattern = re.compile(
            r"^\s*\$([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*"
            r"([\d]+|'[^']*'|\"[^\"]*\"|true|false|null)\s*;",
            re.IGNORECASE,
        )
        for line_num, line in enumerate(lines, 1):
            match = const_pattern.match(line)
            if match:
                var, value = match.group(1), match.group(2)
                if var not in const_assignments and var not in modified_vars:
                    const_assignments[var] = (value, line_num)

        # 2e passe : repérer toute mutation ultérieure de ces variables
        modification_patterns = [
            r'\$([a-zA-Z_][a-zA-Z0-9_]*)\+\+',
            r'\+\+\$([a-zA-Z_][a-zA-Z0-9_]*)',
            r'\$([a-zA-Z_][a-zA-Z0-9_]*)\-\-',
            r'\-\-\$([a-zA-Z_][a-zA-Z0-9_]*)',
            r'\$([a-zA-Z_][a-zA-Z0-9_]*)\s*[+\-*\/%.]=',
            r'\$([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*'
            r'(?![\d]+|\'[^\']*\'|\"[^\"]*\"|true|false|null\s*;)',
        ]
        compiled_mods = [re.compile(p) for p in modification_patterns]
        for line in lines:
            for pattern in compiled_mods:
                for match in pattern.finditer(line):
                    var = match.group(1)
                    modified_vars.add(var)
                    const_assignments.pop(var, None)

        # 3e passe : signaler chaque utilisation hors déclaration
        for var, (value, decl_line) in const_assignments.items():
            usage_re = re.compile(rf'\${var}(?!\s*[=+\-*\/%.]=)')
            for line_num, line in enumerate(lines, 1):
                if line_num == decl_line:
                    continue
                stripped = line.strip()
                if stripped.startswith('//') or stripped.startswith('#'):
                    continue
                for match in usage_re.finditer(line):
                    issues.append(self._create_issue(
                        rule_name='performance.constant_propagation',
                        message=f"Propagation de constante possible : remplacer '${var}' par {value}",
                        file_path=file_path,
                        line=line_num,
                        severity='info',
                        issue_type='performance',
                        suggestion=f"Remplacer '${var}' par {value}",
                        code_snippet=stripped,
                        column=match.start(),
                    ))
