# PHP Optimizer

Outil d'analyse statique et d'optimisation de code PHP, écrit en Python.
Détecte les problèmes de performance, fuites mémoire, vulnérabilités de
sécurité, code mort et annotations de type manquantes, puis génère un
rapport console, JSON ou HTML.

> **Langues :** **Français** (ce fichier) · [English](README.md)

---

## Points forts

- **9 analyseurs spécialisés** orchestrés par `SimpleAnalyzer`
- **~70 règles** classées en 7 catégories avec des poids de sévérité de
  0 (très faible) à 4 (critique)
- **Suggestions adaptées à la version PHP cible** pour les annotations de
  type (PHP 7.0 → 8.2+)
- **Filtrage intelligent** par règle, par catégorie ou par poids minimum
- **Trois formats de rapport** : console couleur, HTML interactif, JSON
  pour CI
- **Aucune exécution PHP** : moteur d'analyse heuristique en regex pur

---

## Installation

```powershell
# Cloner le dépôt
git clone <url-du-depot> phpoptimizer
cd phpoptimizer

# Créer l'environnement virtuel (Windows)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Installer les dépendances et le paquet en mode éditable
pip install -r requirements.txt
pip install -e .
```

> Python ≥ 3.8 requis. La commande installée est `phpoptimizer`.

---

## Démarrage rapide

```powershell
# Analyser un fichier en mode verbeux
phpoptimizer analyze examples/example.php --verbose

# Analyser un dossier récursivement, sortie HTML
phpoptimizer analyze src/ --recursive --output-format html --output rapport.html

# Audit de sécurité uniquement (catégorie critique)
phpoptimizer analyze src/ --include-categories=security --recursive

# Ne montrer que les problèmes de poids ≥ 2
phpoptimizer analyze src/ --min-weight=2 --recursive

# Cibler une version PHP précise pour les annotations de type
phpoptimizer analyze src/ --php-version=7.4 --recursive
```

Exécution en module Python :

```powershell
python -m phpoptimizer analyze examples/ --recursive
```

Générer un fichier de configuration JSON par défaut :

```powershell
python -m phpoptimizer init-config example_config.json
```

---

## Options du CLI

| Option | Description |
| --- | --- |
| `--recursive`, `-r` | Parcourir les sous-dossiers |
| `--output-format` | `console` (par défaut), `json`, `html` |
| `--output`, `-o` | Fichier de sortie (obligatoire pour `json`/`html`) |
| `--rules` | Fichier de configuration JSON (voir plus bas) |
| `--severity` | Sévérité minimum : `info`, `warning`, `error` |
| `--include-rules` | Liste blanche de règles (séparées par des virgules) |
| `--exclude-rules` | Liste noire de règles |
| `--include-categories` | Catégories incluses uniquement |
| `--exclude-categories` | Catégories exclues |
| `--min-weight` | Poids minimum : `0`-`4` |
| `--php-version` | Version PHP cible (`7.0` … `8.2`) |
| `--verbose`, `-v` | Sortie détaillée (descriptions, suggestions, exemples) |

### Catégories et poids

| Catégorie | Poids | Exemples |
| --- | --- | --- |
| `security` | 4 / Critique | Injection SQL, XSS, hachage faible |
| `error` | 3 / Élevé | Foreach sur scalaire, code mort, syntaxe |
| `performance.critical` | 3 / Élevé | Tri/recherche en boucle, requête en boucle, imbrication profonde |
| `performance.general` | 2 / Moyen | Calculs répétés, appels dynamiques, regex |
| `memory` | 2 / Moyen | `unset()` manquant, gros tableaux, fuites |
| `code_quality` | 1 / Faible | Annotations de type, complexité, documentation |
| `psr` | 0 / Très faible | Longueur de ligne, nommage, indentation |

---

## Fichier de configuration JSON

```json
{
  "severity_level": "info",
  "excluded_paths": ["vendor/", "node_modules/"],
  "rules": {
    "performance.repetitive_array_access": {
      "enabled": true,
      "severity": "info",
      "params": { "min_occurrences": 2 }
    },
    "best_practices.line_length": {
      "enabled": true,
      "severity": "info",
      "params": { "max_line_length": 120 }
    },
    "best_practices.missing_documentation": { "enabled": false }
  }
}
```

Paramètres ajustables :

- `performance.repetitive_array_access.min_occurrences` (défaut `3`)
- `performance.large_arrays.max_array_size` (défaut `1000`)
- `performance.inefficient_loops.max_nested_loops` (défaut `3`)
- `best_practices.function_complexity.max_complexity` (défaut `10`)
- `best_practices.too_many_parameters.max_parameters` (défaut `5`)
- `best_practices.line_length.max_line_length` (défaut `120`)

---

## Détections couvertes

### Sécurité (critique)

- `security.sql_injection`, `security.xss_vulnerability`
- `security.weak_password_hashing`, `security.file_inclusion`
- `security.dangerous_function`, `security.authentication`
- `security.configuration`, `security.sensitive_data_exposure`

### Erreurs et code mort (poids élevé)

- `error.foreach_non_iterable` — foreach sur une valeur scalaire
- `error.null_method_call`, `error.uninitialized_variable`
- `error.assignment_in_condition`, `error.string_math_operation`
- `error.unclosed_quotes`, `error.syntax_*`
- `dead_code.unreachable_after_return` / `_after_break`
- `dead_code.always_false_condition`

### Performance critique

