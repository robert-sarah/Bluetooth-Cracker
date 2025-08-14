#!/bin/bash
# Script d'installation pour Advanced Bluetooth Pentest Tool

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/bluetooth-pentest"
BIN_DIR="/usr/local/bin"
CONFIG_DIR="/etc/bluetooth-pentest"

# Fonctions utilitaires
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier les prérequis système
check_prerequisites() {
    log_info "Vérification des prérequis système..."
    
    # Vérifier si on est root
    if [ "$EUID" -ne 0 ]; then
        log_error "Ce script doit être exécuté en tant que root (sudo)"
        exit 1
    fi
    
    # Vérifier la distribution
    if command -v apt-get &> /dev/null; then
        PACKAGE_MANAGER="apt-get"
    elif command -v yum &> /dev/null; then
        PACKAGE_MANAGER="yum"
    elif command -v dnf &> /dev/null; then
        PACKAGE_MANAGER="dnf"
    else
        log_error "Gestionnaire de paquets non supporté"
        exit 1
    fi
    
    log_success "Distribution détectée: $PACKAGE_MANAGER"
}

# Installer les dépendances système
install_system_dependencies() {
    log_info "Installation des dépendances système..."
    
    if [ "$PACKAGE_MANAGER" = "apt-get" ]; then
        apt-get update
        apt-get install -y \
            bluez \
            bluez-tools \
            libbluetooth-dev \
            build-essential \
            cmake \
            pkg-config \
            python3-dev \
            python3-pip \
            git \
            wget \
            curl
    elif [ "$PACKAGE_MANAGER" = "yum" ] || [ "$PACKAGE_MANAGER" = "dnf" ]; then
        $PACKAGE_MANAGER update -y
        $PACKAGE_MANAGER install -y \
            bluez \
            bluez-libs \
            bluez-devel \
            gcc \
            gcc-c++ \
            make \
            cmake \
            python3-devel \
            python3-pip \
            git \
            wget \
            curl
    fi
    
    log_success "Dépendances système installées"
}

# Installer les dépendances Python
install_python_dependencies() {
    log_info "Installation des dépendances Python..."
    
    # Mettre à jour pip
    python3 -m pip install --upgrade pip
    
    # Installer les dépendances
    pip3 install -r requirements.txt
    
    log_success "Dépendances Python installées"
}

# Compiler les modules C/C++
compile_c_modules() {
    log_info "Compilation des modules C/C++..."
    
    cd src/c_modules
    
    # Nettoyer les anciens builds
    make clean 2>/dev/null || true
    
    # Compiler
    make all
    
    # Installer les bibliothèques
    make install
    
    cd ../..
    
    log_success "Modules C/C++ compilés et installés"
}

# Créer les répertoires d'installation
create_directories() {
    log_info "Création des répertoires d'installation..."
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$INSTALL_DIR/logs"
    mkdir -p "$INSTALL_DIR/extracted_data"
    mkdir -p "$INSTALL_DIR/reports"
    
    log_success "Répertoires créés"
}

# Copier les fichiers
copy_files() {
    log_info "Copie des fichiers..."
    
    # Copier les fichiers Python
    cp -r src "$INSTALL_DIR/"
    cp main.py "$INSTALL_DIR/"
    cp requirements.txt "$INSTALL_DIR/"
    cp README.md "$INSTALL_DIR/"
    
    # Copier les outils
    cp -r tools "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/tools/"*.sh
    
    # Copier la configuration
    cp src/utils/config.py "$CONFIG_DIR/config.py"
    
    log_success "Fichiers copiés"
}

# Créer le script de lancement
create_launcher() {
    log_info "Création du script de lancement..."
    
    cat > "$BIN_DIR/bluetooth-pentest" << 'EOF'
#!/bin/bash
# Script de lancement pour Advanced Bluetooth Pentest Tool

cd /opt/bluetooth-pentest
python3 main.py "$@"
EOF
    
    chmod +x "$BIN_DIR/bluetooth-pentest"
    
    log_success "Script de lancement créé: bluetooth-pentest"
}

