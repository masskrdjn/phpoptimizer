"""
Analyseur spécialisé pour les boucles et leur performance
"""

import re
from pathlib import Path
from typing import List, Dict, Any

from .base_analyzer import BaseAnalyzer


class LoopAnalyzer(BaseAnalyzer):
    """Analyseur spécialisé pour les problèmes liés aux boucles"""
    
    def analyze(self, content: str, file_path: Path, lines: List[str]) -> List[Dict[str, Any]]:
        """Analyser les problèmes de boucles dans le code PHP"""
        issues = []
        
        # Variables pour analyser les boucles imbriquées
        loop_stack = []
        in_loop = False
        
        # Analyser les boucles consécutives pour la fusion
        self._detect_consecutive_loop_fusion(lines, file_path, issues)
        
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Ignorer les commentaires et directives Blade
            if self._is_comment_line(line) or self._is_blade_directive(line):
                continue
            
            # Détecter le début d'une boucle
            if re.search(r'\b(for|foreach|while)\s*\(', line_stripped):
                loop_stack.append(line_num)
                in_loop = True
                
                # Détecter foreach sur non-itérable
                self._detect_foreach_non_iterable(line_stripped, line_num, file_path, lines, issues)
                
                # Détecter count() dans une boucle for
                self._detect_count_in_for_loop(line_stripped, line_num, file_path, line, issues)
                
                # Détecter boucles trop imbriquées (plus de 3 niveaux)
                self._detect_deeply_nested_loops(loop_stack, line_num, file_path, line, issues)
                
                # Détecter boucles imbriquées avec même tableau (dès qu'on trouve une boucle imbriquée)
                self._detect_nested_loops_same_array(line_stripped, line_num, file_path, line, lines, loop_stack, issues)
            
            # Détecter la fin d'une boucle (approximatif)
            if line_stripped == '}' and loop_stack:
                loop_stack.pop()
                if not loop_stack:
                    in_loop = False
            
            # Analyses pour le contenu des boucles
            if in_loop and loop_stack:
                # Détecter count() ou sizeof() dans le corps d'une boucle
                self._detect_expensive_functions_in_loop(line_stripped, line_num, file_path, line, issues)

                # Détecter les requêtes SQL dans les boucles
                self._detect_queries_in_loop(line_stripped, line_num, file_path, line, issues)

                # Détecter les fonctions lourdes dans les boucles
                self._detect_heavy_functions_in_loop(line_stripped, line_num, file_path, line, issues)

                # Détecter création répétée d'objets dans les boucles
                self._detect_object_creation_in_loop(line_stripped, line_num, file_path, line, issues)

                # Détecter les accès répétés aux superglobales dans les boucles
                self._detect_superglobal_access_in_loop(line_stripped, line_num, file_path, line, issues)

                # Détecter les problèmes de complexité algorithmique
                self._detect_algorithmic_complexity_issues(line_stripped, line_num, file_path, line, issues, loop_stack)

        return issues

    def _detect_superglobal_access_in_loop(self, line_stripped: str, line_num: int,
                                           file_path: Path, line: str,
                                           issues: List[Dict[str, Any]]) -> None:
        """Détecter les accès aux superglobales à l'intérieur d'une boucle.

        Chaque accès est coûteux à répétition : la valeur est généralement
        constante pendant la boucle, donc l'extraire avant la boucle évite des
        recherches superflues dans des tableaux superglobaux à chaque itération.
        """
        superglobals = ('$_SESSION', '$_COOKIE', '$_GET', '$_POST',
                        '$_SERVER', '$_ENV', '$_REQUEST', '$_FILES', '$GLOBALS')

        # Ignorer la ligne d'en-tête de la boucle elle-même (foreach/for/while)
        if re.match(r'\s*(for|foreach|while)\s*\(', line_stripped):
            return

        cleaned = self._remove_strings_and_comments(line)
        for superglobal in superglobals:
            if superglobal in cleaned:
                issues.append(self._create_issue(
                    rule_name='performance.superglobal_access_in_loop',
                    message=(
                        f"Accès à la superglobale {superglobal} dans une boucle. "
                        "Stockez la valeur dans une variable locale avant la boucle."
                    ),
                    file_path=file_path,
                    line=line_num,
                    severity='info',
                    issue_type='performance',
                    suggestion=(
                        f"Extrayez l'accès à {superglobal} hors de la boucle et "
                        "réutilisez la variable locale."
                    ),
                    code_snippet=line.strip(),
                ))

    def _detect_consecutive_loop_fusion(self, lines: List[str], file_path: Path, issues: List[Dict[str, Any]]) -> None:
        """Détecter les opportunités de fusion de boucles consécutives"""
        loops = []
        i = 0
        
        while i < len(lines):
            line_stripped = lines[i].strip()
            
            # Ignorer les commentaires et lignes vides
            if self._is_comment_line(lines[i]) or not line_stripped:
                i += 1
                continue
            
            # Détecter une boucle
            loop_match = re.search(r'\b(for|foreach|while)\s*\(', line_stripped)
            if loop_match:
                pass  # Loop trouvée
                loop_info = self._extract_loop_info(line_stripped, i + 1)  # +1 car enumerate commence à 1
                if loop_info:
                    # Trouver la fin de la boucle
                    end_line = self._find_loop_end(lines, i)
                    pass  # Fin de boucle trouvée
                    if end_line:
                        loop_info['end_line'] = end_line + 1  # +1 car enumerate commence à 1
                        loops.append(loop_info)
                        pass  # Boucle ajoutée
                        i = end_line + 1
                    else:
                        i += 1
                else:
                    i += 1
            else:
                i += 1
        
        # Analyser les boucles pour trouver les opportunités de fusion
        self._analyze_loop_fusion_opportunities(loops, file_path, lines, issues)

    def _find_loop_end(self, lines: List[str], start_index: int) -> int:
        """Trouver la ligne de fin d'une boucle"""
        brace_count = 0
        found_opening_brace = False
        
        for i in range(start_index, len(lines)):
            line = lines[i].strip()
            
            # Compter les accolades
            for char in line:
                if char == '{':
                    brace_count += 1
                    found_opening_brace = True
                elif char == '}':
                    brace_count -= 1
                    
                    # Si on revient à 0, c'est la fin de la boucle la plus externe
                    if found_opening_brace and brace_count == 0:
                        return i
        
        return None
    
    def _detect_foreach_non_iterable(self, line_stripped: str, line_num: int, file_path: Path, 
                                   lines: List[str], issues: List[Dict[str, Any]]) -> None:
        """Détecter foreach sur une variable non-itérable"""
        foreach_match = re.search(r'foreach\s*\(\s*\$([a-zA-Z_][a-zA-Z0-9_]*)\s+as\s+', line_stripped)
        if foreach_match:
            var_name = foreach_match.group(1)
            # Chercher dans les lignes précédentes si cette variable a été assignée à un scalaire
            for prev_line_num in range(max(0, line_num - 20), line_num):
                if prev_line_num < len(lines):
                    prev_line = lines[prev_line_num].strip()
                    # Détecter assignation à un scalaire (nombre, chaîne, booléen, null)
                    scalar_pattern = rf'\${var_name}\s*=\s*(?:true|false|null|\d+(?:\.\d+)?|["\'][^"\']*["\'])\s*;'
                    if re.search(scalar_pattern, prev_line, re.IGNORECASE):
                        issues.append(self._create_issue(
                            'error.foreach_non_iterable',
                            f'foreach sur la variable non itérable ${var_name} (valeur scalaire affectée)',
                            file_path,
                            line_num,
                            'error',
                            'error',
                            f'Vérifier que ${var_name} est un tableau ou un objet itérable avant d\'utiliser foreach',
                            lines[line_num - 1].strip()
                        ))
                        break
    
    def _detect_count_in_for_loop(self, line_stripped: str, line_num: int, file_path: Path, 
                                 line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter count() dans une condition de boucle for"""
        if re.search(r'for\s*\([^;]*;\s*[^;]*count\s*\(', line_stripped):
            issues.append(self._create_issue(
                'performance.inefficient_loops',
                'Appel de count() dans une condition de boucle for (inefficace)',
                file_path,
                line_num,
                'warning',
                'performance',
                'Stocker count() dans une variable avant la boucle: $length = count($array); for($i = 0; $i < $length; $i++)',
                line.strip()
            ))
    
    def _detect_deeply_nested_loops(self, loop_stack: List[int], line_num: int, file_path: Path, 
                                  line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les boucles trop imbriquées"""
        if len(loop_stack) > 3:
            issues.append(self._create_issue(
                'performance.deeply_nested_loops',
                f'Boucle imbriquée trop profonde (niveau {len(loop_stack)})',
                file_path,
                line_num,
                'warning',
                'performance',
                'Extraire la logique interne en fonction séparée pour réduire la complexité',
                line.strip()
            ))
    
    def _detect_expensive_functions_in_loop(self, line_stripped: str, line_num: int, file_path: Path, 
                                          line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les fonctions coûteuses dans les boucles"""
        if (re.search(r'\b(count|sizeof)\s*\(', line_stripped) and
            not re.search(r'for\s*\(', line_stripped)):  # Éviter double détection
            issues.append(self._create_issue(
                'performance.function_in_loop',
                'Appel de fonction coûteuse (count/sizeof) dans une boucle',
                file_path,
                line_num,
                'warning',
                'performance',
                'Stocker le résultat dans une variable avant la boucle',
                line.strip()
            ))
    
    def _detect_queries_in_loop(self, line_stripped: str, line_num: int, file_path: Path, 
                               line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les requêtes SQL dans les boucles"""
        if re.search(r'\b(mysql_query|mysqli_query|query|execute)\s*\(', line_stripped):
            issues.append(self._create_issue(
                'performance.query_in_loop',
                'Requête de base de données dans une boucle (problème N+1)',
                file_path,
                line_num,
                'error',
                'performance',
                'Extraire la requête hors de la boucle ou utiliser une requête groupée',
                line.strip()
            ))
    
    def _detect_heavy_functions_in_loop(self, line_stripped: str, line_num: int, file_path: Path, 
                                      line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les fonctions lourdes dans les boucles"""
        heavy_functions = [
            ('file_get_contents', 'Lecture de fichier'),
            ('file_put_contents', 'Écriture de fichier'),
            ('glob', 'Recherche de fichiers'),
            ('scandir', 'Lecture de répertoire'),
            ('opendir', 'Ouverture de répertoire'),
            ('readdir', 'Lecture de répertoire'),
            ('curl_exec', 'Requête HTTP/cURL'),
            ('file_exists', 'Vérification d\'existence de fichier'),
            ('is_file', 'Vérification de type de fichier'),
            ('is_dir', 'Vérification de répertoire'),
            ('filemtime', 'Lecture de métadonnées de fichier'),
            ('filesize', 'Lecture de taille de fichier'),
            ('pathinfo', 'Analyse de chemin'),
            ('realpath', 'Résolution de chemin'),
            ('basename', 'Extraction de nom de fichier'),
            ('dirname', 'Extraction de répertoire')
        ]
        
        for func, description in heavy_functions:
            if re.search(rf'\b{func}\s*\(', line_stripped):
                issues.append(self._create_issue(
                    'performance.heavy_function_in_loop',
                    f'{description} dans une boucle peut être très lent',
                    file_path,
                    line_num,
                    'warning',
                    'performance',
                    f'Extraire {func}() hors de la boucle et mettre en cache le résultat',
                    line.strip()
                ))
                break
    
    def _detect_object_creation_in_loop(self, line_stripped: str, line_num: int, file_path: Path, 
                                      line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter la création répétée d'objets dans les boucles"""
        object_patterns = [
            (r'\$\w+\s*=\s*new\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*;', 'new {class}({args})'),
            (r'\$\w+\s*=\s*([A-Za-z_][A-ZaZ0-9_]*)::\s*getInstance\s*\(\s*\)\s*;', '{class}::getInstance()'),
            (r'\$\w+\s*=\s*([A-Za-z_][A-ZaZ0-9_]*)::\s*create\s*\(([^)]*)\)\s*;', '{class}::create({args})'),
            (r'\$\w+\s*=\s*(DateTime|DateTimeImmutable)\s*\(\s*["\'][^"\']*["\']\s*\)\s*;', 'new {class}()'),
            (r'\$\w+\s*=\s*json_decode\s*\(\s*["\'][^"\']*["\']\s*\)\s*;', 'json_decode()'),
            (r'\$\w+\s*=\s*simplexml_load_string\s*\(\s*["\'][^"\']*["\']\s*\)\s*;', 'simplexml_load_string()'),
            (r'\$\w+\s*=\s*DOMDocument\s*\(\s*\)\s*;', 'new DOMDocument()'),
            (r'\$\w+\s*=\s*PDO\s*\(\s*[^)]+\)\s*;', 'new PDO()'),
        ]
        
        for pattern, description in object_patterns:
            match = re.search(pattern, line_stripped)
            if match:
                class_name = match.group(1) if match.groups() else 'Object'
                args = match.group(2) if len(match.groups()) > 1 else ''
                
                # Vérifier si les arguments sont constants (pas de variables)
                if not re.search(r'\$[a-zA-Z_]', args):  # Pas de variables dans les arguments
                    issues.append(self._create_issue(
                        'performance.object_creation_in_loop',
                        f'Création répétée d\'objet {class_name} dans une boucle avec arguments constants',
                        file_path,
                        line_num,
                        'warning',
                        'performance',
                        f'Extraire la création de {class_name} hors de la boucle et réutiliser l\'instance',
                        line.strip()
                    ))
                    break
    
    def _detect_algorithmic_complexity_issues(self, line_stripped: str, line_num: int, file_path: Path, 
                                            line: str, issues: List[Dict[str, Any]], loop_stack: List[int]) -> None:
        """Détecter les problèmes de complexité algorithmique"""
        # Détecter les tris dans les boucles
        sort_functions = ['sort', 'rsort', 'asort', 'arsort', 'ksort', 'krsort', 'usort', 'uasort', 'uksort', 'array_multisort']
        for sort_func in sort_functions:
            if re.search(rf'\b{sort_func}\s*\(', line_stripped):
                issues.append(self._create_issue(
                    'performance.sort_in_loop',
                    f'Fonction de tri {sort_func}() dans une boucle - complexité O(n²log n) ou pire',
                    file_path,
                    line_num,
                    'warning',
                    'performance',
                    f'Extraire le tri {sort_func}() hors de la boucle pour améliorer les performances',
                    line.strip()
                ))
                break
        
        # Détecter recherche linéaire dans boucle
        search_functions = ['in_array', 'array_search', 'array_key_exists']
        for search_func in search_functions:
            if re.search(rf'\b{search_func}\s*\(', line_stripped):
                issues.append(self._create_issue(
                    'performance.linear_search_in_loop',
                    f'Recherche linéaire {search_func}() dans une boucle - complexité O(n²)',
                    file_path,
                    line_num,
                    'warning',
                    'performance',
                    f'Convertir le tableau en clé-valeur ou utiliser array_flip() avant la boucle pour une recherche O(1)',
                    line.strip()
                ))
                break
    
    def _detect_nested_loops_same_array(self, line_stripped: str, line_num: int, file_path: Path, 
                                      line: str, lines: List[str], loop_stack: List[int], 
                                      issues: List[Dict[str, Any]]) -> None:
        """Détecter les boucles imbriquées sur le même tableau (évite les faux positifs sur structures hiérarchiques)"""
        if len(loop_stack) >= 2:
            # Analyse plus précise des boucles foreach
            current_foreach = re.search(r'foreach\s*\(\s*\$([a-zA-Z_][a-zA-Z0-9_]*(?:\->[a-zA-Z_][a-zA-Z0-9_]*)*)\s+as\s+(?:\$([a-zA-Z_][a-zA-Z0-9_]*)\s*=>\s*)?\$([a-zA-Z_][a-zA-Z0-9_]*)', line_stripped)
            if current_foreach:
                current_array = current_foreach.group(1)
                current_key = current_foreach.group(2)  # peut être None
                current_value = current_foreach.group(3)
                
                # Chercher dans les boucles parentes actives (seulement dans la boucle parente directe)
                for prev_line_num in range(max(0, line_num - 10), line_num):
                    if prev_line_num < len(lines):
                        prev_line = lines[prev_line_num].strip()
                        prev_foreach = re.search(r'foreach\s*\(\s*\$([a-zA-Z_][a-zA-Z0-9_]*(?:\->[a-zA-Z_][a-zA-Z0-9_]*)*)\s+as\s+(?:\$([a-zA-Z_][a-zA-Z0-9_]*)\s*=>\s*)?\$([a-zA-Z_][a-zA-Z0-9_]*)', prev_line)
                        if prev_foreach:
                            prev_array = prev_foreach.group(1)
                            prev_key = prev_foreach.group(2)  # peut être None
                            prev_value = prev_foreach.group(3)
                            
                            # Vérifier si c'est vraiment le même tableau exact (pas une structure hiérarchique)
                            if prev_array == current_array:
                                # Éviter les faux positifs pour les patterns hiérarchiques courants
                                if not self._is_hierarchical_pattern(prev_array, prev_key, prev_value, current_array, current_key, current_value):
                                    issues.append(self._create_issue(
                                        'performance.nested_loop_same_array',
                                        f'Boucles imbriquées sur le même tableau ${current_array} - complexité O(n²)',
                                        file_path,
                                        line_num,
                                        'warning',
                                        'performance',
                                        'Revoir l\'algorithme pour éviter le parcours quadratique du même tableau',
                                        line.strip()
                                    ))
                                    break
                            
                            # Arrêter à la première boucle parente trouvée pour éviter les faux positifs
                            break
    
    def _is_hierarchical_pattern(self, outer_array: str, outer_key: str, outer_value: str,
                               inner_array: str, inner_key: str, inner_value: str) -> bool:
        """
        Détecter si les boucles imbriquées représentent un pattern hiérarchique légitime
        
        Exemples de patterns légitimes :
        - foreach ($data as $category => $items) { foreach ($items as $item) {...} }
        - foreach ($this->cards as $type => $cardList) { foreach ($cardList as $card) {...} }
        - foreach ($tree as $node => $children) { foreach ($children as $child) {...} }
        """
        # CRITÈRE PRINCIPAL : Si la boucle interne utilise la valeur de la boucle externe comme tableau
        # C'est probablement un pattern hiérarchique légitime
        if outer_value and inner_array == outer_value:
            return True
            
        # Si les tableaux sont identiques, c'est un vrai problème O(n²)
        if outer_array == inner_array:
            return False
        
        # Patterns hiérarchiques courants avec noms suggérant une hiérarchie
        hierarchical_patterns = [
            # Pattern pluriel/singulier : $categories -> $category, $items -> $item
            (r'(.+)s$', r'\1$'),  # products -> product, items -> item, etc.
            (r'(.+)ies$', r'\1y$'),  # categories -> category, companies -> company
            (r'(.+)ves$', r'\1f$'),  # leaves -> leaf, knives -> knife
            (r'(.+)children$', r'\1child$'),  # children -> child
            
            # Patterns suggérant parent/enfant ou collection/item
            (r'.*(list|array|collection|data|items|cards|records|entries).*', r'.*(item|card|record|entry|element).*'),
            (r'.*(parent|node|tree|group|category|type).*', r'.*(child|item|element|card|record).*'),
        ]
        
        # Vérifier les patterns de nommage hiérarchique entre outer_value et inner_array
        if outer_value and inner_array:
            for pattern_plural, pattern_singular in hierarchical_patterns:
                if (re.match(pattern_plural, outer_value, re.IGNORECASE) and 
                    re.match(pattern_singular, inner_array, re.IGNORECASE)):
                    return True
        
        # Cas spécial : si la boucle externe a une clé et la boucle interne utilise cette valeur
        # C'est probablement hiérarchique (foreach ($array as $key => $subarray))
        if outer_key and outer_value and inner_array == outer_value:
            return True
            
        return False
    
    def _extract_loop_info(self, line_stripped: str, line_num: int) -> Dict[str, Any]:
        """Extraire les informations d'une boucle pour l'analyse de fusion"""
        loop_info = {
            'line_num': line_num,
            'end_line': None,
            'type': None,
            'array_var': None,
            'key_var': None,
            'value_var': None,
            'condition': None,
            'line_content': line_stripped
        }
        
        # Analyser foreach
        foreach_match = re.search(r'foreach\s*\(\s*\$([a-zA-Z_][a-zA-Z0-9_]*(?:\->[a-zA-Z_][a-zA-Z0-9_]*)*)\s+as\s+(?:\$([a-zA-Z_][a-zA-Z0-9_]*)\s*=>\s*)?\$([a-zA-Z_][a-zA-Z0-9_]*)', line_stripped)
        if foreach_match:
            loop_info['type'] = 'foreach'
            loop_info['array_var'] = foreach_match.group(1)
            loop_info['key_var'] = foreach_match.group(2)  # peut être None
            loop_info['value_var'] = foreach_match.group(3)
            return loop_info
        
        # Analyser for
        for_match = re.search(r'for\s*\(\s*([^;]+);\s*([^;]+);\s*([^)]+)\s*\)', line_stripped)
        if for_match:
            loop_info['type'] = 'for'
            loop_info['condition'] = for_match.group(2).strip()
            # Extraire la variable de condition pour détecter l'itération sur un tableau
            array_access_match = re.search(r'\$([a-zA-Z_][a-zA-Z0-9_]*)\[', loop_info['condition'])
            if array_access_match:
                loop_info['array_var'] = array_access_match.group(1)
            return loop_info
        
        # Analyser while
        while_match = re.search(r'while\s*\(\s*([^)]+)\s*\)', line_stripped)
        if while_match:
            loop_info['type'] = 'while'
            loop_info['condition'] = while_match.group(1).strip()
            return loop_info
        
        return None

    def _analyze_loop_fusion_opportunities(self, loops: List[Dict[str, Any]], 
                                         file_path: Path, lines: List[str], 
                                         issues: List[Dict[str, Any]]) -> None:
        """Analyser les boucles pour trouver les opportunités de fusion"""
        if len(loops) < 2:
            return
        
        i = 0
        while i < len(loops) - 1:
            current_loop = loops[i]
            next_loop = loops[i + 1]
            
            # Vérifier si les boucles sont vraiment consécutives (pas de code significatif entre)
            if self._are_loops_consecutive(current_loop, next_loop, lines):
                # Vérifier si les boucles peuvent être fusionnées
                if self._can_loops_be_merged(current_loop, next_loop, lines):
                    self._add_loop_fusion_issue(current_loop, next_loop, file_path, lines, issues)
                    i += 2  # Passer les deux boucles analysées
                else:
                    i += 1
            else:
                i += 1

    def _detect_loop_fusion_opportunities(self, consecutive_loops: List[Dict[str, Any]], 
                                        file_path: Path, lines: List[str], 
                                        issues: List[Dict[str, Any]]) -> None:
        """Détecter les opportunités de fusion de boucles consécutives (méthode de compatibilité)"""
        # Cette méthode est maintenant remplacée par _analyze_loop_fusion_opportunities
        # mais on la garde pour la compatibilité
        pass

    def _are_loops_consecutive(self, loop1: Dict[str, Any], loop2: Dict[str, Any], 
                             lines: List[str]) -> bool:
        """Vérifier si deux boucles sont consécutives (sans code significatif entre)"""
        if not loop1.get('end_line') or not loop2.get('line_num'):
            return False
        
        # Conversion des numéros de ligne (1-based) en indices (0-based)
        start_index = loop1['end_line']  # Index de la première ligne après la première boucle
        end_index = loop2['line_num'] - 2  # Index de la dernière ligne avant la deuxième boucle (-2 car 1-based et on exclut)
        
        # Si end_index < start_index, cela signifie que les boucles sont directement consécutives
        if end_index < start_index:
            return True
        
        # Vérifier qu'il n'y a pas plus de 5 lignes entre les boucles
        if (end_index - start_index + 1) > 5:
            return False
        
        # Vérifier qu'il n'y a pas de code significatif entre les boucles
        for line_index in range(start_index, end_index + 1):
            if line_index < len(lines):
                line = lines[line_index].strip()
                # Ignorer les lignes vides, commentaires et accolades de fermeture
                if (line and 
                    not line.startswith('//') and 
                    not line.startswith('/*') and 
                    not line.startswith('*') and 
                    not line.startswith('#') and
                    line != '}' and
                    line != '?>'):
                    return False
        
        return True

    def _can_loops_be_merged(self, loop1: Dict[str, Any], loop2: Dict[str, Any], 
                           lines: List[str]) -> bool:
        """Vérifier si deux boucles peuvent être fusionnées"""
        # Les boucles doivent être du même type
        if loop1['type'] != loop2['type']:
            return False
        
        # Pour foreach, vérifier qu'elles parcourent le même tableau
        if loop1['type'] == 'foreach':
            if loop1['array_var'] != loop2['array_var']:
                return False
            
            # Vérifier que les variables de boucle sont compatibles
            return self._check_loop_variable_independence(loop1, loop2, lines)
        
        # Pour for, vérifier des conditions similaires
        if loop1['type'] == 'for':
            if loop1['array_var'] and loop2['array_var']:
                return loop1['array_var'] == loop2['array_var']
        
        return False

    def _check_loop_variable_independence(self, loop1: Dict[str, Any], loop2: Dict[str, Any], 
                                        lines: List[str]) -> bool:
        """Vérifier que les variables de boucle sont compatibles pour la fusion"""
        # Variables de la première boucle
        loop1_value = loop1.get('value_var')
        loop1_key = loop1.get('key_var')
        
        # Variables de la deuxième boucle
        loop2_value = loop2.get('value_var')
        loop2_key = loop2.get('key_var')
        
        # Cas 1: Variables exactement identiques - parfait pour la fusion
        if loop1_key == loop2_key and loop1_value == loop2_value:
            return True
        
        # Cas 2: Patterns de variables différents - vérifier compatibilité
        # Par exemple: foreach ($array as $item) vs foreach ($array as $key => $item)
        if (loop1_key is None) != (loop2_key is None):
            return False  # Patterns incompatibles (avec/sans clé)
        
        # Cas 3: Même pattern mais variables différentes - vérifier non-interférence
        # Par exemple: foreach ($array as $a) vs foreach ($array as $b)
        # Ou: foreach ($array as $k1 => $v1) vs foreach ($array as $k2 => $v2)
        if loop1_value != loop2_value or (loop1_key and loop2_key and loop1_key != loop2_key):
            # Vérifier que les variables ne s'interfèrent pas
            return self._check_variable_non_interference(loop1, loop2, lines)
        
        return True

    def _check_variable_non_interference(self, loop1: Dict[str, Any], loop2: Dict[str, Any], 
                                       lines: List[str]) -> bool:
        """Vérifier que les variables des deux boucles ne s'interfèrent pas"""
        # Obtenir le contenu des deux boucles
        loop1_content = self._get_loop_content(loop1, lines)
        loop2_content = self._get_loop_content(loop2, lines)
        
        # Variables de la première boucle
        loop1_vars = set()
        if loop1.get('key_var'):
            loop1_vars.add(loop1['key_var'])
        if loop1.get('value_var'):
            loop1_vars.add(loop1['value_var'])
        
        # Variables de la deuxième boucle
        loop2_vars = set()
        if loop2.get('key_var'):
            loop2_vars.add(loop2['key_var'])
        if loop2.get('value_var'):
            loop2_vars.add(loop2['value_var'])
        
        # Vérifier qu'aucune variable de loop1 n'est utilisée dans loop2
        for var in loop1_vars:
            if var not in loop2_vars:  # Si la variable n'est pas dans loop2_vars
                pattern = rf'\${var}\b'
                if re.search(pattern, loop2_content):
                    return False
        
        # Vérifier qu'aucune variable de loop2 n'est utilisée dans loop1
        for var in loop2_vars:
            if var not in loop1_vars:  # Si la variable n'est pas dans loop1_vars
                pattern = rf'\${var}\b'
                if re.search(pattern, loop1_content):
                    return False
        
        return True

    def _get_loop_content(self, loop_info: Dict[str, Any], lines: List[str]) -> str:
        """Obtenir le contenu d'une boucle"""
        if not loop_info.get('end_line'):
            return ""
        
        start_line = loop_info['line_num']
        end_line = loop_info['end_line']
        
        content_lines = []
        for i in range(start_line, min(end_line, len(lines))):
            content_lines.append(lines[i])
        
        return '\n'.join(content_lines)

    def _add_loop_fusion_issue(self, loop1: Dict[str, Any], loop2: Dict[str, Any], 
                             file_path: Path, lines: List[str], 
                             issues: List[Dict[str, Any]]) -> None:
        """Ajouter un problème de fusion de boucles"""
        array_name = loop1.get('array_var', 'même structure')
        
        # Créer la suggestion de fusion
        fusion_suggestion = self._generate_fusion_suggestion(loop1, loop2, lines)
        
        issues.append(self._create_issue(
            'performance.loop_fusion_opportunity',
            f'Boucles consécutives sur ${array_name} peuvent être fusionnées pour améliorer les performances',
            file_path,
            loop1['line_num'],
            'info',
            'performance',
            f'Fusionner les boucles lignes {loop1["line_num"]} et {loop2["line_num"]} pour réduire les itérations.\n{fusion_suggestion}',
            f'{loop1["line_content"]}\n...\n{loop2["line_content"]}'
        ))

    def _generate_fusion_suggestion(self, loop1: Dict[str, Any], loop2: Dict[str, Any], 
                                  lines: List[str]) -> str:
        """Générer une suggestion de code pour la fusion"""
        if loop1['type'] == 'foreach':
            array_var = loop1['array_var']
            
            # Déterminer les variables à utiliser pour la boucle fusionnée
            # Priorité aux variables avec clé si une des boucles en a une
            loop1_key = loop1.get('key_var')
            loop1_value = loop1.get('value_var', 'value')
            loop2_key = loop2.get('key_var')
            loop2_value = loop2.get('value_var', 'value')
            
            # Choisir les variables pour la fusion
            if loop1_key and loop2_key:
                # Les deux ont des clés, utiliser celles de la première boucle
                key_var = loop1_key
                value_var = loop1_value
            elif loop1_key:
                # Seule la première a une clé
                key_var = loop1_key
                value_var = loop1_value
            elif loop2_key:
                # Seule la deuxième a une clé
                key_var = loop2_key
                value_var = loop2_value
            else:
                # Aucune n'a de clé
                key_var = None
                value_var = loop1_value
            
            # Obtenir le contenu des boucles (sans les lignes de déclaration)
            loop1_body = self._extract_loop_body(loop1, lines)
            loop2_body = self._extract_loop_body(loop2, lines)
            
            # Adapter le contenu si les variables sont différentes
            adapted_loop1_body = self._adapt_loop_body_variables(loop1_body, loop1, key_var, value_var)
            adapted_loop2_body = self._adapt_loop_body_variables(loop2_body, loop2, key_var, value_var)
            
            # Générer la boucle fusionnée
            if key_var:
                foreach_declaration = f"foreach (${array_var} as ${key_var} => ${value_var})"
            else:
                foreach_declaration = f"foreach (${array_var} as ${value_var})"
            
            fusion_code = f"""
Exemple de fusion:
{foreach_declaration} {{
    // Code de la première boucle
{adapted_loop1_body}
    
    // Code de la deuxième boucle  
{adapted_loop2_body}
}}"""
            
            return fusion_code
        
        return "Fusionner le contenu des deux boucles en une seule."

    def _adapt_loop_body_variables(self, body: str, original_loop: Dict[str, Any], 
                                  new_key_var: str, new_value_var: str) -> str:
        """Adapter les variables dans le corps de la boucle"""
        if not body:
            return "    // Corps de boucle"
        
        adapted_body = body
        original_key = original_loop.get('key_var')
        original_value = original_loop.get('value_var')
        
        # Remplacer les variables si nécessaire
        if original_key and new_key_var and original_key != new_key_var:
            # Remplacer $original_key par $new_key_var
            adapted_body = re.sub(rf'\${original_key}\b', f'${new_key_var}', adapted_body)
        
        if original_value and new_value_var and original_value != new_value_var:
            # Remplacer $original_value par $new_value_var
            adapted_body = re.sub(rf'\${original_value}\b', f'${new_value_var}', adapted_body)
        
        return adapted_body

    def _extract_loop_body(self, loop_info: Dict[str, Any], lines: List[str]) -> str:
        """Extraire le corps d'une boucle (sans la ligne de déclaration)"""
        if not loop_info.get('end_line'):
            return "    // Corps de boucle"
        
        start_line = loop_info['line_num']  # Ligne après la déclaration
        end_line = loop_info['end_line'] - 1  # Ligne avant l'accolade fermante
        
        body_lines = []
        brace_count = 0
        found_opening_brace = False
        
        for i in range(start_line - 1, min(end_line, len(lines))):
            line = lines[i].strip()
            
            # Ignorer la ligne de déclaration de la boucle
            if i == start_line - 1:
                # Chercher l'accolade ouvrante
                if '{' in line:
                    found_opening_brace = True
                    # Si la boucle est sur une seule ligne avec {, prendre seulement ce qui suit {
                    after_brace = line.split('{', 1)
                    if len(after_brace) > 1 and after_brace[1].strip():
                        body_lines.append('    ' + after_brace[1].strip())
                continue
            
            if not found_opening_brace and '{' in line:
                found_opening_brace = True
                continue
            
            if found_opening_brace and line and line != '}':
                # Ajouter une indentation si la ligne n'en a pas déjà
                if not line.startswith('    '):
                    body_lines.append('    ' + line)
                else:
                    body_lines.append(line)
        
        return '\n'.join(body_lines) if body_lines else "    // Corps de boucle"
