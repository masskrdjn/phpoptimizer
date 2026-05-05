"""
Analyseur spécialisé pour la détection d'erreurs
"""

import re
from pathlib import Path
from typing import List, Dict, Any

from .base_analyzer import BaseAnalyzer


class ErrorAnalyzer(BaseAnalyzer):
    """Analyseur spécialisé pour la détection d'erreurs de code"""
    
    def analyze(self, content: str, file_path: Path, lines: List[str]) -> List[Dict[str, Any]]:
        """Analyser les erreurs dans le code PHP"""
        issues = []
        
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Ignorer les commentaires et directives Blade
            if self._is_comment_line(line) or self._is_blade_directive(line):
                continue
            
            # Détecter les erreurs de syntaxe communes
            self._detect_syntax_errors(line_stripped, line_num, file_path, line, issues)
            
            # Détecter les appels de méthode sur null
            self._detect_null_method_calls(line_stripped, line_num, file_path, line, lines, issues)
            
            # Détecter les variables non initialisées
            self._detect_uninitialized_variables(line_stripped, line_num, file_path, line, lines, issues)
            
            # Détecter les erreurs d'arguments de fonction
            self._detect_function_argument_errors(line_stripped, line_num, file_path, line, issues)
            
            # Détecter les affectations dans les conditions
            self._detect_assignment_in_conditions(line_stripped, line_num, file_path, line, issues)
            
            # Détecter les erreurs de typographie
            self._detect_typos(line_stripped, line_num, file_path, line, issues)
            
            # Détecter les problèmes de chaînes de caractères
            self._detect_string_issues(line_stripped, line_num, file_path, line, issues)
            
            # Détecter les problèmes de type
            self._detect_type_errors(line_stripped, line_num, file_path, line, issues)
            
            # Détecter les erreurs de logique
            self._detect_logic_errors(line_stripped, line_num, file_path, line, issues)
        
        return issues
    
    def _detect_syntax_errors(self, line_stripped: str, line_num: int, file_path: Path, 
                             line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les erreurs de syntaxe communes"""
        # Parenthèses non fermées dans les structures de contrôle
        if re.search(r'\b(if|for|while|foreach|switch)\s*\([^)]*$', line_stripped):
            issues.append(self._create_issue(
                'error.syntax_parentheses',
                'Parenthèse non fermée dans la structure de contrôle',
                file_path,
                line_num,
                'error',
                'error',
                'Vérifier que toutes les parenthèses sont correctement fermées',
                line.strip()
            ))
        
        # Accolades non ouvertes après structure de contrôle
        if re.search(r'\b(if|for|while|foreach|switch)\s*\([^)]*\)\s*$', line_stripped):
            issues.append(self._create_issue(
                'error.syntax_braces',
                'Structure de contrôle sans accolade ouvrante ou instruction',
                file_path,
                line_num,
                'warning',
                'error',
                'Ajouter une accolade ouvrante { ou une instruction sur la ligne suivante',
                line.strip()
            ))
        
        # Point-virgule manquant
        if (re.search(r'\$[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[^;]*$', line_stripped) and
            not re.search(r'(if|for|while|foreach|switch|function|class|interface|trait)', line_stripped) and
            not re.search(r'\$[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*\[', line_stripped) and  # Ignorer les déclarations de tableaux
            not re.search(r'\$[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*\{', line_stripped) and  # Ignorer les déclarations d'objet ou de closure
            not re.search(r'\$[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*new\s+', line_stripped) and  # Ignorer les instanciations multi-lignes
            not re.search(r'\$[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*\(', line_stripped) and  # Ignorer les expressions entre parenthèses
            not re.search(r'\$[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\(.*\[', line_stripped) and  # Ignorer les appels de fonction avec tableaux
            not line_stripped.endswith('.') and  # Ignorer la continuation de concaténation
            not line_stripped.endswith('+') and  # Ignorer la continuation arithmétique
            not line_stripped.endswith('-') and  # Ignorer la continuation arithmétique
            not line_stripped.endswith('*') and  # Ignorer la continuation arithmétique
            not line_stripped.endswith('/') and  # Ignorer la continuation arithmétique
            not line_stripped.endswith('&&') and  # Ignorer la continuation logique
            not line_stripped.endswith('||')):  # Ignorer la continuation logique
            issues.append(self._create_issue(
                'error.syntax_semicolon',
                'Point-virgule potentiellement manquant à la fin de l\'instruction',
                file_path,
                line_num,
                'warning',
                'error',
                'Ajouter un point-virgule à la fin de l\'instruction',
                line.strip()
            ))
    
    def _detect_null_method_calls(self, line_stripped: str, line_num: int, file_path: Path, 
                                 line: str, lines: List[str], issues: List[Dict[str, Any]]) -> None:
        """Détecter les appels de méthode sur des variables potentiellement null"""
        # Variables spéciales PHP qui ne peuvent pas être null
        special_vars = {
            '$this',     # Variable d'instance de classe
            '$GLOBALS',  # Variables globales
            '$_GET',     # Variables GET
            '$_POST',    # Variables POST
            '$_REQUEST', # Variables REQUEST
            '$_SESSION', # Variables SESSION
            '$_COOKIE',  # Variables COOKIE
            '$_SERVER',  # Variables SERVER
            '$_ENV',     # Variables d'environnement
            '$_FILES',   # Variables de fichiers uploadés
        }
        
        # Patterns pour détecter les appels sur variables potentiellement null
        null_patterns = [
            (r'\$[a-zA-Z_][a-zA-Z0-9_]*\s*->\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\(', 'Appel de méthode sur variable potentiellement null'),
            (r'\$[a-zA-Z_][a-zA-Z0-9_]*\[.*\]\s*->\s*[a-zA-Z_][a-zA-Z0-9_]*', 'Appel de méthode sur élément de tableau potentiellement null')
        ]
        
        for pattern, description in null_patterns:
            match = re.search(pattern, line_stripped)
            if match:
                # Extraire le nom de la variable sur laquelle on appelle la méthode (pas celle qui reçoit le résultat)
                method_call_match = re.search(r'(\$[a-zA-Z_][a-zA-Z0-9_]*)\s*->\s*[a-zA-Z_][a-zA-Z0-9_]*', line_stripped)
                if method_call_match:
                    var_name = method_call_match.group(1)
                    
                    # Ignorer les variables spéciales PHP
                    if var_name in special_vars:
                        continue
                    
                    # Vérifier si la variable est sûrement initialisée
                    is_safely_initialized = False
                    
                    # 1. Chercher si c'est une variable d'exception dans un bloc catch
                    for i in range(max(0, line_num - 10), line_num):
                        if i - 1 < len(lines) and i - 1 >= 0:  # Ajuster l'index pour lines
                            prev_line = lines[i - 1].strip()
                            # Pattern pour catch (Exception $e) ou catch (Type $var)
                            if re.search(rf'catch\s*\([^)]*{re.escape(var_name)}\s*\)', prev_line):
                                is_safely_initialized = True
                                break
                    
                    # 2. Chercher si la variable vient d'être instanciée avec 'new'
                    if not is_safely_initialized:
                        # Chercher dans les lignes précédentes (jusqu'à 10 lignes avant)
                        # line_num est basé sur 1, mais lines est indexé à partir de 0
                        for i in range(max(0, line_num - 10), line_num):
                            if i - 1 < len(lines) and i - 1 >= 0:  # Ajuster l'index pour lines
                                prev_line = lines[i - 1].strip()
                                # Pattern pour $var = new Class() ou $var = new Class
                                if re.search(rf'{re.escape(var_name)}\s*=\s*new\s+[a-zA-Z_][a-zA-Z0-9_]*', prev_line):
                                    is_safely_initialized = True
                                    break
                                # Pattern pour $var = functionThatReturnsObject()
                                if re.search(rf'{re.escape(var_name)}\s*=\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\(.*\)\s*;?\s*$', prev_line):
                                    # Vérifier si c'est probablement une fonction qui retourne un objet
                                    func_patterns = [
                                        r'create', r'get[A-Z]', r'find', r'load', r'fetch', 
                                        r'build', r'make', r'construct', r'instance'
                                    ]
                                    if any(re.search(pattern, prev_line, re.IGNORECASE) for pattern in func_patterns):
                                        is_safely_initialized = True
                                        break
                    
                    # 3. Chercher si il y a une vérification isset/null dans les lignes précédentes  
                    if not is_safely_initialized:
                        for i in range(max(0, line_num - 5), line_num):
                            if i - 1 < len(lines) and i - 1 >= 0:  # Ajuster l'index pour lines
                                prev_line = lines[i - 1].strip()
                                if re.search(rf'isset\s*\(\s*{re.escape(var_name)}\s*\)|{re.escape(var_name)}\s*!==?\s*null|{re.escape(var_name)}\s*!=\s*null', prev_line):
                                    is_safely_initialized = True
                                    break
                    
                    # Ignorer si la variable est sûrement initialisée
                    if is_safely_initialized:
                        continue
                    
                    # Si aucune initialisation sûre n'a été trouvée, signaler le problème
                    issues.append(self._create_issue(
                        'error.null_method_call',
                        description,
                        file_path,
                        line_num,
                        'warning',
                        'error',
                        'Vérifier que la variable n\'est pas null avant l\'appel de méthode avec isset() ou une condition',
                        line.strip()
                    ))
                break
    
    def _detect_uninitialized_variables(self, line_stripped: str, line_num: int, file_path: Path, 
                                      line: str, lines: List[str], issues: List[Dict[str, Any]]) -> None:
        """Détecter les variables potentiellement non initialisées"""
        # Variables spéciales PHP qui sont toujours disponibles
        special_vars = {
            '$this',     # Variable d'instance de classe
            '$GLOBALS',  # Variables globales
            '$_GET',     # Variables GET
            '$_POST',    # Variables POST
            '$_REQUEST', # Variables REQUEST
            '$_SESSION', # Variables SESSION
            '$_COOKIE',  # Variables COOKIE
            '$_SERVER',  # Variables SERVER
            '$_ENV',     # Variables d'environnement
            '$_FILES',   # Variables de fichiers uploadés
            '$argc',     # Nombre d'arguments en ligne de commande
            '$argv',     # Arguments en ligne de commande
        }
        
        # Chercher les utilisations de variables dans les conditions
        if re.search(r'\b(if|while|for)\s*\([^)]*\$[a-zA-Z_][a-zA-Z0-9_]*', line_stripped):
            var_matches = re.findall(r'\$[a-zA-Z_][a-zA-Z0-9_]*', line_stripped)
            for var_name in var_matches:
                # Ignorer les variables spéciales PHP
                if var_name in special_vars:
                    continue
                # Chercher une initialisation dans les lignes précédentes
                initialized = False
                
                # Chercher dans un contexte plus large pour les fonctions
                search_range = min(50, line_num)  # Chercher dans 50 lignes ou jusqu'au début
                
                for prev_line_num in range(max(0, line_num - search_range), line_num):
                    if prev_line_num < len(lines):
                        prev_line = lines[prev_line_num].strip()
                        
                        # Vérifier les assignations classiques
                        if re.search(rf'{re.escape(var_name)}\s*=', prev_line):
                            initialized = True
                            break
                        # Vérifier les variables de boucle foreach
                        if re.search(rf'foreach\s*\([^)]*as\s*{re.escape(var_name)}\b', prev_line):
                            initialized = True
                            break
                        # Vérifier les variables de boucle foreach avec clé => valeur
                        if re.search(rf'foreach\s*\([^)]*=>\s*{re.escape(var_name)}\b', prev_line):
                            initialized = True
                            break
                        # Vérifier les paramètres de fonction (pattern amélioré)
                        if re.search(rf'function\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*{re.escape(var_name)}\b', prev_line):
                            initialized = True
                            break
                        # Vérifier si on est dans une fonction et chercher la déclaration
                        # Pattern plus flexible pour les paramètres de fonction
                        if re.search(rf'function.*\([^)]*{re.escape(var_name)}\b', prev_line):
                            initialized = True
                            break
                
                # Vérification spéciale : si on est dans une boucle foreach active
                if not initialized:
                    # Chercher si on est dans le corps d'une boucle foreach
                    foreach_depth = 0
                    for check_line_num in range(max(0, line_num - 20), line_num):
                        if check_line_num < len(lines):
                            check_line = lines[check_line_num].strip()
                            # Compter les ouvertures et fermetures de blocs
                            foreach_depth += check_line.count('{') - check_line.count('}')
                            # Si on trouve une boucle foreach et qu'on est dans son corps
                            if (foreach_depth > 0 and 
                                re.search(rf'foreach\s*\([^)]*as\s*\$[a-zA-Z_][a-zA-Z0-9_]*\s*\)\s*\{{', check_line)):
                                # Chercher si la variable est initialisée dans le corps de la boucle
                                for body_line_num in range(check_line_num + 1, line_num):
                                    if body_line_num < len(lines):
                                        body_line = lines[body_line_num].strip()
                                        if re.search(rf'{re.escape(var_name)}\s*=', body_line):
                                            initialized = True
                                            break
                                if initialized:
                                    break
                
                # Si toujours pas trouvé, chercher la déclaration de fonction englobante
                if not initialized:
                    # Chercher la fonction englobante en remontant plus loin
                    for func_line_num in range(max(0, line_num - 100), line_num):
                        if func_line_num < len(lines):
                            func_line = lines[func_line_num].strip()
                            # Si on trouve une déclaration de fonction avec notre variable en paramètre
                            if (re.search(r'function\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(', func_line) and 
                                re.search(rf'{re.escape(var_name)}\b', func_line)):
                                initialized = True
                                break
                
                if not initialized:
                    issues.append(self._create_issue(
                        'error.uninitialized_variable',
                        f'Variable {var_name} potentiellement non initialisée',
                        file_path,
                        line_num,
                        'warning',
                        'error',
                        f'S\'assurer que {var_name} est initialisée avant utilisation',
                        line.strip()
                    ))
    
    def _detect_function_argument_errors(self, line_stripped: str, line_num: int, file_path: Path, 
                                       line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les erreurs d'arguments de fonction"""
        # Fonctions avec nombre d'arguments fixes (simplifié)
        function_args = {
            'strpos': (2, 3),  # min, max arguments
            'substr': (2, 3),
            'array_slice': (2, 4),
            'preg_match': (2, 5),
            'json_decode': (1, 4),
            'fopen': (2, 4),
            'file_get_contents': (1, 5),
            'mysqli_query': (2, 3)
        }
        
        func_match = re.search(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)', line_stripped)
        if func_match:
            func_name = func_match.group(1)
            args_str = func_match.group(2).strip()
            
            if func_name in function_args:
                # Compter les arguments (approximatif)
                if args_str:
                    args_count = len(re.split(r',(?![^(]*\))', args_str))
                else:
                    args_count = 0
                
                min_args, max_args = function_args[func_name]
                
                if args_count < min_args or args_count > max_args:
                    issues.append(self._create_issue(
                        'error.incorrect_argument_count',
                        f'Fonction {func_name}() : nombre d\'arguments incorrect ({args_count}), attendu: {min_args}-{max_args}',
                        file_path,
                        line_num,
                        'error',
                        'error',
                        f'Vérifier la documentation de {func_name}() et corriger le nombre d\'arguments',
                        line.strip()
                    ))
    
    def _detect_assignment_in_conditions(self, line_stripped: str, line_num: int, file_path: Path, 
                                        line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les affectations dans les conditions"""
        # Fonctions pour lesquelles l'affectation dans une condition est légitime
        legitimate_assignment_functions = [
            'json_decode', 'file_get_contents', 'fopen', 'fscanf', 'fgets', 'fgetcsv',
            'mysqli_query', 'curl_exec', 'preg_match', 'strpos', 'array_pop', 'array_shift',
            'mysql_query', 'pg_query', 'sqlite_query', 'opendir', 'readdir', 'glob',
            'stream_context_create', 'imagecreatefrom', 'getimagesize', 'parse_url'
        ]
        
        # Détecter = au lieu de == dans les conditions, mais exclure les affectations légitimes
        condition_patterns = [
            r'\bif\s*\([^)]*\$[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[^=]',
            r'\bwhile\s*\([^)]*\$[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[^=]',
            r'\belseif\s*\([^)]*\$[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[^=]'
        ]
        
        for pattern in condition_patterns:
            match = re.search(pattern, line_stripped)
            if match:
                # Vérifier si c'est une affectation légitime avec une fonction connue
                is_legitimate = False
                for func in legitimate_assignment_functions:
                    if func + '(' in line_stripped:
                        is_legitimate = True
                        break
                
                # Vérifier aussi les patterns courants d'affectation intentionnelle
                legitimate_patterns = [
                    r'=\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\(',  # affectation d'appel de fonction
                    r'=\s*new\s+',  # affectation de new
                    r'=\s*\$[a-zA-Z_][a-zA-Z0-9_]*\s*\[',  # affectation d'accès tableau
                ]
                
                for legitimate_pattern in legitimate_patterns:
                    if re.search(legitimate_pattern, line_stripped):
                        is_legitimate = True
                        break
                
                if not is_legitimate:
                    issues.append(self._create_issue(
                        'error.assignment_in_condition',
                        'Affectation (=) détectée dans une condition, vouliez-vous utiliser == ou === ?',
                        file_path,
                        line_num,
                        'error',
                        'error',
                        'Remplacer = par == pour une comparaison ou === pour une comparaison stricte',
                        line.strip()
                    ))
                break
    
    def _detect_typos(self, line_stripped: str, line_num: int, file_path: Path, 
                     line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les erreurs de typographie courantes"""
        common_typos = {
            'echp': 'echo',
            'prnt': 'print',
            'var_dumped': 'var_dump',
            'vardump': 'var_dump',
            'lenght': 'length',
            'widht': 'width',
            'heigh': 'height',
            'retrun': 'return',
            'fucntion': 'function',
            'calss': 'class',
            'pubilc': 'public',
            'privte': 'private',
            'protcted': 'protected'
        }
        
        for typo, correction in common_typos.items():
            if re.search(rf'\b{typo}\b', line_stripped, re.IGNORECASE):
                issues.append(self._create_issue(
                    'error.typo',
                    f'Erreur de typographie: "{typo}"',
                    file_path,
                    line_num,
                    'warning',
                    'error',
                    f'Corriger en: "{correction}"',
                    line.strip()
                ))
                break
    
    def _detect_string_issues(self, line_stripped: str, line_num: int, file_path: Path, 
                             line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les problèmes de chaînes de caractères"""
        # Désactiver temporairement la détection des guillemets non fermés 
        # car elle génère trop de faux positifs sur du code PHP valide
        # Cette fonctionnalité pourra être réactivée avec un algorithme plus robuste
        return
        
        # Code désactivé temporairement...
        # Ignorer les commentaires pour la détection des guillemets
        line_without_comments = line_stripped
        
        # Retirer les commentaires de ligne //
        comment_pos = line_without_comments.find('//')
        if comment_pos != -1:
            line_without_comments = line_without_comments[:comment_pos]
        
        # Retirer les commentaires de bloc /* */
        line_without_comments = re.sub(r'/\*.*?\*/', '', line_without_comments)
        
        # Ne pas analyser les lignes qui paraissent valides (réduit les faux positifs)
        line_clean = line_without_comments.strip()
        if not line_clean or line_clean.endswith(';'):
            # Ignorer les lignes terminées par un point-virgule (instructions probablement complètes)
            return
        
        # Algorithme amélioré pour compter les guillemets non échappés
        single_quote_count = self._count_unescaped_quotes(line_without_comments, "'")
        double_quote_count = self._count_unescaped_quotes(line_without_comments, '"')
        
        # Réduire la sévérité à "info" pour éviter les faux positifs critiques
        if single_quote_count % 2 != 0:
            issues.append(self._create_issue(
                'error.unclosed_quotes',
                'Guillemets simples potentiellement non fermés',
                file_path,
                line_num,
                'info',  # Sévérité abaissée pour éviter les faux positifs critiques
                'error',
                'Vérifier que tous les guillemets simples sont correctement fermés',
                line.strip()
            ))
        
        if double_quote_count % 2 != 0:
            issues.append(self._create_issue(
                'error.unclosed_quotes',
                'Guillemets doubles potentiellement non fermés',
                file_path,
                line_num,
                'info',  # Sévérité abaissée pour éviter les faux positifs critiques
                'error',
                'Vérifier que tous les guillemets doubles sont correctement fermés',
                line.strip()
            ))
    
    def _count_unescaped_quotes(self, text: str, quote_char: str) -> int:
        """Compter les guillemets non échappés dans une chaîne"""
        count = 0
        i = 0
        while i < len(text):
            if text[i] == quote_char:
                # Compter les antislashs précédents
                escape_count = 0
                j = i - 1
                while j >= 0 and text[j] == '\\':
                    escape_count += 1
                    j -= 1
                
                # Si nombre pair d'antislashs (ou 0), le guillemet n'est pas échappé
                if escape_count % 2 == 0:
                    count += 1
            i += 1
        
        return count
    
    def _detect_type_errors(self, line_stripped: str, line_num: int, file_path: Path, 
                           line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les erreurs de type potentielles"""
        # Opérations mathématiques sur des chaînes
        if re.search(r'["\'][^"\']*["\'][\s]*[\+\-\*\/][\s]*["\'][^"\']*["\']', line_stripped):
            issues.append(self._create_issue(
                'error.string_math_operation',
                'Opération mathématique entre chaînes de caractères',
                file_path,
                line_num,
                'warning',
                'error',
                'Vérifier que les valeurs sont numériques ou utiliser la concaténation (.)',
                line.strip()
            ))
        
        # Comparaison avec des types différents
        type_comparison_patterns = [
            (r'["\'][^"\']*["\'][\s]*===?[\s]*\d+', 'Comparaison chaîne/nombre'),
            (r'\d+[\s]*===?[\s]*["\'][^"\']*["\']', 'Comparaison nombre/chaîne'),
            (r'true[\s]*===?[\s]*\d+', 'Comparaison booléen/nombre'),
            (r'\d+[\s]*===?[\s]*true', 'Comparaison nombre/booléen')
        ]
        
        for pattern, description in type_comparison_patterns:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                issues.append(self._create_issue(
                    'error.type_comparison',
                    f'Comparaison de types différents: {description}',
                    file_path,
                    line_num,
                    'warning',
                    'error',
                    'Vérifier que les types sont compatibles ou utiliser une conversion explicite',
                    line.strip()
                ))
                break
    
    def _detect_logic_errors(self, line_stripped: str, line_num: int, file_path: Path, 
                            line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les erreurs de logique"""
        # Conditions toujours vraies ou fausses
        always_true_patterns = [
            r'\btrue\s*==\s*true\b',
            r'\b1\s*==\s*1\b',
            r'\$[a-zA-Z_][a-zA-Z0-9_]*\s*==\s*\$[a-zA-Z_][a-zA-Z0-9_]*'  # même variable
        ]
        
        for pattern in always_true_patterns:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                issues.append(self._create_issue(
                    'error.always_true_condition',
                    'Condition qui semble toujours vraie',
                    file_path,
                    line_num,
                    'warning',
                    'error',
                    'Vérifier la logique de la condition',
                    line.strip()
                ))
                break
        
        # Return dans une boucle
        if re.search(r'\breturn\b', line_stripped) and re.search(r'(for|foreach|while)', line_stripped):
            issues.append(self._create_issue(
                'error.return_in_loop',
                'Return détecté dans une structure de boucle',
                file_path,
                line_num,
                'info',
                'error',
                'Vérifier si le return est intentionnel ou si une variable de contrôle serait plus appropriée',
                line.strip()
            ))
