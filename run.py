#!/usr/bin/env python3
"""
Script de lancement rapide pour l'outil de pentest Bluetooth
"""

import sys
import os
import subprocess

def check_root():
    """Vérifier si on est root"""
    if os.geteuid() != 0:
        print("⚠️  Cet outil nécessite des privilèges root pour fonctionner correctement.")
        print("   Relancez avec: sudo python3 run.py")
        return False
    return True

def check_dependencies():
    """Vérifier les dépendances"""
    print("🔍 Vérification des dépendances...")
    
    # Vérifier Python
    if sys.version_info < (3, 6):
        print("❌ Python 3.6+ requis")
        return False
    
    # Vérifier les modules Python
    try:
        import PyQt5
        print("✅ PyQt5")
    except ImportError:
        print("❌ PyQt5 non installé. Installez avec: pip3 install PyQt5")
        return False
    
    # Vérifier les outils système
    tools = ['hcitool', 'bluetoothctl']
    for tool in tools:
        try:
            subprocess.run([tool, '--help'], capture_output=True, check=False)
            print(f"✅ {tool}")
        except FileNotFoundError:
            print(f"❌ {tool} non trouvé")
            return False
    
    return True

def main():
    """Fonction principale"""
    print("🔵 Advanced Bluetooth Pentest Tool - Lancement rapide")
    print("=" * 50)
    
    # Vérifications
    if not check_root():
        sys.exit(1)
    
    if not check_dependencies():
        print("\n❌ Dépendances manquantes. Exécutez d'abord: ./install.sh")
        sys.exit(1)
    
    print("\n✅ Toutes les vérifications passées!")
    print("🚀 Lancement de l'interface graphique...")
    
    # Lancer l'application principale
    try:
        from main import main as app_main
        app_main()
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("   Assurez-vous que tous les modules sont installés.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur lors du lancement: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
