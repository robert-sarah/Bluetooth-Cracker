# Advanced Bluetooth Pentest Tool

Un outil de pentest Bluetooth avancé avec interface graphique PyQt5, intégrant des attaques comme BlueBorne et KNOB.

## Fonctionnalités

### Attaques Implémentées
- **BlueBorne Attack** : Exploitation des vulnérabilités de propagation Bluetooth
- **KNOB Attack** : Attaque sur la négociation de clés Bluetooth
- **BlueSmack** : Attaque par déni de service
- **BlueSnarf** : Extraction de données
- **BlueJacking** : Envoi de messages non autorisés
- **L2CAP Injection** : Injection de paquets L2CAP
- **SDP Overflow** : Débordement du Service Discovery Protocol

### Composants Techniques
- Interface graphique PyQt5 moderne
- Modules C/C++ pour les attaques de bas niveau
- Scripts Python pour l'orchestration
- Intégration des outils Linux (bluez, hcitool)
- Analyse en temps réel des paquets Bluetooth

## Installation

### Prérequis Système
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y bluez bluez-tools libbluetooth-dev
sudo apt-get install -y build-essential cmake pkg-config
sudo apt-get install -y python3-dev python3-pip

# CentOS/RHEL
sudo yum install -y bluez bluez-libs bluez-devel
sudo yum install -y gcc gcc-c++ make cmake
sudo yum install -y python3-devel python3-pip
```

### Installation Python
```bash
pip3 install -r requirements.txt
```

### Compilation des modules C/C++
```bash
cd src/c_modules
make clean && make all
```

## Utilisation

### Lancement de l'interface graphique
```bash
python3 main.py
```

### Utilisation en ligne de commande
```bash
python3 cli_tool.py --scan
python3 cli_tool.py --attack blueborne --target 00:11:22:33:44:55
python3 cli_tool.py --attack knob --target 00:11:22:33:44:55
```

## Structure du Projet

```
bestpirater/
├── main.py                 # Interface graphique principale
├── src/
│   ├── gui/               # Composants PyQt5
│   ├── attacks/           # Modules d'attaques
│   ├── c_modules/         # Modules C/C++ compilés
│   ├── utils/             # Utilitaires
│   └── core/              # Logique métier
├── tools/                 # Scripts Linux
├── docs/                  # Documentation
└── tests/                 # Tests unitaires
```

## Sécurité et Légalité

⚠️ **AVERTISSEMENT** : Cet outil est destiné uniquement à des fins éducatives et de test de sécurité autorisés. L'utilisation de cet outil contre des systèmes sans autorisation explicite est illégale.

## Licence

Ce projet est fourni à des fins éducatives uniquement.
