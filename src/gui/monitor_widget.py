#!/usr/bin/env python3
"""
Widget de monitoring des paquets Bluetooth en temps réel
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTextEdit, QGroupBox, QComboBox, 
                             QCheckBox, QSpinBox, QTableWidget, QTableWidgetItem,
                             QSplitter, QFrame, QHeaderView)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor
import time
import struct
import subprocess
import re
import os

class PacketCaptureThread(QThread):
    packet_captured = pyqtSignal(dict)
    
    def __init__(self, bluetooth_manager):
        super().__init__()
        self.bluetooth_manager = bluetooth_manager
        self.running = False
        self.filters = []
        self.capture_process = None
        
    def run(self):
        """Thread de capture de paquets Bluetooth réels"""
        self.running = True
        
        try:
            # Utiliser btmon pour capturer les paquets Bluetooth
            self.capture_process = subprocess.Popen(
                ['btmon', '--write', '-'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            while self.running and self.capture_process.poll() is None:
                line = self.capture_process.stdout.readline()
                if not line:
                    break
                    
                # Parser la ligne de btmon
                packet_data = self._parse_btmon_line(line)
                if packet_data:
                    # Appliquer les filtres
                    if self.should_show_packet(packet_data):
                        self.packet_captured.emit(packet_data)
                        
        except Exception as e:
            print(f"Erreur lors de la capture: {e}")
        finally:
            if self.capture_process:
                self.capture_process.terminate()
                
    def _parse_btmon_line(self, line: str) -> dict:
        """Parser une ligne de btmon"""
        try:
            # Ignorer les lignes vides
            if not line.strip():
                return None
                
            # Parser les différents types de paquets
            if 'HCI' in line:
                return self._parse_hci_packet(line)
            elif 'L2CAP' in line:
                return self._parse_l2cap_packet(line)
            elif 'RFCOMM' in line:
                return self._parse_rfcomm_packet(line)
            elif 'SDP' in line:
                return self._parse_sdp_packet(line)
            elif 'OBEX' in line:
                return self._parse_obex_packet(line)
            else:
                return self._parse_generic_packet(line)
                
        except Exception as e:
            print(f"Erreur parsing ligne btmon: {e}")
            return None
            
    def _parse_hci_packet(self, line: str) -> dict:
        """Parser un paquet HCI"""
        # Extraire les informations HCI
        timestamp_match = re.search(r'(\d{2}:\d{2}:\d{2}\.\d{6})', line)
        timestamp = timestamp_match.group(1) if timestamp_match else time.strftime("%H:%M:%S")
        
        # Déterminer la direction
        direction = "OUT" if "> HCI" in line else "IN" if "< HCI" in line else "UNKNOWN"
        
        # Extraire le type de commande
        cmd_match = re.search(r'(\w+)\s+(\w+)', line)
        if cmd_match:
            packet_type = f"HCI_{cmd_match.group(1)}"
        else:
            packet_type = "HCI"
            
        # Extraire les données hexadécimales
        hex_data = re.findall(r'([0-9A-Fa-f]{2})', line)
        data = [int(x, 16) for x in hex_data] if hex_data else []
        
        return {
            'timestamp': timestamp,
            'type': packet_type,
            'direction': direction,
            'source': 'HCI',
            'destination': 'HCI',
            'length': len(data),
            'data': data,
            'raw_line': line.strip()
        }
        
    def _parse_l2cap_packet(self, line: str) -> dict:
        """Parser un paquet L2CAP"""
        timestamp_match = re.search(r'(\d{2}:\d{2}:\d{2}\.\d{6})', line)
        timestamp = timestamp_match.group(1) if timestamp_match else time.strftime("%H:%M:%S")
        
        direction = "OUT" if "> L2CAP" in line else "IN" if "< L2CAP" in line else "UNKNOWN"
        
        # Extraire le CID
        cid_match = re.search(r'CID: (\w+)', line)
        cid = cid_match.group(1) if cid_match else "Unknown"
        
        # Extraire les données
        hex_data = re.findall(r'([0-9A-Fa-f]{2})', line)
        data = [int(x, 16) for x in hex_data] if hex_data else []
        
        return {
            'timestamp': timestamp,
            'type': 'L2CAP',
            'direction': direction,
            'source': f'L2CAP:{cid}',
            'destination': f'L2CAP:{cid}',
            'length': len(data),
            'data': data,
            'raw_line': line.strip()
        }
        
    def _parse_rfcomm_packet(self, line: str) -> dict:
        """Parser un paquet RFCOMM"""
        timestamp_match = re.search(r'(\d{2}:\d{2}:\d{2}\.\d{6})', line)
        timestamp = timestamp_match.group(1) if timestamp_match else time.strftime("%H:%M:%S")
        
        direction = "OUT" if "> RFCOMM" in line else "IN" if "< RFCOMM" in line else "UNKNOWN"
        
        # Extraire le port
        port_match = re.search(r'Port: (\d+)', line)
        port = port_match.group(1) if port_match else "Unknown"
        
        # Extraire les données
        hex_data = re.findall(r'([0-9A-Fa-f]{2})', line)
        data = [int(x, 16) for x in hex_data] if hex_data else []
        
        return {
            'timestamp': timestamp,
            'type': 'RFCOMM',
            'direction': direction,
            'source': f'RFCOMM:{port}',
            'destination': f'RFCOMM:{port}',
            'length': len(data),
            'data': data,
            'raw_line': line.strip()
        }
        
    def _parse_sdp_packet(self, line: str) -> dict:
        """Parser un paquet SDP"""
        timestamp_match = re.search(r'(\d{2}:\d{2}:\d{2}\.\d{6})', line)
        timestamp = timestamp_match.group(1) if timestamp_match else time.strftime("%H:%M:%S")
        
        direction = "OUT" if "> SDP" in line else "IN" if "< SDP" in line else "UNKNOWN"
        
        # Extraire les données
        hex_data = re.findall(r'([0-9A-Fa-f]{2})', line)
        data = [int(x, 16) for x in hex_data] if hex_data else []
        
        return {
            'timestamp': timestamp,
            'type': 'SDP',
            'direction': direction,
            'source': 'SDP',
            'destination': 'SDP',
            'length': len(data),
            'data': data,
            'raw_line': line.strip()
        }
        
    def _parse_obex_packet(self, line: str) -> dict:
        """Parser un paquet OBEX"""
        timestamp_match = re.search(r'(\d{2}:\d{2}:\d{2}\.\d{6})', line)
        timestamp = timestamp_match.group(1) if timestamp_match else time.strftime("%H:%M:%S")
        
        direction = "OUT" if "> OBEX" in line else "IN" if "< OBEX" in line else "UNKNOWN"
        
        # Extraire les données
        hex_data = re.findall(r'([0-9A-Fa-f]{2})', line)
        data = [int(x, 16) for x in hex_data] if hex_data else []
        
        return {
            'timestamp': timestamp,
            'type': 'OBEX',
            'direction': direction,
            'source': 'OBEX',
            'destination': 'OBEX',
            'length': len(data),
            'data': data,
            'raw_line': line.strip()
        }
        
    def _parse_generic_packet(self, line: str) -> dict:
        """Parser un paquet générique"""
        timestamp_match = re.search(r'(\d{2}:\d{2}:\d{2}\.\d{6})', line)
        timestamp = timestamp_match.group(1) if timestamp_match else time.strftime("%H:%M:%S")
        
        # Déterminer le type basé sur le contenu
        if 'AVDTP' in line:
            packet_type = 'AVDTP'
        elif 'AVCTP' in line:
            packet_type = 'AVCTP'
        else:
            packet_type = 'UNKNOWN'
            
        direction = "UNKNOWN"
        
        # Extraire les données
        hex_data = re.findall(r'([0-9A-Fa-f]{2})', line)
        data = [int(x, 16) for x in hex_data] if hex_data else []
        
        return {
            'timestamp': timestamp,
            'type': packet_type,
            'direction': direction,
            'source': packet_type,
            'destination': packet_type,
            'length': len(data),
            'data': data,
            'raw_line': line.strip()
        }
        
    def should_show_packet(self, packet):
        """Vérifier si le paquet doit être affiché selon les filtres"""
        if not self.filters:
            return True
            
        for filter_type, filter_value in self.filters:
            if filter_type == 'type' and packet['type'] != filter_value:
                return False
            elif filter_type == 'direction' and packet['direction'] != filter_value:
                return False
        return True
        
    def set_filters(self, filters):
        """Définir les filtres de paquets"""
        self.filters = filters
        
    def stop(self):
        """Arrêter la capture"""
        self.running = False
        if self.capture_process:
            self.capture_process.terminate()

class PacketMonitorWidget(QWidget):
    def __init__(self, bluetooth_manager):
        super().__init__()
        self.bluetooth_manager = bluetooth_manager
        self.capture_thread = PacketCaptureThread(bluetooth_manager)
        self.packets = []
        self.max_packets = 1000
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """Initialisation de l'interface"""
        layout = QVBoxLayout(self)
        
        # Splitter principal
        splitter = QSplitter(Qt.Horizontal)
        
        # Panneau de gauche - Contrôles et filtres
        left_panel = self.create_controls_panel()
        splitter.addWidget(left_panel)
        
        # Panneau de droite - Affichage des paquets
        right_panel = self.create_packets_panel()
        splitter.addWidget(right_panel)
        
        # Répartition des panneaux
        splitter.setSizes([300, 700])
        layout.addWidget(splitter)
        
    def create_controls_panel(self):
        """Créer le panneau de contrôles"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Contrôles de capture
        capture_group = QGroupBox("🎯 Contrôles de Capture")
        capture_layout = QVBoxLayout(capture_group)
        
        # Boutons de contrôle
        buttons_layout = QHBoxLayout()
        
        self.start_capture_btn = QPushButton("▶️ Démarrer Capture")
        self.start_capture_btn.setMinimumHeight(40)
        
        self.stop_capture_btn = QPushButton("⏹️ Arrêter Capture")
        self.stop_capture_btn.setMinimumHeight(40)
        self.stop_capture_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.start_capture_btn)
        buttons_layout.addWidget(self.stop_capture_btn)
        
        capture_layout.addLayout(buttons_layout)
        
        # Statistiques de capture
        self.capture_stats = QLabel("Paquets capturés: 0")
        self.capture_stats.setStyleSheet("color: #0078d4; font-weight: bold;")
        capture_layout.addWidget(self.capture_stats)
        
        layout.addWidget(capture_group)
        
        # Filtres
        filters_group = QGroupBox("🔍 Filtres")
        filters_layout = QVBoxLayout(filters_group)
        
        # Filtre par type
        filters_layout.addWidget(QLabel("Type de paquet:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems(["Tous", "HCI", "L2CAP", "RFCOMM", "SDP", "OBEX", "AVDTP", "AVCTP"])
        filters_layout.addWidget(self.type_filter)
        
        # Filtre par direction
        filters_layout.addWidget(QLabel("Direction:"))
        self.direction_filter = QComboBox()
        self.direction_filter.addItems(["Toutes", "IN", "OUT"])
        filters_layout.addWidget(self.direction_filter)
        
        # Options de capture
        self.auto_scroll_check = QCheckBox("Défilement automatique")
        self.auto_scroll_check.setChecked(True)
        filters_layout.addWidget(self.auto_scroll_check)
        
        self.hex_view_check = QCheckBox("Vue hexadécimale")
        filters_layout.addWidget(self.hex_view_check)
        
        # Limite de paquets
        filters_layout.addWidget(QLabel("Limite de paquets:"))
        self.max_packets_spin = QSpinBox()
        self.max_packets_spin.setRange(100, 10000)
        self.max_packets_spin.setValue(1000)
        filters_layout.addWidget(self.max_packets_spin)
        
        layout.addWidget(filters_group)
        
        # Actions
        actions_group = QGroupBox("⚡ Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        self.clear_btn = QPushButton("🗑️ Effacer")
        self.save_btn = QPushButton("💾 Sauvegarder")
        self.export_pcap_btn = QPushButton("📦 Exporter PCAP")
        
        actions_layout.addWidget(self.clear_btn)
        actions_layout.addWidget(self.save_btn)
        actions_layout.addWidget(self.export_pcap_btn)
        
        layout.addWidget(actions_group)
        
        layout.addStretch()
        return panel
        
    def create_packets_panel(self):
        """Créer le panneau d'affichage des paquets"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Table des paquets
        packets_group = QGroupBox("📦 Paquets Capturés")
        packets_layout = QVBoxLayout(packets_group)
        
        self.packets_table = QTableWidget()
        self.packets_table.setColumnCount(7)
        self.packets_table.setHorizontalHeaderLabels([
            "Timestamp", "Type", "Direction", "Source", "Destination", "Taille", "Données"
        ])
        
        # Configuration de la table
        header = self.packets_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Timestamp
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Type
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Direction
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Source
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Destination
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Taille
        header.setSectionResizeMode(6, QHeaderView.Stretch)           # Données
        
        self.packets_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.packets_table.setAlternatingRowColors(True)
        
        packets_layout.addWidget(self.packets_table)
        
        # Détails du paquet sélectionné
        details_group = QGroupBox("🔍 Détails du Paquet")
        details_layout = QVBoxLayout(details_group)
        
        self.packet_details = QTextEdit()
        self.packet_details.setReadOnly(True)
        self.packet_details.setMaximumHeight(150)
        self.packet_details.setFont(QFont("Consolas", 9))
        details_layout.addWidget(self.packet_details)
        
        packets_layout.addWidget(details_group)
        layout.addWidget(packets_group)
        
        return panel
        
    def setup_connections(self):
        """Configuration des connexions signal/slot"""
        self.start_capture_btn.clicked.connect(self.start_capture)
        self.stop_capture_btn.clicked.connect(self.stop_capture)
        self.clear_btn.clicked.connect(self.clear_packets)
        self.save_btn.clicked.connect(self.save_packets)
        self.export_pcap_btn.clicked.connect(self.export_pcap)
        
        self.type_filter.currentTextChanged.connect(self.update_filters)
        self.direction_filter.currentTextChanged.connect(self.update_filters)
        self.max_packets_spin.valueChanged.connect(self.update_max_packets)
        
        self.packets_table.itemSelectionChanged.connect(self.show_packet_details)
        
        # Connexion au thread de capture
        self.capture_thread.packet_captured.connect(self.add_packet)
        
    def start_capture(self):
        """Démarrer la capture de paquets"""
        self.start_capture_btn.setEnabled(False)
        self.stop_capture_btn.setEnabled(True)
        
        # Mettre à jour les filtres
        self.update_filters()
        
        # Démarrer le thread de capture
        self.capture_thread.start()
        
    def stop_capture(self):
        """Arrêter la capture de paquets"""
        self.capture_thread.stop()
        self.capture_thread.wait()
        
        self.start_capture_btn.setEnabled(True)
        self.stop_capture_btn.setEnabled(False)
        
    def update_filters(self):
        """Mettre à jour les filtres de capture"""
        filters = []
        
        type_filter = self.type_filter.currentText()
        if type_filter != "Tous":
            filters.append(('type', type_filter))
            
        direction_filter = self.direction_filter.currentText()
        if direction_filter != "Toutes":
            filters.append(('direction', direction_filter))
            
        self.capture_thread.set_filters(filters)
        
    def update_max_packets(self):
        """Mettre à jour la limite de paquets"""
        self.max_packets = self.max_packets_spin.value()
        
    def add_packet(self, packet_data):
        """Ajouter un paquet à la table"""
        # Limiter le nombre de paquets
        if len(self.packets) >= self.max_packets:
            self.packets.pop(0)
            self.packets_table.removeRow(0)
            
        self.packets.append(packet_data)
        
        # Ajouter à la table
        row = self.packets_table.rowCount()
        self.packets_table.insertRow(row)
        
        # Timestamp
        self.packets_table.setItem(row, 0, QTableWidgetItem(packet_data['timestamp']))
        
        # Type
        type_item = QTableWidgetItem(packet_data['type'])
        type_item.setData(Qt.UserRole, row)  # Index dans la liste
        self.packets_table.setItem(row, 1, type_item)
        
        # Direction
        direction_item = QTableWidgetItem(packet_data['direction'])
        direction_item.setForeground(QColor("#00ff00" if packet_data['direction'] == "IN" else "#ff0000"))
        self.packets_table.setItem(row, 2, direction_item)
        
        # Source
        self.packets_table.setItem(row, 3, QTableWidgetItem(packet_data['source']))
        
        # Destination
        self.packets_table.setItem(row, 4, QTableWidgetItem(packet_data['destination']))
        
        # Taille
        self.packets_table.setItem(row, 5, QTableWidgetItem(str(packet_data['length'])))
        
        # Données (aperçu)
        data_preview = self.format_data_preview(packet_data['data'])
        self.packets_table.setItem(row, 6, QTableWidgetItem(data_preview))
        
        # Mettre à jour les statistiques
        self.capture_stats.setText(f"Paquets capturés: {len(self.packets)}")
        
        # Auto-scroll
        if self.auto_scroll_check.isChecked():
            self.packets_table.scrollToBottom()
            
    def format_data_preview(self, data):
        """Formater l'aperçu des données"""
        if self.hex_view_check.isChecked():
            # Vue hexadécimale
            hex_data = ' '.join([f"{b:02x}" for b in data[:8]])
            if len(data) > 8:
                hex_data += "..."
            return hex_data
        else:
            # Vue ASCII
            ascii_data = ''.join([chr(b) if 32 <= b <= 126 else '.' for b in data[:16]])
            if len(data) > 16:
                ascii_data += "..."
            return ascii_data
            
    def show_packet_details(self):
        """Afficher les détails du paquet sélectionné"""
        current_row = self.packets_table.currentRow()
        if current_row >= 0 and current_row < len(self.packets):
            packet = self.packets[current_row]
            
            details = f"""Paquet #{current_row + 1}
Timestamp: {packet['timestamp']}
Type: {packet['type']}
Direction: {packet['direction']}
Source: {packet['source']}
Destination: {packet['destination']}
Taille: {packet['length']} octets

Ligne brute:
{packet.get('raw_line', 'N/A')}

Données (Hex):
{self.format_hex_data(packet['data'])}

Données (ASCII):
{self.format_ascii_data(packet['data'])}
"""
            
            self.packet_details.setText(details)
            
    def format_hex_data(self, data):
        """Formater les données en hexadécimal"""
        hex_lines = []
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            hex_part = ' '.join([f"{b:02x}" for b in chunk])
            ascii_part = ''.join([chr(b) if 32 <= b <= 126 else '.' for b in chunk])
            hex_lines.append(f"{i:04x}: {hex_part:<48} {ascii_part}")
        return '\n'.join(hex_lines)
        
    def format_ascii_data(self, data):
        """Formater les données en ASCII"""
        return ''.join([chr(b) if 32 <= b <= 126 else '.' for b in data])
        
    def clear_packets(self):
        """Effacer tous les paquets"""
        self.packets.clear()
        self.packets_table.setRowCount(0)
        self.packet_details.clear()
        self.capture_stats.setText("Paquets capturés: 0")
        
    def save_packets(self):
        """Sauvegarder les paquets"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            
            filename, _ = QFileDialog.getSaveFileName(
                self, "Sauvegarder les paquets", "", "Fichiers texte (*.txt);;Tous les fichiers (*)"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    for packet in self.packets:
                        f.write(f"{packet.get('raw_line', 'N/A')}\n")
                        
        except Exception as e:
            print(f"Erreur lors de la sauvegarde: {e}")
        
    def export_pcap(self):
        """Exporter au format PCAP"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            
            filename, _ = QFileDialog.getSaveFileName(
                self, "Exporter PCAP", "", "Fichiers PCAP (*.pcap);;Tous les fichiers (*)"
            )
            
            if filename:
                # Convertir les paquets en format PCAP
                self._write_pcap_file(filename)
                
        except Exception as e:
            print(f"Erreur lors de l'export PCAP: {e}")
            
    def _write_pcap_file(self, filename):
        """Écrire un fichier PCAP"""
        try:
            import struct
            
            with open(filename, 'wb') as f:
                # Header PCAP
                f.write(struct.pack('<I', 0xa1b2c3d4))  # Magic number
                f.write(struct.pack('<H', 2))           # Version major
                f.write(struct.pack('<H', 4))           # Version minor
                f.write(struct.pack('<I', 0))           # Timezone
                f.write(struct.pack('<I', 0))           # Timestamp accuracy
                f.write(struct.pack('<I', 65535))       # Snapshot length
                f.write(struct.pack('<I', 147))         # Link layer type (Bluetooth)
                
                # Écrire les paquets
                for packet in self.packets:
                    # Header de paquet PCAP
                    timestamp = int(time.time())
                    f.write(struct.pack('<I', timestamp))  # Timestamp seconds
                    f.write(struct.pack('<I', 0))          # Timestamp microseconds
                    f.write(struct.pack('<I', len(packet['data'])))  # Captured length
                    f.write(struct.pack('<I', len(packet['data'])))  # Original length
                    
                    # Données du paquet
                    f.write(bytes(packet['data']))
                    
        except Exception as e:
            print(f"Erreur lors de l'écriture PCAP: {e}")
