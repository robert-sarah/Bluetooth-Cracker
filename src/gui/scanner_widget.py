#!/usr/bin/env python3
"""
Widget de scan Bluetooth pour l'interface PyQt5 - Version 100% fonctionnelle
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QLabel, QProgressBar,
                             QGroupBox, QSpinBox, QCheckBox, QComboBox, QFileDialog,
                             QMessageBox, QHeaderView)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor
import subprocess
import time
import json
import os

class BluetoothScanThread(QThread):
    device_found = pyqtSignal(dict)
    scan_complete = pyqtSignal(list)
    scan_error = pyqtSignal(str)
    
    def __init__(self, duration=30):
        super().__init__()
        self.duration = duration
        self.running = False
        
    def run(self):
        """Thread de scan Bluetooth réel"""
        self.running = True
        devices = []
        
        try:
            # Activer l'interface Bluetooth
            subprocess.run(['hciconfig', 'hci0', 'up'], capture_output=True, check=True)
            
            # Effectuer le scan avec hcitool
            cmd = ['hcitool', 'scan', '--flush']
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            start_time = time.time()
            while time.time() - start_time < self.duration and self.running:
                line = process.stdout.readline()
                if not line:
                    break
                    
                device = self.parse_scan_line(line)
                if device:
                    devices.append(device)
                    self.device_found.emit(device)
                    
            process.terminate()
            
            if self.running:
                self.scan_complete.emit(devices)
                
        except subprocess.CalledProcessError as e:
            self.scan_error.emit(f"Erreur lors du scan: {e}")
        except Exception as e:
            self.scan_error.emit(f"Erreur inattendue: {e}")
        finally:
            self.running = False
            
    def parse_scan_line(self, line):
        """Parser une ligne de scan hcitool"""
        try:
            parts = line.strip().split()
            if len(parts) >= 2:
                address = parts[0]
                name = ' '.join(parts[1:]) if len(parts) > 1 else "Unknown"
                
                # Obtenir des informations supplémentaires
                device_info = self.get_device_info(address)
                
                return {
                    'address': address,
                    'name': name,
                    'type': device_info.get('type', 'unknown'),
                    'rssi': device_info.get('rssi', -50),
                    'services': device_info.get('services', []),
                    'paired': device_info.get('paired', False),
                    'connected': device_info.get('connected', False)
                }
        except Exception as e:
            print(f"Erreur parsing ligne: {e}")
        return None
        
    def get_device_info(self, address):
        """Obtenir des informations détaillées sur l'appareil"""
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
                info['connected'] = 'Connected: Yes' in output
                
            # Découvrir les services
            services = self.discover_services(address)
            info['services'] = services
            
            # Déterminer le type d'appareil
            info['type'] = self.detect_device_type(info.get('name', ''))
            
        except Exception as e:
            print(f"Erreur lors de l'obtention des infos: {e}")
            
        return info
        
    def discover_services(self, address):
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
        
    def detect_device_type(self, name):
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
            
    def stop(self):
        """Arrêter le scan"""
        self.running = False

