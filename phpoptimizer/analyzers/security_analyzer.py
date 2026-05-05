"""
Analyseur spécialisé pour la sécurité
"""

import re
from pathlib import Path
from typing import List, Dict, Any

from .base_analyzer import BaseAnalyzer


class SecurityAnalyzer(BaseAnalyzer):
    """Analyseur spécialisé pour les problèmes de sécurité"""
    
    def analyze(self, content: str, file_path: Path, lines: List[str]) -> List[Dict[str, Any]]:
        """Analyser les problèmes de sécurité dans le code PHP"""
        issues = []
        
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Ignorer les commentaires et directives Blade
            if self._is_comment_line(line) or self._is_blade_directive(line):
                continue
            
            # Détecter les injections SQL
            self._detect_sql_injection(line_stripped, line_num, file_path, line, issues)
            
            # Détecter les vulnérabilités XSS
            self._detect_xss_vulnerability(line_stripped, line_num, file_path, line, issues)
            
            # Détecter les inclusions de fichiers dangereuses
            self._detect_file_inclusion_vulnerability(line_stripped, line_num, file_path, line, issues)
            
            # Détecter les hachages faibles
            self._detect_weak_password_hashing(line_stripped, line_num, file_path, line, issues)
            
            # Détecter l'exposition de variables sensibles
            self._detect_sensitive_data_exposure(line_stripped, line_num, file_path, line, issues)
            
            # Détecter les problèmes d'authentification et autorisation
            self._detect_auth_issues(line_stripped, line_num, file_path, line, issues)
            
            # Détecter l'utilisation de fonctions dangereuses
            self._detect_dangerous_functions(line_stripped, line_num, file_path, line, issues)
            
            # Détecter les problèmes de configuration
            self._detect_configuration_issues(line_stripped, line_num, file_path, line, issues)
        
        return issues
    
    def _detect_sql_injection(self, line_stripped: str, line_num: int, file_path: Path, 
                             line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les vulnérabilités d'injection SQL"""
        # Patterns d'injection SQL (améliorés pour éviter les faux positifs XPath/autres)
        sql_injection_patterns = [
            (r'mysql_query\s*\([^)]*\$[a-zA-Z_][a-zA-Z0-9_]*', 'mysql_query avec variable non échappée'),
            (r'mysqli_query\s*\([^)]*\$[a-zA-Z_][a-zA-Z0-9_]*', 'mysqli_query avec variable non échappée'),
            # Patterns SQL spécifiques (PDO, bases de données) - éviter XPath, API, etc.
            (r'\$(?:pdo|db|database|connection|conn|mysql|mysqli)\s*->\s*query\s*\([^)]*\$[a-zA-Z_][a-zA-Z0-9_]*', 'Méthode query() de base de données avec variable non échappée'),
            # Mots-clés SQL dans les chaînes avec variables
            (r'SELECT\s+.*\$[a-zA-Z_][a-zA-Z0-9_]*', 'Requête SELECT avec concaténation de variable'),
            (r'INSERT\s+.*\$[a-zA-Z_][a-zA-Z0-9_]*', 'Requête INSERT avec concaténation de variable'),
            (r'UPDATE\s+.*\$[a-zA-Z_][a-zA-Z0-9_]*', 'Requête UPDATE avec concaténation de variable'),
            (r'DELETE\s+.*\$[a-zA-Z_][a-zA-Z0-9_]*', 'Requête DELETE avec concaténation de variable'),
            (r'WHERE\s+.*\$[a-zA-Z_][a-zA-Z0-9_]*', 'Clause WHERE avec concaténation de variable'),
            (r'ORDER\s+BY\s+.*\$[a-zA-Z_][a-zA-Z0-9_]*', 'Clause ORDER BY avec concaténation de variable')
        ]
        
        # Exclusions pour éviter les faux positifs (XPath, API REST, etc.)
        exclusion_patterns = [
            r'\$xpath\s*->\s*query\s*\(',  # Requêtes XPath
            r'\$dom\s*->\s*query\s*\(',    # Requêtes DOM
            r'\$client\s*->\s*query\s*\(', # Requêtes d'un client API
            r'\$api\s*->\s*query\s*\(',    # Requêtes API
            r'curl_.*query',               # cURL avec paramètres query
            r'http_build_query',           # Construction de query string HTTP
        ]
        
        # Vérifier les exclusions d'abord
        for exclusion in exclusion_patterns:
            if re.search(exclusion, line_stripped, re.IGNORECASE):
                return  # Sortir sans signaler - c'est un faux positif
        
        # Vérification particulière pour execute() - permettre les tableaux de paramètres sécurisés
        execute_match = re.search(r'\$(?:[a-zA-Z_][a-zA-Z0-9_]*)\s*->\s*execute\s*\(([^)]+)\)', line_stripped)
        if execute_match:
            execute_content = execute_match.group(1).strip()
            
            # Cas sécurisés : ne pas signaler comme injection SQL
            safe_execute_patterns = [
                # Tableau de paramètres direct: execute([...])
                r'^\[\s*.*\s*\]$',
                # Tableau de paramètres avec variables: execute([$var1, $var2])
                r'^\[\s*\$[a-zA-Z_][a-zA-Z0-9_]*(?:\s*,\s*\$[a-zA-Z_][a-zA-Z0-9_]*)*\s*\]$',
                # Appel sans paramètres: execute()
                r'^\s*$',
                # Variable qui est clairement un tableau de paramètres
                r'^\$[a-zA-Z_][a-zA-Z0-9_]*_params$',
                r'^\$params$',
                r'^\$parameters$',
                r'^\$bindings$'
            ]
            
            is_safe = False
            for safe_pattern in safe_execute_patterns:
                if re.search(safe_pattern, execute_content):
                    is_safe = True
                    break
            
            # Si ce n'est pas un pattern sécurisé, c'est potentiellement dangereux
            if not is_safe and re.search(r'\$[a-zA-Z_][a-zA-Z0-9_]*', execute_content):
                issues.append(self._create_issue(
                    'security.sql_injection',
                    'Injection SQL potentielle: execute() avec variable non sécurisée',
                    file_path,
                    line_num,
                    'error',
                    'security',
                    'Utiliser des requêtes préparées avec des paramètres liés dans un tableau pour éviter les injections SQL',
                    line.strip()
                ))
                return
        
        # Patterns d'injection SQL classiques
        for pattern, description in sql_injection_patterns:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                issues.append(self._create_issue(
                    'security.sql_injection',
                    f'Injection SQL potentielle: {description}',
                    file_path,
                    line_num,
                    'error',
                    'security',
                    'Utiliser des requêtes préparées avec des paramètres liés pour éviter les injections SQL',
                    line.strip()
                ))
                break
    
    def _detect_xss_vulnerability(self, line_stripped: str, line_num: int, file_path: Path, 
                                 line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les vulnérabilités XSS"""
        # Patterns XSS
        xss_patterns = [
            (r'echo\s+\$_(GET|POST|REQUEST|COOKIE|SERVER)\[', 'echo de données utilisateur non filtrées'),
            (r'print\s+\$_(GET|POST|REQUEST|COOKIE|SERVER)\[', 'print de données utilisateur non filtrées'),
            (r'printf\s*\([^)]*\$_(GET|POST|REQUEST|COOKIE|SERVER)\[', 'printf avec données utilisateur'),
            (r'<\?=\s*\$_(GET|POST|REQUEST|COOKIE|SERVER)\[', 'Balise courte PHP avec données utilisateur'),
            (r'echo\s+["\'][^"\']*\$_(GET|POST|REQUEST|COOKIE|SERVER)', 'echo dans chaîne avec données utilisateur'),
            (r'innerHTML\s*=.*\$_(GET|POST|REQUEST|COOKIE|SERVER)', 'innerHTML avec données utilisateur'),
            (r'document\.write\s*\([^)]*\$_(GET|POST|REQUEST|COOKIE|SERVER)', 'document.write avec données utilisateur')
        ]
        
        for pattern, description in xss_patterns:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                # Vérifier si htmlspecialchars ou autre fonction d'échappement est utilisée
                if not re.search(r'htmlspecialchars|htmlentities|filter_var|strip_tags', line_stripped, re.IGNORECASE):
                    issues.append(self._create_issue(
                        'security.xss_vulnerability',
                        f'Vulnérabilité XSS: {description}',
                        file_path,
                        line_num,
                        'error',
                        'security',
                        'Utiliser htmlspecialchars(), htmlentities() ou filter_var() pour échapper les données utilisateur',
                        line.strip()
                    ))
                break
    
    def _detect_file_inclusion_vulnerability(self, line_stripped: str, line_num: int, file_path: Path, 
                                           line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les vulnérabilités d'inclusion de fichiers"""
        # Patterns d'inclusion dangereuse
        inclusion_patterns = [
            (r'include\s*\(\s*\$_(GET|POST|REQUEST)\[', 'include avec données utilisateur'),
            (r'include_once\s*\(\s*\$_(GET|POST|REQUEST)\[', 'include_once avec données utilisateur'),
            (r'require\s*\(\s*\$_(GET|POST|REQUEST)\[', 'require avec données utilisateur'),
            (r'require_once\s*\(\s*\$_(GET|POST|REQUEST)\[', 'require_once avec données utilisateur'),
            (r'file_get_contents\s*\(\s*\$_(GET|POST|REQUEST)\[', 'file_get_contents avec données utilisateur'),
            (r'fopen\s*\(\s*\$_(GET|POST|REQUEST)\[', 'fopen avec données utilisateur'),
            (r'readfile\s*\(\s*\$_(GET|POST|REQUEST)\[', 'readfile avec données utilisateur')
        ]
        
        for pattern, description in inclusion_patterns:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                issues.append(self._create_issue(
                    'security.file_inclusion',
                    f'Inclusion de fichier dangereuse: {description}',
                    file_path,
                    line_num,
                    'error',
                    'security',
                    'Valider et filtrer les noms de fichiers, utiliser une whitelist de fichiers autorisés',
                    line.strip()
                ))
                break
    
    def _detect_weak_password_hashing(self, line_stripped: str, line_num: int, file_path: Path, 
                                     line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les algorithmes de hachage faibles pour les mots de passe"""
        # Algorithmes faibles
        weak_hash_patterns = [
            (r'md5\s*\([^)]*password', 'MD5 pour hachage de mot de passe'),
            (r'sha1\s*\([^)]*password', 'SHA1 pour hachage de mot de passe'),
            (r'hash\s*\(\s*["\']md5["\']', 'hash() avec MD5'),
            (r'hash\s*\(\s*["\']sha1["\']', 'hash() avec SHA1'),
            (r'crypt\s*\([^)]*\$[a-zA-Z_]*password', 'crypt() simple pour mot de passe')
        ]
        
        for pattern, description in weak_hash_patterns:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                issues.append(self._create_issue(
                    'security.weak_password_hashing',
                    f'Algorithme de hachage faible: {description}',
                    file_path,
                    line_num,
                    'error',
                    'security',
                    'Utiliser password_hash() avec PASSWORD_DEFAULT ou PASSWORD_ARGON2ID',
                    line.strip()
                ))
                break
    
    def _detect_sensitive_data_exposure(self, line_stripped: str, line_num: int, file_path: Path, 
                                      line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter l'exposition de données sensibles"""
        # Exposition de données sensibles
        sensitive_patterns = [
            (r'var_dump\s*\(\s*\$_(GET|POST|REQUEST|COOKIE|SESSION)', 'var_dump de données utilisateur'),
            (r'print_r\s*\(\s*\$_(GET|POST|REQUEST|COOKIE|SESSION)', 'print_r de données utilisateur'),
            (r'error_reporting\s*\(\s*E_ALL', 'error_reporting(E_ALL) en production'),
            (r'ini_set\s*\(\s*["\']display_errors["\'].*1', 'display_errors activé'),
            (r'phpinfo\s*\(\s*\)', 'phpinfo() exposé'),
            (r'echo\s+.*password.*\$[a-zA-Z_]', 'echo possible de mot de passe'),
            (r'print\s+.*password.*\$[a-zA-Z_]', 'print possible de mot de passe')
        ]
        
        for pattern, description in sensitive_patterns:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                issues.append(self._create_issue(
                    'security.sensitive_data_exposure',
                    f'Exposition possible de données sensibles: {description}',
                    file_path,
                    line_num,
                    'warning',
                    'security',
                    'Éviter d\'exposer des données sensibles, désactiver les fonctions de debug en production',
                    line.strip()
                ))
                break
    
    def _detect_auth_issues(self, line_stripped: str, line_num: int, file_path: Path, 
                           line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les problèmes d'authentification et d'autorisation"""
        # Problèmes d'authentification
        auth_patterns = [
            (r'session_start\s*\(\s*\).*\$_SESSION\[.*admin.*\]\s*=\s*true', 'Attribution directe de privilèges admin'),
            (r'\$_SESSION\[.*user.*\]\s*=\s*\$_(GET|POST)\[', 'Attribution de session depuis données utilisateur'),
            (r'if\s*\(\s*\$_SESSION\[.*\]\s*\)', 'Vérification de session simple sans validation'),
            (r'setcookie\s*\([^)]*false\s*\)', 'Cookie non sécurisé (httpOnly=false)'),
            (r'session_regenerate_id\s*\(\s*false', 'session_regenerate_id sans suppression de l\'ancien ID')
        ]
        
        for pattern, description in auth_patterns:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                issues.append(self._create_issue(
                    'security.authentication',
                    f'Problème d\'authentification: {description}',
                    file_path,
                    line_num,
                    'warning',
                    'security',
                    'Implémenter une authentification et autorisation robustes',
                    line.strip()
                ))
                break
    
    def _detect_dangerous_functions(self, line_stripped: str, line_num: int, file_path: Path, 
                                  line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter l'utilisation de fonctions dangereuses"""
        # Fonctions dangereuses
        dangerous_functions = [
            ('eval', 'Exécution de code arbitraire'),
            ('exec', 'Exécution de commandes système'),
            ('system', 'Exécution de commandes système'),
            ('shell_exec', 'Exécution de commandes shell'),
            ('passthru', 'Exécution de commandes système'),
            ('proc_open', 'Ouverture de processus'),
            ('popen', 'Ouverture de pipe vers processus'),
            ('assert', 'Assertion (peut exécuter du code)'),
            ('create_function', 'Création de fonction dynamique'),
            ('file_put_contents.*php://input', 'Écriture depuis php://input'),
            ('move_uploaded_file.*\\$_(GET|POST)', 'move_uploaded_file avec données utilisateur')
        ]
        
        for func, description in dangerous_functions:
            if re.search(rf'\b{func}\s*\(', line_stripped, re.IGNORECASE):
                severity = 'error' if func in ['eval', 'exec', 'system'] else 'warning'
                issues.append(self._create_issue(
                    'security.dangerous_function',
                    f'Fonction dangereuse: {func}() - {description}',
                    file_path,
                    line_num,
                    severity,
                    'security',
                    f'Éviter l\'utilisation de {func}(), chercher une alternative plus sûre',
                    line.strip()
                ))
                break
    
    def _detect_configuration_issues(self, line_stripped: str, line_num: int, file_path: Path, 
                                   line: str, issues: List[Dict[str, Any]]) -> None:
        """Détecter les problèmes de configuration de sécurité"""
        # Problèmes de configuration
        config_patterns = [
            (r'ini_set\s*\(\s*["\']allow_url_include["\'].*1', 'allow_url_include activé'),
            (r'ini_set\s*\(\s*["\']allow_url_fopen["\'].*1', 'allow_url_fopen activé'),
            (r'ini_set\s*\(\s*["\']register_globals["\'].*1', 'register_globals activé'),
            (r'extract\s*\(\s*\$_(GET|POST|REQUEST)', 'extract() avec données utilisateur'),
            (r'parse_str\s*\([^)]*\$_(GET|POST|REQUEST)', 'parse_str avec données utilisateur'),
            (r'unserialize\s*\(\s*\$_(GET|POST|REQUEST)', 'unserialize avec données utilisateur')
        ]
        
        for pattern, description in config_patterns:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                issues.append(self._create_issue(
                    'security.configuration',
                    f'Configuration dangereuse: {description}',
                    file_path,
                    line_num,
                    'warning',
                    'security',
                    'Réviser la configuration de sécurité, désactiver les options dangereuses',
                    line.strip()
                ))
