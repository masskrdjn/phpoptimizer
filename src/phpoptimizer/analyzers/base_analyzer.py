"""
Classe de base pour tous les analyseurs
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any


class BaseAnalyzer(ABC):
    """Classe de base abstraite pour tous les analyseurs PHP"""
    
    def __init__(self, config=None):
        """Initialiser l'analyseur avec la configuration"""
        self.config = config
    
    @abstractmethod
    def analyze(self, content: str, file_path: Path, lines: List[str]) -> List[Dict[str, Any]]:
        """
        Analyser le contenu PHP et retourner une liste d'issues
        
        Args:
            content: Contenu complet du fichier
            file_path: Chemin vers le fichier analysé
            lines: Liste des lignes du fichier
            
        Returns:
            Liste des problèmes détectés sous forme de dictionnaires
        """
        pass
    
    def _create_issue(self, rule_name: str, message: str, file_path: Path, line: int, 
                     severity: str, issue_type: str, suggestion: str, 
                     code_snippet: str, column: int = 0) -> Dict[str, Any]:
        """
        Créer un dictionnaire d'issue standardisé
        
        Args:
            rule_name: Nom de la règle violée
            message: Message décrivant le problème
            file_path: Chemin du fichier
            line: Numéro de ligne
            severity: Sévérité (error, warning, info)
            issue_type: Type de problème (security, performance, error, etc.)
            suggestion: Suggestion de correction
            code_snippet: Extrait de code concerné
            column: Numéro de colonne (optionnel)
            
        Returns:
            Dictionnaire représentant l'issue
        """
        return {
            'rule_name': rule_name,
            'message': message,
            'file_path': str(file_path),
            'line': line,
            'column': column,
            'severity': severity,
            'issue_type': issue_type,
            'suggestion': suggestion,
            'code_snippet': code_snippet
        }
    
    def _is_comment_line(self, line: str) -> bool:
        """Vérifier si une ligne est un commentaire"""
        line_stripped = line.strip()
        return (line_stripped.startswith('//') or 
                line_stripped.startswith('#') or 
                line_stripped.startswith('/*') or
                line_stripped.startswith('*'))
    
    def _is_blade_directive(self, line: str) -> bool:
        """Vérifier si une ligne contient une directive Blade Laravel"""
        blade_directives = {
            # Structures de contrôle
            'if', 'elseif', 'unless', 'else', 'endif', 'endunless',
            'for', 'foreach', 'while', 'endfor', 'endforeach', 'endwhile',
            'switch', 'case', 'break', 'default', 'endswitch',
            
            # Inclusions
            'include', 'includeIf', 'includeWhen', 'includeUnless', 'includeFirst',
            'extends', 'section', 'endsection', 'show', 'stop', 'yield', 'parent',
            'component', 'endcomponent', 'slot', 'endslot',
            
            # Autres
            'csrf', 'method', 'auth', 'guest', 'endauth', 'endguest',
            'can', 'cannot', 'endcan', 'endcannot',
            'push', 'endpush', 'prepend', 'endprepend', 'stack',
            'php', 'endphp', 'json', 'dd', 'dump'
        }
        
        line_stripped = line.strip()
        for directive in blade_directives:
            if f'@{directive}' in line_stripped:
                return True
        return False
    
    def _remove_strings_and_comments(self, line: str) -> str:
        """
        Supprimer les chaînes de caractères et commentaires d'une ligne pour l'analyse
        Version simplifiée qui gère les cas les plus courants
        """
        result = []
        in_single_quote = False
        in_double_quote = False
        in_comment = False
        i = 0
        
        while i < len(line):
            char = line[i]
            
            # Gérer les commentaires
            if not in_single_quote and not in_double_quote:
                if char == '/' and i + 1 < len(line) and line[i + 1] == '/':
                    break  # Reste de la ligne est un commentaire
                elif char == '#':
                    break  # Reste de la ligne est un commentaire
            
            # Gérer les guillemets
            if not in_comment:
                if char == "'" and not in_double_quote:
                    in_single_quote = not in_single_quote
                    result.append(' ')  # Remplacer par espace
                elif char == '"' and not in_single_quote:
                    in_double_quote = not in_double_quote
                    result.append(' ')  # Remplacer par espace
                elif not in_single_quote and not in_double_quote:
                    result.append(char)
                else:
                    result.append(' ')  # Remplacer le contenu des chaînes par des espaces
            
            i += 1
        
        return ''.join(result)
