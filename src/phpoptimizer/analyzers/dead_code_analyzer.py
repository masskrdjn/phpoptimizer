"""
Analyseur spécialisé pour la détection de code mort

Repère plusieurs motifs de code inatteignable :
- Code après ``return``, ``exit``, ``die`` ou ``throw``
- Branches conditionnelles toujours fausses (``if (false)``, etc.)
- Code après ``break`` ou ``continue``
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import re

from .base_analyzer import BaseAnalyzer


class DeadCodeAnalyzer(BaseAnalyzer):
    """Analyseur de motifs de code mort."""

    def analyze(self, content: str, file_path: Path, lines: List[str]) -> List[Dict[str, Any]]:
        """Analyser le code PHP à la recherche de code mort."""
        issues: List[Dict[str, Any]] = []

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            # Ignorer lignes vides et commentaires
            if not stripped or self._is_comment_line(stripped):
                continue

            # Code inatteignable après une instruction de flux de contrôle
            unreachable = self._check_unreachable_after_flow_control(lines, line_num - 1)
            if unreachable:
                issues.append(self._create_issue(
                    rule_name='dead_code.unreachable_after_return',
                    message=unreachable['message'],
                    file_path=file_path,
                    line=line_num,
                    severity='warning',
                    issue_type='dead_code',
                    suggestion=unreachable['suggestion'],
                    code_snippet=stripped,
                ))

            # Conditions toujours fausses
            if self._is_always_false_condition(stripped):
                issues.append(self._create_issue(
                    rule_name='dead_code.always_false_condition',
                    message='Condition toujours fausse : le code interne est inatteignable',
                    file_path=file_path,
                    line=line_num,
                    severity='warning',
                    issue_type='dead_code',
                    suggestion='Supprimer le bloc ou corriger la condition pour qu\'elle soit utile',
                    code_snippet=stripped,
                ))

            # Code après break / continue
            if self._is_unreachable_after_break_continue(lines, line_num - 1):
                issues.append(self._create_issue(
                    rule_name='dead_code.unreachable_after_break',
                    message='Code inatteignable après break/continue',
                    file_path=file_path,
                    line=line_num,
                    severity='warning',
                    issue_type='dead_code',
                    suggestion='Supprimer le code situé après break ou continue',
                    code_snippet=stripped,
                ))

        return issues

    def _check_unreachable_after_flow_control(self, lines: List[str],
                                              current_index: int) -> Optional[Dict[str, Any]]:
        """Détecter le code après ``return``, ``exit``, ``die`` ou ``throw``."""
        if current_index >= len(lines):
            return None

        current_line = lines[current_index].strip()

        # Remonter la ligne précédente non vide / non commentée
        for i in range(current_index - 1, max(-1, current_index - 3), -1):
            prev_line = lines[i].strip()

            if not prev_line or self._is_comment_line(prev_line):
                continue

            if self._ends_with_flow_control(prev_line):
                # Si la ligne courante est une frontière de bloc, ce n'est pas du code mort
                if not self._is_block_boundary(current_line):
                    flow_type = self._get_flow_control_type(prev_line)
                    return {
                        'message': f'Code inatteignable après une instruction {flow_type}',
                        'suggestion': f'Supprimer le code après {flow_type}, il ne sera jamais exécuté',
                    }
            break

        return None

    def _is_always_false_condition(self, line: str) -> bool:
        """Repérer les conditions évaluées à false par construction."""
        patterns = (
            r'\bif\s*\(\s*false\s*\)',
            r'\bif\s*\(\s*0\s*\)',
            r'\bif\s*\(\s*null\s*\)',
            r'\bif\s*\(\s*""\s*\)',
            r"\bif\s*\(\s*''\s*\)",
            r'\bwhile\s*\(\s*false\s*\)',
            r'\bwhile\s*\(\s*0\s*\)',
        )
        return any(re.search(p, line, re.IGNORECASE) for p in patterns)

    def _is_unreachable_after_break_continue(self, lines: List[str],
                                             current_index: int) -> bool:
        """Détecter une ligne placée juste après un ``break`` ou ``continue``."""
        if current_index >= len(lines):
            return False

        current_line = lines[current_index].strip()

        for i in range(current_index - 1, max(-1, current_index - 2), -1):
            prev_line = lines[i].strip()

            if not prev_line or self._is_comment_line(prev_line):
                continue

            if re.search(r'\b(break|continue)\s*;?\s*$', prev_line, re.IGNORECASE):
                # Une accolade fermante ne compte pas comme code mort
                if not re.match(r'^\s*}', current_line):
                    return True
            break

        return False

    def _ends_with_flow_control(self, line: str) -> bool:
        """Vérifier si une ligne se termine par une instruction de flux de contrôle."""
        patterns = (
            r'\breturn\b.*?;?\s*$',
            r'\bexit\s*\([^)]*\)\s*;?\s*$',
            r'\bdie\s*\([^)]*\)\s*;?\s*$',
            r'\bthrow\s+.*?;?\s*$',
            r'\bexit\s*;?\s*$',
            r'\bdie\s*;?\s*$',
        )
        return any(re.search(p, line, re.IGNORECASE) for p in patterns)

    def _get_flow_control_type(self, line: str) -> str:
        """Identifier le type d'instruction de flux de contrôle."""
        if re.search(r'\breturn\b', line, re.IGNORECASE):
            return 'return'
        if re.search(r'\bexit\b', line, re.IGNORECASE):
            return 'exit'
        if re.search(r'\bdie\b', line, re.IGNORECASE):
            return 'die'
        if re.search(r'\bthrow\b', line, re.IGNORECASE):
            return 'throw'
        return 'flux de contrôle'

    def _is_block_boundary(self, line: str) -> bool:
        """Indiquer si la ligne est une frontière de bloc (accolade, else, case…)."""
        patterns = (
            r'^\s*}',
            r'^\s*else\b',
            r'^\s*elseif\b',
            r'^\s*catch\b',
            r'^\s*finally\b',
            r'^\s*case\b',
            r'^\s*default\s*:',
        )
        return any(re.match(p, line, re.IGNORECASE) for p in patterns)