class BluetoothScannerWidget(QWidget):
    device_selected = pyqtSignal(str)  # Signal émis quand un appareil est sélectionné
    
    def __init__(self, bluetooth_manager):
        super().__init__()
        self.bluetooth_manager = bluetooth_manager
        self.scan_thread = None
        self.devices = []
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """Initialisation de l'interface"""
        layout = QVBoxLayout(self)
        
        # Groupe de contrôle
        control_group = QGroupBox("Contrôles de Scan")
        control_layout = QHBoxLayout(control_group)
        
        # Boutons de contrôle
        self.scan_button = QPushButton("🔍 Démarrer Scan")
        self.scan_button.setMinimumHeight(40)
        self.stop_button = QPushButton("⏹️ Arrêter Scan")
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setEnabled(False)
        
        # Paramètres de scan
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(5, 300)
        self.duration_spin.setValue(30)
        self.duration_spin.setSuffix(" sec")
        
        self.continuous_check = QCheckBox("Scan continu")
        
        control_layout.addWidget(self.scan_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(QLabel("Durée:"))
        control_layout.addWidget(self.duration_spin)
        control_layout.addWidget(self.continuous_check)
        control_layout.addStretch()
        
        layout.addWidget(control_group)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Table des appareils
        devices_group = QGroupBox("Appareils Découverts")
        devices_layout = QVBoxLayout(devices_group)
        
        self.devices_table = QTableWidget()
        self.devices_table.setColumnCount(7)
        self.devices_table.setHorizontalHeaderLabels([
            "Adresse", "Nom", "Type", "RSSI", "Services", "Appairé", "Connecté"
        ])
        
        # Configuration de la table
        header = self.devices_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Adresse
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Nom
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Type
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # RSSI
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Services
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Appairé
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Connecté
        
        self.devices_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.devices_table.setAlternatingRowColors(True)
        
        devices_layout.addWidget(self.devices_table)
        
        # Boutons d'action
        action_layout = QHBoxLayout()
        self.refresh_button = QPushButton("🔄 Actualiser")
        self.clear_button = QPushButton("🗑️ Effacer")
        self.export_button = QPushButton("💾 Exporter")
        
        action_layout.addWidget(self.refresh_button)
        action_layout.addWidget(self.clear_button)
        action_layout.addWidget(self.export_button)
        action_layout.addStretch()
        
        devices_layout.addLayout(action_layout)
        layout.addWidget(devices_group)
        
        # Statut
        self.status_label = QLabel("Prêt pour le scan")
        self.status_label.setStyleSheet("color: #00ff00; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # Timer pour les mises à jour
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_progress)
        
    def setup_connections(self):
        """Configuration des connexions signal/slot"""
        self.scan_button.clicked.connect(self.start_scan)
        self.stop_button.clicked.connect(self.stop_scan)
        self.refresh_button.clicked.connect(self.refresh_devices)
        self.clear_button.clicked.connect(self.clear_devices)
        self.export_button.clicked.connect(self.export_devices)
        
        # Connexions au thread de scan
        if hasattr(self, 'scan_thread') and self.scan_thread:
            self.scan_thread.device_found.connect(self.on_device_found)
            self.scan_thread.scan_complete.connect(self.on_scan_complete)
            self.scan_thread.scan_error.connect(self.on_scan_error)
        
    def start_scan(self):
        """Démarrer le scan"""
        duration = self.duration_spin.value()
        
        self.scan_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, duration)
        self.progress_bar.setValue(0)
        
        self.status_label.setText("Scan en cours...")
        self.status_label.setStyleSheet("color: #ffff00; font-weight: bold;")
        
        # Démarrer le thread de scan
        self.scan_thread = BluetoothScanThread(duration)
        self.scan_thread.device_found.connect(self.on_device_found)
        self.scan_thread.scan_complete.connect(self.on_scan_complete)
        self.scan_thread.scan_error.connect(self.on_scan_error)
        self.scan_thread.start()
        
        # Démarrer le timer de progression
        self.update_timer.start(1000)
        
    def stop_scan(self):
        """Arrêter le scan"""
        if self.scan_thread:
            self.scan_thread.stop()
            self.scan_thread.wait()
            
        self.update_timer.stop()
        
        self.scan_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        self.status_label.setText("Scan arrêté")
        self.status_label.setStyleSheet("color: #ff0000; font-weight: bold;")
        
    def update_progress(self):
        """Mettre à jour la barre de progression"""
        if self.scan_thread and self.scan_thread.running:
            current = self.progress_bar.value()
            if current < self.progress_bar.maximum():
                self.progress_bar.setValue(current + 1)
                
    def on_device_found(self, device):
        """Callback quand un appareil est trouvé"""
        self.add_device_to_table(device)
        
    def on_scan_complete(self, devices):
        """Callback quand le scan est terminé"""
        self.update_timer.stop()
        self.scan_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        self.status_label.setText(f"Scan terminé - {len(devices)} appareils trouvés")
        self.status_label.setStyleSheet("color: #00ff00; font-weight: bold;")
        
    def on_scan_error(self, error_message):
        """Callback en cas d'erreur de scan"""
        self.update_timer.stop()
        self.scan_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        self.status_label.setText(f"Erreur: {error_message}")
        self.status_label.setStyleSheet("color: #ff0000; font-weight: bold;")
        
        QMessageBox.warning(self, "Erreur de Scan", error_message)
        
    def add_device_to_table(self, device):
        """Ajouter un appareil à la table"""
        row = self.devices_table.rowCount()
        self.devices_table.insertRow(row)
        
        # Adresse
        addr_item = QTableWidgetItem(device['address'])
        addr_item.setData(Qt.UserRole, device['address'])
        self.devices_table.setItem(row, 0, addr_item)
        
        # Nom
        name_item = QTableWidgetItem(device['name'])
        self.devices_table.setItem(row, 1, name_item)
        
        # Type
        type_item = QTableWidgetItem(device['type'])
        self.devices_table.setItem(row, 2, type_item)
        
        # RSSI
        rssi_item = QTableWidgetItem(str(device['rssi']))
        self.devices_table.setItem(row, 3, rssi_item)
        
        # Services
        services_item = QTableWidgetItem(", ".join(device['services']))
        self.devices_table.setItem(row, 4, services_item)
        
        # Appairé
        paired_item = QTableWidgetItem("✓" if device['paired'] else "✗")
        paired_item.setForeground(QColor("#00ff00" if device['paired'] else "#ff0000"))
        self.devices_table.setItem(row, 5, paired_item)
        
        # Connecté
        connected_item = QTableWidgetItem("✓" if device['connected'] else "✗")
        connected_item.setForeground(QColor("#00ff00" if device['connected'] else "#ff0000"))
        self.devices_table.setItem(row, 6, connected_item)
        
    def refresh_devices(self):
        """Actualiser la liste des appareils"""
        self.devices_table.setRowCount(0)
        self.devices.clear()
        
        # Relancer un scan rapide
        self.start_scan()
        
    def clear_devices(self):
        """Effacer la liste des appareils"""
        self.devices_table.setRowCount(0)
        self.devices.clear()
        
    def export_devices(self):
        """Exporter la liste des appareils"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Exporter les appareils", "", "Fichiers JSON (*.json);;Fichiers texte (*.txt)"
        )
        
        if filename:
            try:
                devices_data = []
                for row in range(self.devices_table.rowCount()):
                    device = {
                        'address': self.devices_table.item(row, 0).text(),
                        'name': self.devices_table.item(row, 1).text(),
                        'type': self.devices_table.item(row, 2).text(),
                        'rssi': int(self.devices_table.item(row, 3).text()),
                        'services': self.devices_table.item(row, 4).text().split(", ") if self.devices_table.item(row, 4).text() else [],
                        'paired': self.devices_table.item(row, 5).text() == "✓",
                        'connected': self.devices_table.item(row, 6).text() == "✓"
                    }
                    devices_data.append(device)
                
                if filename.endswith('.json'):
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(devices_data, f, indent=2, ensure_ascii=False)
                else:
                    with open(filename, 'w', encoding='utf-8') as f:
                        for device in devices_data:
                            f.write(f"{device['address']}\t{device['name']}\t{device['type']}\t{device['rssi']}\n")
                            
                QMessageBox.information(self, "Succès", f"Appareils exportés dans {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export: {e}")
        
    def get_selected_device(self):
        """Obtenir l'appareil sélectionné"""
        current_row = self.devices_table.currentRow()
        if current_row >= 0:
            addr_item = self.devices_table.item(current_row, 0)
            if addr_item:
                return addr_item.data(Qt.UserRole)
        return None
