"""
Tests pour les modules d'initialisation
"""

import unittest


class TestPackageImport(unittest.TestCase):
    """Tests d'importation du package"""
    
    def test_main_imports(self):
        """Test des imports principaux"""
        try:
            from phpoptimizer import SimpleAnalyzer, ReportGenerator, Config
            self.assertTrue(True)  # Import réussi
        except ImportError as e:
            self.fail(f"Échec d'import: {e}")
    
    def test_cli_import(self):
        """Test d'import du CLI"""
        try:
            from phpoptimizer.cli import main
            self.assertTrue(True)  # Import réussi
        except ImportError as e:
            self.fail(f"Échec d'import CLI: {e}")
    
    def test_config_import(self):
        """Test d'import de la configuration"""
        try:
            from phpoptimizer.config import Config, SeverityLevel
            self.assertTrue(True)  # Import réussi
        except ImportError as e:
            self.fail(f"Échec d'import config: {e}")


if __name__ == '__main__':
    unittest.main()
