"""
Analyseur spécialisé pour la gestion mémoire
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Set

from .base_analyzer import BaseAnalyzer


class MemoryAnalyzer(BaseAnalyzer):
    """Analyseur spécialisé pour les problèmes de gestion mémoire"""
    
    def analyze(self, content: str, file_path: Path, lines: List[str]) -> List[Dict[str, Any]]:
        """Analyser les problèmes de gestion mémoire dans le code PHP"""
        issues = []
        
        # Détecter les problèmes de gestion mémoire
        self._detect_memory_management_issues(content, file_path, lines, issues)
        
        # Analyser ligne par ligne pour d'autres problèmes
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Ignorer les commentaires et directives Blade
            if self._is_comment_line(line) or self._is_blade_directive(line):
                continue
            
            # Détecter les fuites mémoire potentielles
            self._detect_memory_leaks(line_stripped, line_num, file_path, line, issues)
            
            # Détecter l'utilisation excessive de mémoire
            self._detect_excessive_memory_usage(line_stripped, line_num, file_path, line, issues)
            
            # Détecter les problèmes de références circulaires
            self._detect_circular_references(line_stripped, line_num, file_path, line, issues)
        
        return issues
    
    def _detect_memory_management_issues(self, content: str, file_path: Path, lines: List[str], 
                                       issues: List[Dict[str, Any]]) -> None:
        """Détecter les problèmes de gestion mémoire (oublis de unset())"""
        # Patterns pour détecter les gros tableaux
        large_array_patterns = [
            (r'\$(\w+)\s*=\s*range\s*\(\s*\d+\s*,\s*(\d+)\s*\)', 2),  # range(1, 1000000)
            (r'\$(\w+)\s*=\s*array_fill\s*\(\s*\d+\s*,\s*(\d+)\s*,', 2),  # array_fill(0, 500000, 'data')
            (r'\$(\w+)\s*=\s*array_fill_keys\s*\(\s*range\s*\(\s*\d+\s*,\s*(\d+)\s*\)', 2),  # array_fill_keys
            (r'\$(\w+)\s*=\s*str_repeat\s*\(\s*[\'"][^\'"]*[\'"]\s*,\s*(\d+)\s*\)', 2),  # str_repeat('x', 100000)
        ]
        
        # Variables contenant potentiellement de gros tableaux/données
        large_variables: Set[str] = set()
        
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Détecter les déclarations de gros tableaux
            for pattern, size_group in large_array_patterns:
                match = re.search(pattern, line_stripped)
                if match:
                    var_name = match.group(1)  # Nom de variable
                    size = int(match.group(size_group))  # Taille
                    
                    # Considérer comme "gros" si > 10000 éléments
                    if size > 10000:
                        large_variables.add(var_name)
                        
                        # Vérifier si cette variable est libérée avec unset()
                        if not self._is_variable_unset(content, var_name, line_num):
                            issues.append(self._create_issue(
                                'performance.memory_management',
                                f'Gros tableau ${var_name} ({size} éléments) non libéré avec unset()',
                                file_path,
                                line_num,
                                'warning',
                                'performance',
                                f'Ajouter unset(${var_name}) après utilisation pour libérer la mémoire',
                                line.strip()
                            ))
            
            # Détecter les allocations de gros tableaux avec des boucles
            if re.search(r'for\s*\(\s*\$\w+\s*=\s*0\s*;\s*\$\w+\s*<\s*(\d+)', line_stripped):
                loop_size_match = re.search(r'for\s*\(\s*\$\w+\s*=\s*0\s*;\s*\$\w+\s*<\s*(\d+)', line_stripped)
                if loop_size_match:
                    loop_size = int(loop_size_match.group(1))
                    if loop_size > 10000:
                        # Chercher les variables assignées dans cette boucle
                        for i in range(line_num, min(line_num + 10, len(lines))):
                            if i < len(lines):
                                inner_line = lines[i].strip()
                                if re.search(r'\$\w+\[\s*\$\w+\s*\]\s*=', inner_line):
                                    var_match = re.search(r'\$(\w+)\[', inner_line)
                                    if var_match:
                                        var_name = var_match.group(1)
                                        large_variables.add(var_name)
                                        
                                        if not self._is_variable_unset(content, var_name, i + 1):
                                            issues.append(self._create_issue(
                                                'performance.memory_management',
                                                f'Tableau ${var_name} rempli dans une boucle ({loop_size} itérations) non libéré',
                                                file_path,
                                                i + 1,
                                                'warning',
                                                'performance',
                                                f'Ajouter unset(${var_name}) après utilisation',
                                                inner_line
                                            ))
                                        break
    
    def _detect_memory_leaks(self, line_stripped: str, line_num: int, file_path: Path, 
                            line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les fuites mémoire potentielles"""
        # Ressources non libérées
        resource_patterns = [
            ('fopen', 'fclose', 'Fichier ouvert non fermé'),
            ('curl_init', 'curl_close', 'Session cURL non fermée'),
            ('mysqli_connect', 'mysqli_close', 'Connexion MySQL non fermée'),
            ('imagecreate', 'imagedestroy', 'Image GD non détruite'),
            ('opendir', 'closedir', 'Répertoire ouvert non fermé')
        ]
        
        for open_func, close_func, description in resource_patterns:
            if re.search(rf'\b{open_func}\s*\(', line_stripped):
                # Vérifier si la ressource est fermée dans le même contexte de fonction
                is_closed = self._is_resource_properly_closed(line_num, file_path, open_func, close_func)
                if not is_closed:
                    issues.append(self._create_issue(
                        'performance.resource_leak',
                        f'{description} - vérifier que {close_func}() est appelé',
                        file_path,
                        line_num,
                        'warning',
                        'performance',
                        f'S\'assurer d\'appeler {close_func}() après utilisation de {open_func}()',
                        line.strip()
                    ))
                break

    def _is_resource_properly_closed(self, open_line_num: int, file_path: Path, 
                                   open_func: str, close_func: str) -> bool:
        """Vérifier si une ressource est correctement fermée dans le même contexte"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Trouver le début et la fin de la fonction qui contient l'ouverture de ressource
            function_start, function_end = self._find_function_bounds(lines, open_line_num - 1)
            
            if function_start is None or function_end is None:
                # Si on ne trouve pas les limites de fonction, on assume qu'il n'y a pas de fuite
                # pour éviter les faux positifs (comme dans un scope global)
                return True
            
            # Extraire le nom de la variable de ressource depuis la ligne d'ouverture
            open_line = lines[open_line_num - 1]
            var_match = re.search(rf'\$([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*{open_func}\s*\(', open_line)
            if not var_match:
                # Si on ne peut pas extraire le nom de variable, on assume qu'il n'y a pas de fuite
                return True
            
            resource_var = var_match.group(1)
            
            # Chercher l'appel de fermeture dans le scope de la fonction
            for i in range(function_start, function_end):
                if i < len(lines):
                    line = lines[i].strip()
                    if re.search(rf'{close_func}\s*\(\s*\${resource_var}\s*\)', line):
                        return True
            
            # Si on arrive ici, la ressource n'est pas fermée dans la fonction
            return False
            
        except Exception:
            # En cas d'erreur, on assume qu'il n'y a pas de fuite pour éviter les faux positifs
            return True
    
    def _find_function_bounds(self, lines: List[str], open_line_idx: int) -> tuple:
        """Trouver les limites de la fonction qui contient la ligne donnée"""
        function_start = None
        function_end = None
        
        # Chercher le début de la fonction en remontant
        for i in range(open_line_idx, -1, -1):
            line = lines[i].strip()
            if re.match(r'\s*(public|private|protected)?\s*function\s+\w+\s*\(', line):
                function_start = i
                break
        
        if function_start is None:
            return None, None
        
        # Chercher la fin de la fonction en comptant les accolades
        brace_count = 0
        found_opening_brace = False
        
        for i in range(function_start, len(lines)):
            line = lines[i]
            
            for char in line:
                if char == '{':
                    brace_count += 1
                    found_opening_brace = True
                elif char == '}':
                    brace_count -= 1
                    if found_opening_brace and brace_count == 0:
                        function_end = i + 1
                        return function_start, function_end
        
        return function_start, len(lines)
    
    def _detect_excessive_memory_usage(self, line_stripped: str, line_num: int, file_path: Path, 
                                     line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter l'utilisation excessive de mémoire"""
        # Opérations potentiellement gourmandes en mémoire
        memory_intensive_patterns = [
            (r'file_get_contents\s*\([^)]*http', 'Lecture de fichiers distants sans limite de taille'),
            (r'file\s*\([^)]*\.log', 'Lecture complète de fichiers de log potentiellement volumineux'),
            (r'explode\s*\([^)]*,\s*file_get_contents', 'Explosion d\'un fichier entier en mémoire'),
            (r'str_replace\s*\([^)]*,\s*[^,]*,\s*file_get_contents', 'Remplacement sur fichier entier en mémoire'),
            (r'array_map\s*\([^)]*,\s*range\s*\(\s*\d+\s*,\s*\d{5,}', 'array_map sur un très grand range'),
            (r'array_fill\s*\(\s*\d+\s*,\s*\d{6,}', 'array_fill avec plus de 100000 éléments')
        ]
        
        for pattern, description in memory_intensive_patterns:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                issues.append(self._create_issue(
                    'performance.excessive_memory',
                    f'Utilisation mémoire potentiellement excessive: {description}',
                    file_path,
                    line_num,
                    'warning',
                    'performance',
                    'Considérer un traitement par blocs ou streaming pour économiser la mémoire',
                    line.strip()
                ))
                break
        
        # Patterns spécifiques aux gros tableaux en mémoire
        if re.search(r'array_merge\s*\([^)]*\$[a-zA-Z_][a-zA-Z0-9_]*\s*,\s*\$[a-zA-Z_][a-zA-Z0-9_]*\)', line_stripped):
            issues.append(self._create_issue(
                'performance.array_merge_memory',
                'array_merge() peut doubler l\'utilisation mémoire temporairement',
                file_path,
                line_num,
                'info',
                'performance',
                'Considérer l\'opérateur + ou des boucles pour économiser la mémoire',
                line.strip()
            ))
    
    def _detect_circular_references(self, line_stripped: str, line_num: int, file_path: Path, 
                                  line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les références circulaires potentielles"""
        # Assignation d'objets à eux-mêmes ou références mutuelles
        circular_patterns = [
            (r'\$([a-zA-Z_][a-zA-Z0-9_]*)\s*->\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\$\1', 'Auto-référence d\'objet'),
            (r'\$([a-zA-Z_][a-zA-Z0-9_]*)\[\s*[\'"]?(\w+)[\'"]?\s*\]\s*=\s*&?\s*\$\1', 'Référence circulaire dans tableau'),
            (r'\$([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*&\s*\$\1', 'Référence circulaire directe')
        ]
        
        for pattern, description in circular_patterns:
            if re.search(pattern, line_stripped):
                issues.append(self._create_issue(
                    'performance.circular_reference',
                    f'Référence circulaire potentielle: {description}',
                    file_path,
                    line_num,
                    'warning',
                    'performance',
                    'Éviter les références circulaires qui peuvent causer des fuites mémoire',
                    line.strip()
                ))
                break
    
    def _is_variable_unset(self, content: str, var_name: str, after_line: int) -> bool:
        """
        Vérifier si une variable est libérée avec unset() après sa déclaration.
        
        Args:
            content: Le contenu du fichier PHP
            var_name: Le nom de la variable à rechercher (sans le $)
            after_line: La ligne après laquelle commencer la recherche (1-indexed)
            
        Returns:
            True si un unset() de cette variable est trouvé dans la portée actuelle
        """
        lines = content.split('\n')
        
        # Calculer le niveau d'accolades initial pour déterminer la portée
        initial_brace_level = self._calculate_brace_level(lines, after_line - 1)
        
        # Chercher unset() dans les lignes suivantes
        for i in range(after_line, len(lines)):
            line = lines[i].strip()
            
            # Ignorer les lignes vides et les commentaires
            if not line or self._is_comment_line(line):
                continue
            
            # Vérifier si la variable est dans un unset()
            unset_patterns = [
                rf'unset\s*\(\s*\${var_name}\b',  # unset($var)
                rf'unset\s*\([^)]*,\s*\${var_name}\b',  # unset($other, $var)
                rf'unset\s*\(\s*\${var_name}\s*,',  # unset($var, $other)
            ]
            
            for pattern in unset_patterns:
                if re.search(pattern, line):
                    return True
            
            # Calculer le niveau d'accolades actuel
            current_brace_level = self._calculate_brace_level(lines, i)
            
            # Ne s'arrêter que si on sort vraiment de la fonction/classe
            if current_brace_level < initial_brace_level - 1:
                break
            
            # Arrêter à la fin d'une fonction ou classe
            if re.search(r'^\s*}\s*$', line):
                if self._is_end_of_function_or_class(lines, i, initial_brace_level):
                    break
        
        return False
    
    def _calculate_brace_level(self, lines: List[str], line_index: int) -> int:
        """
        Calculer le niveau d'imbrication des accolades jusqu'à une ligne donnée.
        
        Args:
            lines: Liste des lignes du fichier
            line_index: Index de la ligne (0-based)
            
        Returns:
            Le niveau d'accolades (nombre d'accolades ouvrantes - fermantes)
        """
        brace_count = 0
        
        for i in range(min(line_index + 1, len(lines))):
            line = lines[i]
            
            # Ignorer les accolades dans les chaînes de caractères et commentaires
            line_clean = self._remove_strings_and_comments(line)
            
            # Compter les accolades
            brace_count += line_clean.count('{') - line_clean.count('}')
        
        return brace_count
    
    def _is_end_of_function_or_class(self, lines: List[str], line_index: int, initial_brace_level: int) -> bool:
        """
        Déterminer si une accolade fermante marque la fin d'une fonction ou classe.
        
        Args:
            lines: Liste des lignes du fichier
            line_index: Index de la ligne avec l'accolade fermante
            initial_brace_level: Niveau d'accolades initial
            
        Returns:
            True si c'est la fin d'une fonction ou classe
        """
        current_brace_level = self._calculate_brace_level(lines, line_index)
        
        # Si le niveau d'accolades est significativement plus bas, c'est probablement la fin d'une fonction/classe
        return current_brace_level < initial_brace_level - 1
