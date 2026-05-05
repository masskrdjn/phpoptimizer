"""
Système de suggestions de correction pour PHP Optimizer
"""

from typing import Dict, Any, Optional, Tuple
import re


class SuggestionProvider:
    """Fournisseur de suggestions de correction avec exemples"""
    
    def __init__(self):
        """Initialiser le fournisseur de suggestions"""
        self.suggestions = {
            # Sécurité
            'security.sql_injection': self._get_sql_injection_suggestion,
            'security.xss_vulnerability': self._get_xss_suggestion,
            'security.file_inclusion': self._get_file_inclusion_suggestion,
            'security.weak_password_hashing': self._get_weak_hash_suggestion,
            'security.dangerous_functions': self._get_dangerous_functions_suggestion,
            
            # Performance
            'performance.inefficient_loop': self._get_loop_optimization_suggestion,
            'performance.inefficient_loops': self._get_loop_optimization_suggestion,  # Alias
            'performance.repeated_calculation': self._get_repeated_calc_suggestion,
            'performance.memory_usage': self._get_memory_optimization_suggestion,
            'performance.memory_management': self._get_memory_optimization_suggestion,  # Alias
            'performance.algorithmic_complexity': self._get_complexity_suggestion,
            'performance.unused_variables': self._get_unused_var_suggestion,  # Alias
            'performance.missing_parameter_type': self._get_parameter_type_suggestion,
            'performance.missing_return_type': self._get_return_type_suggestion,
            'performance.mixed_type_opportunity': self._get_mixed_type_suggestion,
            
            # Bonnes pratiques
            'best_practices.function_naming': self._get_naming_suggestion,
            'best_practices.missing_docstring': self._get_docstring_suggestion,
            'best_practices.nullable_types': self._get_nullable_type_suggestion,
            'error.null_method_call': self._get_null_check_suggestion,
            'error.undefined_variable': self._get_undefined_var_suggestion,
            
            # Qualité du code
            'code_quality.unused_variable': self._get_unused_var_suggestion,
            'code_quality.global_variable': self._get_global_var_suggestion,
        }
    
    def get_detailed_suggestion(self, rule_name: str, code_snippet: str, 
                              message: str) -> Tuple[str, str, str]:
        """
        Obtenir une suggestion détaillée avec exemple de correction
        
        Returns:
            Tuple[str, str, str]: (suggestion, exemple_avant, exemple_apres)
        """
        if rule_name in self.suggestions:
            return self.suggestions[rule_name](code_snippet, message)
        
        return (
            "Consultez la documentation pour plus de détails sur cette règle.",
            code_snippet,
            "# Correction nécessaire - consultez la documentation"
        )
    
    def _get_sql_injection_suggestion(self, code_snippet: str, message: str) -> Tuple[str, str, str]:
        """Suggestion pour les injections SQL"""
        suggestion = "Utilisez des requêtes préparées avec des paramètres liés pour éviter les injections SQL."
        
        if 'mysql_query' in code_snippet.lower():
            exemple_apres = """// ❌ Code dangereux
// mysql_query("SELECT * FROM users WHERE id = " . $_GET['id']);

// ✅ Code sécurisé avec PDO
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = ?");
$stmt->execute([$_GET['id']]);
$result = $stmt->fetchAll();"""
        
        elif 'mysqli_query' in code_snippet.lower():
            exemple_apres = """// ❌ Code dangereux
// mysqli_query($conn, "SELECT * FROM users WHERE id = " . $_GET['id']);

// ✅ Code sécurisé avec MySQLi préparé
$stmt = $conn->prepare("SELECT * FROM users WHERE id = ?");
$stmt->bind_param("i", $_GET['id']);
$stmt->execute();
$result = $stmt->get_result();"""
        
        else:
            exemple_apres = """// ❌ Code dangereux avec concaténation
// $query = "SELECT * FROM table WHERE field = '" . $userInput . "'";

// ✅ Code sécurisé avec requête préparée
$stmt = $pdo->prepare("SELECT * FROM table WHERE field = ?");
$stmt->execute([$userInput]);
$result = $stmt->fetchAll();"""
        
        return (suggestion, code_snippet, exemple_apres)
    
    def _get_xss_suggestion(self, code_snippet: str, message: str) -> Tuple[str, str, str]:
        """Suggestion pour les vulnérabilités XSS"""
        suggestion = "Échappez toujours les données utilisateur avant de les afficher."
        
        exemple_apres = """// ❌ Code dangereux
// echo $_GET['name'];

// ✅ Code sécurisé avec échappement
echo htmlspecialchars($_GET['name'], ENT_QUOTES, 'UTF-8');

// ✅ Alternative avec filter_var
echo filter_var($_GET['name'], FILTER_SANITIZE_STRING);"""
        
        return (suggestion, code_snippet, exemple_apres)
    
    def _get_file_inclusion_suggestion(self, code_snippet: str, message: str) -> Tuple[str, str, str]:
        """Suggestion pour les inclusions de fichiers dangereuses"""
        suggestion = "Validez et filtrez les noms de fichiers, utilisez une whitelist."
        
        exemple_apres = """// ❌ Code dangereux
// include($_GET['page'] . '.php');

// ✅ Code sécurisé avec whitelist
$allowed_pages = ['home', 'about', 'contact', 'products'];
$page = $_GET['page'] ?? 'home';

if (in_array($page, $allowed_pages)) {
    include($page . '.php');
} else {
    include('404.php');
}"""
        
        return (suggestion, code_snippet, exemple_apres)
    
    def _get_weak_hash_suggestion(self, code_snippet: str, message: str) -> Tuple[str, str, str]:
        """Suggestion pour les algorithmes de hachage faibles"""
        suggestion = "Utilisez password_hash() et password_verify() pour les mots de passe."
        
        exemple_apres = """// ❌ Code dangereux
// $password_hash = md5($password);

// ✅ Code sécurisé avec password_hash()
$password_hash = password_hash($password, PASSWORD_DEFAULT);

// ✅ Vérification avec password_verify()
if (password_verify($input_password, $stored_hash)) {
    echo "Connexion réussie";
}"""
        
        return (suggestion, code_snippet, exemple_apres)
    
    def _get_dangerous_functions_suggestion(self, code_snippet: str, message: str) -> Tuple[str, str, str]:
        """Suggestion pour les fonctions dangereuses"""
        suggestion = "Évitez les fonctions dangereuses comme eval(), exec(), system()."
        
        if 'eval' in code_snippet.lower():
            exemple_apres = """// ❌ Code dangereux
// eval($code);

// ✅ Alternatives sécurisées:
// - Utilisez symfony/expression-language pour les calculs
// - Utilisez Twig pour les templates
// - Utilisez JSON/YAML pour la configuration"""
        else:
            exemple_apres = """// ❌ Code dangereux
// exec("ls " . $_GET['dir']);

// ✅ Code sécurisé avec validation
$allowed_dirs = ['/var/www/uploads', '/tmp/safe'];
if (in_array($_GET['dir'], $allowed_dirs)) {
    exec("ls " . escapeshellarg($_GET['dir']), $output);
}}"""
        
        return (suggestion, code_snippet, exemple_apres)
    
    def _get_loop_optimization_suggestion(self, code_snippet: str, message: str) -> Tuple[str, str, str]:
        """Suggestion pour l'optimisation des boucles"""
        
        if 'count(' in code_snippet:
            suggestion = "Évitez d'appeler count() à chaque itération de boucle."
            exemple_apres = """// ❌ Code inefficace - count() appelé à chaque itération
// for ($i = 0; $i < count($array); $i++) {
//     echo $array[$i];
// }

// ✅ Code optimisé - count() appelé une seule fois
$length = count($array);
for ($i = 0; $i < $length; $i++) {
    echo $array[$i];
}

// ✅ Encore mieux avec foreach
foreach ($array as $value) {
    echo $value;
}"""
        else:
            suggestion = "Optimisez les boucles en évitant les calculs répétitifs."
            exemple_apres = """// ❌ Code inefficace
// for ($i = 0; $i < expensive_function(); $i++) {
//     // Traitement
// }

// ✅ Code optimisé
$limit = expensive_function();
for ($i = 0; $i < $limit; $i++) {
    // Traitement
}"""
        
        return (suggestion, code_snippet, exemple_apres)
    
    def _get_repeated_calc_suggestion(self, code_snippet: str, message: str) -> Tuple[str, str, str]:
        """Suggestion pour les calculs répétitifs"""
        
        # Détecter le nom de la fonction répétée
        function_match = re.search(r'(\w+)\s*\([^)]*\)', code_snippet)
        func_name = function_match.group(1) if function_match else 'expensive_function'
        
        suggestion = f"Stockez le résultat de {func_name}() dans une variable au lieu de l'appeler plusieurs fois."
        
        exemple_apres = f"""// ❌ Code inefficace - fonction appelée plusieurs fois
// if ({func_name}($param) > 10 && {func_name}($param) < 100) {{
//     return {func_name}($param);
// }}

// ✅ Code optimisé - fonction appelée une seule fois
$result = {func_name}($param);
if ($result > 10 && $result < 100) {{
    return $result;
}}
return false;"""
        
        return (suggestion, code_snippet, exemple_apres)
    
    def _get_memory_optimization_suggestion(self, code_snippet: str, message: str) -> Tuple[str, str, str]:
        """Suggestion pour l'optimisation mémoire"""
        
        if 'range(' in code_snippet or 'huge' in code_snippet.lower() or 'large' in code_snippet.lower():
            suggestion = "Libérez la mémoire des grosses variables avec unset() après utilisation."
            exemple_apres = """// ❌ Code gourmand en mémoire
// $huge_array = range(1, 1000000);
// $result = array_sum($huge_array);
// return $result; // $huge_array reste en mémoire

// ✅ Code optimisé
$huge_array = range(1, 1000000);
$result = array_sum($huge_array);
unset($huge_array); // Libère la mémoire immédiatement
return $result;"""
        else:
            suggestion = "Libérez la mémoire avec unset() pour les grandes variables."
            exemple_apres = """// ❌ Variables qui restent en mémoire
// $large_data = get_massive_data();
// process_data($large_data);

// ✅ Code optimisé
$large_data = get_massive_data();
process_data($large_data);
unset($large_data); // Libère la mémoire"""
        
        return (suggestion, code_snippet, exemple_apres)
    
    def _get_complexity_suggestion(self, code_snippet: str, message: str) -> Tuple[str, str, str]:
        """Suggestion pour la complexité algorithmique"""
        
        if 'foreach' in code_snippet and ('id' in code_snippet or 'find' in message.lower()):
            suggestion = "Utilisez un tableau associatif indexé pour des recherches O(1) au lieu de O(n)."
            exemple_apres = """// ❌ Recherche O(n) - lent avec beaucoup de données
// foreach ($users as $user) {
//     if ($user['id'] == $search_id) {
//         return $user;
//     }
// }

// ✅ Recherche O(1) - rapide même avec beaucoup de données
// Créer un index une seule fois
$users_by_id = array_column($users, null, 'id');
// Recherche instantanée
return $users_by_id[$search_id] ?? null;"""
        else:
            suggestion = "Réduisez la complexité algorithmique avec de meilleures structures de données."
            exemple_apres = """// ❌ Algorithme inefficace
// Utilisez des structures de données appropriées
// et évitez les boucles imbriquées inutiles

// ✅ Algorithme optimisé
// Indexez vos données pour des accès rapides
// Utilisez array_column(), array_flip(), etc."""
        
        return (suggestion, code_snippet, exemple_apres)
    
    def _get_naming_suggestion(self, code_snippet: str, message: str) -> Tuple[str, str, str]:
        """Suggestion pour les noms de fonctions"""
        suggestion = "Utilisez des noms de fonctions descriptifs qui expliquent leur rôle."
        
        exemple_apres = """// ❌ Noms non descriptifs
// function test() { ... }
// function doIt() { ... }
// function func() { ... }

// ✅ Noms descriptifs
function validateUserCredentials() { ... }
function calculateTotalPrice() { ... }
function processPaymentTransaction() { ... }"""
        
        return (suggestion, code_snippet, exemple_apres)
    
    def _get_docstring_suggestion(self, code_snippet: str, message: str) -> Tuple[str, str, str]:
        """Suggestion pour la documentation"""
        suggestion = "Documentez vos fonctions publiques avec des docblocks PHPDoc."
        
        exemple_apres = """// ❌ Fonction sans documentation
// public function process($data) {
//     return $data * 2;
// }

// ✅ Fonction bien documentée
/**
 * Traite les données en les multipliant par deux
 * 
 * @param int|float $data Les données numériques à traiter
 * @return int|float Le résultat du traitement
 * @throws InvalidArgumentException Si les données ne sont pas numériques
 */
public function processData($data) {
    if (!is_numeric($data)) {
        throw new InvalidArgumentException('Les données doivent être numériques');
    }
    return $data * 2;
}"""
        
        return (suggestion, code_snippet, exemple_apres)
    
    def _get_null_check_suggestion(self, code_snippet: str, message: str) -> Tuple[str, str, str]:
        """Suggestion pour les vérifications null"""
        suggestion = "Vérifiez que les variables ne sont pas null avant d'appeler des méthodes."
        
        exemple_apres = """// ❌ Code dangereux sans vérification
// $query = $pdo->prepare($sql);
// $query->execute();

// ✅ Code sécurisé avec vérification
$query = $pdo->prepare($sql);
if ($query !== false) {
    $query->execute();
    $result = $query->fetchAll();
} else {
    throw new Exception('Erreur lors de la préparation de la requête');
}

// ✅ Alternative avec try-catch
try {
    $query = $pdo->prepare($sql);
    $query->execute();
    $result = $query->fetchAll();
} catch (PDOException $e) {
    error_log('Erreur PDO: ' . $e->getMessage());
    throw new Exception('Erreur de base de données');
}"""
        
        return (suggestion, code_snippet, exemple_apres)
    
    def _get_undefined_var_suggestion(self, code_snippet: str, message: str) -> Tuple[str, str, str]:
        """Suggestion pour les variables non définies"""
        suggestion = "Initialisez vos variables ou vérifiez leur existence."
        
        exemple_apres = """// ❌ Variable potentiellement non définie
// echo $undefined_var;

// ✅ Vérification avec isset()
if (isset($var)) {
    echo $var;
} else {
    echo 'Variable non définie';
}

// ✅ Valeur par défaut avec null coalescing
echo $var ?? 'Valeur par défaut';"""
        
        return (suggestion, code_snippet, exemple_apres)
    
    def _get_unused_var_suggestion(self, code_snippet: str, message: str) -> Tuple[str, str, str]:
        """Suggestion pour les variables inutilisées"""
        
        # Extraire le nom de la variable depuis le code
        var_match = re.search(r'\$([a-zA-Z_][a-zA-Z0-9_]*)', code_snippet)
        var_name = var_match.group(1) if var_match else 'unused_var'
        
        suggestion = f"Supprimez la variable ${var_name} car elle n'est pas utilisée."
        
        exemple_apres = f"""// ❌ Variable inutilisée qui pollue le code
// ${var_name} = 'some value';
// return $result;

// ✅ Code nettoyé - variable supprimée
return $result;

// ✅ Si nécessaire pour le debug, préfixez avec _
$_{var_name} = 'debug value'; // Indique l'intention"""
        
        return (suggestion, code_snippet, exemple_apres)
    
    def _get_global_var_suggestion(self, code_snippet: str, message: str) -> Tuple[str, str, str]:
        """Suggestion pour les variables globales"""
        suggestion = "Évitez les variables globales, utilisez des paramètres ou des classes."
        
        exemple_apres = """// ❌ Utilisation de variables globales
// global $config;
// function process() {
//     global $config;
//     return $config['setting'];
// }

// ✅ Injection de dépendances avec une classe
class ConfigService {
    private $config;
    
    public function __construct(array $config) {
        $this->config = $config;
    }
    
    public function getSetting($key) {
        return $this->config[$key] ?? null;
    }
}

// ✅ Alternative avec passage de paramètres
function process(array $config) {
    return $config['setting'];
}"""
        
        return (suggestion, code_snippet, exemple_apres)
    
    def _get_parameter_type_suggestion(self, code_snippet: str, message: str) -> Tuple[str, str, str]:
        """Suggestion pour l'ajout de types de paramètres"""
        suggestion = "Ajoutez des types aux paramètres pour améliorer les performances et la sécurité du type. PHP moderne peut optimiser le code typé avec le compilateur JIT."
        
        # Extraire les informations du contexte si disponible
        param_name = "param"
        suggested_type = "string"
        func_name = "processData"
        
        # Essayer d'extraire des informations du code
        if "function" in code_snippet:
            func_match = re.search(r'function\s+(\w+)', code_snippet)
            if func_match:
                func_name = func_match.group(1)
        
        exemple_apres = f"""// ❌ Sans typage (plus lent, moins sûr)
function {func_name}($data, $options) {{
    return processResult($data, $options);
}}

// ✅ Avec typage (optimisé JIT, détection d'erreurs précoce)
function {func_name}(array $data, array $options): array {{
    return processResult($data, $options);
}}

// ✅ Types plus spécifiques pour de meilleures performances
function calculatePrice(int $quantity, float $unitPrice): float {{
    return $quantity * $unitPrice;
}}

// ✅ Types nullables pour plus de sûreté (PHP 7.1+)
function findUser(?int $userId): ?User {{
    return $userId ? User::find($userId) : null;
}}"""
        
        return suggestion, code_snippet, exemple_apres

    def _get_return_type_suggestion(self, code_snippet: str, message: str) -> Tuple[str, str, str]:
        """Suggestion pour l'ajout de types de retour"""
        suggestion = "Spécifiez le type de retour pour permettre au compilateur JIT d'optimiser l'exécution. Cela améliore aussi la documentation du code."
        
        func_name = "getData"
        if "function" in code_snippet:
            func_match = re.search(r'function\s+(\w+)', code_snippet)
            if func_match:
                func_name = func_match.group(1)
        
        exemple_apres = f"""// ❌ Sans type de retour (pas d'optimisation JIT)
function {func_name}($id) {{
    return User::find($id);
}}

// ✅ Avec type de retour (optimisations JIT activées)
function {func_name}(int $id): ?User {{
    return User::find($id);
}}

// ✅ Exemples de types de retour courants
function getCount(): int {{
    return count($this->items);
}}

function getName(): string {{
    return $this->name ?? 'Unknown';
}}

function isActive(): bool {{
    return $this->status === 'active';
}}

function getItems(): array {{
    return $this->items;
}}

// ✅ Types union (PHP 8.0+)
function getValue(): string|int|null {{
    return $this->value;
}}"""
        
        return suggestion, code_snippet, exemple_apres

    def _get_mixed_type_suggestion(self, code_snippet: str, message: str) -> Tuple[str, str, str]:
        """Suggestion pour optimiser les types trop génériques"""
        suggestion = "Remplacez les types génériques par des types plus spécifiques pour de meilleures performances et une meilleure sécurité."
        
        exemple_apres = """// ❌ Types trop génériques (peu d'optimisation)
function process(mixed $data): mixed {
    return $data;
}

// ✅ Types spécifiques (optimisations JIT)
function processUser(User $user): UserData {
    return new UserData($user);
}

// ✅ Types union quand nécessaire (PHP 8.0+)
function format(string|int $value): string {
    return (string) $value;
}

// ✅ Types génériques avec contraintes
function transform(array $items): array {
    return array_map('strtoupper', $items);
}"""
        
        return suggestion, code_snippet, exemple_apres

    def _get_nullable_type_suggestion(self, code_snippet: str, message: str) -> Tuple[str, str, str]:
        """Suggestion pour l'utilisation de types nullable"""
        suggestion = "Utilisez les types nullable (?type) pour indiquer clairement qu'une valeur peut être null, ce qui améliore la sécurité du code."
        
        exemple_apres = """// ❌ Type ambigu (peut causer des erreurs)
function findUser(int $id): User {
    return User::find($id); // Peut retourner null !
}

// ✅ Type nullable explicite (sécurisé)
function findUser(int $id): ?User {
    return User::find($id);
}

// ✅ Utilisation sécurisée avec vérification
function getUserName(?User $user): string {
    return $user?->getName() ?? 'Guest';
}

// ✅ Paramètres optionnels avec types nullable
function createUser(string $name, ?string $email = null): User {
    return new User($name, $email);
}}

// ✅ Chaining sécurisé (PHP 8.0+)
$userName = $user?->getProfile()?->getName() ?? 'Unknown';"""
        
        return suggestion, code_snippet, exemple_apres