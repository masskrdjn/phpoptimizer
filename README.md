# PHP Optimizer

Static analysis and optimization tool for PHP code, written in Python.
Detects performance issues, memory leaks, security vulnerabilities, dead
code and missing type hints, then produces console, JSON or HTML reports.

> **Languages :** [Français](README_FR.md) · **English** (this file)

---

## Highlights

- **9 specialized analyzers** orchestrated by `SimpleAnalyzer`
- **~70 rules** organised in 7 categories with severity weights from 0
  (very low) to 4 (critical)
- **PHP version-aware suggestions** for type hints (PHP 7.0 → 8.2+)
- **Smart filtering** by rule, category or minimum weight
- **Three output formats**: colored console, interactive HTML, JSON for CI
- **Pure regex / heuristic engine** — no PHP runtime needed

---

## Installation

```powershell
# Clone the repository
git clone <your-repo-url> phpoptimizer
cd phpoptimizer

# Create a virtual environment (Windows)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies and the package itself in editable mode
pip install -r requirements.txt
pip install -e .
```

> Python ≥ 3.8 is required. The console entry point is `phpoptimizer`.

---

## Quick start

```powershell
# Analyze one file with detailed console output
phpoptimizer analyze examples/example.php --verbose

# Analyze a directory recursively, write an HTML report
phpoptimizer analyze path/to/php-project/ --recursive --output-format html --output report.html

# Security audit only (critical category)
phpoptimizer analyze path/to/php-project/ --include-categories=security --recursive

# Show only medium-or-higher severity issues
phpoptimizer analyze path/to/php-project/ --min-weight=2 --recursive

# Target a specific PHP version for type-hint suggestions
phpoptimizer analyze path/to/php-project/ --php-version=7.4 --recursive
```

You can also run the package as a module:

```powershell
python -m phpoptimizer analyze examples/ --recursive
```

Generate a default JSON config file:

```powershell
python -m phpoptimizer init-config example_config.json
```

---

## CLI options

| Option | Description |
| --- | --- |
| `--recursive`, `-r` | Recurse into sub-directories |
| `--output-format` | `console` (default), `json`, `html` |
| `--output`, `-o` | Output file path (mandatory for `json`/`html`) |
| `--rules` | Path to a JSON config file (see below) |
| `--severity` | Minimum severity: `info`, `warning`, `error` |
| `--include-rules` | Whitelist of rule names (comma-separated) |
| `--exclude-rules` | Blacklist of rule names (comma-separated) |
| `--include-categories` | Whitelist of categories |
| `--exclude-categories` | Blacklist of categories |
| `--min-weight` | Minimum weight: `0`-`4` |
| `--php-version` | Target PHP version (`7.0` … `8.2`) |
| `--verbose`, `-v` | Detailed output (descriptions, suggestions, fix examples) |

### Categories and weights

| Category | Weight | Examples |
| --- | --- | --- |
| `security` | 4 / Critical | SQL injection, XSS, weak hashing |
| `error` | 3 / High | Foreach on scalar, dead code, syntax issues |
| `performance.critical` | 3 / High | Sort/search in loop, query in loop, deeply nested |
| `performance.general` | 2 / Medium | Repeated calculations, dynamic calls, regex |
| `memory` | 2 / Medium | Missing `unset()`, large arrays, resource leaks |
| `code_quality` | 1 / Low | Type hints, function complexity, documentation |
| `psr` | 0 / Very low | Line length, naming, indentation |

---

## JSON configuration file

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

Tunable parameters:

- `performance.repetitive_array_access.min_occurrences` (default `3`)
- `performance.large_arrays.max_array_size` (default `1000`)
- `performance.inefficient_loops.max_nested_loops` (default `3`)
- `best_practices.function_complexity.max_complexity` (default `10`)
- `best_practices.too_many_parameters.max_parameters` (default `5`)
- `best_practices.line_length.max_line_length` (default `120`)

---

## What it detects

### Security (critical)

- `security.sql_injection`, `security.xss_vulnerability`
- `security.weak_password_hashing`, `security.file_inclusion`
- `security.dangerous_function`, `security.authentication`
- `security.configuration`, `security.sensitive_data_exposure`

### Errors and dead code (high)

- `error.foreach_non_iterable` — foreach on a scalar variable
- `error.null_method_call`, `error.uninitialized_variable`
- `error.assignment_in_condition`, `error.string_math_operation`
- `error.unclosed_quotes`, `error.syntax_*`
- `dead_code.unreachable_after_return` / `_after_break`
- `dead_code.always_false_condition`

### Performance (critical / high)

