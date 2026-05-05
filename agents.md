# Guide agents - PHP Optimizer

Ce fichier sert de carte rapide pour tout agent qui reprend ce projet. Lis-le avant de modifier le code, puis verifie les fichiers concernes localement : ce guide resume l'etat actuel du depot, il ne remplace pas la lecture du code.

## Vue d'ensemble

PHP Optimizer est un outil Python qui analyse du code PHP et produit des rapports console, JSON ou HTML. Le paquet principal est `phpoptimizer`, l'entree CLI est `phpoptimizer.cli:main`, et l'analyse courante passe par `SimpleAnalyzer`.

Le flux principal est :

1. `phpoptimizer/cli.py` collecte les options Click et les fichiers `.php`.
2. `phpoptimizer/config.py` construit la configuration, les regles, categories, poids et filtres.
3. `phpoptimizer/simple_analyzer.py` lit le fichier PHP, appelle chaque analyseur specialise, filtre et deduplique les issues.
4. `phpoptimizer/reporter.py` rend les resultats en console, JSON ou HTML.

## Installation et environnement

Commandes utiles depuis la racine du depot :

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

Dependances principales :

- `click` pour le CLI.
- `colorama` pour les couleurs console Windows.
- `phply` pour le parsing PHP historique.
- `dataclasses` et `typing-extensions` pour compatibilite.

Le paquet declare Python `>=3.8` dans `setup.py`.

## Commandes de developpement

Tests complets :

```powershell
python -m pytest tests/
```

Tests cibles :

```powershell
python -m pytest tests/test_analyzer.py -v
python -m pytest tests/test_dynamic_calls_analyzer.py -v
python -m pytest tests/test_type_hint_analyzer.py -v
python -m pytest tests/test_type_hint_versions.py -v
```

Execution CLI en mode module :

```powershell
python -m phpoptimizer analyze examples/example.php --verbose
python -m phpoptimizer analyze examples/ --recursive --output-format json --output report.json
python -m phpoptimizer analyze examples/type_hints_example.php --php-version 8.2 --verbose
```

Apres `pip install -e .`, la commande console declaree est :

```powershell
phpoptimizer analyze examples/example.php --verbose
```

Generer une configuration par defaut :

```powershell
python -m phpoptimizer init-config example_config.json
```

## Structure importante

- `phpoptimizer/cli.py` : commandes Click `analyze`, `version`, `init-config`.
- `phpoptimizer/config.py` : `Config`, `RuleConfig`, `RuleCategory`, `SeverityWeight`, regles par defaut.
- `phpoptimizer/simple_analyzer.py` : orchestrateur des analyseurs specialises.
- `phpoptimizer/analyzers/base_analyzer.py` : contrat commun et helper `_create_issue`.
- `phpoptimizer/analyzers/*.py` : detections specialisees.
- `phpoptimizer/reporter.py` : generation console, JSON, HTML.
- `phpoptimizer/suggestions.py` : suggestions detaillees associees aux `rule_name`.
- `phpoptimizer/parser.py` et `phpoptimizer/analyzer.py` : ancien systeme/parser, encore expose par `__init__.py`.
- `phpoptimizer/rules/` : ancien ou futur systeme de regles modulaires ; ne pas supposer qu'il pilote le flux principal actuel.
- `tests/` : tests unitaires `unittest` executes via `pytest`.
- `examples/` : exemples PHP pour essais manuels.
- `README.md`, `README_FR.md`, `CATEGORIES_GUIDE.md`, `CONTRIBUTING.md` : documentation utilisateur et contribution.

## Analyseurs actuels

`SimpleAnalyzer` instancie ces analyseurs dans cet ordre :

1. `LoopAnalyzer`
2. `SecurityAnalyzer`
3. `ErrorAnalyzer`
4. `PerformanceAnalyzer`
5. `MemoryAnalyzer`
6. `CodeQualityAnalyzer`
7. `DeadCodeAnalyzer`
8. `DynamicCallsAnalyzer`
9. `TypeHintAnalyzer`

Chaque analyseur herite de `BaseAnalyzer` et implemente :

```python
def analyze(self, content: str, file_path: Path, lines: List[str]) -> List[Dict[str, Any]]:
    ...
```

Les issues doivent suivre le format cree par `_create_issue` :

```python
{
    "rule_name": "...",
    "message": "...",
    "file_path": "...",
    "line": 1,
    "column": 0,
    "severity": "info|warning|error",
    "issue_type": "security|performance|error|...",
    "suggestion": "...",
    "code_snippet": "..."
}
```

Important : `SimpleAnalyzer` appelle ensuite `config.should_apply_rule(rule_name)`. Une issue dont le `rule_name` n'est pas declare dans `Config._init_default_rules()` sera filtree par defaut. Quand tu ajoutes une nouvelle detection, ajoute aussi sa configuration.

## Categories et poids

Les categories connues sont dans `RuleCategory` :

- `security`
- `error`
- `performance.critical`
- `performance.general`
- `memory`
- `code_quality`
- `psr`

Les poids sont dans `SeverityWeight` :

