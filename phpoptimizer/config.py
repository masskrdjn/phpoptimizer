"""
Configuration du système PHP Optimizer
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from enum import Enum


class SeverityLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class RuleCategory(Enum):
    """Catégories de règles d'optimisation"""
    SECURITY = "security"
    ERROR = "error" 
    PERFORMANCE_CRITICAL = "performance.critical"
    PERFORMANCE_GENERAL = "performance.general"
    MEMORY = "memory"
    CODE_QUALITY = "code_quality"
    PSR = "psr"


class SeverityWeight(Enum):
    """Poids de sévérité pour le filtrage"""
    CRITICAL = 4  # Problèmes de sécurité
    HIGH = 3      # Erreurs bloquantes ou performance majeure
    MEDIUM = 2    # Optimisations importantes
    LOW = 1       # Qualité de code
    VERY_LOW = 0  # Standards de formatage


@dataclass
class RuleConfig:
    """Configuration d'une règle d'optimisation"""
    enabled: bool = True
    severity: SeverityLevel = SeverityLevel.WARNING
    category: RuleCategory = RuleCategory.CODE_QUALITY
    weight: SeverityWeight = SeverityWeight.LOW
    params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.params is None:
            self.params = {}


class Config:
    """Gestionnaire de configuration pour PHP Optimizer"""
    
    def __init__(self):
        self.severity_level = SeverityLevel.INFO
        self.rules: Dict[str, RuleConfig] = {}
        self.excluded_paths: List[str] = []
        self.included_extensions: List[str] = ['.php']
        self.max_file_size: int = 10 * 1024 * 1024  # 10MB
        self.php_version: str = "8.0"  # Version PHP cible par défaut
        
        # Nouveaux filtres par catégorie et poids
        self.included_categories: List[RuleCategory] = []
        self.excluded_categories: List[RuleCategory] = []
        self.min_severity_weight: SeverityWeight = SeverityWeight.VERY_LOW
        
        # Initialiser les règles par défaut
        self._init_default_rules()
    
    def _init_default_rules(self):
        """Initialiser les règles par défaut.

        Chaque règle est nommée selon la convention ``domaine.nom_precis``.
        Toute règle émise par un analyseur doit être déclarée ici, sinon elle
        sera filtrée par :py:meth:`should_apply_rule`.
        """
        SECURITY = RuleCategory.SECURITY
        ERROR = RuleCategory.ERROR
        PERF_CRITICAL = RuleCategory.PERFORMANCE_CRITICAL
        PERF_GENERAL = RuleCategory.PERFORMANCE_GENERAL
        MEMORY = RuleCategory.MEMORY
        CODE_QUALITY = RuleCategory.CODE_QUALITY
        PSR = RuleCategory.PSR

        INFO = SeverityLevel.INFO
        WARNING = SeverityLevel.WARNING
        ERR = SeverityLevel.ERROR

        CRITICAL = SeverityWeight.CRITICAL
        HIGH = SeverityWeight.HIGH
        MEDIUM = SeverityWeight.MEDIUM
        LOW = SeverityWeight.LOW
        VERY_LOW = SeverityWeight.VERY_LOW

        def rule(severity, category, weight, params=None):
            return RuleConfig(enabled=True, severity=severity, category=category,
                              weight=weight, params=params or {})

        default_rules = {
            # ───────── Sécurité (poids critique) ─────────
            'security.sql_injection':           rule(ERR, SECURITY, CRITICAL),
            'security.xss_vulnerability':       rule(ERR, SECURITY, CRITICAL),
            'security.weak_password_hashing':   rule(ERR, SECURITY, CRITICAL),
            'security.file_inclusion':          rule(ERR, SECURITY, CRITICAL),
            'security.dangerous_function':      rule(WARNING, SECURITY, CRITICAL),
            'security.authentication':          rule(WARNING, SECURITY, CRITICAL),
            'security.configuration':           rule(WARNING, SECURITY, HIGH),
            'security.sensitive_data_exposure': rule(WARNING, SECURITY, HIGH),

            # ───────── Erreurs / bugs probables (poids élevé) ─────────
            'error.foreach_non_iterable':        rule(ERR, ERROR, HIGH),
            'error.syntax_parentheses':          rule(ERR, ERROR, HIGH),
            'error.syntax_braces':               rule(ERR, ERROR, HIGH),
            'error.syntax_semicolon':            rule(ERR, ERROR, HIGH),
            'error.unclosed_quotes':             rule(ERR, ERROR, HIGH),
            'error.null_method_call':            rule(WARNING, ERROR, HIGH),
            'error.uninitialized_variable':      rule(WARNING, ERROR, HIGH),
            'error.incorrect_argument_count':    rule(WARNING, ERROR, HIGH),
            'error.assignment_in_condition':     rule(WARNING, ERROR, HIGH),
            'error.typo':                        rule(WARNING, ERROR, MEDIUM),
            'error.string_math_operation':       rule(WARNING, ERROR, HIGH),
            'error.type_comparison':             rule(INFO, ERROR, MEDIUM),
            'error.always_true_condition':       rule(WARNING, ERROR, MEDIUM),
            'error.return_in_loop':              rule(INFO, ERROR, MEDIUM),

            # ───────── Code mort (poids élevé, classés en erreurs) ─────────
            'dead_code.unreachable_after_return': rule(WARNING, ERROR, HIGH),
            'dead_code.unreachable_after_break':  rule(WARNING, ERROR, HIGH),
            'dead_code.always_false_condition':   rule(WARNING, ERROR, HIGH),

            # ───────── Performance critique (poids élevé) ─────────
            'performance.inefficient_loops':       rule(WARNING, PERF_CRITICAL, HIGH,
                                                        {'max_nested_loops': 3}),
            'performance.algorithmic_complexity':  rule(WARNING, PERF_CRITICAL, HIGH),
            'performance.deeply_nested_loops':     rule(WARNING, PERF_CRITICAL, HIGH),
            'performance.nested_loop_same_array':  rule(WARNING, PERF_CRITICAL, HIGH),
            'performance.linear_search_in_loop':   rule(WARNING, PERF_CRITICAL, HIGH),
            'performance.sort_in_loop':            rule(WARNING, PERF_CRITICAL, HIGH),
            'performance.heavy_function_in_loop':  rule(WARNING, PERF_CRITICAL, HIGH),
            'performance.query_in_loop':           rule(WARNING, PERF_CRITICAL, HIGH),
            'performance.expensive_function':      rule(INFO, PERF_CRITICAL, MEDIUM),
            'performance.function_in_loop':        rule(INFO, PERF_CRITICAL, MEDIUM),
            'performance.object_creation_in_loop': rule(WARNING, PERF_CRITICAL, HIGH),
            'performance.loop_fusion_opportunity': rule(INFO, PERF_CRITICAL, MEDIUM),
            'performance.superglobal_access_in_loop': rule(INFO, PERF_CRITICAL, MEDIUM),

            # ───────── Performance générale (poids moyen) ─────────
            'performance.constant_propagation':    rule(INFO, PERF_GENERAL, MEDIUM),
            'performance.repeated_calculations':   rule(WARNING, PERF_GENERAL, MEDIUM),
            'performance.repetitive_array_access': rule(INFO, PERF_GENERAL, MEDIUM,
                                                        {'min_occurrences': 3}),
            'performance.dynamic_method_call':     rule(INFO, PERF_GENERAL, MEDIUM),
            'performance.dynamic_function_call':   rule(INFO, PERF_GENERAL, MEDIUM),
            'performance.string_concatenation':    rule(INFO, PERF_GENERAL, MEDIUM),
            'performance.regex_performance':       rule(INFO, PERF_GENERAL, MEDIUM),
            'performance.regex_overkill':          rule(INFO, PERF_GENERAL, LOW),
            'performance.count_vs_empty':          rule(INFO, PERF_GENERAL, LOW),
            'performance.strlen_vs_empty':         rule(INFO, PERF_GENERAL, LOW),
            'performance.substr_first_char':       rule(INFO, PERF_GENERAL, LOW),
            'performance.array_push_single':       rule(INFO, PERF_GENERAL, LOW),
            'performance.array_merge_single':      rule(INFO, PERF_GENERAL, LOW),
            'performance.unprepared_query':        rule(WARNING, PERF_GENERAL, MEDIUM),
            'performance.inefficient_file_reading': rule(INFO, PERF_GENERAL, MEDIUM),
            'performance.repeated_file_checks':    rule(INFO, PERF_GENERAL, MEDIUM),

            # ───────── Mémoire (poids moyen) ─────────
            'performance.memory_management':       rule(WARNING, MEMORY, MEDIUM,
                                                        {'max_array_size': 1000}),
            'performance.large_arrays':            rule(WARNING, MEMORY, MEDIUM,
                                                        {'max_array_size': 1000}),
            'performance.excessive_memory':        rule(WARNING, MEMORY, MEDIUM),
            'performance.array_merge_memory':      rule(INFO, MEMORY, MEDIUM),
            'performance.resource_leak':           rule(WARNING, MEMORY, HIGH),
            'performance.circular_reference':      rule(WARNING, MEMORY, MEDIUM),
            'performance.unused_variables':        rule(INFO, MEMORY, MEDIUM),
            'performance.unused_global_variable':  rule(INFO, MEMORY, MEDIUM),
            'performance.global_could_be_local':   rule(INFO, MEMORY, MEDIUM),

            # ───────── Qualité de code (poids faible) ─────────
            'performance.missing_parameter_type':  rule(INFO, CODE_QUALITY, LOW),
            'performance.missing_return_type':     rule(INFO, CODE_QUALITY, LOW),
            'performance.mixed_type_opportunity':  rule(INFO, CODE_QUALITY, LOW),
            'best_practices.function_complexity':  rule(WARNING, CODE_QUALITY, LOW,
                                                        {'max_complexity': 10}),
            'best_practices.missing_documentation': rule(INFO, CODE_QUALITY, LOW),
            'best_practices.missing_docstring':    rule(INFO, CODE_QUALITY, LOW),
            'best_practices.too_many_parameters':  rule(INFO, CODE_QUALITY, LOW,
                                                        {'max_parameters': 5}),
            'best_practices.complex_condition':    rule(INFO, CODE_QUALITY, LOW),
            'best_practices.function_naming':      rule(INFO, CODE_QUALITY, LOW),

            # ───────── Erreur interne d'un analyseur ─────────
            'analyzer.error': rule(ERR, ERROR, CRITICAL),

            # ───────── PSR (poids très faible) ─────────
            'best_practices.psr_compliance':       rule(INFO, PSR, VERY_LOW),
            'best_practices.line_length':          rule(INFO, PSR, VERY_LOW,
                                                        {'max_line_length': 120}),
            'best_practices.naming':               rule(INFO, PSR, VERY_LOW),
            'best_practices.brace_style':          rule(INFO, PSR, VERY_LOW),
            'best_practices.mixed_indentation':    rule(INFO, PSR, VERY_LOW),
            'best_practices.multiple_statements':  rule(INFO, PSR, VERY_LOW),
        }

        self.rules.update(default_rules)
    
    def load_rules_file(self, file_path: Path):
        """Charger les règles depuis un fichier JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Mettre à jour la configuration
            if 'severity_level' in data:
                self.severity_level = SeverityLevel(data['severity_level'])
            
            if 'excluded_paths' in data:
                self.excluded_paths = data['excluded_paths']
            
            if 'rules' in data:
                for rule_name, rule_data in data['rules'].items():
                    if rule_name in self.rules:
                        # Mettre à jour la règle existante
                        self.rules[rule_name].enabled = rule_data.get('enabled', True)
                        self.rules[rule_name].severity = SeverityLevel(
                            rule_data.get('severity', 'warning')
                        )
                        self.rules[rule_name].params.update(
                            rule_data.get('params', {})
                        )
                        
        except Exception as e:
            raise ValueError(f"Erreur lors du chargement du fichier de règles: {e}")
    
    def save_default_config(self, file_path: Path):
        """Sauvegarder la configuration par défaut dans un fichier"""
        config_data = {
            'severity_level': self.severity_level.value,
            'excluded_paths': self.excluded_paths,
            'included_extensions': self.included_extensions,
            'max_file_size': self.max_file_size,
            'rules': {}
        }
        
        # Convertir les règles en dictionnaire
        for rule_name, rule_config in self.rules.items():
            config_data['rules'][rule_name] = {
                'enabled': rule_config.enabled,
                'severity': rule_config.severity.value,
                'params': rule_config.params
            }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    def set_severity_level(self, level: str):
        """Définir le niveau de sévérité minimum"""
        self.severity_level = SeverityLevel(level)
    
    def is_rule_enabled(self, rule_name: str) -> bool:
        """Vérifier si une règle est activée"""
        return rule_name in self.rules and self.rules[rule_name].enabled
    
    def get_rule_config(self, rule_name: str) -> RuleConfig:
        """Obtenir la configuration d'une règle"""
        return self.rules.get(rule_name, RuleConfig())
    
    def should_process_file(self, file_path: Path) -> bool:
        """Vérifier si un fichier doit être traité"""
        # Vérifier l'extension
        if file_path.suffix not in self.included_extensions:
            return False
        
        # Vérifier les chemins exclus
        file_str = str(file_path)
        for excluded in self.excluded_paths:
            if excluded in file_str:
                return False
        
        # Vérifier la taille du fichier
        try:
            if file_path.stat().st_size > self.max_file_size:
                return False
        except OSError:
            return False
        
        return True

    def supports_union_types(self) -> bool:
        """Vérifier si la version PHP supporte les types union (PHP 8.0+)"""
        return self._version_compare(self.php_version, "8.0") >= 0
    
    def supports_nullable_types(self) -> bool:
        """Vérifier si la version PHP supporte les types nullable (PHP 7.1+)"""
        return self._version_compare(self.php_version, "7.1") >= 0
    
    def supports_mixed_type(self) -> bool:
        """Vérifier si la version PHP supporte le type mixed (PHP 8.0+)"""
        return self._version_compare(self.php_version, "8.0") >= 0
    
    def supports_never_type(self) -> bool:
        """Vérifier si la version PHP supporte le type never (PHP 8.1+)"""
        return self._version_compare(self.php_version, "8.1") >= 0
    
    def _version_compare(self, version1: str, version2: str) -> int:
        """
        Comparer deux versions PHP
        Retourne: -1 si version1 < version2, 0 si égales, 1 si version1 > version2
        """
        def version_to_tuple(v: str) -> tuple:
            return tuple(map(int, v.split('.')))
        
        v1_tuple = version_to_tuple(version1)
        v2_tuple = version_to_tuple(version2)
        
        if v1_tuple < v2_tuple:
            return -1
        elif v1_tuple > v2_tuple:
            return 1
        else:
            return 0

    def set_category_filters(self, included_categories: List[str] = None, excluded_categories: List[str] = None):
        """Définir les filtres par catégorie"""
        if included_categories:
            self.included_categories = [RuleCategory(cat) for cat in included_categories]
        if excluded_categories:
            self.excluded_categories = [RuleCategory(cat) for cat in excluded_categories]

    def set_min_severity_weight(self, weight: str):
        """Définir le poids minimum de sévérité"""
        self.min_severity_weight = SeverityWeight(int(weight))

    def should_apply_rule(self, rule_name: str) -> bool:
        """
        Vérifier si une règle doit être appliquée selon les filtres de catégorie et poids
        """
        if rule_name not in self.rules:
            return False
            
        rule_config = self.rules[rule_name]
        
        # Vérifier si la règle est activée
        if not rule_config.enabled:
            return False
            
        # Vérifier les catégories incluses
        if self.included_categories and rule_config.category not in self.included_categories:
            return False
            
        # Vérifier les catégories exclues
        if self.excluded_categories and rule_config.category in self.excluded_categories:
            return False
            
        # Vérifier le poids minimum
        if rule_config.weight.value < self.min_severity_weight.value:
            return False
            
        return True

    def get_rules_by_category(self, category: RuleCategory) -> Dict[str, RuleConfig]:
        """Obtenir toutes les règles d'une catégorie"""
        return {
            name: config for name, config in self.rules.items()
            if config.category == category
        }

    def get_rules_by_weight(self, min_weight: SeverityWeight) -> Dict[str, RuleConfig]:
        """Obtenir toutes les règles ayant au moins un certain poids"""
        return {
            name: config for name, config in self.rules.items()
            if config.weight.value >= min_weight.value
        }
