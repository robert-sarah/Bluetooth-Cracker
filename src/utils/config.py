#!/usr/bin/env python3
"""
Module de configuration pour l'outil de pentest Bluetooth
"""

import json
import os
from typing import Dict, Any

class Config:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load_default_config()
        self.load_config()
        
    def load_default_config(self) -> Dict[str, Any]:
        """Charger la configuration par défaut"""
        return {
            "bluetooth": {
                "interface": "hci0",
                "scan_timeout": 30,
                "max_devices": 100,
                "rssi_threshold": -80
            },
            "attacks": {
                "blueborne": {
                    "enabled": True,
                    "timeout": 60,
                    "retries": 3,
                    "payload_size": 1024
                },
                "knob": {
                    "enabled": True,
                    "timeout": 30,
                    "key_length": 1,
                    "force_weak_key": True
                },
                "bluesmack": {
                    "enabled": True,
                    "timeout": 10,
                    "packet_size": 600,
                    "packet_count": 100
                },
                "bluesnarf": {
                    "enabled": True,
                    "timeout": 45,
                    "obex_port": 9,
                    "extract_contacts": True,
                    "extract_calendar": True
                },
                "bluejacking": {
                    "enabled": True,
                    "timeout": 15,
                    "message": "Test BlueJacking",
                    "max_length": 160
                },
                "l2cap_injection": {
                    "enabled": True,
                    "timeout": 20,
                    "channel": 1,
                    "payload": "A" * 100
                },
                "sdp_overflow": {
                    "enabled": True,
                    "timeout": 25,
                    "overflow_size": 2048,
                    "pattern": "A"
                },
                "pin_cracking": {
                    "enabled": True,
                    "timeout": 120,
                    "min_pin": 4,
                    "max_pin": 8,
                    "dictionary_file": "pins.txt"
                },
                "bluebug": {
                    "enabled": True,
                    "timeout": 40,
                    "commands": ["AT+CGMI", "AT+CGMM", "AT+CGSN"]
                }
            },
            "monitoring": {
                "packet_capture": {
                    "enabled": True,
                    "max_packets": 10000,
                    "filter_types": ["L2CAP", "HCI", "SDP", "RFCOMM"],
                    "save_pcap": True
                },
                "real_time_analysis": {
                    "enabled": True,
                    "alert_threshold": 10,
                    "suspicious_patterns": [
                        "malformed_l2cap",
                        "excessive_connections",
                        "weak_encryption"
                    ]
                }
            },
            "logging": {
                "level": "INFO",
                "file_enabled": True,
                "file_path": "logs/pentest.log",
                "max_file_size": 10485760,  # 10MB
                "backup_count": 5,
                "console_enabled": True
            },
            "interface": {
                "theme": "dark",
                "language": "fr",
                "auto_save": True,
                "confirm_actions": True,
                "show_tooltips": True
            },
            "security": {
                "stealth_mode": True,
                "randomize_mac": True,
                "fake_device_name": "Unknown Device",
                "max_attack_duration": 300,
                "cooldown_period": 60
            },
            "tools": {
                "hcitool_path": "/usr/bin/hcitool",
                "bluez_path": "/usr/bin/bluetoothctl",
                "btmon_path": "/usr/bin/btmon",
                "custom_scripts": []
            }
        }
        
    def load_config(self):
        """Charger la configuration depuis le fichier"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self.merge_config(file_config)
            except Exception as e:
                print(f"Erreur lors du chargement de la configuration: {e}")
                
    def save_config(self):
        """Sauvegarder la configuration dans le fichier"""
        try:
            # Créer le répertoire si nécessaire
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration: {e}")
            
    def merge_config(self, new_config: Dict[str, Any]):
        """Fusionner une nouvelle configuration avec l'existante"""
        def merge_dicts(base, update):
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge_dicts(base[key], value)
                else:
                    base[key] = value
                    
        merge_dicts(self.config, new_config)
        
    def get(self, key_path: str, default=None):
        """Obtenir une valeur de configuration par chemin"""
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
            
    def set(self, key_path: str, value):
        """Définir une valeur de configuration par chemin"""
        keys = key_path.split('.')
        config = self.config
        
        # Naviguer jusqu'au dernier niveau
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
            
        # Définir la valeur
        config[keys[-1]] = value
        
    def get_attack_config(self, attack_name: str) -> Dict[str, Any]:
        """Obtenir la configuration d'une attaque spécifique"""
        return self.get(f"attacks.{attack_name}", {})
        
    def is_attack_enabled(self, attack_name: str) -> bool:
        """Vérifier si une attaque est activée"""
        return self.get(f"attacks.{attack_name}.enabled", False)
        
    def get_bluetooth_config(self) -> Dict[str, Any]:
        """Obtenir la configuration Bluetooth"""
        return self.get("bluetooth", {})
        
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Obtenir la configuration de monitoring"""
        return self.get("monitoring", {})
        
    def get_logging_config(self) -> Dict[str, Any]:
        """Obtenir la configuration de logging"""
        return self.get("logging", {})
        
    def get_interface_config(self) -> Dict[str, Any]:
        """Obtenir la configuration de l'interface"""
        return self.get("interface", {})
        
    def get_security_config(self) -> Dict[str, Any]:
        """Obtenir la configuration de sécurité"""
        return self.get("security", {})
        
    def get_tools_config(self) -> Dict[str, Any]:
        """Obtenir la configuration des outils"""
        return self.get("tools", {})
        
    def validate_config(self) -> bool:
        """Valider la configuration"""
        required_sections = ["bluetooth", "attacks", "monitoring", "logging"]
        
        for section in required_sections:
            if section not in self.config:
                print(f"Section manquante dans la configuration: {section}")
                return False
                
        # Valider les chemins des outils
        tools_config = self.get_tools_config()
        for tool_name, tool_path in tools_config.items():
            if tool_path and not os.path.exists(tool_path):
                print(f"Outil non trouvé: {tool_name} -> {tool_path}")
                
        return True
        
    def reset_to_defaults(self):
        """Réinitialiser la configuration aux valeurs par défaut"""
        self.config = self.load_default_config()
        
    def export_config(self, filename: str):
        """Exporter la configuration vers un fichier"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de l'export de la configuration: {e}")
            
    def import_config(self, filename: str):
        """Importer la configuration depuis un fichier"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
                self.merge_config(imported_config)
        except Exception as e:
            print(f"Erreur lors de l'import de la configuration: {e}")
            
    def get_config_summary(self) -> Dict[str, Any]:
        """Obtenir un résumé de la configuration"""
        return {
            "bluetooth_interface": self.get("bluetooth.interface"),
            "enabled_attacks": [
                attack for attack, config in self.config["attacks"].items()
                if config.get("enabled", False)
            ],
            "logging_level": self.get("logging.level"),
            "stealth_mode": self.get("security.stealth_mode"),
            "monitoring_enabled": self.get("monitoring.packet_capture.enabled")
        }
