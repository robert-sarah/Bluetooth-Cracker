#ifndef BLUETOOTH_ATTACKS_H
#define BLUETOOTH_ATTACKS_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Types de données
typedef struct {
    char address[18];
    char name[256];
    int8_t rssi;
    bool paired;
    bool trusted;
    bool connected;
} bluetooth_device_t;

typedef struct {
    uint8_t type;
    uint8_t direction;
    uint16_t length;
    uint8_t data[1024];
    uint64_t timestamp;
} bluetooth_packet_t;

// Codes de retour
#define BT_SUCCESS 0
#define BT_ERROR -1
#define BT_TIMEOUT -2
#define BT_NOT_FOUND -3
#define BT_PERMISSION_DENIED -4

// Types d'attaques
typedef enum {
    ATTACK_BLUEBORNE = 1,
    ATTACK_KNOB = 2,
    ATTACK_BLUESMACK = 3,
    ATTACK_BLUESNARF = 4,
    ATTACK_BLUEJACKING = 5,
    ATTACK_L2CAP_INJECTION = 6,
    ATTACK_SDP_OVERFLOW = 7,
    ATTACK_PIN_CRACKING = 8,
    ATTACK_BLUEBUG = 9
} attack_type_t;

// Configuration d'attaque
typedef struct {
    attack_type_t type;
    char target_address[18];
    uint32_t timeout;
    uint32_t retries;
    uint32_t delay;
    bool stealth_mode;
    bool verbose;
} attack_config_t;

// Callback pour les événements
typedef void (*attack_callback_t)(const char* message, int level);

// Fonctions principales
int bt_init(void);
void bt_cleanup(void);

// Scan et découverte
int bt_scan_devices(bluetooth_device_t* devices, int max_devices, int timeout);
int bt_get_device_info(const char* address, bluetooth_device_t* device);
int bt_discover_services(const char* address, char** services, int max_services);

// Attaques
int bt_execute_attack(const attack_config_t* config, attack_callback_t callback);
int bt_stop_attack(void);

// Attaques spécifiques
int bt_blueborne_attack(const char* target, attack_callback_t callback);
int bt_knob_attack(const char* target, attack_callback_t callback);
int bt_bluesmack_attack(const char* target, uint16_t packet_size, uint32_t count, attack_callback_t callback);
int bt_bluesnarf_attack(const char* target, attack_callback_t callback);
int bt_bluejacking_attack(const char* target, const char* message, attack_callback_t callback);
int bt_l2cap_injection(const char* target, uint16_t channel, const uint8_t* payload, uint16_t length, attack_callback_t callback);
int bt_sdp_overflow(const char* target, uint16_t size, attack_callback_t callback);
int bt_pin_cracking(const char* target, uint8_t min_length, uint8_t max_length, attack_callback_t callback);
int bt_bluebug_attack(const char* target, const char** commands, int command_count, attack_callback_t callback);

// Capture de paquets
int bt_start_packet_capture(const char* interface, attack_callback_t callback);
int bt_stop_packet_capture(void);
int bt_get_captured_packet(bluetooth_packet_t* packet);

// Utilitaires
int bt_parse_address(const char* address_str, uint8_t* address_bytes);
int bt_format_address(const uint8_t* address_bytes, char* address_str);
int bt_check_vulnerability(const char* target, attack_type_t attack_type);
int bt_send_raw_packet(const char* target, const uint8_t* data, uint16_t length);

// Gestion des erreurs
const char* bt_get_error_string(int error_code);
void bt_set_debug_level(int level);

#ifdef __cplusplus
}
#endif

#endif // BLUETOOTH_ATTACKS_H
