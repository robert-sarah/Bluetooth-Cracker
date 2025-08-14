# Guide d'Utilisation - Advanced Bluetooth Pentest Tool

## 🚀 Installation Rapide

### Prérequis
- Linux (Ubuntu/Debian/Kali/Parrot)
- Python 3.6+
- Privilèges root
- Interface Bluetooth

### Installation
```bash
# Cloner le projet
git clone <repository>
cd bestpirater

# Installation automatique
sudo ./install.sh

# Ou installation manuelle
sudo pip3 install -r requirements.txt
sudo ./src/c_modules/make
```

## 🔧 Utilisation

### Lancement Rapide
```bash
sudo python3 run.py
```

### Lancement Complet
```bash
sudo python3 main.py
```

### Test d'Installation
```bash
python3 test_installation.py
```

## 📱 Interface Graphique

### Onglet Scanner
- **Démarrer Scan**: Lance un scan Bluetooth
- **Durée**: Configure la durée du scan (5-300 secondes)
- **Scan Continu**: Active le scan en continu
- **Export**: Exporte les résultats en JSON/TXT

### Onglet Attaques
- **BlueBorne**: Exploitation de la vulnérabilité BlueBorne
- **KNOB**: Attaque Key Negotiation of Bluetooth
- **BlueSmack**: Attaque DoS par paquets L2CAP
- **BlueSnarf**: Extraction de données via OBEX
- **BlueJacking**: Envoi de messages non sollicités
- **L2CAP Injection**: Injection de paquets malveillants
- **SDP Overflow**: Débordement de buffer SDP
- **PIN Cracking**: Crackage de codes PIN
- **BlueBug**: Exploitation de commandes AT

### Onglet Monitor
- **Capture de Paquets**: Capture en temps réel
- **Filtres**: Filtrage par type et direction
- **Export PCAP**: Export des captures
- **Analyse Hex**: Vue hexadécimale

### Onglet Logs
- **Niveaux**: DEBUG, INFO, WARNING, ERROR
- **Filtrage**: Par niveau et contenu
- **Export**: JSON, TXT, CSV
- **Recherche**: Recherche dans les logs

## 🛠️ Outils en Ligne de Commande

### Scanner Bluetooth
```bash
./tools/bluetooth_scanner.sh [adresse_cible]
```

### Exploit BlueBorne
```bash
./tools/blueborne_exploit.sh [adresse_cible]
```

## ⚙️ Configuration

### Fichier config.json
```json
{
  "bluetooth": {
    "interface": "hci0",
    "scan_duration": 30
  },
  "attacks": {
    "blueborne": {
      "enabled": true,
      "timeout": 30
    }
  }
}
```

### Variables d'Environnement
```bash
export BLUETOOTH_PENTEST_CONFIG=/path/to/config.json
export BLUETOOTH_PENTEST_LOG_LEVEL=DEBUG
```

## 🔍 Exemples d'Utilisation

### Scan Simple
1. Ouvrir l'onglet Scanner
2. Cliquer sur "Démarrer Scan"
3. Attendre les résultats
4. Sélectionner une cible

### Attaque BlueBorne
1. Aller dans l'onglet Attaques
2. Sélectionner "BlueBorne"
3. Entrer l'adresse de la cible
4. Configurer les paramètres
5. Lancer l'attaque

### Monitor de Trafic
1. Ouvrir l'onglet Monitor
2. Cliquer sur "Démarrer Capture"
3. Appliquer des filtres si nécessaire
4. Analyser les paquets capturés

## 🛡️ Sécurité

### Privilèges Requis
- **Root**: Nécessaire pour les opérations Bluetooth
- **Capabilities**: CAP_NET_ADMIN, CAP_NET_RAW

### Logs de Sécurité
- Toutes les attaques sont loggées
- Horodatage et détails complets
- Rotation automatique des logs

### Anonymisation
- Option d'anonymisation des cibles
- Chiffrement des logs sensibles
- Protection des données extraites

## 🐛 Dépannage

### Problèmes Courants

#### Interface Bluetooth Non Détectée
```bash
# Vérifier l'interface
hciconfig

# Activer l'interface
sudo hciconfig hci0 up

# Vérifier les services
sudo systemctl status bluetooth
```

#### Erreur de Permissions
```bash
# Vérifier les privilèges
sudo -v

# Installer les capabilities
sudo setcap 'cap_net_admin,cap_net_raw+ep' /usr/bin/hcitool
```

#### Module C Non Compilé
```bash
# Recompiler
cd src/c_modules
make clean
make all
sudo make install
```

### Logs de Débogage
```bash
# Activer les logs détaillés
export BLUETOOTH_PENTEST_LOG_LEVEL=DEBUG

# Voir les logs système
sudo journalctl -f -u bluetooth
```

## 📊 Rapports

### Génération de Rapports
- Export automatique après chaque attaque
- Format JSON/HTML/PDF
- Inclusions des captures et logs

### Structure des Rapports
```
reports/
├── scan_20240814_143022.json
├── blueborne_attack_20240814_143045.html
├── captured_packets_20240814_143100.pcap
└── logs_20240814_143100.txt
```

## 🔧 Personnalisation

### Nouveaux Modules d'Attaque
1. Créer un fichier dans `src/attacks/`
2. Hériter de la classe de base
3. Implémenter la méthode `execute()`
4. Ajouter au registre des attaques

### Thèmes Personnalisés
- Modification du fichier CSS
- Thèmes sombre/clair
- Couleurs personnalisées

### Scripts Automatisés
- Création de scripts bash
- Intégration avec d'autres outils
- Automatisation des tests

## ⚠️ Avertissements Légaux

### Usage Responsable
- **ÉDUCATIF UNIQUEMENT**: Usage en environnement contrôlé
- **AUTORISATION REQUISE**: Permission écrite obligatoire
- **RESPONSABILITÉ**: L'utilisateur est responsable de ses actions

### Conformité
- Respect des lois locales
- Protection de la vie privée
- Non-divulgation d'informations sensibles

## 📞 Support

### Documentation
- README.md: Vue d'ensemble
- USAGE.md: Guide d'utilisation
- docs/: Documentation technique

### Problèmes
- Issues GitHub
- Logs détaillés
- Tests de diagnostic

### Contribution
- Pull requests bienvenus
- Tests obligatoires
- Documentation requise
