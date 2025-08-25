#!/usr/bin/env python3
"""
Script unifié pour générer toutes les visualisations

Exécute les différents analyseurs de tendances et génère un rapport complet.
"""

import argparse
import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

def run_command(command, description):
    """Exécute une commande et gère les erreurs"""
    print(f"\n🔄 {description}")
    print(f"💻 Commande: {' '.join(command)}")
    
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Terminé avec succès")
        if result.stdout.strip():
            print("📋 Sortie:")
            print(result.stdout)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Erreur")
        print(f"Code de retour: {e.returncode}")
        if e.stderr:
            print(f"Erreur: {e.stderr}")
        if e.stdout:
            print(f"Sortie: {e.stdout}")
        return False, e.stderr
    except FileNotFoundError:
        print(f"❌ {description} - Script non trouvé")
        return False, "Script non trouvé"

def create_master_index(output_base_dir):
    """Crée une page d'index maître pour toutes les visualisations"""
    print("📄 Génération de l'index maître")
    
    # Collecte des répertoires de visualisation
    viz_dirs = {
        'trends': 'Analyses de Tendances',
        'interactive': 'Dashboard Interactif', 
        'geographic': 'Analyses Géographiques',
        'checks': 'Audits et Vérifications'
    }
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Centre d'Analyse Électorale - Nantes Métropole</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{ 
                max-width: 1200px; 
                margin: 0 auto; 
                background: white; 
                border-radius: 20px; 
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{ 
                background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                color: white; 
                padding: 40px; 
                text-align: center; 
            }}
            .header h1 {{ font-size: 2.5rem; margin-bottom: 10px; }}
            .header p {{ font-size: 1.1rem; opacity: 0.9; }}
            .content {{ padding: 40px; }}
            .grid {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
                gap: 30px; 
                margin-top: 30px; 
            }}
            .card {{ 
                background: white; 
                border: 1px solid #e1e8ed;
                border-radius: 15px; 
                padding: 30px; 
                box-shadow: 0 8px 25px rgba(0,0,0,0.08);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                position: relative;
                overflow: hidden;
            }}
            .card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #3498db, #9b59b6);
            }}
            .card:hover {{ 
                transform: translateY(-5px); 
                box-shadow: 0 15px 35px rgba(0,0,0,0.15);
            }}
            .card-icon {{ 
                font-size: 3rem; 
                margin-bottom: 20px; 
                display: block; 
            }}
            .card h3 {{ 
                color: #2c3e50; 
                font-size: 1.4rem; 
                margin-bottom: 15px; 
            }}
            .card p {{ 
                color: #7f8c8d; 
                line-height: 1.6; 
                margin-bottom: 20px; 
            }}
            .btn {{ 
                display: inline-block; 
                background: linear-gradient(135deg, #3498db, #2980b9); 
                color: white; 
                padding: 12px 25px; 
                text-decoration: none; 
                border-radius: 8px; 
                font-weight: 600;
                transition: all 0.3s ease;
            }}
            .btn:hover {{ 
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(52, 152, 219, 0.4);
            }}
            .stats {{ 
                background: #f8f9fa; 
                padding: 25px; 
                border-radius: 10px; 
                margin-bottom: 30px;
                border-left: 4px solid #3498db;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
            }}
            .stat-item {{
                text-align: center;
            }}
            .stat-number {{
                font-size: 2rem;
                font-weight: bold;
                color: #3498db;
                display: block;
            }}
            .stat-label {{
                color: #7f8c8d;
                font-size: 0.9rem;
            }}
            .footer {{
                background: #2c3e50;
                color: white;
                text-align: center;
                padding: 20px;
                opacity: 0.8;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🗳️ Centre d'Analyse Électorale</h1>
                <p>Nantes Métropole • Analyses et Visualisations Interactives</p>
            </div>
            
            <div class="content">
                <div class="stats">
                    <h3>📊 Informations sur l'analyse</h3>
                    <div class="stats-grid">
                        <div class="stat-item">
                            <span class="stat-number">4</span>
                            <span class="stat-label">Modules d'analyse</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">24</span>
                            <span class="stat-label">Communes analysées</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">2012-2022</span>
                            <span class="stat-label">Période couverte</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">{datetime.now().strftime('%d/%m/%Y')}</span>
                            <span class="stat-label">Dernière mise à jour</span>
                        </div>
                    </div>
                </div>
                
                <div class="grid">
    """
    
    # Configuration des modules avec leurs descriptions
    modules = {
        'trends': {
            'icon': '📈',
            'title': 'Analyses de Tendances',
            'description': 'Évolution temporelle des familles politiques, participation électorale, corrélations socio-économiques et comparaisons entre types de scrutin.',
            'files': ['evolution_familles_politiques.png', 'evolution_participation.png', 'rapport_synthese.txt']
        },
        'interactive': {
            'icon': '🎯', 
            'title': 'Dashboard Interactif',
            'description': 'Visualisations interactives avec Plotly : timeline, heatmaps, scatter plots et dashboard complet navigable dans votre navigateur.',
            'files': ['index.html', 'dashboard_electoral.html']
        },
        'geographic': {
            'icon': '🗺️',
            'title': 'Analyses Géographiques', 
            'description': 'Cartes choroplèthes des résultats électoraux, analyse de participation par commune et comparaisons géographiques multi-temporelles.',
            'files': ['evolution_presidentielles_comparison.png', 'analyse_stabilite_communes.csv']
        },
        'checks': {
            'icon': '🔍',
            'title': 'Audits & Vérifications',
            'description': 'Contrôles qualité des données, vérification de la cohérence des résultats et validation des calculs de vainqueurs par commune.',
            'files': ['winner_variation.csv']
        }
    }
    
    for dir_name, module_info in modules.items():
        module_path = os.path.join(output_base_dir, dir_name)
        
        # Vérification de l'existence des fichiers
        files_exist = []
        if os.path.exists(module_path):
            for file_name in module_info['files']:
                file_path = os.path.join(module_path, file_name)
                if os.path.exists(file_path):
                    files_exist.append(file_name)
        
        status = "✅ Disponible" if files_exist else "⏳ En cours"
        files_count = len(files_exist)
        
        html_content += f"""
                    <div class="card">
                        <span class="card-icon">{module_info['icon']}</span>
                        <h3>{module_info['title']}</h3>
                        <p>{module_info['description']}</p>
                        <p><strong>Status:</strong> {status} • <strong>Fichiers:</strong> {files_count}</p>
                        <a href="{dir_name}/index.html" class="btn" target="_blank">
                            Ouvrir l'analyse
                        </a>
                    </div>
        """
    
    html_content += """
                </div>
            </div>
            
            <div class="footer">
                <p>Généré automatiquement par le système d'analyse électorale • Claude Code</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    index_path = os.path.join(output_base_dir, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return index_path

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="Générateur complet de visualisations électorales")
    parser.add_argument("--data", default="/app/data/processed_csv/master_ml.csv",
                       help="Chemin vers le fichier de données")
    parser.add_argument("--output", default="/app/reports",
                       help="Répertoire de base pour toutes les sorties")
    parser.add_argument("--skip-trends", action="store_true", help="Ignorer l'analyse des tendances")
    parser.add_argument("--skip-interactive", action="store_true", help="Ignorer le dashboard interactif")
    parser.add_argument("--skip-geographic", action="store_true", help="Ignorer l'analyse géographique")
    parser.add_argument("--skip-audit", action="store_true", help="Ignorer l'audit des données")
    
    args = parser.parse_args()
    
    print("🚀 Démarrage de la génération complète des visualisations")
    print(f"📊 Source de données: {args.data}")
    print(f"📁 Répertoire de sortie: {args.output}")
    
    # Création du répertoire de base
    os.makedirs(args.output, exist_ok=True)
    
    # Suivi des résultats
    results = {}
    
    # 1. Audit des données (si pas ignoré)
    if not args.skip_audit:
        success, output = run_command([
            'python', '/app/src/audit_winner.py'
        ], "Audit de cohérence des données")
        results['audit'] = success
    
    # 2. Analyse des tendances (si pas ignoré)
    if not args.skip_trends:
        success, output = run_command([
            'python', '/app/src/viz/trends_analyzer.py',
            '--data', args.data,
            '--output', os.path.join(args.output, 'trends')
        ], "Génération des analyses de tendances")
        results['trends'] = success
    
    # 3. Dashboard interactif (si pas ignoré)
    if not args.skip_interactive:
        success, output = run_command([
            'python', '/app/src/viz/interactive_dashboard.py',
            '--data', args.data,
            '--output', os.path.join(args.output, 'interactive')
        ], "Génération du dashboard interactif")
        results['interactive'] = success
    
    # 4. Analyse géographique (si pas ignoré) 
    if not args.skip_geographic:
        success, output = run_command([
            'python', '/app/src/viz/geographic_analyzer.py',
            '--data', args.data,
            '--output', os.path.join(args.output, 'geographic'),
            '--all-elections'
        ], "Génération des analyses géographiques")
        results['geographic'] = success
    
    # 5. Génération de l'index maître
    index_file = create_master_index(args.output)
    
    # 6. Rapport de synthèse
    print(f"\n📋 RAPPORT DE SYNTHÈSE")
    print(f"=" * 50)
    
    total_modules = len(results)
    successful_modules = sum(results.values())
    
    print(f"✅ Modules exécutés avec succès: {successful_modules}/{total_modules}")
    
    for module, success in results.items():
        status = "✅ Succès" if success else "❌ Échec"
        print(f"   {module.capitalize()}: {status}")
    
    print(f"\n📄 Index principal généré: {os.path.basename(index_file)}")
    print(f"🌐 Ouvrir dans votre navigateur: {args.output}/index.html")
    print(f"📁 Tous les fichiers dans: {args.output}")
    
    # Sauvegarde du rapport JSON
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'data_source': args.data,
        'output_directory': args.output,
        'modules_executed': results,
        'success_rate': f"{successful_modules}/{total_modules}",
        'index_file': index_file
    }
    
    report_path = os.path.join(args.output, 'generation_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f"📊 Rapport détaillé: {os.path.basename(report_path)}")
    
    if successful_modules == total_modules:
        print("\n🎉 Toutes les visualisations ont été générées avec succès!")
    else:
        print(f"\n⚠️  {total_modules - successful_modules} module(s) ont rencontré des erreurs")
        sys.exit(1)

if __name__ == "__main__":
    main()