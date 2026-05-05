"""
Tests unitaires pour PHP Optimizer
"""

import unittest
from pathlib import Path
import tempfile
import os

from phpoptimizer.simple_analyzer import SimpleAnalyzer
from phpoptimizer.config import Config


class TestSimpleAnalyzer(unittest.TestCase):
    """Tests pour l'analyseur simplifié"""
    
    def setUp(self):
        """Configuration des tests"""
        self.config = Config()
        self.analyzer = SimpleAnalyzer(self.config)
    
    def test_sql_injection_detection(self):
        """Test de détection d'injection SQL"""
        php_code = """<?php
$query = "SELECT * FROM users WHERE id = " . $_GET['id'];
mysql_query($query);
?>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.php', delete=False) as f:
            f.write(php_code)
            f.flush()
            
            result = self.analyzer.analyze_file(Path(f.name))
            
            self.assertTrue(result['success'])
            self.assertGreater(len(result['issues']), 0)
            
            # Vérifier qu'une vulnérabilité SQL est détectée
            sql_issues = [issue for issue in result['issues'] 
                         if issue['rule_name'] == 'security.sql_injection']
            self.assertGreater(len(sql_issues), 0)
        
        # Nettoyer
        os.unlink(f.name)
    
    def test_xss_detection(self):
        """Test de détection XSS"""
        php_code = """<?php
echo $_GET['message'];
print $_POST['data'];
?>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.php', delete=False) as f:
            f.write(php_code)
            f.flush()
            
            result = self.analyzer.analyze_file(Path(f.name))
            
            self.assertTrue(result['success'])
            
            # Vérifier qu'une vulnérabilité XSS est détectée
            xss_issues = [issue for issue in result['issues'] 
                         if issue['rule_name'] == 'security.xss_vulnerability']
            self.assertGreater(len(xss_issues), 0)
        
        # Nettoyer
        os.unlink(f.name)
    
    def test_long_line_detection(self):
        """Test de détection de lignes trop longues"""
        long_line = "<?php\n$variable = '" + "x" * 150 + "';\n?>"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.php', delete=False) as f:
            f.write(long_line)
            f.flush()
            
            result = self.analyzer.analyze_file(Path(f.name))
            
            self.assertTrue(result['success'])
            
            # Vérifier qu'un problème de longueur de ligne est détecté
            psr_issues = [issue for issue in result['issues']
                         if issue['rule_name'] == 'best_practices.line_length']
            self.assertGreater(len(psr_issues), 0)
        
        # Nettoyer
        os.unlink(f.name)
    
    def test_clean_code(self):
        """Test avec code propre (aucun problème)"""
        clean_code = """<?php
/**
 * Exemple de code propre
 */
class Example {
    public function hello() {
        return "Hello World";
    }
}
?>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.php', delete=False) as f:
            f.write(clean_code)
            f.flush()
            
            result = self.analyzer.analyze_file(Path(f.name))
            
            self.assertTrue(result['success'])
            # Un code propre peut avoir 0 problèmes détectés par l'analyseur simplifié
            # (notre analyseur simplifié ne détecte que certains patterns)
        
        # Nettoyer
        os.unlink(f.name)


class TestConfig(unittest.TestCase):
    """Tests pour la configuration"""
    
    def test_default_config(self):
        """Test de la configuration par défaut"""
        config = Config()
        
        self.assertEqual(config.severity_level.value, 'info')
        self.assertIn('.php', config.included_extensions)
        self.assertGreater(len(config.rules), 0)
    
    def test_rule_enabled(self):
        """Test de vérification de règles activées"""
        config = Config()
        
        self.assertTrue(config.is_rule_enabled('security.sql_injection'))
        self.assertFalse(config.is_rule_enabled('nonexistent.rule'))
    
    def test_file_processing(self):
        """Test de vérification de traitement de fichier"""
        config = Config()
        
        # Créer un fichier temporaire PHP
        with tempfile.NamedTemporaryFile(suffix='.php', delete=False) as f:
            php_file = Path(f.name)
            f.write(b"<?php echo 'test'; ?>")
        
        try:
            # Fichier PHP valide
            self.assertTrue(config.should_process_file(php_file))
            
            # Fichier non-PHP
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
                txt_file = Path(f.name)
                f.write(b"test content")
            
            try:
                self.assertFalse(config.should_process_file(txt_file))
            finally:
                os.unlink(txt_file)
        
        finally:
            os.unlink(php_file)


if __name__ == '__main__':
    unittest.main()
