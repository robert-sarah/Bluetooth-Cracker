#!/usr/bin/env python3
"""
Widget de logs pour l'interface PyQt5
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTextEdit, QGroupBox, QComboBox, QCheckBox,
                             QLabel, QSpinBox, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QTextCursor
import time
import os

class LoggerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.logs = []
        self.max_logs = 10000
        self.log_levels = {
            "DEBUG": 0,
            "INFO": 1,
            "WARNING": 2,
            "ERROR": 3,
            "CRITICAL": 4
        }
        self.current_level = "INFO"
        self.init_ui()
        
    def init_ui(self):
        """Initialisation de l'interface"""
        layout = QVBoxLayout(self)
        
        # Contrôles de logs
        controls_group = QGroupBox("🎛️ Contrôles de Logs")
        controls_layout = QHBoxLayout(controls_group)
        
        # Niveau de log
        controls_layout.addWidget(QLabel("Niveau:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_combo.setCurrentText("INFO")
        controls_layout.addWidget(self.level_combo)
        
        # Options
        self.auto_scroll_check = QCheckBox("Défilement auto")
        self.auto_scroll_check.setChecked(True)
        controls_layout.addWidget(self.auto_scroll_check)
        
        self.timestamp_check = QCheckBox("Afficher timestamps")
        self.timestamp_check.setChecked(True)
        controls_layout.addWidget(self.timestamp_check)
        
        self.color_check = QCheckBox("Couleurs")
        self.color_check.setChecked(True)
        controls_layout.addWidget(self.color_check)
        
        # Limite de logs
        controls_layout.addWidget(QLabel("Limite:"))
        self.max_logs_spin = QSpinBox()
        self.max_logs_spin.setRange(100, 100000)
        self.max_logs_spin.setValue(10000)
        controls_layout.addWidget(self.max_logs_spin)
        
        controls_layout.addStretch()
        layout.addWidget(controls_group)
        
        # Zone de logs
        logs_group = QGroupBox("📝 Logs")
        logs_layout = QVBoxLayout(logs_group)
        
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setFont(QFont("Consolas", 10))
        self.logs_text.setLineWrapMode(QTextEdit.NoWrap)
        logs_layout.addWidget(self.logs_text)
        
        # Barre de statut
        self.status_label = QLabel("Logs: 0")
        self.status_label.setStyleSheet("color: #0078d4; font-weight: bold;")
        logs_layout.addWidget(self.status_label)
        
        layout.addWidget(logs_group)
        
        # Actions
        actions_group = QGroupBox("⚡ Actions")
        actions_layout = QHBoxLayout(actions_group)
        
        self.clear_btn = QPushButton("🗑️ Effacer")
        self.save_btn = QPushButton("💾 Sauvegarder")
        self.export_btn = QPushButton("📤 Exporter")
        self.copy_btn = QPushButton("📋 Copier")
        self.find_btn = QPushButton("🔍 Rechercher")
        
        actions_layout.addWidget(self.clear_btn)
        actions_layout.addWidget(self.save_btn)
        actions_layout.addWidget(self.export_btn)
        actions_layout.addWidget(self.copy_btn)
        actions_layout.addWidget(self.find_btn)
        actions_layout.addStretch()
        
        layout.addWidget(actions_group)
        
        # Connexions
        self.setup_connections()
        
        # Ajouter quelques logs de test
        self.add_log("INFO", "Système de logs initialisé")
        self.add_log("DEBUG", "Interface graphique chargée")
        
    def setup_connections(self):
        """Configuration des connexions signal/slot"""
        self.clear_btn.clicked.connect(self.clear_logs)
        self.save_btn.clicked.connect(self.save_logs)
        self.export_btn.clicked.connect(self.export_logs)
        self.copy_btn.clicked.connect(self.copy_logs)
        self.find_btn.clicked.connect(self.find_in_logs)
        
        self.level_combo.currentTextChanged.connect(self.update_log_level)
        self.max_logs_spin.valueChanged.connect(self.update_max_logs)
        
    def add_log(self, level, message, source="System"):
        """Ajouter un log"""
        if self.log_levels.get(level, 0) < self.log_levels.get(self.current_level, 0):
            return
            
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message,
            'source': source
        }
        
        self.logs.append(log_entry)
        
        # Limiter le nombre de logs
        if len(self.logs) > self.max_logs:
            self.logs.pop(0)
            
        # Afficher le log
        self.display_log(log_entry)
        
        # Mettre à jour le statut
        self.status_label.setText(f"Logs: {len(self.logs)}")
        
    def display_log(self, log_entry):
        """Afficher un log dans la zone de texte"""
        if not self.timestamp_check.isChecked():
            timestamp_part = ""
        else:
            timestamp_part = f"[{log_entry['timestamp']}] "
            
        level_part = f"[{log_entry['level']}]"
        source_part = f"[{log_entry['source']}]"
        message_part = log_entry['message']
        
        if self.color_check.isChecked():
            # Couleurs selon le niveau
            color_map = {
                "DEBUG": "#888888",
                "INFO": "#ffffff",
                "WARNING": "#ffff00",
                "ERROR": "#ff0000",
                "CRITICAL": "#ff00ff"
            }
            color = color_map.get(log_entry['level'], "#ffffff")
            
            formatted_log = f'<span style="color: {color}">{timestamp_part}{level_part} {source_part} {message_part}</span>'
        else:
            formatted_log = f"{timestamp_part}{level_part} {source_part} {message_part}"
            
        self.logs_text.append(formatted_log)
        
        # Auto-scroll
        if self.auto_scroll_check.isChecked():
            cursor = self.logs_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.logs_text.setTextCursor(cursor)
            
    def clear_logs(self):
        """Effacer tous les logs"""
        reply = QMessageBox.question(self, 'Confirmation', 
                                   "Êtes-vous sûr de vouloir effacer tous les logs ?",
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.logs.clear()
            self.logs_text.clear()
            self.status_label.setText("Logs: 0")
            
    def save_logs(self):
        """Sauvegarder les logs"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Sauvegarder les logs", "", "Fichiers texte (*.txt);;Tous les fichiers (*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    for log in self.logs:
                        f.write(f"{log['timestamp']} [{log['level']}] [{log['source']}] {log['message']}\n")
                        
                QMessageBox.information(self, "Succès", f"Logs sauvegardés dans {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde: {e}")
                
    def export_logs(self):
        """Exporter les logs au format JSON"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Exporter les logs", "", "Fichiers JSON (*.json);;Tous les fichiers (*)"
        )
        
        if filename:
            try:
                import json
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.logs, f, indent=2, ensure_ascii=False)
                    
                QMessageBox.information(self, "Succès", f"Logs exportés dans {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export: {e}")
                
    def copy_logs(self):
        """Copier les logs dans le presse-papiers"""
        try:
            from PyQt5.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            
            # Formater les logs pour la copie
            log_text = ""
            for log in self.logs:
                log_text += f"{log['timestamp']} [{log['level']}] [{log['source']}] {log['message']}\n"
                
            clipboard.setText(log_text)
            QMessageBox.information(self, "Succès", "Logs copiés dans le presse-papiers")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la copie: {e}")
            
    def find_in_logs(self):
        """Rechercher dans les logs"""
        from PyQt5.QtWidgets import QInputDialog
        
        search_text, ok = QInputDialog.getText(self, "Rechercher", "Texte à rechercher:")
        if ok and search_text:
            # Recherche simple dans le texte
            cursor = self.logs_text.textCursor()
            cursor.movePosition(QTextCursor.Start)
            
            # Rechercher le texte
            if self.logs_text.find(search_text):
                QMessageBox.information(self, "Recherche", f"Texte trouvé: {search_text}")
            else:
                QMessageBox.information(self, "Recherche", "Texte non trouvé")
                
    def update_log_level(self):
        """Mettre à jour le niveau de log"""
        self.current_level = self.level_combo.currentText()
        
        # Recharger les logs avec le nouveau niveau
        self.logs_text.clear()
        for log in self.logs:
            if self.log_levels.get(log['level'], 0) >= self.log_levels.get(self.current_level, 0):
                self.display_log(log)
                
    def update_max_logs(self):
        """Mettre à jour la limite de logs"""
        self.max_logs = self.max_logs_spin.value()
        
        # Supprimer les logs en trop
        while len(self.logs) > self.max_logs:
            self.logs.pop(0)
            
        self.status_label.setText(f"Logs: {len(self.logs)}")
        
    def log_debug(self, message, source="System"):
        """Log de niveau DEBUG"""
        self.add_log("DEBUG", message, source)
        
    def log_info(self, message, source="System"):
        """Log de niveau INFO"""
        self.add_log("INFO", message, source)
        
    def log_warning(self, message, source="System"):
        """Log de niveau WARNING"""
        self.add_log("WARNING", message, source)
        
    def log_error(self, message, source="System"):
        """Log de niveau ERROR"""
        self.add_log("ERROR", message, source)
        
    def log_critical(self, message, source="System"):
        """Log de niveau CRITICAL"""
        self.add_log("CRITICAL", message, source)
