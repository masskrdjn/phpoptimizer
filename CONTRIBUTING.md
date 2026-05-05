# Contribution Guide for PHP Optimizer

Thank you for your interest in contributing to PHP Optimizer ! This guide will help you get started.

## Types of contributions

### 🐛 Reporting bugs
- Use the GitHub issue template
- Include a minimal PHP code example that reproduces the problem
- Specify the Python version and OS used
- Describe the expected vs observed behavior

### 💡 Proposing features
- Open an issue to discuss the idea before coding
- Describe the PHP pattern you want to detect
- Explain why it's a performance/security problem
- Suggest improvement ideas

### 🔧 Contributing code
- Fork the repository
- Create a branch for your feature : `git checkout -b feature/new-rule`
- Follow the code conventions (see below)
- Add tests for your contribution
- Submit a pull request

## Development setup

```bash
# 1. Fork and clone
git clone https://github.com/your-username/phpoptimizer.git
cd phpoptimizer

# 2. Virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or .\venv\Scripts\Activate  # Windows

# 3. Install in development mode
pip install -r requirements.txt
pip install -e .

# 4. Verify everything works
python -m pytest tests/
python -m phpoptimizer analyze examples/example.php
```

## Code structure

```
phpoptimizer/
├── src/
│   └── phpoptimizer/
│       ├── simple_analyzer.py    # ⭐ Main analyzer - add your rules here
│       ├── cli.py                # Command line interface
│       ├── reporter.py           # Report generation
│       ├── config.py             # Configuration management
│       └── rules/                # 🚧 Future modular rules system
├── tests/
│   ├── test_analyzer.py     # ⭐ Main tests - add your tests here
│   └── test_*.py           # Specialized tests
└── examples/
    ├── *.php               # ⭐ Code examples - add your test cases
```

## Adding a new detection rule

### 1. Identify the problematic pattern

Example: detecting `array_push()` in a loop

```php
// ❌ Inefficient
for ($i = 0; $i < 1000; $i++) {
    array_push($array, $value);  // Reallocation at each iteration
}

// ✅ Efficient
$array[] = $value;  // Or collect then array_merge
```

### 2. Add detection in `src/phpoptimizer/simple_analyzer.py`

```python
# In the line analysis loop
if (in_loop and loop_stack and 
    re.search(r'\barray_push\s*\(', line_stripped)):
    issues.append({
        'rule_name': 'performance.array_push_in_loop',
        'message': 'array_push() in a loop is inefficient',
        'file_path': str(file_path),
        'line': line_num,
        'column': 0,
        'severity': 'warning',
        'issue_type': 'performance',
        'suggestion': 'Use $array[] = $value or array_merge() after the loop',
        'code_snippet': line.strip()
    })
```

### 3. Add a test

```python
# In tests/test_analyzer.py
def test_array_push_in_loop():
    php_code = '''<?php
    for ($i = 0; $i < 100; $i++) {
        array_push($data, $i);  // Should be detected
    }
    ?>'''
    
    issues = analyze_php_code(php_code)
    array_push_issues = [i for i in issues if i['rule_name'] == 'performance.array_push_in_loop']
    
    assert len(array_push_issues) == 1
    assert array_push_issues[0]['line'] == 3
    assert array_push_issues[0]['severity'] == 'warning'
```

### 4. Add a PHP file example

```php
<?php
// examples/array_push_test.php
// Test detection of array_push in a loop

for ($i = 0; $i < 1000; $i++) {
    array_push($large_array, $value);  // ❌ Should be detected
}

$small_array[] = $value;  // ✅ Should not be detected
?>
```

### 5. Test your contribution

```bash
# Unit tests
python -m pytest tests/test_analyzer.py::test_array_push_in_loop -v

# Test on the example
python -m phpoptimizer analyze examples/array_push_test.php -v

# Full tests
python -m pytest tests/
```

## Code conventions

### Python style
- **PEP 8** : Use `black` for formatting : `pip install black && black .`
- **Type hints** : Add type annotations
- **Docstrings** : Document public functions
- **Descriptive names** : `detect_inefficient_loops()` instead of `check_loops()`

### Error messages
- **Clear and actionable** : "Use isset() instead of array_key_exists()"
- **Contextual** : Mention why it's problematic
- **Suggest solutions** : Propose an alternative

### Tests
- **One test per rule** : Test each pattern individually
- **Negative cases** : Check that good patterns are not detected
- **Edge cases** : Test complex syntax, nesting, etc.

### PHP examples
- **Explicit comments** : Mark what should be detected
- **Variety** : Include different complexity levels
- **Realistic** : Based on real PHP code

## Review process

### Before submitting
1. ✅ Tests pass : `python -m pytest tests/`
2. ✅ Correct formatting : `black src/phpoptimizer/ tests/`
3. ✅ Example works : Test on a real PHP file
4. ✅ Documentation updated : README if necessary

### Pull Request
- **Descriptive title** : "Add detection of array_push() in loop"
- **Detailed description** : Explain the detected problem and solution
- **Screenshots** : Show before/after output if relevant
- **Tests included** : Mention added tests

### Acceptance criteria
- ✅ **Functional** : The rule correctly detects issues
- ✅ **No false positives** : Does not report correct code
- ✅ **Performance** : Does not significantly impact analysis time
- ✅ **Tested** : Appropriate test coverage
- ✅ **Documented** : Clear messages and updated README

## High-priority rules sought

### Performance
- [ ] `array_push()` in loops
- [ ] Repeated `array_merge()` vs accumulation
- [ ] `in_array()` on large arrays (suggest `isset()` with flip)
- [ ] String allocation with `str_repeat()` vs concatenation
- [ ] `file_get_contents()` vs `fread()` for large files

### Security
- [ ] `eval()` with user input
- [ ] `serialize()`/`unserialize()` without validation
- [ ] `extract()` with external data
- [ ] Unescaped HTTP headers
- [ ] Cookies without secure flags

### PHP 8+ best practices
- [ ] `array_key_exists()` vs `isset()` with null coalescing
- [ ] Arrow functions vs classic anonymous
- [ ] `match` vs `switch` for better performance
- [ ] Attributes vs docblock annotations

## Questions ?

- 💬 **GitHub Discussions** : For general questions
- 🐛 **Issues** : For bugs and feature requests

Thank you for helping improve PHP Optimizer ! 🚀
