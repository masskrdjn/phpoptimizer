# Analyse sécurité et règles actuelles (PR follow-up)

## 1) Potentielles failles de sécurité dans l'application des règles

- **Analyse purement regex ligne par ligne** : la détection actuelle ne suit pas les flux de données (taint/source->sink), ce qui peut rater des vulnérabilités multi-lignes (ex: variable contaminée assignée plus haut puis réutilisée). Les détections fonctionnent surtout quand la source utilisateur apparaît directement sur la même ligne que le sink.
- **Contexte d'assainissement incomplet** : plusieurs règles vérifient juste la présence textuelle de fonctions d'assainissement (`htmlspecialchars`, etc.) sans valider le bon contexte d'encodage (HTML, attribut, JS, URL) ni l'ordre des transformations.
- **Modèle SQL partiel** : les patterns SQL couvrent plusieurs cas communs mais peuvent manquer des injections via concaténation plus indirecte (assemblage progressif de requête, méthode intermédiaire, wrappers custom) et générer des faux positifs hors SQL.
- **Filtrage strict des règles inconnues** : toute issue non déclarée dans la config est éliminée, ce qui peut masquer des détections si une règle a été ajoutée côté analyseur mais pas en configuration.
- **Sévérité uniforme sur des cas hétérogènes** : certaines règles critiques utilisent des motifs simples qui peuvent surclasser des faux positifs (bruit) et réduire la confiance développeur.

## 2) Ajouts de règles sécurité recommandés (priorité)

### Priorité haute

1. **`security.command_injection`**
   - Détecter usage non contrôlé de `exec`, `system`, `shell_exec`, backticks, `passthru`, `popen`, `proc_open` avec entrées utilisateur.
2. **`security.insecure_deserialization`**
   - Détecter `unserialize()` sur données non fiables, notamment via `$_POST`, `$_GET`, `$_COOKIE`, payload externe.
3. **`security.path_traversal`**
   - Détecter concaténation de chemins depuis entrées utilisateur (`../`, wrappers `php://`, `phar://`, etc.).
4. **`security.ssrf`**
   - Détecter appels HTTP sortants (`file_get_contents`, cURL, Guzzle) utilisant entrées non validées.
5. **`security.csrf_missing_protection`**
   - Détecter formulaires/actions sensibles sans token CSRF visible.

### Priorité moyenne

6. **`security.open_redirect`**
   - `header('Location: ' . $userInput)` sans whitelist de domaines.
7. **`security.weak_randomness`**
   - Usage de `rand()/mt_rand()/uniqid()` dans contextes sécurité (tokens, reset password).
8. **`security.insecure_cookie_flags`**
   - Cookies sans `Secure`, `HttpOnly`, `SameSite` (ou valeurs faibles).
9. **`security.jwt_misconfiguration`**
   - Algo `none`, absence de vérification signature/issuer/audience/exp.
10. **`security.file_upload_validation`**
    - Upload sans validation extension/MIME/taille/stockage hors webroot.

## 3) Faiblesses actuelles d'application des règles

- **Absence de corrélation inter-règles** : pas de score de confiance combiné (ex: source utilisateur + sink dangereux + absence de sanitization).
- **Absence de mode framework-aware** : Laravel/Symfony/WordPress ont des protections natives qui devraient réduire les faux positifs (ou ajouter des règles dédiées).
- **Manque de métadonnées de preuve** : une issue pourrait fournir `source`, `sink`, `sanitizer détecté/non détecté`, pour faciliter le triage.
- **Pas de niveaux de confiance** (high/medium/low confidence) en plus de la sévérité.
- **Peu de contrôle de bruit** : pas de baseline/suppression fine par hash d'issue ou commentaire inline.

## 4) Plan d'amélioration concret

1. Introduire un mini moteur de **taint tracking local** (intra-fonction) pour `source -> propagation -> sink`.
2. Ajouter un champ d'issue `confidence` et `evidence`.
3. Étendre le `SecurityAnalyzer` avec les 5 règles de priorité haute.
4. Ajouter chaque nouvelle règle dans `Config._init_default_rules()` pour éviter le filtrage silencieux.
5. Ajouter des tests positifs/négatifs par règle pour limiter les faux positifs.
6. Documenter les limites connues par règle (README / guide sécurité).

## 5) Risque global actuel (estimation)

- **Couverture sécurité actuelle** : **basique à intermédiaire** (utile pour erreurs évidentes).
- **Risque principal** : faux négatifs sur vulnérabilités réelles complexes et faux positifs sur motifs textuels ambigus.
- **Impact opérationnel** : bon outil de pré-filtrage, insuffisant seul comme contrôle sécurité principal sans revue humaine/SAST plus avancé.