- `performance.inefficient_loops` — `count()` dans une condition de boucle
- `performance.deeply_nested_loops`, `performance.nested_loop_same_array`
- `performance.linear_search_in_loop`, `performance.sort_in_loop`
- `performance.heavy_function_in_loop`, `performance.query_in_loop`
- `performance.object_creation_in_loop`
- `performance.superglobal_access_in_loop`
- `performance.loop_fusion_opportunity`

### Performance générale

- `performance.constant_propagation`, `performance.repeated_calculations`
- `performance.repetitive_array_access`
- `performance.dynamic_method_call`, `performance.dynamic_function_call`
- `performance.string_concatenation`, `performance.regex_performance`
- `performance.unprepared_query`
- `performance.inefficient_file_reading`, `performance.repeated_file_checks`

### Mémoire

- `performance.memory_management` — gros tableau jamais libéré par `unset()`
- `performance.large_arrays`, `performance.excessive_memory`
- `performance.resource_leak`, `performance.circular_reference`
- `performance.unused_variables`, `performance.unused_global_variable`
- `performance.global_could_be_local`

### Qualité de code et PSR

- `performance.missing_parameter_type`, `performance.missing_return_type`
- `performance.mixed_type_opportunity`
- `best_practices.function_complexity`, `best_practices.too_many_parameters`
- `best_practices.complex_condition`, `best_practices.function_naming`
- `best_practices.line_length`, `best_practices.naming`
- `best_practices.brace_style`, `best_practices.mixed_indentation`

---

## Structure du projet

```
phpoptimizer/                     # Racine du dépôt
├── phpoptimizer/                 # Paquet Python importable (même nom → flat layout standard Python)
│   ├── __init__.py               # API publique : SimpleAnalyzer, ReportGenerator, Config
│   ├── __main__.py               # Point d'entrée `python -m phpoptimizer`
│   ├── cli.py                    # CLI Click (analyze, version, init-config)
│   ├── config.py                 # Config, RuleConfig, catégories, poids
│   ├── simple_analyzer.py        # Orchestrateur des analyseurs spécialisés
│   ├── reporter.py               # Rapports console, JSON et HTML
│   ├── suggestions.py            # Suggestions détaillées avant/après
│   └── analyzers/                # 9 analyseurs spécialisés
│       ├── base_analyzer.py
│       ├── loop_analyzer.py
│       ├── security_analyzer.py
│       ├── error_analyzer.py
│       ├── performance_analyzer.py
│       ├── memory_analyzer.py
│       ├── code_quality_analyzer.py
│       ├── dead_code_analyzer.py
│       ├── dynamic_calls_analyzer.py
│       └── type_hint_analyzer.py
├── tests/                        # Tests unitaires (lancés via pytest)
├── examples/                     # Fichiers PHP pour vérifications manuelles
├── CATEGORIES_GUIDE.md           # Guide de filtrage
├── DYNAMIC_CALLS_OPTIMIZATION.md # Détails sur les appels dynamiques
├── CONTRIBUTING.md               # Guide de contribution
├── agents.md                     # Carte rapide pour les agents IA travaillant sur le dépôt
├── requirements.txt              # Dépendances Python
└── setup.py                      # Métadonnées du paquet
```

> Le sous-dossier `phpoptimizer/` est le paquet Python importable — il
> porte le même nom que le dossier racine, ce qui correspond au "flat
> layout" standard recommandé par la communauté Python.

---

## Architecture en un paragraphe

`SimpleAnalyzer` lit un fichier PHP comme un simple texte, puis demande à
chaque analyseur spécialisé (`LoopAnalyzer`, `SecurityAnalyzer`, …) de
retourner ses issues (de simples dictionnaires construits via
`BaseAnalyzer._create_issue`). Les issues sont ensuite filtrées par
`Config.should_apply_rule()` (la règle doit être activée et passer les
filtres de catégorie / poids actifs), dédupliquées et triées par numéro
de ligne. `ReportGenerator` produit la sortie.

Pour ajouter une règle :

1. Implémenter la détection dans le bon analyseur de
   `phpoptimizer/analyzers/` en utilisant `_create_issue(rule_name, …)`
2. Déclarer le `rule_name` dans `Config._init_default_rules()` avec une
   catégorie, une sévérité et un poids — sinon la règle sera filtrée
3. Ajouter éventuellement une suggestion détaillée dans
   `phpoptimizer/suggestions.py`
4. Ajouter au moins un test positif et un test négatif dans `tests/`

Voir [`agents.md`](agents.md) et [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## Tests

```powershell
python -m pytest tests/
python -m pytest tests/test_analyzer.py -v
```

La suite est écrite en style `unittest` et lancée via `pytest`.

---

## Exemple de sortie

```
============================================================
  RAPPORT D'ANALYSE PHP OPTIMIZER
============================================================
Statistiques générales:
   Fichiers analysés : 1/1
   Problèmes détectés : 5

Répartition par sévérité:
   Erreurs : 1
   Avertissements : 2
   Informations : 2

📄 examples/simple_test.php
   📍 Ligne 12 : Injection SQL : requête SELECT avec concaténation de variable
      💡 Solution : Utiliser une requête préparée avec paramètres liés
   📍 Ligne 34 : Gros tableau $large_data (50000 éléments) non libéré avec unset()
      💡 Solution : Appeler unset($large_data) une fois la donnée inutile
```

---

## Contribution

Voir [CONTRIBUTING.md](CONTRIBUTING.md). Les rapports de bugs, nouvelles
règles et nouveaux analyseurs sont les bienvenus.

---

## Licence

MIT — voir [LICENSE](LICENSE).
