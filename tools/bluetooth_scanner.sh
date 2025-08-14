#!/bin/bash
# Script de scan Bluetooth avancé pour l'outil de pentest

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCAN_DURATION=${1:-30}
OUTPUT_FILE="bluetooth_scan_$(date +%Y%m%d_%H%M%S).txt"
VERBOSE=${2:-false}

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

# Vérifier les prérequis
check_prerequisites() {
    log_info "Vérification des prérequis..."
    
    # Vérifier si hcitool est disponible
    if ! command -v hcitool &> /dev/null; then
        log_error "hcitool non trouvé. Installez bluez-tools."
        exit 1
    fi
    
    # Vérifier si hciconfig est disponible
    if ! command -v hciconfig &> /dev/null; then
        log_error "hciconfig non trouvé. Installez bluez-tools."
        exit 1
    fi
    
    # Vérifier si sdptool est disponible
    if ! command -v sdptool &> /dev/null; then
        log_error "sdptool non trouvé. Installez bluez-tools."
        exit 1
    fi
    
    log_success "Tous les prérequis sont satisfaits"
}

# Initialiser l'interface Bluetooth
init_bluetooth() {
    log_info "Initialisation de l'interface Bluetooth..."
    
    # Activer l'interface hci0
    if ! hciconfig hci0 up &> /dev/null; then
        log_error "Impossible d'activer l'interface hci0"
        exit 1
    fi
    
    # Vérifier que l'interface est active
    if ! hciconfig hci0 | grep -q "UP RUNNING"; then
        log_error "L'interface hci0 n'est pas active"
        exit 1
    fi
    
    log_success "Interface Bluetooth initialisée"
}

# Scanner les appareils Bluetooth
scan_devices() {
    log_info "Démarrage du scan Bluetooth (durée: ${SCAN_DURATION}s)..."
    
    # Effectuer le scan avec hcitool
    echo "=== SCAN BLUETOOTH - $(date) ===" > "$OUTPUT_FILE"
    echo "Durée: ${SCAN_DURATION} secondes" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    # Scan initial
    log_info "Scan initial en cours..."
    hcitool scan --flush | tee -a "$OUTPUT_FILE"
    
    # Scan détaillé des appareils trouvés
    log_info "Analyse détaillée des appareils..."
    echo "" >> "$OUTPUT_FILE"
    echo "=== ANALYSE DÉTAILLÉE ===" >> "$OUTPUT_FILE"
    
    # Extraire les adresses MAC du scan
    addresses=$(hcitool scan --flush | grep -E '^[[:xdigit:]]{2}:[[:xdigit:]]{2}:[[:xdigit:]]{2}:[[:xdigit:]]{2}:[[:xdigit:]]{2}:[[:xdigit:]]{2}' | awk '{print $1}')
    
    if [ -z "$addresses" ]; then
        log_warning "Aucun appareil trouvé"
        return
    fi
    
    # Analyser chaque appareil
    for addr in $addresses; do
        log_info "Analyse de l'appareil: $addr"
        echo "" >> "$OUTPUT_FILE"
        echo "--- Appareil: $addr ---" >> "$OUTPUT_FILE"
        
        # Informations de base
        echo "Informations de base:" >> "$OUTPUT_FILE"
        hcitool info "$addr" 2>/dev/null | tee -a "$OUTPUT_FILE" || echo "Impossible d'obtenir les informations" >> "$OUTPUT_FILE"
        
        # Services
        echo "" >> "$OUTPUT_FILE"
        echo "Services:" >> "$OUTPUT_FILE"
        sdptool browse "$addr" 2>/dev/null | grep -E "(Service Name|Service RecHandle|Protocol Descriptor List)" | tee -a "$OUTPUT_FILE" || echo "Impossible de découvrir les services" >> "$OUTPUT_FILE"
        
        # Test de connectivité L2CAP
        echo "" >> "$OUTPUT_FILE"
        echo "Test de connectivité L2CAP:" >> "$OUTPUT_FILE"
        test_l2cap_connectivity "$addr" >> "$OUTPUT_FILE"
        
        # Test de connectivité RFCOMM
        echo "" >> "$OUTPUT_FILE"
        echo "Test de connectivité RFCOMM:" >> "$OUTPUT_FILE"
        test_rfcomm_connectivity "$addr" >> "$OUTPUT_FILE"
        
        echo "----------------------------------------" >> "$OUTPUT_FILE"
    done
}

