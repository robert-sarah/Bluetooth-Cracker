#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Widget de scan Bluetooth PyQt5 – Version robuste & 100% fonctionnelle (BlueZ)
- Dépendances système : hciconfig, hcitool, bluetoothctl, sdptool (BlueZ)
- Peut nécessiter sudo/capabilities pour hcitool/sdptool
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QProgressBar,
    QGroupBox, QSpinBox, QCheckBox, QFileDialog,
    QMessageBox, QHeaderView
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QColor, QGuiApplication, QCursor

import subprocess
import time
import json
import shutil
import signal
import os
from typing import Dict, Any, List, Optional

# =========================
# Utilitaires système
# =========================

REQUIRED_CMDS = ["hciconfig", "hcitool", "bluetoothctl", "sdptool"]

def cmd_exists(cmd: str) -> bool:
    return shutil.which(cmd) is not None

def ensure_commands_or_message(parent_widget: QWidget) -> bool:
    missing = [c for c in REQUIRED_CMDS if not cmd_exists(c)]
    if missing:
        QMessageBox.critical(
            parent_widget,
            "Outils manquants",
            "Les outils suivants sont introuvables :\n- "
            + "\n- ".join(missing)
            + "\n\nInstalle BlueZ (ex: sudo apt install bluez) puis réessaie."
        )
        return False
    return True

def run_checked(cmd: List[str], timeout: int = 10) -> subprocess.CompletedProcess:
    """
    Lance une commande en capturant stdout/stderr.
    N'élève pas d'exception si returncode != 0 (on gère en amont).
    """
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        cp = subprocess.CompletedProcess(cmd, returncode=124, stdout="", stderr=f"Timeout: {e}")
        return cp
    except Exception as e:
        cp = subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr=str(e))
        return cp

def require_hci_up() -> Optional[str]:
    """
    Tente d'activer hci0. Retourne None si OK, sinon un message d'erreur utilisateur.
    """
    # Vérifier l'interface
    cp = run_checked(["hciconfig"], timeout=5)
    if cp.returncode != 0:
        return "Impossible d'interroger l'interface Bluetooth (hciconfig)."

    # Activer hci0
    cp = run_checked(["hciconfig", "hci0", "up"], timeout=5)
    if cp.returncode != 0:
        # Permissions ? (sudo/cap)
        return (
            "Impossible d'activer l'interface hci0.\n"
            "• Essaie avec sudo (ou donne des capabilities à hcitool/sdptool)\n"
            "• Exemple: sudo setcap cap_net_raw+epi $(which hcitool)"
        )
    return None


# =========================
# Thread de Scan
# =========================