- `performance.inefficient_loops` — `count()` inside loop conditions
- `performance.deeply_nested_loops`, `performance.nested_loop_same_array`
- `performance.linear_search_in_loop`, `performance.sort_in_loop`
- `performance.heavy_function_in_loop`, `performance.query_in_loop`
- `performance.object_creation_in_loop`
- `performance.superglobal_access_in_loop`
- `performance.loop_fusion_opportunity`

### Performance (general / medium)

- `performance.constant_propagation`, `performance.repeated_calculations`
- `performance.repetitive_array_access`
- `performance.dynamic_method_call`, `performance.dynamic_function_call`
- `performance.string_concatenation`, `performance.regex_performance`
- `performance.unprepared_query`
- `performance.inefficient_file_reading`, `performance.repeated_file_checks`

### Memory

- `performance.memory_management` — large array not `unset()`
- `performance.large_arrays`, `performance.excessive_memory`
- `performance.resource_leak`, `performance.circular_reference`
- `performance.unused_variables`, `performance.unused_global_variable`
- `performance.global_could_be_local`

### Code quality and PSR

- `performance.missing_parameter_type`, `performance.missing_return_type`
- `performance.mixed_type_opportunity`
- `best_practices.function_complexity`, `best_practices.too_many_parameters`
- `best_practices.complex_condition`, `best_practices.function_naming`
- `best_practices.line_length`, `best_practices.naming`
- `best_practices.brace_style`, `best_practices.mixed_indentation`

---

## Project layout

```
phpoptimizer/                     # Repository root
├── src/
│   └── phpoptimizer/             # Importable Python package
│       ├── __init__.py           # Public API: SimpleAnalyzer, ReportGenerator, Config
│       ├── __main__.py           # `python -m phpoptimizer` entry point
│       ├── cli.py                # Click CLI (analyze, version, init-config)
│       ├── config.py             # Config + RuleConfig + categories/weights
│       ├── simple_analyzer.py    # Orchestrator that runs each specialized analyzer
│       ├── reporter.py           # Console, JSON and HTML reports
│       ├── suggestions.py        # Detailed before/after correction examples
│       └── analyzers/            # 9 specialized analyzers
│           ├── base_analyzer.py
│           ├── loop_analyzer.py
│           ├── security_analyzer.py
│           ├── error_analyzer.py
│           ├── performance_analyzer.py
│           ├── memory_analyzer.py
│           ├── code_quality_analyzer.py
│           ├── dead_code_analyzer.py
│           ├── dynamic_calls_analyzer.py
│           └── type_hint_analyzer.py
├── tests/                        # Unit tests (run via pytest)
├── examples/                     # PHP files used for manual checks
├── CATEGORIES_GUIDE.md           # Filtering guide
├── DYNAMIC_CALLS_OPTIMIZATION.md # Dynamic calls deep-dive
├── CONTRIBUTING.md               # Contribution guide
├── agents.md                     # Quick map for AI agents working on the repo
├── requirements.txt              # Python dependencies
└── setup.py                      # Package metadata
```

> The package uses the standard Python `src/` layout: repository metadata,
> tests and examples stay at the root, while importable code lives under
> `src/phpoptimizer/`.

---

## Architecture in one paragraph

`SimpleAnalyzer` reads a PHP file as raw text, then asks each specialized
analyzer (`LoopAnalyzer`, `SecurityAnalyzer`, …) to return a list of issues
(plain dictionaries built via `BaseAnalyzer._create_issue`). Issues are
then filtered by `Config.should_apply_rule()` (rule must be enabled and
match the active category / weight filters), deduplicated and sorted.
`ReportGenerator` renders the result.

Adding a rule:

1. Implement detection in the right analyzer in `src/phpoptimizer/analyzers/`
   using `_create_issue(rule_name, …)`
2. Declare the new `rule_name` in `Config._init_default_rules()` with a
   category, severity and weight — otherwise it will be filtered out
3. Optionally add a custom suggestion in `src/phpoptimizer/suggestions.py`
4. Add at least one positive and one negative test in `tests/`

See [`agents.md`](agents.md) and [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## Tests

```powershell
python -m pytest tests/
python -m pytest tests/test_analyzer.py -v
```

The test suite uses `unittest` style and is executed via `pytest`.

---

## Example output

```
============================================================
  PHP OPTIMIZER ANALYSIS REPORT
============================================================
General stats:
   Files analyzed: 1/1
   Issues found: 5

By severity:
   Errors: 1
   Warnings: 2
   Info: 2

📄 examples/simple_test.php
   📍 Line 12: SQL injection: SELECT query with variable concatenation
      💡 Solution: Use a prepared statement with bound parameters
   📍 Line 34: Large array $large_data (50000 elements) not freed with unset()
      💡 Solution: Call unset($large_data) once it is no longer needed
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Bug reports, additional rules and
new analyzers are welcome.

---

## License

MIT — see [LICENSE](LICENSE).
