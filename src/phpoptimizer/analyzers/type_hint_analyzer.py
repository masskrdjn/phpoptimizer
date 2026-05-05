"""
Type Hint Analyzer - Détecte les opportunités d'ajout de type hints pour optimiser les performances PHP
"""

import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from .base_analyzer import BaseAnalyzer


class TypeHintAnalyzer(BaseAnalyzer):
    """Analyseur pour la détection des opportunités d'ajout de type hints PHP"""
    
    def __init__(self, config=None):
        super().__init__()
        self.config = config  # Configuration pour connaître la version PHP cible
        
        # Patterns pour détecter les fonctions sans type hints
        self.function_pattern = re.compile(
            r'(?:(?:public|private|protected|static)\s+)*function\s+(\w+)\s*\(([^)]*)\)(?:\s*:\s*(\w+(?:\|\w+)*|\?\w+))?\s*\{',
            re.IGNORECASE | re.MULTILINE
        )
        
        # Patterns pour détecter les types à partir du contexte
        self.type_inference_patterns = {
            'int': [
                re.compile(r'\$\w+\s*=\s*\d+'),  # $var = 42
                re.compile(r'\$\w+\s*=\s*count\('),  # $var = count()
                re.compile(r'\$\w+\s*=\s*strlen\('),  # $var = strlen()
                re.compile(r'\$\w+\s*=\s*sizeof\('),  # $var = sizeof()
            ],
            'float': [
                re.compile(r'\$\w+\s*=\s*\d+\.\d+'),  # $var = 3.14
                re.compile(r'\$\w+\s*=\s*floatval\('),  # $var = floatval()
            ],
            'string': [
                re.compile(r'\$\w+\s*=\s*["\'][^"\']*["\']'),  # $var = "text"
                re.compile(r'\$\w+\s*=\s*trim\('),  # $var = trim()
                re.compile(r'\$\w+\s*=\s*strtolower\('),  # $var = strtolower()
                re.compile(r'\$\w+\s*=\s*strtoupper\('),  # $var = strtoupper()
                re.compile(r'\$\w+\s*=\s*substr\('),  # $var = substr()
            ],
            'bool': [
                re.compile(r'\$\w+\s*=\s*(?:true|false)'),  # $var = true
                re.compile(r'\$\w+\s*=\s*is_\w+\('),  # $var = is_array()
                re.compile(r'\$\w+\s*=\s*empty\('),  # $var = empty()
                re.compile(r'\$\w+\s*=\s*isset\('),  # $var = isset()
            ],
            'array': [
                re.compile(r'\$\w+\s*=\s*\['),  # $var = [
                re.compile(r'\$\w+\s*=\s*array\('),  # $var = array()
                re.compile(r'\$\w+\s*=\s*explode\('),  # $var = explode()
                re.compile(r'\$\w+\s*=\s*range\('),  # $var = range()
            ]
        }
        
        # Fonctions de retour connues
        self.return_type_patterns = {
            'int': ['count', 'strlen', 'sizeof', 'strpos', 'strrpos', 'rand', 'mt_rand', 'array_sum'],
            'float': ['floatval', 'microtime', 'round', 'ceil', 'floor'],
            'string': ['trim', 'strtolower', 'strtoupper', 'substr', 'str_replace', 'htmlspecialchars'],
            'bool': ['is_array', 'is_string', 'is_int', 'is_float', 'empty', 'isset', 'in_array'],
            'array': ['explode', 'range', 'array_merge', 'array_keys', 'array_values']
        }
        
        # Superglobales et variables spéciales PHP
        self.php_superglobals = {
            '$_GET', '$_POST', '$_REQUEST', '$_SESSION', '$_COOKIE', 
            '$_SERVER', '$_ENV', '$_FILES', '$GLOBALS'
        }

    def _adapt_type_for_php_version(self, type_hint: str) -> str:
        """Adapter un type hint selon la version PHP cible"""
        if not self.config:
            return type_hint
        
        # Si le type contient des pipes (union types), vérifier la compatibilité
        if '|' in type_hint:
            if not self.config.supports_union_types():
                # PHP < 8.0 : convertir les union types en types plus génériques
                if type_hint == 'int|float':
                    return 'float'  # float accepte aussi les int
                elif 'string' in type_hint and 'int' in type_hint:
                    return 'string'  # Privilégier string pour les conversions
                else:
                    # Pour les autres union types, utiliser le premier type ou mixed si supporté
                    types = type_hint.split('|')
                    if self.config.supports_mixed_type():
                        return 'mixed'
                    else:
                        return types[0]  # Premier type de l'union
        
        # Vérifier les types spéciaux PHP 8.0+
        if type_hint == 'mixed' and not self.config.supports_mixed_type():
            return ''  # Pas de suggestion pour mixed si non supporté
        
        # Vérifier les types nullable
        if type_hint.startswith('?') and not self.config.supports_nullable_types():
            # PHP < 7.1 : enlever le ? et garder le type de base ou ne pas suggérer
            base_type = type_hint[1:]
            if base_type == 'mixed':
                return ''  # Pas de suggestion
            return base_type
        
        # Vérifier le type nullable mixed spécialement
        if type_hint == '?mixed':
            if not self.config.supports_nullable_types():
                return ''  # PHP < 7.1 ne supporte pas nullable
            elif not self.config.supports_mixed_type():
                return ''  # PHP < 8.0 ne supporte pas mixed
        
        return type_hint

    def analyze(self, content: str, file_path: Path, lines: List[str]) -> List[Dict]:
        """Analyse le contenu pour détecter les opportunités de type hints"""
        issues = []
        
        # Analyser les fonctions
        for match in self.function_pattern.finditer(content):
            func_name = match.group(1)
            params = match.group(2).strip() if match.group(2) else ""
            return_type = match.group(3)
            
            line_num = content[:match.start()].count('\n') + 1
            
            # Analyser les paramètres
            param_issues = self._analyze_function_parameters(
                func_name, params, content, file_path, line_num, lines, match.start()
            )
            issues.extend(param_issues)
            
            # Analyser le type de retour
            return_issues = self._analyze_return_type(
                func_name, return_type, content, file_path, line_num, lines, match.start()
            )
            issues.extend(return_issues)
        
        return issues

    def _analyze_function_parameters(self, func_name: str, params: str, content: str, 
                                   file_path: Path, line_num: int, lines: List[str], 
                                   func_start: int) -> List[Dict]:
        """Analyse les paramètres d'une fonction pour suggérer des types"""
        issues = []
        
        if not params:
            return issues
            
        # Parser les paramètres
        param_list = self._parse_parameters(params)
        
        for param in param_list:
            param_name = param['name']
            param_type = param['type']
            
            # Si le paramètre n'a pas de type, essayer d'en inférer un
            if not param_type:
                inferred_type = self._infer_parameter_type(
                    param_name, func_name, content, func_start, lines
                )
                
                if inferred_type:
                    # Adapter le type selon la version PHP
                    adapted_type = self._adapt_type_for_php_version(inferred_type)
                    
                    # Ne créer l'issue que si on a un type valide après adaptation
                    if adapted_type:
                        issues.append(self._create_issue(
                            rule_name='performance.missing_parameter_type',
                            message=f"Le paramètre '{param_name}' pourrait être typé en '{adapted_type}' pour de meilleures performances",
                            file_path=file_path,
                            line=line_num,
                            severity='info',
                            issue_type='performance',
                            suggestion=f"Ajouter une annotation de type : {adapted_type} {param_name}",
                            code_snippet=f"function {func_name}({params})"
                        ))
        
        return issues

    def _analyze_return_type(self, func_name: str, current_return_type: Optional[str], 
                           content: str, file_path: Path, line_num: int, 
                           lines: List[str], func_start: int) -> List[Dict]:
        """Analyse le type de retour d'une fonction"""
        issues = []
        
        # Si la fonction a déjà un type de retour, pas besoin de suggestion
        if current_return_type:
            return issues
            
        # Extraire le corps de la fonction
        func_body = self._extract_function_body(content, func_start)
        
        # Analyser les instructions return
        inferred_type = self._infer_return_type(func_body)
        
        if inferred_type:
            # Adapter le type selon la version PHP
            adapted_type = self._adapt_type_for_php_version(inferred_type)
            
            # Ne créer l'issue que si on a un type valide après adaptation
            if adapted_type:
                issues.append(self._create_issue(
                    rule_name='performance.missing_return_type',
                    message=f"La fonction '{func_name}' pourrait préciser un type de retour '{adapted_type}' pour profiter du JIT",
                    file_path=file_path,
                    line=line_num,
                    severity='info',
                    issue_type='performance',
                    suggestion=f"Ajouter un type de retour : : {adapted_type}",
                    code_snippet=f"function {func_name}"
                ))
        
        return issues

    def _parse_parameters(self, params: str) -> List[Dict]:
        """Parse la liste des paramètres d'une fonction"""
        param_list = []
        
        if not params.strip():
            return param_list
            
        # Séparer les paramètres (attention aux valeurs par défaut avec virgules)
        params_raw = re.split(r',(?![^(]*\))', params)
        
        for param in params_raw:
            param = param.strip()
            if not param:
                continue
                
            # Parser le type et le nom
            type_match = re.match(r'(?:(\w+(?:\|\w+)*|\?\w+)\s+)?(\$\w+)', param)
            if type_match:
                param_type = type_match.group(1)
                param_name = type_match.group(2)
                param_list.append({
                    'type': param_type,
                    'name': param_name
                })
        
        return param_list

    def _infer_parameter_type(self, param_name: str, func_name: str, content: str, 
                            func_start: int, lines: List[str]) -> Optional[str]:
        """Inférer le type d'un paramètre à partir de son usage"""
        
        # Extraire le corps de la fonction
        func_body = self._extract_function_body(content, func_start)
        
        # Chercher des indices sur le type du paramètre
        
        # 1. Vérifications de type explicites
        if re.search(rf'is_array\s*\(\s*{re.escape(param_name)}\s*\)', func_body):
            return 'array'
        if re.search(rf'is_string\s*\(\s*{re.escape(param_name)}\s*\)', func_body):
            return 'string'
        if re.search(rf'is_int\s*\(\s*{re.escape(param_name)}\s*\)', func_body):
            return 'int'
        if re.search(rf'is_float\s*\(\s*{re.escape(param_name)}\s*\)', func_body):
            return 'float'
        if re.search(rf'is_bool\s*\(\s*{re.escape(param_name)}\s*\)', func_body):
            return 'bool'
            
        # 2. Usage comme array
        if re.search(rf'{re.escape(param_name)}\s*\[', func_body):
            return 'array'
        if re.search(rf'foreach\s*\(\s*{re.escape(param_name)}\s+as', func_body):
            return 'array'
        if re.search(rf'count\s*\(\s*{re.escape(param_name)}\s*\)', func_body):
            return 'array'
        if re.search(rf'array_sum\s*\(\s*{re.escape(param_name)}\s*\)', func_body):
            return 'array'
        if re.search(rf'array_\w+\s*\(\s*{re.escape(param_name)}\s*\)', func_body):
            return 'array'
            
        # 3. Usage comme string
        if re.search(rf'strlen\s*\(\s*{re.escape(param_name)}\s*\)', func_body):
            return 'string'
        if re.search(rf'{re.escape(param_name)}\s*\.\s*["\']', func_body):
            return 'string'
        if re.search(rf'trim\s*\(\s*{re.escape(param_name)}\s*\)', func_body):
            return 'string'
            
        # 4. Usage arithmétique
        if re.search(rf'{re.escape(param_name)}\s*[+\-*/]\s*\d', func_body):
            return 'int|float'
        if re.search(rf'{re.escape(param_name)}\s*[+\-*/]\s*\$\w+', func_body):
            return 'int|float'
        if re.search(rf'\$\w+\s*[+\-*/]\s*{re.escape(param_name)}', func_body):
            return 'int|float'
        # Comparaisons arithmétiques
        if re.search(rf'{re.escape(param_name)}\s*[<>=!]+\s*\d', func_body):
            return 'int|float'
        if re.search(rf'\d+\s*[<>=!]+\s*{re.escape(param_name)}', func_body):
            return 'int|float'
            
        return None

    def _infer_return_type(self, func_body: str) -> Optional[str]:
        """Inférer le type de retour d'une fonction"""
        
        # Chercher toutes les instructions return
        return_matches = re.finditer(r'return\s+([^;]+);', func_body, re.IGNORECASE)
        return_types = set()
        has_null = False
        
        for match in return_matches:
            return_expr = match.group(1).strip()
            
            # Analyser l'expression de retour
            if return_expr in ['true', 'false']:
                return_types.add('bool')
            elif return_expr.lower() == 'null':
                has_null = True
            elif re.match(r'^\d+$', return_expr):
                return_types.add('int')
            elif re.match(r'^\d+\.\d+$', return_expr):
                return_types.add('float')
            elif re.match(r'^["\'].*["\']$', return_expr):
                return_types.add('string')
            elif return_expr.startswith('[') or return_expr.startswith('array('):
                return_types.add('array')
            # Fonctions connues (avant les expressions génériques)
            elif 'count(' in return_expr or 'strlen(' in return_expr or 'sizeof(' in return_expr:
                return_types.add('int')
            elif any(func + '(' in return_expr for func in self.return_type_patterns['int']):
                return_types.add('int')
            elif any(func + '(' in return_expr for func in self.return_type_patterns['string']):
                return_types.add('string')
            elif any(func + '(' in return_expr for func in self.return_type_patterns['bool']):
                return_types.add('bool')
            elif any(func + '(' in return_expr for func in self.return_type_patterns['array']):
                return_types.add('array')
            elif any(func + '(' in return_expr for func in self.return_type_patterns['float']):
                return_types.add('float')
            # Expressions booléennes complexes (après les fonctions)
            elif ('!==' in return_expr or '===' in return_expr or 
                  '!=' in return_expr or '==' in return_expr or
                  '>' in return_expr or '<' in return_expr or
                  '>=' in return_expr or '<=' in return_expr or
                  'false' in return_expr.lower() or 'true' in return_expr.lower()):
                return_types.add('bool')
            # Appels de fonctions inconnues - suggérer mixed
            elif re.search(r'\w+\s*\([^)]*\)', return_expr):
                return_types.add('mixed')
            # Opérations arithmétiques - suggérer int|float
            elif re.search(r'\$\w+\s*[+\-*/]\s*\$\w+', return_expr):
                return_types.add('int|float')
            elif re.search(r'\$\w+\s*[+\-*/]\s*\d+', return_expr):
                return_types.add('int|float')
            elif re.search(r'\d+\s*[+\-*/]\s*\$\w+', return_expr):
                return_types.add('int|float')
        
        # Si tous les returns sont du même type
        if len(return_types) == 1:
            return_type = return_types.pop()
            # Si on a null en plus d'un autre type, suggérer nullable
            if has_null:
                if return_type == 'mixed':
                    return "?mixed"
                else:
                    return f"?{return_type}"
            return return_type
        
        # Si plusieurs types, suggérer union type (PHP 8+)
        if len(return_types) > 1:
            union_type = '|'.join(sorted(return_types))
            if has_null:
                union_type = f"?({union_type})"
            return union_type
        
        # Si seulement null
        if has_null and not return_types:
            return "?mixed"
            
        return None

    def _extract_function_body(self, content: str, func_start: int) -> str:
        """Extraire le corps d'une fonction"""
        
        # Trouver l'accolade ouvrante
        brace_start = content.find('{', func_start)
        if brace_start == -1:
            return ""
            
        # Compter les accolades pour trouver la fermeture
        brace_count = 0
        i = brace_start
        
        while i < len(content):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    return content[brace_start + 1:i]
            i += 1
        
        return content[brace_start + 1:]

    def get_rules(self) -> List[str]:
        """Retourne la liste des règles gérées par cet analyseur"""
        return [
            'performance.missing_parameter_type',
            'performance.missing_return_type',
            'performance.mixed_type_opportunity',
            'best_practices.nullable_types'
        ]
