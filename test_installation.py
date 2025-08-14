#!/usr/bin/env python3
"""
Script de test pour vérifier l'installation de l'outil de pentest Bluetooth
"""

import sys
import os
import subprocess
import importlib

def test_python_modules():
    """Tester l'import des modules Python"""
    print("🔍 Test des modules Python...")
    
    modules_to_test = [
        'PyQt5',
        'PyQt5.QtWidgets',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'subprocess',
        'socket',
        'struct',
        'time',
        'json'
    ]
    
    failed_modules = []
    
    for module in modules_to_test:
        try:
            importlib.import_module(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            failed_modules.append(module)
    
    return len(failed_modules) == 0

def test_system_tools():
    """Tester la disponibilité des outils système"""
    print("\n🔧 Test des outils système...")
    
    tools_to_test = [
        'hcitool',
        'hciconfig',
        'sdptool',
        'bluetoothctl',
        'l2ping',
        'rfcomm',
        'obexftp',
        'btmon'
    ]
    
    failed_tools = []
    
    for tool in tools_to_test:
        try:
            result = subprocess.run([tool, '--help'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            if result.returncode == 0 or result.returncode == 1:  # --help retourne souvent 1
                print(f"  ✅ {tool}")
            else:
                print(f"  ❌ {tool}: code de retour {result.returncode}")
                failed_tools.append(tool)
        except FileNotFoundError:
            print(f"  ❌ {tool}: non trouvé")
            failed_tools.append(tool)
        except subprocess.TimeoutExpired:
            print(f"  ⚠️  {tool}: timeout")
    
    return len(failed_tools) == 0

def test_bluetooth_interface():
    """Tester l'interface Bluetooth"""
    print("\n📡 Test de l'interface Bluetooth...")
    
    try:
        # Vérifier si hci0 existe
        result = subprocess.run(['hciconfig', 'hci0'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        
        if result.returncode == 0:
            if 'UP RUNNING' in result.stdout:
                print("  ✅ Interface Bluetooth hci0 active")
                return True
            else:
                print("  ⚠️  Interface Bluetooth hci0 inactive")
                return False
        else:
            print("  ❌ Interface Bluetooth hci0 non trouvée")
            return False
            
    except Exception as e:
        print(f"  ❌ Erreur lors du test Bluetooth: {e}")
        return False

def test_project_modules():
    """Tester les modules du projet"""
    print("\n📦 Test des modules du projet...")
    
    # Ajouter le répertoire src au path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    
    modules_to_test = [
        'src.utils.config',
        'src.core.bluetooth_manager',
        'src.gui.scanner_widget',
        'src.gui.attack_widget',
        'src.gui.monitor_widget',
        'src.gui.logger_widget',
        'src.attacks.blueborne_attack',
        'src.attacks.knob_attack',
        'src.attacks.bluesmack_attack',
        'src.attacks.bluesnarf_attack',
        'src.attacks.bluejacking_attack',
        'src.attacks.l2cap_injection_attack',
        'src.attacks.sdp_overflow_attack',
        'src.attacks.pin_cracking_attack',
        'src.attacks.bluebug_attack'
    ]
    
    failed_modules = []
    
    for module in modules_to_test:
        try:
            importlib.import_module(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            failed_modules.append(module)
    
    return len(failed_modules) == 0

def test_c_modules():
    """Tester les modules C/C++"""
    print("\n⚙️  Test des modules C/C++...")
    
    c_module_path = os.path.join(os.path.dirname(__file__), 'src', 'c_modules')
    
    if os.path.exists(c_module_path):
        files_to_check = [
            'Makefile',
            'bluetooth_attacks.h',
            'bluetooth_attacks.c'
        ]
        
        for file in files_to_check:
            file_path = os.path.join(c_module_path, file)
            if os.path.exists(file_path):
                print(f"  ✅ {file}")
            else:
                print(f"  ❌ {file}: non trouvé")
                return False
        
        # Essayer de compiler
        try:
            result = subprocess.run(['make', 'clean'], 
                                  cwd=c_module_path, 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            
            result = subprocess.run(['make'], 
                                  cwd=c_module_path, 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=30)
            
            if result.returncode == 0:
                print("  ✅ Compilation réussie")
                return True
            else:
                print(f"  ❌ Erreur de compilation: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"  ❌ Erreur lors de la compilation: {e}")
            return False
    else:
        print("  ❌ Répertoire c_modules non trouvé")
        return False

def main():
    """Fonction principale"""
    print("=== TEST D'INSTALLATION - OUTIL DE PENTEST BLUETOOTH ===\n")
    
    tests = [
        ("Modules Python", test_python_modules),
        ("Outils système", test_system_tools),
        ("Interface Bluetooth", test_bluetooth_interface),
        ("Modules du projet", test_project_modules),
        ("Modules C/C++", test_c_modules)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ Erreur lors du test {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "="*50)
    print("RÉSUMÉ DES TESTS")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSÉ" if result else "❌ ÉCHOUÉ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nRésultat: {passed}/{total} tests passés")
    
    if passed == total:
        print("\n🎉 Tous les tests sont passés! L'installation est complète.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) ont échoué. Vérifiez l'installation.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
