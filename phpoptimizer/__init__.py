"""
PHP Optimizer
Outil d'analyse et d'optimisation de code PHP
"""

__version__ = "0.2.0"
__author__ = "PHP Optimizer Team"
__email__ = "contact@phpoptimizer.dev"

from .simple_analyzer import SimpleAnalyzer
from .reporter import ReportGenerator
from .config import Config

__all__ = ['SimpleAnalyzer', 'ReportGenerator', 'Config']
