"""
Analyseur PHP principal refactorisé utilisant des analyseurs spécialisés
"""

import time
from pathlib import Path
from typing import List, Dict, Any

from .config import Config
from .analyzers.base_analyzer import BaseAnalyzer
from .analyzers.loop_analyzer import LoopAnalyzer
from .analyzers.security_analyzer import SecurityAnalyzer
from .analyzers.error_analyzer import ErrorAnalyzer
from .analyzers.performance_analyzer import PerformanceAnalyzer
from .analyzers.memory_analyzer import MemoryAnalyzer
from .analyzers.code_quality_analyzer import CodeQualityAnalyzer
from .analyzers.dead_code_analyzer import DeadCodeAnalyzer
from .analyzers.dynamic_calls_analyzer import DynamicCallsAnalyzer
from .analyzers.type_hint_analyzer import TypeHintAnalyzer


class SimpleAnalyzer:
    """
    Analyseur PHP principal qui coordonne plusieurs analyseurs spécialisés
    """

    def __init__(self, config: Config, exclude_rules: List[str] = None, include_rules: List[str] = None):
        """
        Initialiser l'analyseur avec la configuration et les filtres de règles

        Args:
            config: Configuration de l'analyseur
            exclude_rules: Liste des règles à exclure (noms complets)
            include_rules: Liste des règles à inclure uniquement (noms complets)
        """
        self.config = config
        self.exclude_rules = exclude_rules or []
        self.include_rules = include_rules or []

        # Initialiser les analyseurs spécialisés
        self.analyzers: List[BaseAnalyzer] = [
            LoopAnalyzer(config),
            SecurityAnalyzer(config),
            ErrorAnalyzer(config),
            PerformanceAnalyzer(config),
            MemoryAnalyzer(config),
            CodeQualityAnalyzer(config),
            DeadCodeAnalyzer(config),
            DynamicCallsAnalyzer(config),
            TypeHintAnalyzer(config)
        ]
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyser un fichier PHP
        
        Args:
            file_path: Chemin vers le fichier à analyser
            
        Returns:
            Dictionnaire contenant les résultats d'analyse
        """
        start_time = time.time()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            result = self.analyze_content(content, file_path)
            
            # Transformer le format pour le reporter
            if 'error' in result:
                return {
                    'file_path': str(file_path),
                    'success': False,
                    'error_message': result['error'],
                    'issues': [],
                    'analysis_time': result.get('analysis_time', 0)
                }
            else:
                return {
                    'file_path': str(file_path),
                    'success': True,
                    'issues': result.get('issues', []),
                    'analysis_time': result.get('analysis_time', 0),
                    'stats': result.get('stats', {})
                }
            
        except Exception as e:
            return {
                'file_path': str(file_path),
                'success': False,
                'error_message': f'Erreur lors de la lecture du fichier: {str(e)}',
                'issues': [],
                'analysis_time': time.time() - start_time
            }
    
    def analyze_content(self, content: str, file_path: Path) -> Dict[str, Any]:
        """
        Analyser le contenu d'un fichier PHP
        
        Args:
            content: Contenu du fichier PHP
            file_path: Chemin vers le fichier
            
        Returns:
            Dictionnaire contenant les résultats d'analyse
        """
        start_time = time.time()
        all_issues = []
        
        try:
            lines = content.split('\n')

            # Exécuter chaque analyseur spécialisé
            for analyzer in self.analyzers:
                try:
                    analyzer_issues = analyzer.analyze(content, file_path, lines)
                    all_issues.extend(analyzer_issues)
                except Exception as e:
                    # En cas d'erreur dans un analyseur, on continue avec les
                    # autres et on signale le problème comme une issue
                    all_issues.append({
                        'rule_name': 'analyzer.error',
                        'message': f'Erreur dans {analyzer.__class__.__name__}: {str(e)}',
                        'file_path': str(file_path),
                        'line': 1,
                        'severity': 'error',
                        'issue_type': 'analyzer',
                        'suggestion': 'Vérifier la syntaxe du fichier PHP',
                        'code_snippet': ''
                    })

            # Appliquer les filtres d'inclusion/exclusion de règles
            filtered_issues = []
            for issue in all_issues:
                rule_name = issue.get('rule_name', '')
                
                # Vérifier les filtres par catégorie et poids d'abord
                if not self.config.should_apply_rule(rule_name):
                    continue
                
                # Si include_rules est défini, n'inclure que ces règles
                if self.include_rules:
                    if rule_name not in self.include_rules:
                        continue
                # Sinon, exclure les règles listées
                if self.exclude_rules:
                    if rule_name in self.exclude_rules:
                        continue
                filtered_issues.append(issue)

            # Trier les issues par numéro de ligne
            filtered_issues.sort(key=lambda x: x.get('line', 0))

            # Dédupliquer sur (rule_name, line, message) en restant tolérant
            # aux issues incomplètes
            unique_issues = []
            seen_issues = set()

            for issue in filtered_issues:
                issue_key = (
                    issue.get('rule_name', ''),
                    issue.get('line', 0),
                    issue.get('message', ''),
                )
                if issue_key not in seen_issues:
                    unique_issues.append(issue)
                    seen_issues.add(issue_key)

            analysis_time = time.time() - start_time

            return {
                'file_path': str(file_path),
                'issues': unique_issues,
                'analysis_time': analysis_time,
                'stats': self._calculate_stats(unique_issues)
            }

        except Exception as e:
            # Relancer l'exception pour qu'elle soit capturée par analyze_file
            raise Exception(f'Erreur lors de l\'analyse: {str(e)}')
    
    def _calculate_stats(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculer les statistiques sur les issues détectées
        
        Args:
            issues: Liste des issues détectées
            
        Returns:
            Dictionnaire avec les statistiques
        """
        if not issues:
            return {
                'total_issues': 0,
                'by_severity': {},
                'by_type': {},
                'by_rule': {}
            }
        
        # Compter par sévérité
        by_severity = {}
        for issue in issues:
            severity = issue.get('severity', 'unknown')
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # Compter par type
        by_type = {}
        for issue in issues:
            issue_type = issue.get('issue_type', 'unknown')
            by_type[issue_type] = by_type.get(issue_type, 0) + 1
        
        # Compter par règle
        by_rule = {}
        for issue in issues:
            rule_name = issue.get('rule_name', 'unknown')
            by_rule[rule_name] = by_rule.get(rule_name, 0) + 1
        
        return {
            'total_issues': len(issues),
            'by_severity': by_severity,
            'by_type': by_type,
            'by_rule': by_rule
        }
    
    def get_analyzer_info(self) -> Dict[str, Any]:
        """
        Obtenir des informations sur les analyseurs disponibles
        
        Returns:
            Dictionnaire avec les informations sur les analyseurs
        """
        analyzer_info = {}
        
        for analyzer in self.analyzers:
            analyzer_name = analyzer.__class__.__name__
            analyzer_info[analyzer_name] = {
                'description': analyzer.__doc__.strip() if analyzer.__doc__ else 'Aucune description',
                'module': analyzer.__class__.__module__
            }
        
        return {
            'total_analyzers': len(self.analyzers),
            'analyzers': analyzer_info,
            'version': '2.0.0'
        }
    
    def enable_analyzer(self, analyzer_class_name: str) -> bool:
        """
        Activer un analyseur spécifique
        
        Args:
            analyzer_class_name: Nom de la classe de l'analyseur
            
        Returns:
            True si l'analyseur a été trouvé et activé
        """
        for analyzer in self.analyzers:
            if analyzer.__class__.__name__ == analyzer_class_name:
                # Logique pour activer/désactiver pourrait être ajoutée ici
                return True
        return False
    
    def disable_analyzer(self, analyzer_class_name: str) -> bool:
        """
        Désactiver un analyseur spécifique
        
        Args:
            analyzer_class_name: Nom de la classe de l'analyseur
            
        Returns:
            True si l'analyseur a été trouvé et désactivé
        """
        # Pour l'instant, on garde tous les analyseurs actifs
        # Cette fonctionnalité pourrait être implémentée plus tard
        return False
