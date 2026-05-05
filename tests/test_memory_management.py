"""
Tests unitaires spécifiques pour la détection des oublis de unset()
"""

import unittest
from pathlib import Path
from phpoptimizer.simple_analyzer import SimpleAnalyzer
from phpoptimizer.config import Config


class TestMemoryManagement(unittest.TestCase):
    """Tests pour la détection des problèmes de gestion mémoire"""
    
    def setUp(self):
        self.analyzer = SimpleAnalyzer(Config())
    
    def test_large_array_without_unset(self):
        """Test: gros tableau sans unset() doit être détecté"""
        code = """<?php
        $bigArray = range(1, 50000);
        foreach ($bigArray as $value) {
            echo $value;
        }
        // Pas de unset($bigArray)
        ?>"""
        
        result = self.analyzer.analyze_content(code, Path("test.php"))
        
        # Vérifier qu'un problème de gestion mémoire est détecté
        memory_issues = [issue for issue in result['issues'] 
                        if issue.get('rule_name') == 'performance.memory_management']
        self.assertGreater(len(memory_issues), 0, "Devrait détecter l'oubli de unset() sur un gros tableau")
        
        # Vérifier le message
        issue = memory_issues[0]
        self.assertIn("bigArray", issue['message'])
        self.assertIn("50000", issue['message'])
    
    def test_large_array_with_unset(self):
        """Test: gros tableau avec unset() ne doit PAS être détecté"""
        code = """<?php
        $bigArray = range(1, 50000);
        foreach ($bigArray as $value) {
            echo $value;
        }
        unset($bigArray); // Correctement libéré
        ?>"""
        
        result = self.analyzer.analyze_content(code, Path("test.php"))
        
        # Vérifier qu'AUCUN problème de gestion mémoire n'est détecté
        memory_issues = [issue for issue in result['issues'] 
                        if issue.get('rule_name') == 'performance.memory_management']
        self.assertEqual(len(memory_issues), 0, "Ne devrait PAS détecter de problème si unset() est présent")
    
    def test_array_fill_without_unset(self):
        """Test: array_fill sans unset() doit être détecté"""
        code = """<?php
        $bigArray = array_fill(0, 60000, 'data');
        processData($bigArray);
        // Pas de unset($bigArray)
        ?>"""
        
        result = self.analyzer.analyze_content(code, Path("test.php"))
        
        memory_issues = [issue for issue in result['issues'] 
                        if issue.get('rule_name') == 'performance.memory_management']
        self.assertGreater(len(memory_issues), 0, "Devrait détecter l'oubli de unset() sur array_fill")
        
        issue = memory_issues[0]
        self.assertIn("bigArray", issue['message'])
        self.assertIn("60000", issue['message'])
    
    def test_array_fill_with_unset(self):
        """Test: array_fill avec unset() ne doit PAS être détecté"""
        code = """<?php
        $bigArray = array_fill(0, 60000, 'data');
        processData($bigArray);
        unset($bigArray);
        ?>"""
        
        result = self.analyzer.analyze_content(code, Path("test.php"))
        
        memory_issues = [issue for issue in result['issues'] 
                        if issue.get('rule_name') == 'performance.memory_management']
        self.assertEqual(len(memory_issues), 0, "Ne devrait PAS détecter de problème si unset() est présent")
    
    def test_multiple_unset(self):
        """Test: plusieurs variables dans un unset() ne doivent PAS être détectées"""
        code = """<?php
        $array1 = range(1, 30000);
        $array2 = array_fill(0, 35000, 'data');
        processData($array1, $array2);
        unset($array1, $array2); // Les deux libérées ensemble
        ?>"""
        
        result = self.analyzer.analyze_content(code, Path("test.php"))
        
        memory_issues = [issue for issue in result['issues'] 
                        if issue.get('rule_name') == 'performance.memory_management']
        self.assertEqual(len(memory_issues), 0, "Ne devrait PAS détecter de problème si les variables sont dans unset()")
    
    def test_unset_in_nested_block(self):
        """Test: unset() dans un bloc imbriqué doit être reconnu"""
        code = """<?php
        function testFunction() {
            $bigArray = range(1, 45000);
            
            if ($condition) {
                processData($bigArray);
                unset($bigArray); // unset() dans un bloc if
            }
        }
        ?>"""
        
        result = self.analyzer.analyze_content(code, Path("test.php"))
        
        memory_issues = [issue for issue in result['issues'] 
                        if issue.get('rule_name') == 'performance.memory_management']
        self.assertEqual(len(memory_issues), 0, "Devrait reconnaître unset() même dans un bloc imbriqué")
    
    def test_loop_array_without_unset(self):
        """Test: tableau rempli dans boucle sans unset() doit être détecté"""
        code = """<?php
        for ($i = 0; $i < 50000; $i++) {
            $loopArray[$i] = "data_$i";
        }
        processData($loopArray);
        // Pas de unset($loopArray)
        ?>"""
        
        result = self.analyzer.analyze_content(code, Path("test.php"))
        
        memory_issues = [issue for issue in result['issues'] 
                        if issue.get('rule_name') == 'performance.memory_management']
        self.assertGreater(len(memory_issues), 0, "Devrait détecter l'oubli de unset() sur tableau de boucle")
        
        issue = memory_issues[0]
        self.assertIn("loopArray", issue['message'])
        self.assertIn("50000", issue['message'])
    
    def test_loop_array_with_unset(self):
        """Test: tableau rempli dans boucle avec unset() ne doit PAS être détecté"""
        code = """<?php
        for ($i = 0; $i < 40000; $i++) {
            $loopArray[$i] = "data_$i";
        }
        processData($loopArray);
        unset($loopArray);
        ?>"""
        
        result = self.analyzer.analyze_content(code, Path("test.php"))
        
        memory_issues = [issue for issue in result['issues'] 
                        if issue.get('rule_name') == 'performance.memory_management']
        self.assertEqual(len(memory_issues), 0, "Ne devrait PAS détecter de problème si unset() est présent")
    
    def test_str_repeat_without_unset(self):
        """Test: str_repeat sans unset() doit être détecté"""
        code = """<?php
        $bigString = str_repeat('x', 50000);
        echo strlen($bigString);
        // Pas de unset($bigString)
        ?>"""
        
        result = self.analyzer.analyze_content(code, Path("test.php"))
        
        memory_issues = [issue for issue in result['issues'] 
                        if issue.get('rule_name') == 'performance.memory_management']
        self.assertGreater(len(memory_issues), 0, "Devrait détecter l'oubli de unset() sur str_repeat")
        
        issue = memory_issues[0]
        self.assertIn("bigString", issue['message'])
        self.assertIn("50000", issue['message'])
    
    def test_small_arrays_ignored(self):
        """Test: les petits tableaux ne doivent PAS être détectés"""
        code = """<?php
        $smallArray1 = range(1, 100);    // Trop petit
        $smallArray2 = array_fill(0, 500, 'data');  // Trop petit
        $smallString = str_repeat('x', 1000);  // Trop petit
        
        // Pas de unset() - mais c'est OK car petits tableaux
        ?>"""
        
        result = self.analyzer.analyze_content(code, Path("test.php"))
        
        memory_issues = [issue for issue in result['issues'] 
                        if issue.get('rule_name') == 'performance.memory_management']
        self.assertEqual(len(memory_issues), 0, "Ne devrait PAS détecter les petits tableaux")
    
    def test_function_scope_boundary(self):
        """Test: la détection doit s'arrêter à la fin de fonction"""
        code = """<?php
        function func1() {
            $bigArray1 = range(1, 50000);
            // Pas de unset() - DOIT ÊTRE DÉTECTÉ
        }
        
        function func2() {
            $bigArray2 = range(1, 60000);
            unset($bigArray2); // OK
        }
        
        // unset($bigArray1); // Ceci ne compte pas car hors de la fonction
        ?>"""
        
        result = self.analyzer.analyze_content(code, Path("test.php"))
        
        memory_issues = [issue for issue in result['issues'] 
                        if issue.get('rule_name') == 'performance.memory_management']
        
        # Devrait détecter bigArray1 mais pas bigArray2
        bigArray1_issues = [issue for issue in memory_issues if 'bigArray1' in issue['message']]
        bigArray2_issues = [issue for issue in memory_issues if 'bigArray2' in issue['message']]
        
        self.assertGreater(len(bigArray1_issues), 0, "Devrait détecter bigArray1 sans unset()")
        self.assertEqual(len(bigArray2_issues), 0, "Ne devrait PAS détecter bigArray2 avec unset()")
    
    def test_foreach_on_non_iterable(self):
        """Test: foreach sur une variable non itérable doit être détecté"""
        code = """<?php
        $foo = 42;
        foreach ($foo as $item) {
            echo $item;
        }
        ?>"""
        result = self.analyzer.analyze_content(code, Path("test.php"))
        issues = [issue for issue in result['issues'] if issue.get('rule_name') == 'error.foreach_non_iterable']
        self.assertGreater(len(issues), 0, "Devrait détecter foreach sur un non-itérable")
        self.assertIn("foreach sur la variable non itérable", issues[0]['message'])

    def test_heavy_functions_in_loop(self):
        """Test: fonctions lourdes dans une boucle doivent être détectées"""
        code = """<?php
        for ($i = 0; $i < 100; $i++) {
            $content = file_get_contents("file_$i.txt");
            $files = glob("*.txt");
            $exists = file_exists("test.txt");
        }
        ?>"""
        result = self.analyzer.analyze_content(code, Path("test.php"))
        heavy_issues = [issue for issue in result['issues'] if issue.get('rule_name') == 'performance.heavy_function_in_loop']
        
        self.assertGreaterEqual(len(heavy_issues), 3, "Devrait détecter au moins 3 fonctions lourdes")
        
        # Vérifier types détectés
        messages = [issue['message'] for issue in heavy_issues]
        self.assertTrue(any('Lecture de fichier' in msg for msg in messages))
        self.assertTrue(any('Recherche de fichiers' in msg for msg in messages))
        self.assertTrue(any('Vérification d\'existence' in msg for msg in messages))

    def test_object_creation_in_loop(self):
        """Test: création répétée d'objets dans une boucle doit être détectée"""
        code = """<?php
        for ($i = 0; $i < 100; $i++) {
            $date = new DateTime('2023-01-01');
            $dom = new DOMDocument();
            $logger = Logger::getInstance();
        }
        ?>"""
        result = self.analyzer.analyze_content(code, Path("test.php"))
        object_issues = [issue for issue in result['issues'] if issue.get('rule_name') == 'performance.object_creation_in_loop']
        
        self.assertGreaterEqual(len(object_issues), 2, "Devrait détecter au moins 2 créations d'objets répétées")
        
        # Vérifier types détectés
        messages = [issue['message'] for issue in object_issues]
        self.assertTrue(any('DateTime' in msg for msg in messages))
        self.assertTrue(any('DOMDocument' in msg for msg in messages))

    def test_algorithmic_complexity_sort_in_loop(self):
        """Test: détection des tris dans les boucles"""
        code = """<?php
        $data = range(1, 1000);
        foreach ($users as $user) {
            sort($data); // ❌ Tri dans boucle
            usort($user_data, 'compare_func'); // ❌ Tri personnalisé
        }
        ?>"""
        
        result = self.analyzer.analyze_content(code, Path("test.php"))
        
        # Vérifier qu'un problème de tri dans boucle est détecté
        sort_issues = [issue for issue in result['issues'] 
                      if issue.get('rule_name') == 'performance.sort_in_loop']
        self.assertGreater(len(sort_issues), 0, "Devrait détecter les tris dans les boucles")
        
        # Vérifier les messages
        sort_issue = sort_issues[0]
        self.assertIn("sort", sort_issue['message'].lower())
        self.assertIn("complexité", sort_issue['message'].lower())
    
    def test_algorithmic_complexity_linear_search_in_loop(self):
        """Test: détection de recherche linéaire dans boucle"""
        code = """<?php
        $large_array = range(1, 10000);
        foreach ($items as $item) {
            if (in_array($item->id, $large_array)) { // ❌ Recherche linéaire O(n²)
                echo "Found!";
            }
            $key = array_search($item->name, $names); // ❌ Recherche linéaire
        }
        ?>"""
        
        result = self.analyzer.analyze_content(code, Path("test.php"))
        
        # Vérifier qu'un problème de recherche linéaire est détecté
        search_issues = [issue for issue in result['issues'] 
                        if issue.get('rule_name') == 'performance.linear_search_in_loop']
        self.assertGreater(len(search_issues), 0, "Devrait détecter la recherche linéaire dans les boucles")
        
        # Vérifier le message
        search_issue = search_issues[0]
        self.assertIn("recherche linéaire", search_issue['message'].lower())
        self.assertIn("o(n²)", search_issue['message'].lower())
    
    def test_algorithmic_complexity_nested_loops_same_array(self):
        """Test: détection de boucles imbriquées sur le même tableau"""
        code = """<?php
        foreach ($users as $user1) {
            foreach ($users as $user2) { // ❌ Même tableau - O(n²)
                if ($user1->id !== $user2->id) {
                    echo "Different users";
                }
            }
        }
        ?>"""
        
        result = self.analyzer.analyze_content(code, Path("test.php"))
        
        # Vérifier qu'un problème de boucles imbriquées est détecté
        nested_issues = [issue for issue in result['issues'] 
                        if issue.get('rule_name') == 'performance.nested_loop_same_array']
        self.assertGreater(len(nested_issues), 0, "Devrait détecter les boucles imbriquées sur le même tableau")
        
        # Vérifier le message
        nested_issue = nested_issues[0]
        self.assertIn("boucles imbriquées", nested_issue['message'].lower())
        self.assertIn("users", nested_issue['message'])
    
    def test_object_creation_in_loop_with_constants(self):
        """Test: détection de création d'objets répétée avec arguments constants"""
        code = """<?php
        for ($i = 0; $i < 100; $i++) {
            $date = new DateTime('2023-01-01'); // ❌ Arguments constants
            $logger = Logger::getInstance(); // ❌ Singleton
        }
        ?>"""
        
        result = self.analyzer.analyze_content(code, Path("test.php"))
        
        # Vérifier qu'un problème de création d'objets est détecté
        object_issues = [issue for issue in result['issues'] 
                        if issue.get('rule_name') == 'performance.object_creation_in_loop']
        self.assertGreater(len(object_issues), 0, "Devrait détecter la création répétée d'objets avec arguments constants")
        
        # Vérifier le message
        object_issue = object_issues[0]
        self.assertIn("création répétée", object_issue['message'].lower())
        self.assertIn("arguments constants", object_issue['message'])
    
    def test_object_creation_in_loop_with_variables_ok(self):
        """Test: création d'objets avec variables ne doit PAS être détectée"""
        code = """<?php
        foreach ($configs as $config) {
            $pdo = new PDO($config->dsn, $config->user, $config->pass); // ✅ Arguments variables
            $result = $pdo->query($config->sql);
        }
        ?>"""
        result = self.analyzer.analyze_content(code, Path("test.php"))
        
        # Vérifier qu'aucun problème de création d'objets n'est détecté
        object_issues = [issue for issue in result['issues'] 
                        if issue.get('rule_name') == 'performance.object_creation_in_loop']
        self.assertEqual(len(object_issues), 0, "Ne devrait PAS détecter la création d'objets avec arguments variables")

    def test_superglobal_access_in_loop(self):
        """Test: détection d'accès répétés aux superglobales dans les boucles"""
        code = """<?php
        foreach ($users as $user) {
            $sessionData = $_SESSION['user_data']; // ❌ Accès répété
            $cookieValue = $_COOKIE['preferences']; // ❌ Accès répété
            $userId = $_GET['id']; // ❌ Accès répété
            $postData = $_POST['data']; // ❌ Accès répété
        }
        ?>"""
        
        result = self.analyzer.analyze_content(code, Path("test.php"))
        
        # Vérifier qu'un problème d'accès aux superglobales est détecté
        superglobal_issues = [issue for issue in result['issues'] 
                             if issue.get('rule_name') == 'performance.superglobal_access_in_loop']
        self.assertGreater(len(superglobal_issues), 0, "Devrait détecter les accès répétés aux superglobales")
        
        # Vérifier les messages pour différentes superglobales
        detected_superglobals = [issue['message'] for issue in superglobal_issues]
        self.assertTrue(any('$_SESSION' in msg for msg in detected_superglobals), "Devrait détecter $_SESSION")
        self.assertTrue(any('$_COOKIE' in msg for msg in detected_superglobals), "Devrait détecter $_COOKIE")
        self.assertTrue(any('$_GET' in msg for msg in detected_superglobals), "Devrait détecter $_GET")
        self.assertTrue(any('$_POST' in msg for msg in detected_superglobals), "Devrait détecter $_POST")
    
    def test_superglobal_access_outside_loop_ok(self):
        """Test: accès aux superglobales hors boucle ne doit PAS être détecté"""
        code = """<?php
        $sessionData = $_SESSION['user_data']; // ✅ OK - hors boucle
        $cookieValue = $_COOKIE['preferences']; // ✅ OK - hors boucle
        foreach ($items as $item) {
            echo "Using stored data: " . $sessionData . " - " . $cookieValue;
        }
        ?>"""
        
        result = self.analyzer.analyze_content(code, Path("test.php"))
        
        # Vérifier qu'aucun problème d'accès aux superglobales n'est détecté
        superglobal_issues = [issue for issue in result['issues'] 
                             if issue.get('rule_name') == 'performance.superglobal_access_in_loop']
        self.assertEqual(len(superglobal_issues), 0, "Ne devrait PAS détecter les accès aux superglobales hors boucle")
    
    def test_superglobal_access_server_and_env(self):
        """Test: détection d'accès à $_SERVER et $_ENV dans les boucles"""
        code = """<?php
        for ($i = 0; $i < 10; $i++) {
            $serverInfo = $_SERVER['HTTP_HOST']; // ❌ Accès répété
            $envVar = $_ENV['PATH']; // ❌ Accès répété
            $globalVar = $GLOBALS['config']; // ❌ Accès répété
        }
        ?>"""
        
        result = self.analyzer.analyze_content(code, Path("test.php"))
        
        # Vérifier qu'un problème d'accès aux superglobales est détecté
        superglobal_issues = [issue for issue in result['issues'] 
                             if issue.get('rule_name') == 'performance.superglobal_access_in_loop']
        self.assertGreater(len(superglobal_issues), 0, "Devrait détecter les accès répétés aux superglobales")
        
        # Vérifier les messages pour $_SERVER, $_ENV et $GLOBALS
        detected_superglobals = [issue['message'] for issue in superglobal_issues]
        self.assertTrue(any('$_SERVER' in msg for msg in detected_superglobals), "Devrait détecter $_SERVER")
        self.assertTrue(any('$_ENV' in msg for msg in detected_superglobals), "Devrait détecter $_ENV")
        self.assertTrue(any('$GLOBALS' in msg for msg in detected_superglobals), "Devrait détecter $GLOBALS")

    def test_unused_global_variable_detection(self):
        """Test: détection des variables globales jamais utilisées"""
        code = """<?php
        function test_function() {
            global $unused_var; // ❌ Jamais utilisée
            echo "Function without using global variable";
        }
        ?>"""
        
        result = self.analyzer.analyze_content(code, Path("test.php"))
        
        # Vérifier qu'un problème de variable globale inutilisée est détecté
        unused_global_issues = [issue for issue in result['issues'] 
                               if issue.get('rule_name') == 'performance.unused_global_variable']
        self.assertGreater(len(unused_global_issues), 0, "Devrait détecter les variables globales inutilisées")
        
        # Vérifier le message
        issue = unused_global_issues[0]
        self.assertIn("unused_var", issue['message'])
        self.assertIn("jamais utilisée", issue['message'])
    
    def test_global_could_be_local_detection(self):
        """Test: détection des variables globales qui pourraient être locales"""
        code = """<?php
        function test_function() {
            global $local_candidate; // ❌ Pourrait être locale
            $local_candidate = "only used here"; // Assignée dans cette fonction
            echo $local_candidate; // Utilisée seulement ici
        }
        ?>"""
        
        result = self.analyzer.analyze_content(code, Path("test.php"))
        
        # Vérifier qu'un problème de variable qui pourrait être locale est détecté
        could_be_local_issues = [issue for issue in result['issues'] 
                                if issue.get('rule_name') == 'performance.global_could_be_local']
        self.assertGreater(len(could_be_local_issues), 0, "Devrait détecter les variables globales qui pourraient être locales")
        
        # Vérifier le message
        issue = could_be_local_issues[0]
        self.assertIn("local_candidate", issue['message'])
        self.assertIn("pourrait être locale", issue['message'])
    
    def test_proper_global_usage_not_detected(self):
        """Test: variables globales correctement utilisées ne doivent PAS être détectées"""
        code = """<?php
        $global_config = "shared data";
        
        function test_function1() {
            global $global_config; // ✅ OK - utilisée globalement
            echo $global_config;
        }
        
        function test_function2() {
            global $global_config; // ✅ OK - utilisée dans plusieurs fonctions
            return $global_config . " modified";
        }
        ?>"""
        
        result = self.analyzer.analyze_content(code, Path("test.php"))
        
        # Vérifier qu'aucun problème n'est détecté pour les variables globales correctement utilisées
        global_issues = [issue for issue in result['issues'] 
                        if issue.get('rule_name') in ['performance.unused_global_variable', 'performance.global_could_be_local']]
        self.assertEqual(len(global_issues), 0, "Ne devrait PAS détecter de problème pour les variables globales correctement utilisées")
    
    def test_multiple_globals_mixed_usage(self):
        """Test: détection dans une déclaration avec plusieurs variables globales"""
        code = """<?php
        function test_function() {
            global $used_var, $unused_var; // ❌ $unused_var jamais utilisée
            echo $used_var; // $used_var est utilisée
        }
        ?>"""
        
        result = self.analyzer.analyze_content(code, Path("test.php"))
        
        # Vérifier qu'un problème est détecté pour la variable non utilisée
        unused_global_issues = [issue for issue in result['issues'] 
                               if issue.get('rule_name') == 'performance.unused_global_variable']
        self.assertGreater(len(unused_global_issues), 0, "Devrait détecter la variable globale inutilisée dans une déclaration multiple")
        
        # Vérifier que c'est bien la bonne variable qui est détectée
        issue = unused_global_issues[0]
        self.assertIn("unused_var", issue['message'])
    
    def test_superglobals_not_detected(self):
        """Test: les superglobales ne doivent PAS être détectées comme variables globales problématiques"""
        code = """<?php
        function test_function() {
            echo $_GET['param']; // ✅ OK - superglobale
            echo $_SESSION['data']; // ✅ OK - superglobale
            echo $_POST['value']; // ✅ OK - superglobale
        }
        ?>"""
        
        result = self.analyzer.analyze_content(code, Path("test.php"))
        
        # Vérifier qu'aucun problème n'est détecté pour les superglobales
        global_issues = [issue for issue in result['issues'] 
                        if issue.get('rule_name') in ['performance.unused_global_variable', 'performance.global_could_be_local']]
        self.assertEqual(len(global_issues), 0, "Ne devrait PAS détecter de problème pour les superglobales")


if __name__ == '__main__':
    unittest.main()
