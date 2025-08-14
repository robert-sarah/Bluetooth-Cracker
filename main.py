#!/usr/bin/env python3
"""
Advanced Bluetooth Pentest Tool - Interface Graphique Principale
"""

import sys
import os
import subprocess
import threading
import time
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTabWidget, QPushButton, QTextEdit, 
                             QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                             QProgressBar, QGroupBox, QGridLayout, QComboBox,
                             QCheckBox, QSpinBox, QMessageBox, QSplitter,
                             QFrame, QHeaderView, QMenu, QAction, QFileDialog)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPixmap

# Ajout du chemin des modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import des widgets GUI
from src.gui.scanner_widget import BluetoothScannerWidget
from src.gui.attack_widget import AttackWidget
from src.gui.monitor_widget import PacketMonitorWidget
from src.gui.logger_widget import LoggerWidget

# Import du gestionnaire Bluetooth
from src.core.bluetooth_manager import BluetoothManager

# Import de la configuration
from src.utils.config import Config

# Import de tous les modules d'attaques
from src.attacks.blueborne_attack import BlueBorneAttack
from src.attacks.knob_attack import KNOBAttack
from src.attacks.bluesmack_attack import BlueSmackAttack
from src.attacks.bluesnarf_attack import BlueSnarfAttack
from src.attacks.bluejacking_attack import BlueJackingAttack
from src.attacks.l2cap_injection_attack import L2CAPInjectionAttack
from src.attacks.sdp_overflow_attack import SDPOverflowAttack
from src.attacks.pin_cracking_attack import PINCrackingAttack
from src.attacks.bluebug_attack import BlueBugAttack

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.bluetooth_manager = BluetoothManager()
        self.init_ui()
        self.setup_menu()
        
    def init_ui(self):
        """Initialisation de l'interface utilisateur"""
        self.setWindowTitle("Advanced Bluetooth Pentest Tool v2.0")
        self.setGeometry(100, 100, 1400, 900)
        
        # Style moderne
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #3c3c3c;
            }
            QTabBar::tab {
                background-color: #4a4a4a;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #0078d4;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555555;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
            QTableWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                gridline-color: #555555;
                border: 1px solid #555555;
            }
            QHeaderView::section {
                background-color: #4a4a4a;
                color: #ffffff;
                padding: 4px;
                border: 1px solid #555555;
            }
            QLineEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 4px;
                border-radius: 2px;
            }
            QComboBox {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 4px;
                border-radius: 2px;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Barre de titre
        title_layout = QHBoxLayout()
        title_label = QLabel("🔵 Advanced Bluetooth Pentest Tool")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet("color: #0078d4; padding: 10px;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Status bar
        self.status_label = QLabel("Prêt")
        self.status_label.setStyleSheet("color: #00ff00; padding: 5px;")
        title_layout.addWidget(self.status_label)
        
        main_layout.addLayout(title_layout)
        
        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # Onglets principaux
        self.tab_widget = QTabWidget()
        
        # Onglet Scanner
        self.scanner_widget = BluetoothScannerWidget(self.bluetooth_manager)
        self.tab_widget.addTab(self.scanner_widget, "🔍 Scanner")
        
        # Onglet Attaques
        self.attack_widget = AttackWidget(self.bluetooth_manager)
        self.tab_widget.addTab(self.attack_widget, "⚔️ Attaques")
        
        # Onglet Monitor
        self.monitor_widget = PacketMonitorWidget(self.bluetooth_manager)
        self.tab_widget.addTab(self.monitor_widget, "📊 Monitor")
        
        # Onglet Logs
        self.logger_widget = LoggerWidget()
        self.tab_widget.addTab(self.logger_widget, "📝 Logs")
        
        main_layout.addWidget(self.tab_widget)
        
        # Barre de statut
        self.statusBar().showMessage("Outil de pentest Bluetooth prêt")
        
        # Timer pour les mises à jour
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(1000)
        
    def setup_menu(self):
        """Configuration du menu principal"""
        menubar = self.menuBar()
        
        # Menu Fichier
        file_menu = menubar.addMenu('Fichier')
        
        new_action = QAction('Nouveau Scan', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_scan)
        file_menu.addAction(new_action)
        
        save_action = QAction('Sauvegarder Logs', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_logs)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Quitter', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu Outils
        tools_menu = menubar.addMenu('Outils')
        
        config_action = QAction('Configuration', self)
        config_action.triggered.connect(self.show_config)
        tools_menu.addAction(config_action)
        
        # Menu Attaques
        attacks_menu = menubar.addMenu('Attaques')
        
        # Sous-menu pour chaque type d'attaque
        attack_types = [
            ('BlueBorne', self.launch_blueborne),
            ('KNOB', self.launch_knob),
            ('BlueSmack', self.launch_bluesmack),
            ('BlueSnarf', self.launch_bluesnarf),
            ('BlueJacking', self.launch_bluejacking),
            ('L2CAP Injection', self.launch_l2cap_injection),
            ('SDP Overflow', self.launch_sdp_overflow),
            ('PIN Cracking', self.launch_pin_cracking),
            ('BlueBug', self.launch_bluebug)
        ]
        
        for attack_name, attack_func in attack_types:
            action = QAction(attack_name, self)
            action.triggered.connect(attack_func)
            attacks_menu.addAction(action)
        
        # Menu Aide
        help_menu = menubar.addMenu('Aide')
        
        about_action = QAction('À propos', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def new_scan(self):
        """Démarrer un nouveau scan"""
        self.scanner_widget.start_scan()
        
    def save_logs(self):
        """Sauvegarder les logs"""
        self.logger_widget.save_logs()
        
    def show_config(self):
        """Afficher la configuration"""
        QMessageBox.information(self, "Configuration", "Configuration à implémenter")
        
    def launch_blueborne(self):
        """Lancer l'attaque BlueBorne"""
        self.tab_widget.setCurrentIndex(1)  # Onglet Attaques
        self.attack_widget.select_attack("BlueBorne")
        
    def launch_knob(self):
        """Lancer l'attaque KNOB"""
        self.tab_widget.setCurrentIndex(1)
        self.attack_widget.select_attack("KNOB")
        
    def launch_bluesmack(self):
        """Lancer l'attaque BlueSmack"""
        self.tab_widget.setCurrentIndex(1)
        self.attack_widget.select_attack("BlueSmack")
        
    def launch_bluesnarf(self):
        """Lancer l'attaque BlueSnarf"""
        self.tab_widget.setCurrentIndex(1)
        self.attack_widget.select_attack("BlueSnarf")
        
    def launch_bluejacking(self):
        """Lancer l'attaque BlueJacking"""
        self.tab_widget.setCurrentIndex(1)
        self.attack_widget.select_attack("BlueJacking")
        
    def launch_l2cap_injection(self):
        """Lancer l'attaque L2CAP Injection"""
        self.tab_widget.setCurrentIndex(1)
        self.attack_widget.select_attack("L2CAP Injection")
        
    def launch_sdp_overflow(self):
        """Lancer l'attaque SDP Overflow"""
        self.tab_widget.setCurrentIndex(1)
        self.attack_widget.select_attack("SDP Overflow")
        
    def launch_pin_cracking(self):
        """Lancer l'attaque PIN Cracking"""
        self.tab_widget.setCurrentIndex(1)
        self.attack_widget.select_attack("PIN Cracking")
        
    def launch_bluebug(self):
        """Lancer l'attaque BlueBug"""
        self.tab_widget.setCurrentIndex(1)
        self.attack_widget.select_attack("BlueBug")
        
    def show_about(self):
        """Afficher la boîte de dialogue À propos"""
        QMessageBox.about(self, "À propos", 
                         "Advanced Bluetooth Pentest Tool v2.0\n\n"
                         "Outil de pentest Bluetooth avancé avec interface graphique.\n"
                         "Inclut les attaques BlueBorne, KNOB, BlueSmack, BlueSnarf,\n"
                         "BlueJacking, L2CAP Injection, SDP Overflow, PIN Cracking,\n"
                         "et BlueBug.\n\n"
                         "⚠️ Usage éducatif uniquement !")
        
    def update_status(self):
        """Mise à jour du statut"""
        
        if  self.bluetooth_manager.is_scanning():
            self.status_label.setText("Scanning...")
            self.status_label.setStyleSheet("color: #ffff00; padding: 5px;")
        elif self.bluetooth_manager.is_attacking():
            self.status_label.setText("Attaque en cours...")
            self.status_label.setStyleSheet("color: #ff0000; padding: 5px;")
        else:
            self.status_label.setText("Prêt")
            self.status_label.setStyleSheet("color: #00ff00; padding: 5px;")
            
    def closeEvent(self, event):
        """Gestion de la fermeture de l'application"""
        reply = QMessageBox.question(self, 'Quitter', 
                                   "Êtes-vous sûr de vouloir quitter ?",
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.bluetooth_manager.cleanup()
            event.accept()
        else:
            event.ignore()

def main():
    """Fonction principale"""
    app = QApplication(sys.argv)
    
    # Vérification des privilèges
    if os.geteuid() != 0:
        QMessageBox.warning(None, "Privilèges", 
                          "⚠️ Cet outil nécessite des privilèges root pour fonctionner correctement.\n"
                          "Relancez avec sudo pour de meilleures performances.")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