# Créer le service systemd
create_systemd_service() {
    log_info "Création du service systemd..."
    
    cat > /etc/systemd/system/bluetooth-pentest.service << EOF
[Unit]
Description=Advanced Bluetooth Pentest Tool
After=network.target bluetooth.service

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    
    log_success "Service systemd créé"
}

# Configurer les permissions
setup_permissions() {
    log_info "Configuration des permissions..."
    
    # Donner les permissions appropriées
    chown -R root:root "$INSTALL_DIR"
    chmod -R 755 "$INSTALL_DIR"
    
    # Permissions spéciales pour les logs et données
    chmod 777 "$INSTALL_DIR/logs"
    chmod 777 "$INSTALL_DIR/extracted_data"
    chmod 777 "$INSTALL_DIR/reports"
    
    log_success "Permissions configurées"
}

# Tester l'installation
test_installation() {
    log_info "Test de l'installation..."
    
    # Vérifier que les outils sont disponibles
    if ! command -v hcitool &> /dev/null; then
        log_error "hcitool non trouvé"
        return 1
    fi
    
    if ! command -v bluetoothctl &> /dev/null; then
        log_error "bluetoothctl non trouvé"
        return 1
    fi
    
    # Vérifier que Python peut importer les modules
    if ! python3 -c "import PyQt5" 2>/dev/null; then
        log_error "PyQt5 non installé"
        return 1
    fi
    
    log_success "Installation testée avec succès"
    return 0
}

# Afficher les informations post-installation
show_post_install_info() {
    echo ""
    echo "=== INSTALLATION TERMINÉE ==="
    echo ""
    echo "L'outil Advanced Bluetooth Pentest Tool a été installé avec succès."
    echo ""
    echo "Informations importantes:"
    echo "- Répertoire d'installation: $INSTALL_DIR"
    echo "- Configuration: $CONFIG_DIR"
    echo "- Script de lancement: bluetooth-pentest"
    echo ""
    echo "Utilisation:"
    echo "  bluetooth-pentest                    # Interface graphique"
    echo "  bluetooth-pentest --help             # Aide"
    echo "  bluetooth-pentest --scan             # Scan rapide"
    echo ""
    echo "Outils disponibles:"
    echo "  $INSTALL_DIR/tools/bluetooth_scanner.sh"
    echo "  $INSTALL_DIR/tools/blueborne_exploit.sh"
    echo ""
    echo "⚠️  AVERTISSEMENT: Cet outil est destiné uniquement à des fins éducatives"
    echo "   et de test de sécurité autorisés. L'utilisation contre des systèmes"
    echo "   sans autorisation explicite est illégale."
    echo ""
}

# Fonction principale
main() {
    echo "=== INSTALLATION DE L'OUTIL DE PENTEST BLUETOOTH ==="
    echo ""
    
    check_prerequisites
    install_system_dependencies
    install_python_dependencies
    create_directories
    copy_files
    compile_c_modules
    create_launcher
    create_systemd_service
    setup_permissions
    
    if test_installation; then
        show_post_install_info
        log_success "Installation terminée avec succès!"
    else
        log_error "Installation échouée lors des tests"
        exit 1
    fi
}

# Gestion des erreurs
cleanup_on_error() {
    log_error "Erreur lors de l'installation"
    log_info "Nettoyage en cours..."
    
    # Supprimer les fichiers partiellement installés
    rm -rf "$INSTALL_DIR" 2>/dev/null || true
    rm -f "$BIN_DIR/bluetooth-pentest" 2>/dev/null || true
    rm -f /etc/systemd/system/bluetooth-pentest.service 2>/dev/null || true
    
    exit 1
}

# Gestion des signaux
trap cleanup_on_error ERR
trap cleanup_on_error SIGINT SIGTERM

# Exécution
main "$@"