class BluetoothScanThread(QThread):
    device_found = pyqtSignal(dict)     # émis pour chaque découverte/maj
    scan_complete = pyqtSignal(list)    # émis à la fin avec la liste unique
    scan_error = pyqtSignal(str)

    def __init__(self, duration: int = 30, parent=None):
        super().__init__(parent)
        self.duration = max(5, int(duration))
        self.running = False
        self._devices_by_addr: Dict[str, Dict[str, Any]] = {}

    def stop(self):
        self.running = False

    # ---------- Parsers / helpers ----------

    def parse_hcitool_scan_output(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse la sortie de 'hcitool scan --flush'
        Format typique:
            Scanning ...
                AA:BB:CC:DD:EE:FF    Device Name
        """
        devices = []
        if not text:
            return devices

        for line in text.splitlines():
            line = line.strip()
            if not line or line.lower().startswith("scanning"):
                continue
            # ligne typique: "AA:BB:CC:DD:EE:FF   Nom"
            parts = line.split()
            if len(parts) >= 1 and ":" in parts[0]:
                address = parts[0]
                name = line[len(address):].strip()
                if name.startswith("(") and name.endswith(")"):  # edge cases
                    name = name[1:-1].strip()
                if not name:
                    name = "Unknown"
                devices.append({"address": address, "name": name})
        return devices

    def enrich_with_bluetoothctl(self, address: str, info: Dict[str, Any]) -> None:
        """
        Complète info depuis 'bluetoothctl info <ADDR>'
        Cherche: RSSI, Paired, Connected, Icon/Type (si dispo)
        """
        cp = run_checked(["bluetoothctl", "info", address], timeout=6)
        if cp.returncode != 0 or not cp.stdout:
            # Valeurs par défaut si indisponible
            info.setdefault("rssi", None)
            info.setdefault("paired", False)
            info.setdefault("connected", False)
            return

        rssi = None
        paired = False
        connected = False
        dev_type = info.get("type", "unknown")

        for ln in cp.stdout.splitlines():
            line = ln.strip()
            if line.startswith("RSSI:"):
                try:
                    rssi = int(line.split(":", 1)[1].strip())
                except Exception:
                    rssi = None
            elif line.startswith("Paired:"):
                paired = ("yes" in line.lower())
            elif line.startswith("Connected:"):
                connected = ("yes" in line.lower())
            elif line.startswith("Icon:") and dev_type == "unknown":
                # exemple: Icon: phone / audio-card / computer …
                icon = line.split(":", 1)[1].strip().lower()
                # map rapide
                if any(k in icon for k in ["phone", "smartphone", "cellphone"]):
                    dev_type = "phone"
                elif "computer" in icon or "pc" in icon:
                    dev_type = "computer"
                elif any(k in icon for k in ["audio", "headset", "earbud", "headphones"]):
                    dev_type = "headset"
                elif "speaker" in icon:
                    dev_type = "speaker"

        info["rssi"] = rssi
        info["paired"] = paired
        info["connected"] = connected
        info["type"] = dev_type

    def discover_services(self, address: str, max_services: int = 30) -> List[str]:
        """
        Découvre des services via 'sdptool browse <ADDR>'.
        Limite à max_services pour éviter de remplir la table sans fin.
        """
        cp = run_checked(["sdptool", "browse", address], timeout=12)
        services: List[str] = []
        if cp.returncode != 0 or not cp.stdout:
            return services

        for ln in cp.stdout.splitlines():
            line = ln.strip()
            if "Service Name:" in line or "service name:" in line.lower():
                svc = line.split(":", 1)[1].strip()
                if svc:
                    services.append(svc)
                    if len(services) >= max_services:
                        break
        return services

    def detect_device_type_by_name(self, name: str) -> str:
        name_lower = (name or "").lower()
        if any(w in name_lower for w in ["phone", "mobile", "samsung", "iphone", "huawei", "xiaomi", "oneplus", "tecno", "infinix", "itel"]):
            return "phone"
        if any(w in name_lower for w in ["laptop", "pc", "computer", "macbook", "thinkpad", "dell", "hp", "asus", "acer"]):
            return "computer"
        if any(w in name_lower for w in ["headset", "earbuds", "airpods", "buds", "jbl", "sony", "anker", "beats"]):
            return "headset"
        if any(w in name_lower for w in ["speaker", "sound", "audio", "bose", "harman", "marshall"]):
            return "speaker"
        return "unknown"

    # ---------- Run ----------

    def run(self):
        self.running = True
        self._devices_by_addr.clear()

        # 1) Activer l'interface
        err = require_hci_up()
        if err:
            self.scan_error.emit(err)
            self.running = False
            return

        start = time.time()
        # 2) Boucles courtes jusqu’à durée totale
        #    hcitool scan retourne tout de suite la liste actuelle; on itère
        while self.running and (time.time() - start) < self.duration:
            cp = run_checked(["hcitool", "scan", "--flush"], timeout=8)
            if cp.returncode not in (0,):  # 0 = OK (parfois 1 à vide)
                # message non bloquant – on continue pour voir si prochaine boucle marche
                pass

            # 3) Parse résultat de cette passe
            discovered = self.parse_hcitool_scan_output(cp.stdout or "")
            for d in discovered:
                addr = d["address"]
                # Construire/mettre à jour l’info
                info = self._devices_by_addr.get(addr, {})
                info["address"] = addr
                info["name"] = d.get("name") or info.get("name") or "Unknown"

                # Type par nom si inconnu
                info.setdefault("type", self.detect_device_type_by_name(info["name"]))

                # Enrichir avec bluetoothctl si pas déjà fait récemment
                if "paired" not in info or "connected" not in info or "rssi" not in info:
                    self.enrich_with_bluetoothctl(addr, info)

                # Services si pas déjà récupéré
                if "services" not in info:
                    info["services"] = self.discover_services(addr)

                # Défauts propres si rien trouvé
                info.setdefault("paired", False)
                info.setdefault("connected", False)
                info.setdefault("rssi", None)
                info.setdefault("services", [])

                # Déterminer type si toujours inconnu
                if info.get("type", "unknown") == "unknown":
                    info["type"] = self.detect_device_type_by_name(info.get("name", ""))

                self._devices_by_addr[addr] = info
                # Emettre pour MAJ de table en temps réel
                self.device_found.emit(info)

            # petite pause pour ne pas saturer le bus
            for _ in range(10):
                if not self.running:
                    break
                time.sleep(0.1)

        self.running = False
        # 4) Fin
        self.scan_complete.emit(list(self._devices_by_addr.values()))


# =========================
# Widget principal
# =========================

class BluetoothScannerWidget(QWidget):
    device_selected = pyqtSignal(str)  # adresse

    def __init__(self, bluetooth_manager=None):  # bluetooth_manager optionnel
        super().__init__()
        self.bluetooth_manager = bluetooth_manager
        self.scan_thread: Optional[BluetoothScanThread] = None
        self._rows_by_addr: Dict[str, int] = {}  # map addr -> row
        self._devices_cache: Dict[str, Dict[str, Any]] = {}

        self.init_ui()
        self.setup_connections()

    # ---------- UI ----------

    def init_ui(self):
        self.setWindowTitle("Bluetooth Scanner – BlueZ")
        layout = QVBoxLayout(self)

        # Groupe contrôles
        control_group = QGroupBox("Contrôles de Scan")
        control_layout = QHBoxLayout(control_group)

        self.scan_button = QPushButton("🔍 Démarrer Scan")
        self.scan_button.setMinimumHeight(36)
        self.stop_button = QPushButton("⏹️ Arrêter")
        self.stop_button.setMinimumHeight(36)
        self.stop_button.setEnabled(False)

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(5, 600)
        self.duration_spin.setValue(30)
        self.duration_spin.setSuffix(" sec")

        self.continuous_check = QCheckBox("Scan continu")

        control_layout.addWidget(self.scan_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addSpacing(12)
        control_layout.addWidget(QLabel("Durée :"))
        control_layout.addWidget(self.duration_spin)
        control_layout.addSpacing(12)
        control_layout.addWidget(self.continuous_check)
        control_layout.addStretch()
        layout.addWidget(control_group)

        # Progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Table devices
        devices_group = QGroupBox("Appareils Découverts")
        devices_layout = QVBoxLayout(devices_group)

        self.devices_table = QTableWidget()
        self.devices_table.setColumnCount(7)
        self.devices_table.setHorizontalHeaderLabels(
            ["Adresse", "Nom", "Type", "RSSI", "Services", "Appairé", "Connecté"]
        )
        header = self.devices_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)

        self.devices_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.devices_table.setAlternatingRowColors(True)
        self.devices_table.setEditTriggers(QTableWidget.NoEditTriggers)

        devices_layout.addWidget(self.devices_table)

        # Actions
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

        # Status
        self.status_label = QLabel("Prêt pour le scan")
        self.status_label.setStyleSheet("color: #00aa00; font-weight: bold;")
        layout.addWidget(self.status_label)

        # Timer progression
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_progress)

        # Astuce UX : double-clic pour sélectionner
        self.devices_table.doubleClicked.connect(self._on_double_click_row)

    def setup_connections(self):
        self.scan_button.clicked.connect(self.start_scan)
        self.stop_button.clicked.connect(self.stop_scan)
        self.refresh_button.clicked.connect(self.refresh_devices)
        self.clear_button.clicked.connect(self.clear_devices)
        self.export_button.clicked.connect(self.export_devices)

    # ---------- Scan control ----------

    def start_scan(self):
        if not ensure_commands_or_message(self):
            return

        # Reset de la table si on ne veut pas cumuler
        # (on garde pour refresh ; ici on conserve l’existant)
        duration = self.duration_spin.value()

        self._set_busy(True)
        self.status_label.setText("Scan en cours…")
        self.status_label.setStyleSheet("color: #d8a500; font-weight: bold;")

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, duration)
        self.progress_bar.setValue(0)

        self.scan_thread = BluetoothScanThread(duration)
        self.scan_thread.device_found.connect(self.on_device_found)
        self.scan_thread.scan_complete.connect(self.on_scan_complete)
        self.scan_thread.scan_error.connect(self.on_scan_error)
        self.scan_thread.start()

        self.update_timer.start(1000)

    def stop_scan(self):
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.stop()
            self.scan_thread.wait(3000)

        self.update_timer.stop()
        self._set_busy(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Scan arrêté")
        self.status_label.setStyleSheet("color: #cc0000; font-weight: bold;")

    def update_progress(self):
        if self.scan_thread and self.scan_thread.running:
            cur = self.progress_bar.value()
            if cur < self.progress_bar.maximum():
                self.progress_bar.setValue(cur + 1)

    # ---------- Slots thread ----------

    def on_device_found(self, device: Dict[str, Any]):
        self._devices_cache[device["address"]] = device
        self._add_or_update_row(device)

    def on_scan_complete(self, devices: List[Dict[str, Any]]):
        self.update_timer.stop()
        self._set_busy(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Scan terminé – {len(devices)} appareil(s) trouvé(s)")
        self.status_label.setStyleSheet("color: #00aa00; font-weight: bold;")

        # Scan continu ?
        if self.continuous_check.isChecked():
            # petite pause UX pour respirer
            QTimer.singleShot(800, self.start_scan)

    def on_scan_error(self, error_message: str):
        self.update_timer.stop()
        self._set_busy(False)
        self.progress_bar.setVisible(False)

        self.status_label.setText(f"Erreur: {error_message}")
        self.status_label.setStyleSheet("color: #cc0000; font-weight: bold;")
        QMessageBox.warning(self, "Erreur de Scan", error_message)

    # ---------- Table helpers ----------

    def _add_or_update_row(self, d: Dict[str, Any]):
        addr = d.get("address", "")
        if not addr:
            return

        row = self._rows_by_addr.get(addr, -1)
        if row == -1:
            # nouvelle ligne
            row = self.devices_table.rowCount()
            self.devices_table.insertRow(row)
            self._rows_by_addr[addr] = row

            addr_item = QTableWidgetItem(addr)
            addr_item.setData(Qt.UserRole, addr)
            self.devices_table.setItem(row, 0, addr_item)
        # Nom
        name_item = QTableWidgetItem(d.get("name", "Unknown"))
        self.devices_table.setItem(row, 1, name_item)

        # Type
        type_item = QTableWidgetItem(d.get("type", "unknown"))
        self.devices_table.setItem(row, 2, type_item)

        # RSSI
        rssi_val = d.get("rssi", None)
        rssi_text = str(rssi_val) if isinstance(rssi_val, int) else "N/A"
        rssi_item = QTableWidgetItem(rssi_text)
        self.devices_table.setItem(row, 3, rssi_item)

        # Services
        services = d.get("services", [])
        services_item = QTableWidgetItem(", ".join(services[:30]))
        self.devices_table.setItem(row, 4, services_item)

        # Appairé
        paired = bool(d.get("paired", False))
        paired_item = QTableWidgetItem("✓" if paired else "✗")
        paired_item.setForeground(QColor("#00aa00" if paired else "#cc0000"))
        self.devices_table.setItem(row, 5, paired_item)

        # Connecté
        connected = bool(d.get("connected", False))
        connected_item = QTableWidgetItem("✓" if connected else "✗")
        connected_item.setForeground(QColor("#00aa00" if connected else "#cc0000"))
        self.devices_table.setItem(row, 6, connected_item)

    # ---------- Actions ----------

    def refresh_devices(self):
        """Efface la table et relance un scan rapide avec la durée actuelle"""
        self.clear_devices()
        self.start_scan()

    def clear_devices(self):
        self.devices_table.setRowCount(0)
        self._rows_by_addr.clear()
        self._devices_cache.clear()

    def export_devices(self):
        fname, _ = QFileDialog.getSaveFileName(
            self, "Exporter les appareils", "", "Fichiers JSON (*.json);;Fichiers texte (*.txt)"
        )
        if not fname:
            return

        try:
            # construire depuis cache pour éviter des trous
            devices_data = []
            # S’assurer de l’ordre d’affichage
            for row in range(self.devices_table.rowCount()):
                addr = self.devices_table.item(row, 0).text()
                name = self.devices_table.item(row, 1).text()
                typ = self.devices_table.item(row, 2).text()
                rssi_txt = self.devices_table.item(row, 3).text()
                try:
                    rssi = int(rssi_txt)
                except Exception:
                    rssi = None
                services_txt = self.devices_table.item(row, 4).text()
                services = [s.strip() for s in services_txt.split(",")] if services_txt else []
                paired = self.devices_table.item(row, 5).text() == "✓"
                connected = self.devices_table.item(row, 6).text() == "✓"

                devices_data.append({
                    "address": addr,
                    "name": name,
                    "type": typ,
                    "rssi": rssi,
                    "services": [s for s in services if s],
                    "paired": paired,
                    "connected": connected
                })

            if fname.endswith(".json"):
                with open(fname, "w", encoding="utf-8") as f:
                    json.dump(devices_data, f, indent=2, ensure_ascii=False)
            else:
                with open(fname, "w", encoding="utf-8") as f:
                    for dev in devices_data:
                        f.write(
                            f"{dev['address']}\t{dev['name']}\t{dev['type']}\t{dev['rssi']}\t"
                            f"{'|'.join(dev['services'])}\t{'Yes' if dev['paired'] else 'No'}\t"
                            f"{'Yes' if dev['connected'] else 'No'}\n"
                        )
            QMessageBox.information(self, "Succès", f"Appareils exportés dans {fname}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export : {e}")

    def get_selected_device(self) -> Optional[str]:
        row = self.devices_table.currentRow()
        if row >= 0:
            item = self.devices_table.item(row, 0)
            if item:
                return item.data(Qt.UserRole)
        return None

    # ---------- UX helpers ----------

    def _set_busy(self, busy: bool):
        self.scan_button.setEnabled(not busy)
        self.stop_button.setEnabled(busy)
        if busy:
            self.setCursor(QCursor(Qt.BusyCursor))
        else:
            self.unsetCursor()

    def _on_double_click_row(self):
        addr = self.get_selected_device()
        if addr:
            self.device_selected.emit(addr)
            # copie dans le presse-papiers pour commodité
            cb = QGuiApplication.clipboard()
            cb.setText(addr)
            QMessageBox.information(self, "Appareil sélectionné",
                                    f"Adresse copiée dans le presse-papiers : {addr}")