- `4` : critique, surtout securite.
- `3` : eleve, erreurs ou performance majeure.
- `2` : moyen, optimisations importantes.
- `1` : faible, qualite de code.
- `0` : tres faible, formatage et conventions.

Le CLI expose les filtres :

```powershell
--include-rules
--exclude-rules
--include-categories
--exclude-categories
--min-weight
--php-version
```

Avant de changer ce systeme, lire `CATEGORIES_GUIDE.md` et les tests associes.

## Ajouter une nouvelle regle

Procedure recommandee :

1. Choisir l'analyseur specialise existant le plus proche, ou creer un fichier dans `phpoptimizer/analyzers/` si la responsabilite est nouvelle.
2. Utiliser `_create_issue(...)` plutot qu'un dictionnaire ad hoc, sauf si le fichier suit deja un motif local precis.
3. Ajouter le `rule_name` dans `Config._init_default_rules()` avec categorie, severite, poids et parametres.
4. Si l'analyseur est nouveau, l'importer dans `phpoptimizer/analyzers/__init__.py` et l'ajouter a `SimpleAnalyzer.analyzers`.
5. Ajouter ou ajuster les suggestions detaillees dans `phpoptimizer/suggestions.py` si le rapport doit montrer un exemple de correction.
6. Ajouter des tests dans `tests/test_*.py` avec au moins un cas positif et, si le risque de faux positif existe, un cas negatif.
7. Ajouter un exemple PHP dans `examples/` seulement si cela aide a valider manuellement ou documenter la regle.
8. Lancer les tests cibles puis, si possible, `python -m pytest tests/`.

Convention de nommage des regles : `domaine.nom_precis`, par exemple `security.sql_injection`, `performance.dynamic_method_call`, `best_practices.line_length`.

## Ajouter ou modifier le CLI

Le CLI utilise Click dans `phpoptimizer/cli.py`. Pour une nouvelle option :

1. Ajouter un `@click.option`.
2. Passer la valeur a `Config` ou a `SimpleAnalyzer`.
3. Verifier l'effet avec un test CLI si possible, sinon au moins une execution manuelle sur `examples/`.
4. Mettre a jour `README.md` et `README_FR.md` si l'option est utilisateur.

Attention : le nom de commande installe par `setup.py` est `phpoptimizer`, mais certains documents anciens mentionnent `php-optimizer`. Privilegier `phpoptimizer` pour les nouvelles docs.

## Tests et style

Les tests sont ecrits avec `unittest`, mais l'usage projet est de les lancer via `pytest`.

Bonnes pratiques locales :

- Garder les tests proches du comportement modifie.
- Utiliser des snippets PHP minimaux avec `tempfile` quand on teste `SimpleAnalyzer.analyze_file`.
- Filtrer les issues par `issue["rule_name"]`.
- Verifier les cas de non-detection pour limiter les faux positifs.
- Ne pas introduire de refactor large sans besoin direct.
- Respecter les patterns regex et helpers existants dans chaque analyseur.

Il n'y a pas de configuration `black`, `ruff` ou `mypy` dans le depot. `CONTRIBUTING.md` recommande Black, mais ne l'applique pas automatiquement.

## Points d'attention

- Le worktree peut contenir des fichiers non suivis. Au moment de creation de ce guide, `test_categories.py` etait non suivi : ne pas le supprimer ni le modifier sans demande explicite.
- Plusieurs fichiers de documentation contiennent des caracteres accentues et symboles. Sous PowerShell, l'affichage peut etre degrade selon l'encodage de la console ; ne conclus pas trop vite que le fichier est corrompu.
- `reporter.py` importe `AnalysisResult` et `Issue` depuis `phpoptimizer/analyzer.py`, mais le flux principal CLI utilise des dictionnaires issus de `SimpleAnalyzer`.
- `Config.should_apply_rule()` filtre strictement les regles inconnues. C'est une source frequente de "ma detection ne sort pas".
- Certains noms de regles testes peuvent ne pas etre tous declares dans `Config`; verifier avant de modifier le filtrage global.
- `rules/` existe, mais le chemin principal actuel est `analyzers/` plus `SimpleAnalyzer`.
- `collect_php_files()` dans `cli.py` ne consulte pas `Config.should_process_file()`. Si tu veux appliquer exclusions, extensions ou taille max au CLI, il faut modifier ce chemin consciemment.
- Eviter les commandes destructrices Git. Le depot peut contenir du travail utilisateur non commite.

## Documentation a consulter selon la tache

- Usage general : `README.md` et `README_FR.md`.
- Categories, poids et filtres : `CATEGORIES_GUIDE.md`.
- Ajout de regles et conventions : `CONTRIBUTING.md`.
- Appels dynamiques : `DYNAMIC_CALLS_OPTIMIZATION.md`.
- Historique de changements : `CHANGELOG.md`.

## Checklist avant de rendre la main

Avant de finaliser une modification :

1. `git status --short` pour distinguer tes changements du travail existant.
2. Tests cibles sur les fichiers touches.
3. Tests complets si la modification touche `Config`, `SimpleAnalyzer`, le CLI ou un contrat commun.
4. Verification manuelle CLI si le comportement utilisateur change.
5. Mise a jour de la documentation si une option, categorie ou regle visible change.

