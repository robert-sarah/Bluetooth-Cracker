#!/usr/bin/env python3
"""
Widget d'attaques Bluetooth pour l'interface PyQt5
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QProgressBar, QGroupBox, 
                             QComboBox, QSpinBox, QCheckBox, QTextEdit,
                             QGridLayout, QFrame, QSplitter)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor

class AttackWidget(QWidget):
    attack_started = pyqtSignal(str, str)  # type, target
    attack_stopped = pyqtSignal()
    
    def __init__(self, bluetooth_manager):
        super().__init__()
        self.bluetooth_manager = bluetooth_manager
        self.attack_descriptions = {
            "BlueBorne": "Exploitation de vulnérabilités critiques permettant l'exécution de code à distance via Bluetooth.",
            "KNOB": "Attaque sur la négociation de clés pour forcer l'utilisation de clés faibles.",
            "BlueSmack": "Attaque par déni de service en envoyant des paquets L2CAP de grande taille.",
            "BlueSnarf": "Extraction de données (contacts, calendrier, messages) via le protocole OBEX.",
            "BlueJacking": "Envoi de messages non sollicités via le protocole OBEX.",
            "L2CAP Injection": "Injection de paquets malveillants dans les canaux L2CAP.",
            "SDP Overflow": "Débordement de buffer sur le Service Discovery Protocol.",
            "PIN Cracking": "Crackage de codes PIN par force brute ou dictionnaire.",
            "BlueBug": "Exploitation de bugs pour exécuter des commandes AT sur les appareils."
        }
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """Initialisation de l'interface"""
        layout = QVBoxLayout(self)
        
        # Splitter principal
        splitter = QSplitter(Qt.Horizontal)
        
        # Panneau de gauche - Configuration des attaques
        left_panel = self.create_attack_config_panel()
        splitter.addWidget(left_panel)
        
        # Panneau de droite - Logs et statut
        right_panel = self.create_logs_panel()
        splitter.addWidget(right_panel)
        
        # Répartition des panneaux
        splitter.setSizes([400, 600])
        layout.addWidget(splitter)
        
    def create_attack_config_panel(self):
        """Créer le panneau de configuration des attaques"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Sélection de la cible
        target_group = QGroupBox("🎯 Cible")
        target_layout = QGridLayout(target_group)
        
        target_layout.addWidget(QLabel("Adresse MAC:"), 0, 0)
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("00:11:22:33:44:55")
        target_layout.addWidget(self.target_input, 0, 1)
        
        self.target_from_scanner_btn = QPushButton("📱 Depuis Scanner")
        target_layout.addWidget(self.target_from_scanner_btn, 1, 0, 1, 2)
        
        layout.addWidget(target_group)
        
        # Sélection de l'attaque
        attack_group = QGroupBox("⚔️ Type d'Attaque")
        attack_layout = QVBoxLayout(attack_group)
        
        self.attack_combo = QComboBox()
        self.attack_combo.addItems([
            "BlueBorne",
            "KNOB", 
            "BlueSmack",
            "BlueSnarf",
            "BlueJacking",
            "L2CAP Injection",
            "SDP Overflow",
            "PIN Cracking",
            "BlueBug"
        ])
        attack_layout.addWidget(self.attack_combo)
        
        # Description de l'attaque
        self.attack_desc = QLabel()
        self.attack_desc.setWordWrap(True)
        self.attack_desc.setStyleSheet("color: #cccccc; font-style: italic; padding: 10px;")
        attack_layout.addWidget(self.attack_desc)
        
        layout.addWidget(attack_group)
        
        # Paramètres avancés
        params_group = QGroupBox("⚙️ Paramètres Avancés")
        params_layout = QGridLayout(params_group)
        
        params_layout.addWidget(QLabel("Timeout (sec):"), 0, 0)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)
        self.timeout_spin.setValue(60)
        params_layout.addWidget(self.timeout_spin, 0, 1)
        
        params_layout.addWidget(QLabel("Tentatives:"), 1, 0)
        self.attempts_spin = QSpinBox()
        self.attempts_spin.setRange(1, 100)
        self.attempts_spin.setValue(10)
        params_layout.addWidget(self.attempts_spin, 1, 1)
        
        params_layout.addWidget(QLabel("Délai (sec):"), 2, 0)
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(0, 60)
        self.delay_spin.setValue(1)
        self.delay_spin.setSuffix(" sec")
        params_layout.addWidget(self.delay_spin, 2, 1)
        
        # Options
        self.stealth_check = QCheckBox("Mode furtif")
        params_layout.addWidget(self.stealth_check, 3, 0)
        
        self.verbose_check = QCheckBox("Mode verbeux")
        self.verbose_check.setChecked(True)
        params_layout.addWidget(self.verbose_check, 3, 1)
        
        layout.addWidget(params_group)
        
        # Contrôles d'attaque
        controls_group = QGroupBox("🎮 Contrôles")
        controls_layout = QHBoxLayout(controls_group)
        
        self.start_button = QPushButton("🚀 Lancer Attaque")
        self.start_button.setMinimumHeight(40)
        self.start_button.setStyleSheet("background-color: #28a745;")
        
        self.stop_button = QPushButton("⏹️ Arrêter")
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("background-color: #dc3545;")
        
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)
        
        layout.addWidget(controls_group)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        return panel
        
    def create_logs_panel(self):
        """Créer le panneau de logs"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # En-tête des logs
        logs_header = QHBoxLayout()
        logs_header.addWidget(QLabel("📋 Logs d'Attaque"))
        
        self.clear_logs_btn = QPushButton("🗑️ Effacer")
        logs_header.addWidget(self.clear_logs_btn)
        
        self.save_logs_btn = QPushButton("💾 Sauvegarder")
        logs_header.addWidget(self.save_logs_btn)
        
        logs_header.addStretch()
        layout.addLayout(logs_header)
        
        # Zone de logs
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                border: 1px solid #555555;
            }
        """)
        layout.addWidget(self.logs_text)
        
        # Statut
        self.status_label = QLabel("Prêt pour l'attaque")
        self.status_label.setStyleSheet("color: #00ff00; font-weight: bold; padding: 5px;")
        layout.addWidget(self.status_label)
        
        return panel
        
    def setup_connections(self):
        """Configuration des connexions signal/slot"""
        self.attack_combo.currentTextChanged.connect(self.update_attack_description)
        self.start_button.clicked.connect(self.start_attack)
        self.stop_button.clicked.connect(self.stop_attack)
        self.clear_logs_btn.clicked.connect(self.clear_logs)
        self.save_logs_btn.clicked.connect(self.save_logs)
        self.target_from_scanner_btn.clicked.connect(self.get_target_from_scanner)
        
        # Initialiser la description
        self.update_attack_description()
        
    def update_attack_description(self):
        """Mettre à jour la description de l'attaque sélectionnée"""
        attack_type = self.attack_combo.currentText()
        description = self.attack_descriptions.get(attack_type, "Description non disponible.")
        self.attack_desc.setText(description)
        
    def select_attack(self, attack_name):
        """Sélectionner une attaque spécifique"""
        index = self.attack_combo.findText(attack_name)
        if index >= 0:
            self.attack_combo.setCurrentIndex(index)
            
    def start_attack(self):
        """Démarrer l'attaque"""
        target = self.target_input.text().strip()
        if not target:
            self.log_message("❌ Erreur: Adresse cible requise", "error")
            return
            
        attack_type = self.attack_combo.currentText()
        
        # Configurer les paramètres
        config = {
            'timeout': self.timeout_spin.value(),
            'attempts': self.attempts_spin.value(),
            'delay': self.delay_spin.value(),
            'stealth': self.stealth_check.isChecked(),
            'verbose': self.verbose_check.isChecked()
        }
        
        self.log_message(f"🚀 Démarrage de l'attaque {attack_type} sur {target}", "info")
        self.log_message(f"⚙️ Configuration: {config}", "info")
        
        # Démarrer l'attaque via le gestionnaire Bluetooth
        success = self.bluetooth_manager.execute_attack(attack_type, target, config, self.log_message)
        
        if success:
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indéterminé
            self.status_label.setText("Attaque en cours...")
            self.status_label.setStyleSheet("color: #ffff00; font-weight: bold; padding: 5px;")
        else:
            self.log_message("❌ Échec du démarrage de l'attaque", "error")
            
    def stop_attack(self):
        """Arrêter l'attaque"""
        self.bluetooth_manager.stop_attack()
        
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Attaque arrêtée")
        self.status_label.setStyleSheet("color: #ff0000; font-weight: bold; padding: 5px;")
        
        self.log_message("⏹️ Attaque arrêtée par l'utilisateur", "warning")
        
    def get_target_from_scanner(self):
        """Obtenir la cible depuis le scanner"""
        # Cette méthode sera connectée au scanner
        self.log_message("📱 Fonctionnalité à implémenter: sélection depuis le scanner", "info")
        
    def log_message(self, message, level="info"):
        """Ajouter un message aux logs"""
        timestamp = QTimer().remainingTime()  # Utiliser le temps actuel
        timestamp_str = f"[{timestamp:08d}]"
        
        # Couleurs selon le niveau
        color_map = {
            "info": "#ffffff",
            "warning": "#ffff00", 
            "error": "#ff0000",
            "success": "#00ff00"
        }
        
        color = color_map.get(level, "#ffffff")
        formatted_message = f'<span style="color: {color};">{timestamp_str} [{level.upper()}] {message}</span>'
        
        self.logs_text.append(formatted_message)
        
        # Auto-scroll
        cursor = self.logs_text.textCursor()
        cursor.movePosition(cursor.End)
        self.logs_text.setTextCursor(cursor)
        
    def clear_logs(self):
        """Effacer les logs"""
        self.logs_text.clear()
        self.log_message("🗑️ Logs effacés", "info")
        
    def save_logs(self):
        """Sauvegarder les logs"""
        # Cette fonctionnalité sera implémentée plus tard
        self.log_message("💾 Fonctionnalité de sauvegarde à implémenter", "info")
