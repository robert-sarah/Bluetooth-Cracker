#!/usr/bin/env python3
"""
Gestionnaire Bluetooth principal pour l'outil de pentest
"""

import os
import subprocess
import threading
import time
import json
import socket
import struct
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import re

class DeviceType(Enum):
    PHONE = "phone"
    COMPUTER = "computer"
    HEADSET = "headset"
    SPEAKER = "speaker"
    UNKNOWN = "unknown"

@dataclass
class BluetoothDevice:
    address: str
    name: str
    device_type: DeviceType
    rssi: int
    services: List[str]
    paired: bool
    trusted: bool
    connected: bool

class BluetoothManager:
    def __init__(self):
        self.devices = {}
        self.is_scanning = False
        self.is_attacking = False
        self.scan_thread = None
        self.attack_thread = None
        self.current_attack = None
        self.callbacks = {
            'device_found': [],
            'scan_complete': [],
            'attack_progress': [],
            'attack_complete': []
        }
        
    def add_callback(self, event: str, callback: Callable):
        """Ajouter un callback pour un événement"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
            
    def _notify_callbacks(self, event: str, data=None):
        """Notifier tous les callbacks d'un événement"""
        for callback in self.callbacks.get(event, []):
            try:
                callback(data)
            except Exception as e:
                print(f"Erreur dans callback {event}: {e}")
                
    def check_bluetooth_available(self) -> bool:
        """Vérifier si Bluetooth est disponible"""
        try:
            # Vérifier si hciconfig est disponible
            result = subprocess.run(['hciconfig'], capture_output=True, text=True)
            if result.returncode != 0:
                return False
                
            # Vérifier si l'interface Bluetooth est active
            result = subprocess.run(['hciconfig', 'hci0'], capture_output=True, text=True)
            return 'UP RUNNING' in result.stdout
            
        except FileNotFoundError:
            return False
            
    def start_scan(self, duration: int = 30):
        """Démarrer un scan Bluetooth"""
        if self.is_scanning:
            return
            
        self.is_scanning = True
        self.scan_thread = threading.Thread(target=self._scan_worker, args=(duration,))
        self.scan_thread.daemon = True
        self.scan_thread.start()
        
    def _scan_worker(self, duration: int):
        """Worker pour le scan Bluetooth"""
        try:
            # Activer l'interface Bluetooth si nécessaire
            subprocess.run(['hciconfig', 'hci0', 'up'], capture_output=True)
            
            # Utiliser hcitool pour le scan
            cmd = ['hcitool', 'scan', '--flush']
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            start_time = time.time()
            while time.time() - start_time < duration and self.is_scanning:
                line = process.stdout.readline()
                if not line:
                    break
                    
                device = self._parse_scan_line(line)
                if device:
                    self.devices[device.address] = device
                    self._notify_callbacks('device_found', device)
                    
            process.terminate()
            
            if self.is_scanning:
                self._notify_callbacks('scan_complete', list(self.devices.values()))
                
        except Exception as e:
            print(f"Erreur lors du scan: {e}")
        finally:
            self.is_scanning = False
            
    def _parse_scan_line(self, line: str) -> Optional[BluetoothDevice]:
        """Parser une ligne de scan hcitool"""
        try:
            parts = line.strip().split()
            if len(parts) >= 2:
                address = parts[0]
                name = ' '.join(parts[1:]) if len(parts) > 1 else "Unknown"
                
                # Enrichir les informations de l'appareil
                device_info = self._enrich_device_info(address)
                
                return BluetoothDevice(
                    address=address,
                    name=name,
                    device_type=DeviceType(device_info.get('type', 'unknown')),
                    rssi=device_info.get('rssi', -50),
                    services=device_info.get('services', []),
                    paired=device_info.get('paired', False),
                    trusted=device_info.get('trusted', False),
                    connected=device_info.get('connected', False)
                )
        except Exception as e:
            print(f"Erreur parsing ligne scan: {e}")
        return None
        
    def _enrich_device_info(self, address: str) -> Dict:
        """Enrichir les informations d'un appareil"""
        info = {}
        
        try:
            # Informations de base
            cmd = ['hcitool', 'info', address]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                output = result.stdout
                
                # Extraire le RSSI
                if 'RSSI:' in output:
                    rssi_line = [line for line in output.split('\n') if 'RSSI:' in line]
                    if rssi_line:
                        try:
                            rssi = int(rssi_line[0].split(':')[1].strip())
                            info['rssi'] = rssi
                        except:
                            pass
                            
                # Vérifier si l'appareil est appairé
                info['paired'] = 'Paired: Yes' in output
                info['trusted'] = 'Trusted: Yes' in output
                info['connected'] = 'Connected: Yes' in output
                
            # Découvrir les services
            services = self._discover_services(address)
            info['services'] = services
            
            # Déterminer le type d'appareil
            info['type'] = self._detect_device_type(info.get('name', ''))
            
        except Exception as e:
            print(f"Erreur lors de l'obtention des infos: {e}")
            
        return info
        
    def _discover_services(self, address: str) -> List[str]:
        """Découvrir les services d'un appareil"""
        services = []
        
        try:
            cmd = ['sdptool', 'browse', address]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'service name:' in line.lower():
                        service_name = line.split(':', 1)[1].strip()
                        services.append(service_name)
                        
        except Exception as e:
            print(f"Erreur lors de la découverte des services: {e}")
            
        return services
        
    def _detect_device_type(self, name: str) -> str:
        """Détecter le type d'appareil basé sur le nom"""
        name_lower = name.lower()
        
        if any(word in name_lower for word in ['phone', 'mobile', 'samsung', 'iphone', 'huawei', 'xiaomi', 'oneplus']):
            return 'phone'
        elif any(word in name_lower for word in ['laptop', 'pc', 'computer', 'macbook', 'thinkpad', 'dell']):
            return 'computer'
        elif any(word in name_lower for word in ['headset', 'earbuds', 'airpods', 'jbl', 'sony']):
            return 'headset'
        elif any(word in name_lower for word in ['speaker', 'sound', 'audio', 'bose', 'harman']):
            return 'speaker'
        else:
            return 'unknown'
            
    def stop_scan(self):
        """Arrêter le scan"""
        self.is_scanning = False
        if self.scan_thread:
            self.scan_thread.join()
            
    def get_devices(self) -> List[BluetoothDevice]:
        """Obtenir la liste des appareils découverts"""
        return list(self.devices.values())
        
    def execute_attack(self, attack_type: str, target: str, config: Dict, log_callback: Callable = None) -> bool:
        """Exécuter une attaque spécifique"""
        if self.is_attacking:
            log_callback("❌ Une attaque est déjà en cours", "error") if log_callback else None
            return False
            
        try:
            self.is_attacking = True
            
            # Importer et instancier l'attaque appropriée
            attack_class = self._get_attack_class(attack_type)
            if not attack_class:
                log_callback(f"❌ Type d'attaque non supporté: {attack_type}", "error") if log_callback else None
                return False
                
            # Créer l'instance d'attaque
            self.current_attack = attack_class(config, log_callback)
            
            # Démarrer l'attaque dans un thread séparé
            self.attack_thread = threading.Thread(
                target=self._execute_attack_worker,
                args=(attack_type, target, config, log_callback)
            )
            self.attack_thread.daemon = True
            self.attack_thread.start()
            
            return True
            
        except Exception as e:
            log_callback(f"❌ Erreur lors du démarrage de l'attaque: {e}", "error") if log_callback else None
            self.is_attacking = False
            return False
            
    def _get_attack_class(self, attack_type: str):
        """Obtenir la classe d'attaque appropriée"""
        attack_classes = {
            "BlueBorne": "src.attacks.blueborne_attack.BlueBorneAttack",
            "KNOB": "src.attacks.knob_attack.KNOBAttack",
            "BlueSmack": "src.attacks.bluesmack_attack.BlueSmackAttack",
            "BlueSnarf": "src.attacks.bluesnarf_attack.BlueSnarfAttack",
            "BlueJacking": "src.attacks.bluejacking_attack.BlueJackingAttack",
            "L2CAP Injection": "src.attacks.l2cap_injection_attack.L2CAPInjectionAttack",
            "SDP Overflow": "src.attacks.sdp_overflow_attack.SDPOverflowAttack",
            "PIN Cracking": "src.attacks.pin_cracking_attack.PINCrackingAttack",
            "BlueBug": "src.attacks.bluebug_attack.BlueBugAttack"
        }
        
        class_path = attack_classes.get(attack_type)
        if not class_path:
            return None
            
        try:
            module_name, class_name = class_path.rsplit('.', 1)
            module = __import__(module_name, fromlist=[class_name])
            return getattr(module, class_name)
        except Exception as e:
            print(f"Erreur import classe d'attaque {attack_type}: {e}")
            return None
            
    def _execute_attack_worker(self, attack_type: str, target: str, config: Dict, log_callback: Callable):
        """Worker pour l'exécution d'attaque"""
        try:
            log_callback(f"🚀 Démarrage de l'attaque {attack_type} sur {target}", "info") if log_callback else None
            
            # Exécuter l'attaque
            success = self.current_attack.execute(target)
            
            if success:
                log_callback(f"✅ Attaque {attack_type} réussie sur {target}", "success") if log_callback else None
            else:
                log_callback(f"❌ Attaque {attack_type} échouée sur {target}", "error") if log_callback else None
                
        except Exception as e:
            log_callback(f"❌ Erreur lors de l'attaque {attack_type}: {e}", "error") if log_callback else None
        finally:
            self.is_attacking = False
            self.current_attack = None
            
    def stop_attack(self):
        """Arrêter l'attaque en cours"""
        if self.current_attack:
            self.current_attack.stop()
            
        self.is_attacking = False
        if self.attack_thread:
            self.attack_thread.join()
            
    def is_scanning(self) -> bool:
        """Vérifier si un scan est en cours"""
        return self.is_scanning
        
    def is_attacking(self) -> bool:
        """Vérifier si une attaque est en cours"""
        return self.is_attacking
        
    def get_bluetooth_info(self) -> Dict:
        """Obtenir les informations Bluetooth du système"""
        info = {}
        
        try:
            # Informations de l'adaptateur
            result = subprocess.run(['hciconfig', 'hci0'], capture_output=True, text=True)
            if result.returncode == 0:
                output = result.stdout
                
                # Extraire l'adresse MAC
                mac_match = re.search(r'BD Address: ([0-9A-F:]+)', output)
                if mac_match:
                    info['mac_address'] = mac_match.group(1)
                    
                # Extraire le nom
                name_match = re.search(r'Device Name: (.+)', output)
                if name_match:
                    info['device_name'] = name_match.group(1)
                    
                # Statut
                info['status'] = 'UP RUNNING' if 'UP RUNNING' in output else 'DOWN'
                
        except Exception as e:
            print(f"Erreur lors de l'obtention des infos Bluetooth: {e}")
            
        return info
        
    def cleanup(self):
        """Nettoyer les ressources"""
        self.stop_scan()
        self.stop_attack()