# Tester la connectivité L2CAP
test_l2cap_connectivity() {
    local addr="$1"
    local ports=(1 3 5 7 9 11 13 15 17 19 21 23 25 27 29 31)
    
    for port in "${ports[@]}"; do
        if timeout 2 l2ping -c 1 -s 1 "$addr" &> /dev/null; then
            echo "  Port L2CAP $port: OUVERT"
        else
            echo "  Port L2CAP $port: fermé"
        fi
    done
}

# Tester la connectivité RFCOMM
test_rfcomm_connectivity() {
    local addr="$1"
    local ports=(1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20)
    
    for port in "${ports[@]}"; do
        if timeout 2 rfcomm connect /dev/null "$addr" "$port" &> /dev/null; then
            echo "  Port RFCOMM $port: OUVERT"
        else
            echo "  Port RFCOMM $port: fermé"
        fi
    done
}

# Analyser les vulnérabilités
analyze_vulnerabilities() {
    log_info "Analyse des vulnérabilités..."
    
    echo "" >> "$OUTPUT_FILE"
    echo "=== ANALYSE DES VULNÉRABILITÉS ===" >> "$OUTPUT_FILE"
    
    # Vérifier les versions Bluetooth vulnérables
    echo "Vérification des versions Bluetooth vulnérables:" >> "$OUTPUT_FILE"
    
    addresses=$(hcitool scan --flush | grep -E '^[[:xdigit:]]{2}:[[:xdigit:]]{2}:[[:xdigit:]]{2}:[[:xdigit:]]{2}:[[:xdigit:]]{2}:[[:xdigit:]]{2}' | awk '{print $1}')
    
    for addr in $addresses; do
        echo "" >> "$OUTPUT_FILE"
        echo "Appareil: $addr" >> "$OUTPUT_FILE"
        
        # Vérifier BlueBorne
        if hcitool info "$addr" 2>/dev/null | grep -q "4\.[0-2]"; then
            echo "  [VULNÉRABLE] BlueBorne - Version Bluetooth 4.0-4.2 détectée" >> "$OUTPUT_FILE"
        fi
        
        # Vérifier KNOB
        if hcitool info "$addr" 2>/dev/null | grep -q "Secure Simple Pairing"; then
            echo "  [VULNÉRABLE] KNOB - Secure Simple Pairing détecté" >> "$OUTPUT_FILE"
        fi
        
        # Vérifier BlueSmack
        if l2ping -c 1 -s 600 "$addr" &> /dev/null; then
            echo "  [VULNÉRABLE] BlueSmack - L2CAP accepte les gros paquets" >> "$OUTPUT_FILE"
        fi
        
        # Vérifier BlueSnarf
        if sdptool browse "$addr" 2>/dev/null | grep -q "OBEX"; then
            echo "  [VULNÉRABLE] BlueSnarf - Service OBEX détecté" >> "$OUTPUT_FILE"
        fi
    done
}

# Générer un rapport
generate_report() {
    log_info "Génération du rapport..."
    
    echo "" >> "$OUTPUT_FILE"
    echo "=== RAPPORT FINAL ===" >> "$OUTPUT_FILE"
    echo "Date: $(date)" >> "$OUTPUT_FILE"
    echo "Durée du scan: ${SCAN_DURATION} secondes" >> "$OUTPUT_FILE"
    
    # Compter les appareils
    device_count=$(hcitool scan --flush | grep -c -E '^[[:xdigit:]]{2}:[[:xdigit:]]{2}:[[:xdigit:]]{2}:[[:xdigit:]]{2}:[[:xdigit:]]{2}:[[:xdigit:]]{2}' || echo "0")
    echo "Appareils découverts: $device_count" >> "$OUTPUT_FILE"
    
    # Compter les vulnérabilités
    vuln_count=$(grep -c "VULNÉRABLE" "$OUTPUT_FILE" || echo "0")
    echo "Vulnérabilités détectées: $vuln_count" >> "$OUTPUT_FILE"
    
    log_success "Rapport généré: $OUTPUT_FILE"
}

# Fonction principale
main() {
    echo "=== SCANNER BLUETOOTH AVANCÉ ==="
    echo "Durée du scan: ${SCAN_DURATION} secondes"
    echo "Fichier de sortie: $OUTPUT_FILE"
    echo ""
    
    check_prerequisites
    init_bluetooth
    scan_devices
    analyze_vulnerabilities
    generate_report
    
    log_success "Scan terminé avec succès"
    echo ""
    echo "Résultats sauvegardés dans: $OUTPUT_FILE"
}

# Gestion des signaux
cleanup() {
    log_info "Nettoyage en cours..."
    hciconfig hci0 down &> /dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Exécution
main "$@"
