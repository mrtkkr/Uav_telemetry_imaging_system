# src/ui/waypoint_panel.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QListWidget, QPushButton, QLineEdit, QSpinBox,
                               QComboBox, QDoubleSpinBox, QGroupBox, QFormLayout,
                               QListWidgetItem, QMessageBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from datetime import datetime


class WaypointPanel(QWidget):
    """Waypoint/Görev Noktası Yönetim Paneli"""

    # Sinyal tanımlamaları
    waypointAdded = Signal(float, float, float)  # lat, lon, alt
    missionStarted = Signal(list)  # waypoint listesi
    missionCleared = Signal()

    def __init__(self):
        super().__init__()
        self.waypoints = []
        self.mission_name = ""
        self.init_ui()

    def init_ui(self):
        """UI bileşenlerini oluştur"""
        layout = QVBoxLayout()

        # Başlık
        title = QLabel("🗺️ Görev Planlama Sistemi")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Görev bilgileri
        self._create_mission_info_group(layout)

        # Waypoint ekleme formu
        self._create_waypoint_form_group(layout)

        # Waypoint listesi
        self._create_waypoint_list_group(layout)

        # Kontrol butonları
        self._create_control_buttons(layout)

        # İstatistikler
        self.stats_label = QLabel("📊 Görev: 0 waypoint, 0.0 km, ~0 dk")
        layout.addWidget(self.stats_label)

        layout.addStretch()
        self.setLayout(layout)

        # Başlangıç durumu
        self._update_stats()

    def _create_mission_info_group(self, parent_layout):
        """Görev bilgileri grubu"""
        group = QGroupBox("📝 Görev Bilgileri")
        layout = QFormLayout()

        self.mission_name_edit = QLineEdit()
        self.mission_name_edit.setPlaceholderText("Görev adı girin...")
        layout.addRow("Görev Adı:", self.mission_name_edit)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def _create_waypoint_form_group(self, parent_layout):
        """Waypoint ekleme formu"""
        group = QGroupBox("➕ Yeni Waypoint Ekle")
        layout = QFormLayout()

        # Koordinatlar
        self.lat_spin = QDoubleSpinBox()
        self.lat_spin.setRange(-90, 90)
        self.lat_spin.setDecimals(6)
        self.lat_spin.setValue(39.9334)  # Ankara
        layout.addRow("Enlem (Lat):", self.lat_spin)

        self.lon_spin = QDoubleSpinBox()
        self.lon_spin.setRange(-180, 180)
        self.lon_spin.setDecimals(6)
        self.lon_spin.setValue(32.8597)  # Ankara
        layout.addRow("Boylam (Lon):", self.lon_spin)

        self.alt_spin = QDoubleSpinBox()
        self.alt_spin.setRange(0, 1000)
        self.alt_spin.setValue(100)
        self.alt_spin.setSuffix(" m")
        layout.addRow("Rakım:", self.alt_spin)

        # Eylem tipi
        self.action_combo = QComboBox()
        self.action_combo.addItems(["FLY_TO", "HOVER", "LAND", "TAKEOFF", "PHOTO"])
        layout.addRow("Eylem:", self.action_combo)

        # Bekleme süresi
        self.hold_time_spin = QSpinBox()
        self.hold_time_spin.setRange(0, 300)
        self.hold_time_spin.setSuffix(" sn")
        layout.addRow("Bekleme:", self.hold_time_spin)

        # Ekleme butonu
        self.add_waypoint_btn = QPushButton("➕ Waypoint Ekle")
        self.add_waypoint_btn.clicked.connect(self.add_waypoint)
        layout.addRow(self.add_waypoint_btn)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def _create_waypoint_list_group(self, parent_layout):
        """Waypoint listesi"""
        group = QGroupBox("📋 Waypoint Listesi")
        layout = QVBoxLayout()

        self.waypoint_list = QListWidget()
        self.waypoint_list.setMaximumHeight(200)
        layout.addWidget(self.waypoint_list)

        # Liste butonları
        list_buttons = QHBoxLayout()

        self.move_up_btn = QPushButton("⬆️ Yukarı")
        self.move_down_btn = QPushButton("⬇️ Aşağı")
        self.remove_btn = QPushButton("❌ Kaldır")

        list_buttons.addWidget(self.move_up_btn)
        list_buttons.addWidget(self.move_down_btn)
        list_buttons.addWidget(self.remove_btn)

        layout.addLayout(list_buttons)
        group.setLayout(layout)
        parent_layout.addWidget(group)

        # Liste buton sinyalleri
        self.move_up_btn.clicked.connect(self.move_waypoint_up)
        self.move_down_btn.clicked.connect(self.move_waypoint_down)
        self.remove_btn.clicked.connect(self.remove_waypoint)

    def _create_control_buttons(self, parent_layout):
        """Ana kontrol butonları"""
        button_layout = QHBoxLayout()

        self.start_mission_btn = QPushButton("🚀 Görevi Başlat")
        self.clear_mission_btn = QPushButton("🗑️ Görevi Temizle")
        self.save_mission_btn = QPushButton("💾 Görevi Kaydet")

        button_layout.addWidget(self.start_mission_btn)
        button_layout.addWidget(self.clear_mission_btn)
        button_layout.addWidget(self.save_mission_btn)

        parent_layout.addLayout(button_layout)

        # Buton sinyalleri
        self.start_mission_btn.clicked.connect(self.start_mission)
        self.clear_mission_btn.clicked.connect(self.clear_mission)
        self.save_mission_btn.clicked.connect(self.save_mission)

    def add_waypoint(self):
        """Yeni waypoint ekle"""
        lat = self.lat_spin.value()
        lon = self.lon_spin.value()
        alt = self.alt_spin.value()
        action = self.action_combo.currentText()
        hold_time = self.hold_time_spin.value()

        waypoint = {
            'order': len(self.waypoints),
            'latitude': lat,
            'longitude': lon,
            'altitude': alt,
            'action': action,
            'hold_time': hold_time,
            'timestamp': datetime.now()
        }

        self.waypoints.append(waypoint)
        self._update_waypoint_list()
        self._update_stats()

        # Sinyal gönder
        self.waypointAdded.emit(lat, lon, alt)

        print(f"✅ Waypoint eklendi: {lat:.5f}, {lon:.5f}, {alt}m")

    def remove_waypoint(self):
        """Seçili waypoint'i kaldır"""
        current_row = self.waypoint_list.currentRow()
        if current_row >= 0:
            removed = self.waypoints.pop(current_row)
            self._reorder_waypoints()
            self._update_waypoint_list()
            self._update_stats()
            print(f"❌ Waypoint kaldırıldı: {removed['latitude']:.5f}, {removed['longitude']:.5f}")

    def move_waypoint_up(self):
        """Waypoint'i yukarı taşı"""
        current_row = self.waypoint_list.currentRow()
        if current_row > 0:
            self.waypoints[current_row], self.waypoints[current_row - 1] = \
                self.waypoints[current_row - 1], self.waypoints[current_row]
            self._reorder_waypoints()
            self._update_waypoint_list()
            self.waypoint_list.setCurrentRow(current_row - 1)

    def move_waypoint_down(self):
        """Waypoint'i aşağı taşı"""
        current_row = self.waypoint_list.currentRow()
        if current_row < len(self.waypoints) - 1:
            self.waypoints[current_row], self.waypoints[current_row + 1] = \
                self.waypoints[current_row + 1], self.waypoints[current_row]
            self._reorder_waypoints()
            self._update_waypoint_list()
            self.waypoint_list.setCurrentRow(current_row + 1)

    def start_mission(self):
        """Görevi başlat"""
        if not self.waypoints:
            QMessageBox.warning(self, "Uyarı", "En az 1 waypoint eklemelisiniz!")
            return

        mission_name = self.mission_name_edit.text() or f"Mission_{datetime.now().strftime('%H%M%S')}"

        reply = QMessageBox.question(
            self, 'Görev Başlat',
            f'"{mission_name}" görevini başlatmak istiyor musunuz?\n'
            f'{len(self.waypoints)} waypoint var.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.missionStarted.emit(self.waypoints.copy())
            print(f"🚀 Görev başlatıldı: {mission_name}")

    def clear_mission(self):
        """Tüm waypoint'leri temizle"""
        reply = QMessageBox.question(
            self, 'Görev Temizle',
            'Tüm waypoint\'leri temizlemek istiyor musunuz?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.waypoints.clear()
            self._update_waypoint_list()
            self._update_stats()
            self.missionCleared.emit()
            print("🗑️ Görev temizlendi")

    def save_mission(self):
        """Görevi kaydet (basit text formatı)"""
        if not self.waypoints:
            QMessageBox.warning(self, "Uyarı", "Kaydedilecek waypoint yok!")
            return

        mission_name = self.mission_name_edit.text() or f"mission_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        filename = f"{mission_name}.txt"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# Görev: {mission_name}\n")
                f.write(f"# Oluşturulma: {datetime.now()}\n")
                f.write(f"# Waypoint sayısı: {len(self.waypoints)}\n\n")

                for i, wp in enumerate(self.waypoints):
                    f.write(f"WP{i}: {wp['latitude']:.6f}, {wp['longitude']:.6f}, "
                            f"{wp['altitude']}m, {wp['action']}, {wp['hold_time']}s\n")

            QMessageBox.information(self, "Başarılı", f"Görev kaydedildi: {filename}")
            print(f"💾 Görev kaydedildi: {filename}")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {e}")

    def _update_waypoint_list(self):
        """Waypoint listesini güncelle"""
        self.waypoint_list.clear()

        for i, wp in enumerate(self.waypoints):
            text = (f"WP{i}: {wp['latitude']:.5f}, {wp['longitude']:.5f}, "
                    f"{wp['altitude']}m - {wp['action']}")

            if wp['hold_time'] > 0:
                text += f" ({wp['hold_time']}s)"

            item = QListWidgetItem(text)

            # Renk kodlama
            if wp['action'] == 'TAKEOFF':
                item.setBackground(QColor(200, 255, 200))  # Açık yeşil
            elif wp['action'] == 'LAND':
                item.setBackground(QColor(255, 200, 200))  # Açık kırmızı
            elif wp['action'] == 'HOVER':
                item.setBackground(QColor(255, 255, 200))  # Açık sarı

            self.waypoint_list.addItem(item)

    def _reorder_waypoints(self):
        """Waypoint sıralarını güncelle"""
        for i, wp in enumerate(self.waypoints):
            wp['order'] = i

    def _update_stats(self):
        """İstatistikleri güncelle"""
        count = len(self.waypoints)

        # Toplam mesafe hesapla
        total_distance = 0
        if count > 1:
            for i in range(1, count):
                prev_wp = self.waypoints[i - 1]
                curr_wp = self.waypoints[i]
                distance = self._calculate_distance(
                    prev_wp['latitude'], prev_wp['longitude'],
                    curr_wp['latitude'], curr_wp['longitude']
                )
                total_distance += distance

        # Tahmini süre (15 m/s ortalama hızla)
        flight_time = (total_distance / 15 / 60) if total_distance > 0 else 0  # dakika
        hold_time = sum(wp['hold_time'] for wp in self.waypoints) / 60  # dakika
        total_time = flight_time + hold_time + 2  # +2 dk iniş-kalkış

        self.stats_label.setText(
            f"📊 Görev: {count} waypoint, {total_distance / 1000:.1f} km, ~{total_time:.0f} dk"
        )

    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """İki nokta arası mesafe (Haversine formülü - metre)"""
        import math

        R = 6371000  # Dünya yarıçapı (metre)
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (math.sin(delta_phi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c