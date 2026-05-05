"""
Analyseur pour la détection d'appels dynamiques optimisables.

Détecte les cas où des appels de méthodes ou fonctions dynamiques peuvent être 
remplacés par des appels directs pour améliorer les performances.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from .base_analyzer import BaseAnalyzer


class DynamicCallsAnalyzer(BaseAnalyzer):
    """Analyseur pour la réduction des appels dynamiques."""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.name = "Dynamic Calls Analyzer"
        self.description = "Détecte les appels dynamiques qui peuvent être optimisés"
    def analyze(self, content: str, file_path: Path, lines: List[str]) -> List[Dict[str, Any]]:
        """
        Analyse un fichier pour détecter les appels dynamiques optimisables.
        
        Args:
            content: Contenu complet du fichier
            file_path: Chemin du fichier à analyser
            lines: Liste des lignes du fichier
            
        Returns:
            Liste des problèmes détectés sous forme de dictionnaires
        """
        issues = []
        
        # Stocker les assignations de variables pour détecter les valeurs constantes
        variable_assignments = {}
        
        # Première passe : détecter les assignations de variables constantes
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Ignorer les commentaires et lignes vides
            if self._is_comment_line(line) or not line_stripped:
                continue
                
            # Détecter les assignations simples avec valeurs constantes
            self._track_variable_assignment(line_stripped, line_num, variable_assignments)
        
        # Deuxième passe : détecter les appels dynamiques
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Ignorer les commentaires et lignes vides
            if self._is_comment_line(line) or not line_stripped:
                continue
            
            # Détecter les appels de méthodes dynamiques
            method_issue = self._analyze_dynamic_method_call(line_stripped, line_num, file_path, 
                                                           variable_assignments, line)
            if method_issue:
                issues.append(method_issue)
            
            # Détecter les appels de fonctions dynamiques
            function_issue = self._analyze_dynamic_function_call(line_stripped, line_num, file_path, 
                                                               variable_assignments, line)
            if function_issue:
                issues.append(function_issue)
            
        return issues
    
    def _track_variable_assignment(self, line_stripped: str, line_num: int, 
                                 variable_assignments: Dict[str, Dict[str, Any]]):
        """Suit les assignations de variables pour détecter les valeurs constantes."""
        try:
            # Pattern pour détecter les assignations simples : $var = 'value' ou $var = "value"
            pattern = r'\$([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*["\']([^"\']+)["\']'
            match = re.search(pattern, line_stripped)
            
            if match:
                var_name = match.group(1)
                value = match.group(2)
                
                # Vérifier que ce n'est pas une réassignation (il y avait déjà une assignation)
                if var_name in variable_assignments:
                    # C'est une réassignation, marquer comme non-constante
                    variable_assignments[var_name]['is_constant'] = False
                    variable_assignments[var_name]['confidence'] = 0.1
                else:
                    # Première assignation
                    variable_assignments[var_name] = {
                        'value': value,
                        'line': line_num,
                        'is_constant': True,
                        'confidence': 0.9
                    }
        except Exception:
            pass
    
    def _analyze_dynamic_method_call(self, line_stripped: str, line_num: int, file_path: Path,
                                   variable_assignments: Dict[str, Dict[str, Any]], 
                                   original_line: str) -> Optional[Dict[str, Any]]:
        """Analyse un appel de méthode pour détecter s'il est dynamique."""
        try:
            # Pattern pour appel de méthode dynamique : $object->$method(...)
            pattern = r'(\$[a-zA-Z_][a-zA-Z0-9_]*)\s*->\s*(\$[a-zA-Z_][a-zA-Z0-9_]*)\s*\('
            match = re.search(pattern, line_stripped)
            
            if match:
                object_var = match.group(1)
                method_var = match.group(2)[1:]  # Enlever le $
                
                # Vérifier si on connaît la valeur de la variable méthode et si elle est constante
                if (method_var in variable_assignments and 
                    variable_assignments[method_var].get('is_constant', False)):
                    
                    assignment = variable_assignments[method_var]
                    method_name = assignment['value']
                    confidence = assignment['confidence']
                    
                    # Seulement signaler si le niveau de confiance est élevé
                    if confidence >= 0.8:
                        # Extraire les paramètres s'il y en a
                        params_match = re.search(r'\((.*?)\)', line_stripped)
                        params = params_match.group(1) if params_match else ''
                        
                        original_call = f"{object_var}->${method_var}({params})"
                        suggested_call = f"{object_var}->{method_name}({params})"
                        
                        return self._create_issue(
                            'performance.dynamic_method_call',
                            f'Appel de méthode dynamique détecté : peut être remplacé par un appel direct',
                            file_path,
                            line_num,
                            'info',
                            'performance',
                            f'Remplacer "{original_call}" par "{suggested_call}" pour améliorer les performances',
                            original_line.strip()
                        )
        except Exception:
            pass
        
        return None
    
    def _analyze_dynamic_function_call(self, line_stripped: str, line_num: int, file_path: Path,
                                     variable_assignments: Dict[str, Dict[str, Any]], 
                                     original_line: str) -> Optional[Dict[str, Any]]:
        """Analyse un appel de fonction pour détecter s'il est dynamique."""
        try:
            # Pattern pour appel de fonction dynamique : $function(...)
            # Exclure les appels de méthodes ($obj->$method) déjà traités
            pattern = r'^[^>]*(\$[a-zA-Z_][a-zA-Z0-9_]*)\s*\('
            match = re.search(pattern, line_stripped)
            
            if match and '->' not in line_stripped[:match.start()]:
                func_var = match.group(1)[1:]  # Enlever le $
                
                # Vérifier si on connaît la valeur de la variable fonction et si elle est constante
                if (func_var in variable_assignments and 
                    variable_assignments[func_var].get('is_constant', False)):
                    
                    assignment = variable_assignments[func_var]
                    func_name = assignment['value']
                    confidence = assignment['confidence']
                    
                    # Seulement signaler si le niveau de confiance est élevé
                    if confidence >= 0.8:
                        # Extraire les paramètres s'il y en a
                        params_match = re.search(r'\((.*?)\)', line_stripped)
                        params = params_match.group(1) if params_match else ''
                        
                        original_call = f"${func_var}({params})"
                        suggested_call = f"{func_name}({params})"
                        
                        return self._create_issue(
                            'performance.dynamic_function_call',
                            f'Appel de fonction dynamique détecté : peut être remplacé par un appel direct',
                            file_path,
                            line_num,
                            'info',
                            'performance',
                            f'Remplacer "{original_call}" par "{suggested_call}" pour améliorer les performances',
                            original_line.strip()
                        )
        except Exception:
            pass
        
        return None
