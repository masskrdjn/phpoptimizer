"""
Générateur de rapports pour PHP Optimizer
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from enum import Enum
from datetime import datetime
from colorama import Fore, Style

from .suggestions import SuggestionProvider


class OutputFormat(Enum):
    CONSOLE = "console"
    JSON = "json"
    HTML = "html"
    
    @classmethod
    def from_string(cls, value: str):
        """Créer enum depuis string"""
        for format_type in cls:
            if format_type.value == value:
                return format_type
        raise ValueError(f"Format non supporté: {value}")


class ReportGenerator:
    """Générateur de rapports d'analyse"""
    
    def __init__(self):
        """Initialiser le générateur de rapports"""
        self.suggestion_provider = SuggestionProvider()
    
    def generate_console_report(self, results: List[Dict[str, Any]], verbose: bool = False):
        """Générer un rapport console coloré"""
        if not results:
            print(f"{Fore.YELLOW}Aucun résultat à afficher{Style.RESET_ALL}")
            return
        
        # Statistiques générales
        total_files = len(results)
        successful_files = sum(1 for r in results if r.get('success', False))
        total_issues = sum(len(r.get('issues', [])) for r in results)
        
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}  RAPPORT D'ANALYSE PHP OPTIMIZER{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        print(f"\n{Fore.BLUE}Statistiques générales:{Style.RESET_ALL}")
        print(f"   Fichiers analysés: {successful_files}/{total_files}")
        print(f"   Problèmes détectés: {total_issues}")
        
        if total_issues == 0:
            print(f"\n{Fore.GREEN}✅ Aucun problème détecté ! Excellent travail !{Style.RESET_ALL}")
            return
        
        # Résumé par sévérité
        severity_counts = {'error': 0, 'warning': 0, 'info': 0}
        for result in results:
            for issue in result.get('issues', []):
                severity = issue.get('severity', 'info')
                if severity in severity_counts:
                    severity_counts[severity] += 1
        
        print(f"\n🎯 {Fore.BLUE}Répartition par sévérité:{Style.RESET_ALL}")
        if severity_counts['error'] > 0:
            print(f"   {Fore.RED}❌ Erreurs: {severity_counts['error']}{Style.RESET_ALL}")
        if severity_counts['warning'] > 0:
            print(f"   {Fore.YELLOW}⚠️  Avertissements: {severity_counts['warning']}{Style.RESET_ALL}")
        if severity_counts['info'] > 0:
            print(f"   {Fore.BLUE}ℹ️  Informations: {severity_counts['info']}{Style.RESET_ALL}")
        
        # Détails par fichier
        print(f"\n📁 {Fore.BLUE}Détails par fichier:{Style.RESET_ALL}")
        
        for result in results:
            if not result.get('success', False):
                print(f"\n{Fore.RED}❌ {result.get('file_path', 'Unknown')}{Style.RESET_ALL}")
                print(f"   Erreur: {result.get('error_message', 'Erreur inconnue')}")
                continue
            
            issues = result.get('issues', [])
            if not issues:
                if verbose:
                    print(f"\n{Fore.GREEN}✅ {result.get('file_path', 'Unknown')}{Style.RESET_ALL}")
                    print(f"   Aucun problème détecté")
                continue
            
            print(f"\n{Fore.YELLOW}📄 {result.get('file_path', 'Unknown')}{Style.RESET_ALL}")
            print(f"   {len(issues)} problème(s) détecté(s)")
            
            if verbose:
                # Grouper par ligne pour un affichage plus lisible
                issues_by_line = {}
                for issue in issues:
                    line = issue.get('line', 0)
                    if line not in issues_by_line:
                        issues_by_line[line] = []
                    issues_by_line[line].append(issue)
                
                for line_num in sorted(issues_by_line.keys()):
                    line_issues = issues_by_line[line_num]
                    print(f"\n   📍 {Fore.CYAN}Ligne {line_num}:{Style.RESET_ALL}")
                    
                    for issue in line_issues:
                        # Utiliser la nouvelle fonction de formatage détaillé
                        detailed_output = self._format_detailed_issue(issue)
                        print(detailed_output, end='')
        
        # Top des règles les plus déclenchées
        rule_counts = {}
        for result in results:
            for issue in result.get('issues', []):
                rule_name = issue.get('rule_name', 'unknown')
                rule_counts[rule_name] = rule_counts.get(rule_name, 0) + 1
        
        if rule_counts:
            print(f"\n🏆 {Fore.BLUE}Top des problèmes les plus fréquents:{Style.RESET_ALL}")
            sorted_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)
            
            for i, (rule_name, count) in enumerate(sorted_rules[:5], 1):
                print(f"   {i}. {rule_name}: {count} occurrence(s)")
        
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    def generate_file_report(self, results: List[Dict[str, Any]], 
                           output_path: str, format_type: OutputFormat):
        """Générer un rapport dans un fichier"""
        output_file = Path(output_path)
        
        if format_type == OutputFormat.JSON:
            self._generate_json_report(results, output_file)
        elif format_type == OutputFormat.HTML:
            self._generate_html_report(results, output_file)
        else:
            raise ValueError(f"Format de fichier non supporté: {format_type}")
    
    def _generate_json_report(self, results: List[Dict[str, Any]], output_file: Path):
        """Générer un rapport JSON"""
        report_data = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_files': len(results),
                'successful_analyses': sum(1 for r in results if r.get('success', False)),
                'total_issues': sum(len(r.get('issues', [])) for r in results),
                'total_analysis_time': sum(r.get('analysis_time', 0) for r in results)
            },
            'results': results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    def _generate_html_report(self, results: List[Dict[str, Any]], output_file: Path):
        """Générer un rapport HTML"""
        # Calculer les statistiques
        total_files = len(results)
        successful_files = sum(1 for r in results if r.get('success', False))
        total_issues = sum(len(r.get('issues', [])) for r in results)
        
        severity_counts = {'error': 0, 'warning': 0, 'info': 0}
        rule_counts = {}
        
        for result in results:
            for issue in result.get('issues', []):
                severity = issue.get('severity', 'info')
                if severity in severity_counts:
                    severity_counts[severity] += 1
                rule_name = issue.get('rule_name', 'unknown')
                rule_counts[rule_name] = rule_counts.get(rule_name, 0) + 1
        
        # Générer le HTML
        html_content = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport PHP Optimizer</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }}
        .header h1 {{ margin: 0; font-size: 2.5em; }}
        .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; padding: 30px; }}
        .stat-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #333; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        .severity-error {{ color: #dc3545; }}
        .severity-warning {{ color: #ffc107; }}
        .severity-info {{ color: #17a2b8; }}
        .content {{ padding: 0 30px 30px 30px; }}
        .file-result {{ margin-bottom: 30px; border: 1px solid #e9ecef; border-radius: 8px; overflow: hidden; }}
        .file-header {{ background: #f8f9fa; padding: 15px 20px; border-bottom: 1px solid #e9ecef; }}
        .file-path {{ font-weight: bold; color: #333; }}
        .issue-count {{ color: #666; font-size: 0.9em; }}
        .issues {{ padding: 20px; }}
        .issue {{ margin-bottom: 20px; padding: 15px; border-left: 4px solid #ddd; background: #f8f9fa; }}
        .issue.error {{ border-left-color: #dc3545; }}
        .issue.warning {{ border-left-color: #ffc107; }}
        .issue.info {{ border-left-color: #17a2b8; }}
        .issue-header {{ display: flex; justify-content: between; align-items: center; margin-bottom: 10px; }}
        .issue-message {{ font-weight: bold; color: #333; }}
        .issue-line {{ color: #666; font-size: 0.9em; }}
        .issue-suggestion {{ color: #666; margin-bottom: 10px; }}
        .code-snippet-header {{ font-weight: bold; color: #333; margin: 10px 0 5px 0; }}
        .code-snippet {{ background: #2d3748; color: #e2e8f0; padding: 10px; border-radius: 4px; font-family: 'Courier New', monospace; font-size: 0.9em; overflow-x: auto; margin-bottom: 10px; }}
        .correction-example {{ margin-top: 15px; }}
        .correction-header {{ 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 8px; 
            padding: 8px 12px; 
            background: #e8f5e8; 
            border-radius: 4px 4px 0 0; 
        }}
        .correction-title {{ font-weight: bold; color: #155724; }}
        .copy-code-btn {{ 
            background: #28a745; 
            color: white; 
            border: none; 
            padding: 4px 8px; 
            border-radius: 3px; 
            cursor: pointer; 
            font-size: 0.8em;
            transition: background-color 0.2s;
        }}
        .copy-code-btn:hover {{ background: #218838; }}
        .correction-code {{ 
            background: #f8f9fa; 
            border: 1px solid #d1ecf1; 
            padding: 15px; 
            margin: 0; 
            border-radius: 0 0 4px 4px; 
            font-family: 'Courier New', monospace; 
            font-size: 0.85em; 
            line-height: 1.4;
            overflow-x: auto;
            white-space: pre-wrap;
        }}
        .no-issues {{ text-align: center; padding: 40px; color: #28a745; }}
        .file-header-content {{ display: flex; justify-content: space-between; align-items: center; }}
        .copy-url-btn {{ 
            background: #6c757d; 
            color: white; 
            border: none; 
            padding: 8px 12px; 
            border-radius: 4px; 
            cursor: pointer; 
            font-size: 0.8em;
            display: flex;
            align-items: center;
            gap: 5px;
            transition: background-color 0.2s;
        }}
        .copy-url-btn:hover {{ background: #5a6268; }}
        .copy-url-btn.copied {{ background: #28a745; }}
        .copy-icon {{ font-size: 1em; }}
        .tooltip {{ position: relative; }}
        .tooltip-text {{ 
            position: absolute; 
            bottom: 125%; 
            left: 50%; 
            transform: translateX(-50%);
            background: #333; 
            color: white; 
            padding: 5px 8px; 
            border-radius: 4px; 
            font-size: 0.7em;
            white-space: nowrap;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.2s;
            z-index: 1000;
        }}
        .tooltip:hover .tooltip-text {{ opacity: 1; visibility: visible; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Rapport PHP Optimizer</h1>
            <p>Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{successful_files}/{total_files}</div>
                <div class="stat-label">Fichiers analysés</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_issues}</div>
                <div class="stat-label">Problèmes détectés</div>
            </div>
            <div class="stat-card">
                <div class="stat-number severity-error">{severity_counts['error']}</div>
                <div class="stat-label">Erreurs</div>
            </div>
            <div class="stat-card">
                <div class="stat-number severity-warning">{severity_counts['warning']}</div>
                <div class="stat-label">Avertissements</div>
            </div>
            <div class="stat-card">
                <div class="stat-number severity-info">{severity_counts['info']}</div>
                <div class="stat-label">Informations</div>
            </div>
        </div>
        
        <div class="content">
"""
        
        if total_issues == 0:
            html_content += """
            <div class="no-issues">
                <h2>🎉 Aucun problème détecté !</h2>
                <p>Votre code respecte toutes les règles d'optimisation configurées.</p>
            </div>
"""
        else:
            for result in results:
                if not result.get('success', False):
                    file_path = result.get('file_path', 'Unknown')
                    html_content += f"""
            <div class="file-result">
                <div class="file-header">
                    <div class="file-header-content">
                        <div>
                            <div class="file-path">❌ {file_path}</div>
                            <div class="issue-count">Erreur d'analyse: {result.get('error_message', 'Erreur inconnue')}</div>
                        </div>
                        <button class="copy-url-btn tooltip" onclick="return copyToClipboard(event, '{file_path.replace(chr(92), chr(92) + chr(92))}')">
                            <span class="copy-icon">📋</span>
                            <span>Copier le chemin</span>
                            <span class="tooltip-text">Copier le chemin du fichier</span>
                        </button>
                    </div>
                </div>
            </div>
"""
                    continue
                
                issues = result.get('issues', [])
                if not issues:
                    continue
                
                file_path = result.get('file_path', 'Unknown')
                html_content += f"""
            <div class="file-result">
                <div class="file-header">
                    <div class="file-header-content">
                        <div>
                            <div class="file-path">📄 {file_path}</div>
                            <div class="issue-count">{len(issues)} problème(s) détecté(s)</div>
                        </div>
                        <button class="copy-url-btn tooltip" onclick="return copyToClipboard(event, '{file_path.replace(chr(92), chr(92) + chr(92))}')">
                            <span class="copy-icon">📋</span>
                            <span>Copier le chemin</span>
                            <span class="tooltip-text">Copier le chemin du fichier</span>
                        </button>
                    </div>
                </div>
                <div class="issues">
"""
                
                for issue in issues:
                    severity = issue.get('severity', 'info')
                    
                    # Obtenir la suggestion - utiliser celle de l'issue en priorité
                    rule_name = issue.get('rule_name', '')
                    code_snippet = issue.get('code_snippet', '')
                    message = issue.get('message', '')
                    
                    # Si l'issue a déjà une suggestion personnalisée, l'utiliser
                    custom_suggestion = issue.get('suggestion', '')
                    if custom_suggestion and custom_suggestion != "Consultez la documentation pour plus de détails sur cette règle.":
                        suggestion = custom_suggestion
                        exemple_avant = ""
                        exemple_apres = ""
                    else:
                        # Sinon, utiliser le provider par défaut
                        suggestion, exemple_avant, exemple_apres = self.suggestion_provider.get_detailed_suggestion(
                            rule_name, code_snippet, message
                        )
                    
                    html_content += f"""
                    <div class="issue {severity}">
                        <div class="issue-header">
                            <div class="issue-message">{issue.get('message', '')}</div>
                            <div class="issue-line">Ligne {issue.get('line', 0)}</div>
                        </div>
                        <div class="issue-suggestion">💡 <strong>Solution:</strong> {suggestion.replace('\n', '<br>')}</div>
"""
                    
                    if code_snippet:
                        html_content += f"""
                        <div class="code-snippet-header">🔍 Code concerné:</div>
                        <div class="code-snippet">{code_snippet}</div>
"""
                    
                    # Ajouter l'exemple de correction s'il existe
                    if exemple_apres and exemple_apres != "# Correction nécessaire - consultez la documentation":
                        # Échapper le HTML pour l'affichage
                        import html
                        escaped_example = html.escape(exemple_apres)
                        html_content += f"""
                        <div class="correction-example">
                            <div class="correction-header">
                                <span class="correction-title">📝 Exemple de correction:</span>
                                <button class="copy-code-btn" onclick="copyCodeExample(this)">📋 Copier</button>
                            </div>
                            <pre class="correction-code"><code>{escaped_example}</code></pre>
                        </div>
"""
                    
                    html_content += "                    </div>\n"
                
                html_content += """
                </div>
            </div>
"""
        
        # Créer le JavaScript avec échappements corrects
        js_script = r"""
        </div>
    </div>
    
    <script>
        // Définir la fonction dans le scope global
        window.copyToClipboard = function(event, filePath) {
            // Empêcher le comportement par défaut
            event.preventDefault();
            event.stopPropagation();
            
            const button = event.target.closest('.copy-url-btn');
            if (!button) {
                return false;
            }
            
            const originalText = button.innerHTML;
            
            // Convertir le chemin Windows en chemin normalisé
            let normalizedPath;
            if (filePath.match(/^[a-zA-Z]:/)) {
                // Chemin Windows absolu (C:, D:, etc.) - juste normaliser les slashes
                normalizedPath = filePath.replace(/\\/g, '/');
            } else {
                // Chemin relatif - ajouter le chemin de base
                const basePath = window.location.href.split('/').slice(0, -1).join('/').replace('file:///', '');
                normalizedPath = basePath + '/' + filePath.replace(/\\/g, '/');
            }
            
            // Fonction d'erreur
            function showError(error) {
                button.innerHTML = '<span class="copy-icon">❌</span><span>Erreur</span>';
                button.style.background = '#dc3545';
                setTimeout(() => {
                    button.innerHTML = originalText;
                    button.style.background = '';
                }, 2000);
                
                // Dernier recours : afficher l'URL
                setTimeout(() => {
                    if (confirm('Impossible de copier automatiquement. Voulez-vous voir le chemin à copier manuellement ?')) {
                        prompt('Copiez ce chemin:', normalizedPath);
                    }
                }, 100);
            }
            
            // Méthode moderne (API Clipboard)
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(normalizedPath)
                    .then(() => {
                        showSuccess();
                    })
                    .catch(err => {
                        window.fallbackCopy(normalizedPath, showSuccess, showError);
                    });
            } else {
                window.fallbackCopy(normalizedPath, showSuccess, showError);
            }
            
            return false;
        }
        
        // Fonction fallback également dans le scope global
        window.fallbackCopy = function(text, onSuccess, onError) {
            try {
                // Créer un élément textarea temporaire
                const textarea = document.createElement('textarea');
                textarea.value = text;
                textarea.style.position = 'fixed';
                textarea.style.top = '0';
                textarea.style.left = '0';
                textarea.style.width = '2em';
                textarea.style.height = '2em';
                textarea.style.padding = '0';
                textarea.style.border = 'none';
                textarea.style.outline = 'none';
                textarea.style.boxShadow = 'none';
                textarea.style.background = 'transparent';
                textarea.style.opacity = '0';
                
                document.body.appendChild(textarea);
                
                // Focus et sélection
                textarea.focus();
                textarea.select();
                textarea.setSelectionRange(0, textarea.value.length);
                
                // Tentative de copie
                const successful = document.execCommand('copy');
                
                // Nettoyage
                document.body.removeChild(textarea);
                
                if (successful) {
                    onSuccess();
                } else {
                    onError('execCommand a retourné false');
                }
                
            } catch (err) {
                onError(err);
            }
        }
        
                // Fonction pour copier les exemples de code
        window.copyCodeExample = function(button) {
            const codeElement = button.closest('.correction-example').querySelector('.correction-code code');
            const code = codeElement.textContent;
            
            const originalText = button.innerHTML;
            
            function showSuccess() {
                button.innerHTML = '✅ Copié';
                button.style.background = '#28a745';
                setTimeout(() => {
                    button.innerHTML = originalText;
                    button.style.background = '';
                }, 2000);
            }
            
            function showError() {
                button.innerHTML = '❌ Erreur';
                button.style.background = '#dc3545';
                setTimeout(() => {
                    button.innerHTML = originalText;
                    button.style.background = '';
                }, 2000);
            }
            
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(code)
                    .then(showSuccess)
                    .catch(() => window.fallbackCopy(code, showSuccess, showError));
            } else {
                window.fallbackCopy(code, showSuccess, showError);
            }
        }
        
        // Test des capacités au chargement (optionnel)
    </script>
</body>
</html>
"""
        
        html_content += js_script
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _get_severity_color(self, severity: str) -> str:
        """Obtenir la couleur pour une sévérité"""
        colors = {
            'error': Fore.RED,
            'warning': Fore.YELLOW,
            'info': Fore.BLUE
        }
        return colors.get(severity, Fore.WHITE)
    
    def _get_severity_icon(self, severity: str) -> str:
        """Obtenir l'icône pour une sévérité"""
        icons = {
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️'
        }
        return icons.get(severity, '•')
    
    def _get_detailed_description(self, issue: Dict[str, Any]) -> str:
        """Retourner une description détaillée de l'erreur basée sur la règle"""
        rule_name = issue.get('rule_name', '')
        code_snippet = issue.get('code_snippet', '')
        
        descriptions = {
            'performance.select_star': {
                'description': "L'utilisation de SELECT * récupère toutes les colonnes de la table, même celles non utilisées.",
                'impact': "Impact sur les performances : transfert de données inutiles, utilisation mémoire accrue.",
                'solution': "Spécifiez uniquement les colonnes nécessaires : SELECT id, nom, quantite FROM produit",
                'example': "❌ SELECT * FROM produit\n✅ SELECT id, nom, quantite FROM produit"
            },
            'performance.query_in_loop': {
                'description': "Exécution de requêtes SQL à l'intérieur d'une boucle (problème N+1).",
                'impact': "Impact critique : multiplication des accès base de données, ralentissements majeurs.",
                'solution': "Regroupez les requêtes ou utilisez des JOINs pour récupérer toutes les données en une fois.",
                'example': "❌ foreach($users as $user) { query('SELECT * FROM posts WHERE user_id='.$user['id']); }\n✅ query('SELECT * FROM posts WHERE user_id IN ('.implode(',', $userIds).')')"
            },
            'performance.memory_management': {
                'description': "Gros tableau ou structure de données non libérée avec unset().",
                'impact': "Impact mémoire : accumulation en mémoire, risque de dépassement de memory_limit.",
                'solution': "Libérez explicitement les gros tableaux avec unset() après utilisation.",
                'example': f"❌ {code_snippet}\n✅ {code_snippet}\n    unset($large_array); // Libération mémoire"
            },
            'performance.inefficient_loops': {
                'description': "Appel de count() dans la condition d'une boucle for.",
                'impact': "Impact performance : count() recalculé à chaque itération.",
                'solution': "Stockez count() dans une variable avant la boucle.",
                'example': "❌ for($i=0; $i<count($array); $i++)\n✅ $length = count($array); for($i=0; $i<$length; $i++)"
            },
            'performance.string_concatenation_in_loop': {
                'description': "Concaténation de chaînes avec .= dans une boucle.",
                'impact': "Impact performance : réallocation de chaîne à chaque itération.",
                'solution': "Utilisez un tableau et implode() pour de meilleures performances.",
                'example': "❌ foreach($items as $item) { $str .= $item; }\n✅ $parts = []; foreach($items as $item) { $parts[] = $item; } $str = implode('', $parts);"
            },
            'performance.obsolete_function': {
                'description': "Utilisation d'une fonction PHP obsolète ou dépréciée.",
                'impact': "Impact sécurité/maintenance : fonction supprimée dans les nouvelles versions PHP.",
                'solution': "Remplacez par l'équivalent moderne selon la fonction.",
                'example': "❌ mysql_query() → ✅ PDO ou mysqli\n❌ ereg() → ✅ preg_match()\n❌ split() → ✅ explode() ou preg_split()"
            },
            'performance.error_suppression': {
                'description': "Utilisation de l'opérateur @ pour supprimer les erreurs.",
                'impact': "Impact performance : @ masque toutes les erreurs et ralentit l'exécution.",
                'solution': "Gérez les erreurs explicitement avec try/catch ou vérifications conditionnelles.",
                'example': "❌ @file_get_contents($url)\n✅ if(file_exists($file)) { $content = file_get_contents($file); }"
            },
            'security.sql_injection': {
                'description': "Variable utilisateur directement incluse dans une requête SQL.",
                'impact': "RISQUE CRITIQUE : injection SQL possible, compromission de la base de données.",
                'solution': "Utilisez IMPÉRATIVEMENT des requêtes préparées avec des paramètres liés.",
                'example': "❌ \"SELECT * FROM users WHERE id = $id\"\n✅ \"SELECT * FROM users WHERE id = ?\" avec bindParam()"
            },
            'security.xss_vulnerability': {
                'description': "Affichage direct de données utilisateur sans échappement.",
                'impact': "RISQUE CRITIQUE : injection de code JavaScript, vol de sessions.",
                'solution': "Échappez TOUJOURS les données avec htmlspecialchars() ou équivalent.",
                'example': "❌ echo $_GET['name']\n✅ echo htmlspecialchars($_GET['name'], ENT_QUOTES, 'UTF-8')"
            },
            'performance.inefficient_xpath': {
                'description': "Utilisation de sélecteurs XPath lents ou inefficaces.",
                'impact': "Impact performance : parcours complet de l'arbre XML, très lent sur gros documents.",
                'solution': "Utilisez des sélecteurs XPath spécifiques plutôt que des descendants génériques.",
                'example': "❌ //*[@id='element'] ou //div//span\n✅ /root/section/div[@id='element']"
            },
            'performance.inefficient_array_check': {
                'description': "Utilisation d'array_key_exists() au lieu d'isset() pour des vérifications simples.",
                'impact': "Impact performance : array_key_exists() est plus lent car il vérifie aussi les valeurs null.",
                'solution': "Utilisez isset() si les valeurs null ne sont pas importantes dans votre contexte.",
                'example': "❌ if (array_key_exists($key, $array))\n✅ if (isset($array[$key]))"
            },
            'performance.file_operations': {
                'description': "Ouvertures/fermetures répétées de fichiers dans des boucles.",
                'impact': "Impact performance : opérations I/O coûteuses répétées inutilement.",
                'solution': "Groupez les opérations fichiers ou utilisez file_get_contents() pour les petits fichiers.",
                'example': "❌ foreach($files as $file) { $fp = fopen($file, 'r'); ... fclose($fp); }\n✅ $content = file_get_contents($file); // Pour petits fichiers"
            },
            'performance.unused_variables': {
                'description': "Variables déclarées mais apparemment non utilisées dans le code.",
                'impact': "Impact maintenance : code difficile à lire, possibles fuites mémoire mineures.",
                'solution': "Supprimez les variables inutilisées ou vérifiez qu'elles sont réellement utilisées.",
                'example': "❌ $unused_var = 'test'; // Variable jamais utilisée\n✅ // Supprimez la ligne ou utilisez la variable"
            },
            'performance.repeated_calculations': {
                'description': "Expressions mathématiques identiques calculées plusieurs fois.",
                'impact': "Impact performance : recalculs inutiles, surtout dans les boucles.",
                'solution': "Stockez le résultat du calcul dans une variable réutilisable.",
                'example': "❌ $a = $x * $y + $z; $b = $x * $y + $z;\n✅ $calc = $x * $y + $z; $a = $calc; $b = $calc;"
            },
            'performance.dom_query_in_loop': {
                'description': "Requêtes DOM coûteuses (getElementById, querySelector) dans des boucles.",
                'impact': "Impact performance critique : parcours DOM répété, très lent sur gros documents.",
                'solution': "Extrayez les requêtes DOM hors des boucles et réutilisez les résultats.",
                'example': "❌ for($i=0; $i<100; $i++) { $el = $dom->getElementById('item'); }\n✅ $el = $dom->getElementById('item'); for($i=0; $i<100; $i++) { /* utiliser $el */ }"
            },
            'performance.inefficient_regex': {
                'description': "Expressions régulières avec des quantificateurs inefficaces comme .*",
                'impact': "Impact performance : backtracking excessif, risque de ReDoS (Regex Denial of Service).",
                'solution': "Utilisez des quantificateurs plus spécifiques (+, ?, {n,m}) et des classes de caractères précises.",
                'example': "❌ preg_match('/.*@.*/', $email)\n✅ preg_match('/[^@]+@[^@]+\\.[^@]+/', $email)"
            },
            'security.weak_password_hashing': {
                'description': "Utilisation d'algorithmes de hachage faibles (MD5, SHA1) pour les mots de passe.",
                'impact': "RISQUE CRITIQUE : mots de passe facilement cassables par force brute ou rainbow tables.",
                'solution': "Utilisez password_hash() avec PASSWORD_DEFAULT ou PASSWORD_ARGON2ID.",
                'example': "❌ $hash = md5($password)\n✅ $hash = password_hash($password, PASSWORD_DEFAULT)"
            },
            'security.file_inclusion': {
                'description': "Inclusion de fichiers basée sur des données utilisateur non validées.",
                'impact': "RISQUE CRITIQUE : inclusion de fichiers arbitraires, exécution de code malveillant.",
                'solution': "Validez et filtrez strictement les noms de fichiers, utilisez une whitelist.",
                'example': "❌ include $_GET['page'].'.php'\n✅ $allowed = ['home', 'about']; if(in_array($_GET['page'], $allowed)) include $_GET['page'].'.php'"
            },
            'best_practices.psr_compliance': {
                'description': "Lignes de code dépassant la limite recommandée de 120 caractères.",
                'impact': "Impact lisibilité : code difficile à lire, problèmes d'affichage sur certains écrans.",
                'solution': "Découpez les lignes longues, utilisez des variables intermédiaires.",
                'example': "❌ $very_long_variable_name = some_function_with_many_parameters($param1, $param2, $param3, $param4);\n✅ $result = some_function_with_many_parameters(\n    $param1, $param2,\n    $param3, $param4\n);"
            }
        }
        
        rule_info = descriptions.get(rule_name, {
            'description': "Problème détecté par l'analyseur.",
            'impact': "Impact à évaluer selon le contexte.",
            'solution': "Consultez la documentation pour plus de détails.",
            'example': ""
        })
        
        return rule_info

    def _format_detailed_issue(self, issue: Dict[str, Any]) -> str:
        """Formater un problème avec des détails complets et exemples de correction"""
        severity = issue.get('severity', 'info')
        severity_color = self._get_severity_color(severity)
        severity_icon = self._get_severity_icon(severity)
        
        # Message principal
        output = f"      {severity_color}{severity_icon} {issue.get('message', '')}{Style.RESET_ALL}\n"
        
        # Obtenir la suggestion - utiliser celle de l'issue en priorité
        rule_name = issue.get('rule_name', '')
        code_snippet = issue.get('code_snippet', '')
        message = issue.get('message', '')
        
        # Si l'issue a déjà une suggestion personnalisée, l'utiliser
        custom_suggestion = issue.get('suggestion', '')
        if custom_suggestion and custom_suggestion != "Consultez la documentation pour plus de détails sur cette règle.":
            suggestion = custom_suggestion
            exemple_avant = ""
            exemple_apres = ""
        else:
            # Sinon, utiliser le provider par défaut
            suggestion, exemple_avant, exemple_apres = self.suggestion_provider.get_detailed_suggestion(
                rule_name, code_snippet, message
            )
        
        # Description détaillée
        rule_info = self._get_detailed_description(issue)
        output += f"        📖 {Fore.LIGHTBLUE_EX}Description:{Style.RESET_ALL} {rule_info['description']}\n"
        
        # Impact
        impact_color = Fore.RED if severity == 'error' else Fore.YELLOW if severity == 'warning' else Fore.CYAN
        output += f"        ⚠️  {impact_color}Impact:{Style.RESET_ALL} {rule_info['impact']}\n"
        
        # Solution suggérée améliorée
        output += f"        💡 {Fore.GREEN}Solution:{Style.RESET_ALL} {suggestion}\n"
        
        # Code incriminé
        if code_snippet:
            output += f"        🔍 {Fore.LIGHTRED_EX}Code concerné:{Style.RESET_ALL} {code_snippet}\n"
        
        # Exemple de correction détaillé
        if exemple_apres and exemple_apres != "# Correction nécessaire - consultez la documentation":
            output += f"        📝 {Fore.LIGHTGREEN_EX}Exemple de correction:{Style.RESET_ALL}\n"
            for line in exemple_apres.split('\n'):
                if line.strip():
                    output += f"           {Fore.LIGHTBLACK_EX}{line}{Style.RESET_ALL}\n"
        
        return output
