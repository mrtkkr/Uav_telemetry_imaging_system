# src/ui/alarm_panel.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QListWidget, QPushButton, QFrame, QListWidgetItem)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPalette, QColor
from datetime import datetime


class AlarmPanel(QWidget):
    """Alarm ve Uyarı Paneli"""

    # Sinyal tanımlamaları
    clearAlarmsRequested = Signal()
    muteAlarmsRequested = Signal()

    def __init__(self):
        super().__init__()
        self.alarms_muted = False
        self.last_alarms = {}  # BUNU EKLEYİN
        self.init_ui()

    def init_ui(self):
        """UI bileşenlerini oluştur"""
        layout = QVBoxLayout()

        # Başlık
        title = QLabel("🚨 Alarm ve Uyarı Sistemi")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Durum göstergesi
        self.status_frame = QFrame()
        self.status_frame.setFrameStyle(QFrame.Shape.Box)
        self.status_frame.setFixedHeight(60)

        status_layout = QHBoxLayout()

        self.status_label = QLabel("✅ Sistem Normal")
        self.status_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        status_layout.addWidget(self.status_label)
        self.status_frame.setLayout(status_layout)
        layout.addWidget(self.status_frame)

        # Aktif alarmlar listesi
        alarm_label = QLabel("📋 Aktif Alarmlar:")
        alarm_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(alarm_label)

        self.alarm_list = QListWidget()
        self.alarm_list.setMaximumHeight(200)
        layout.addWidget(self.alarm_list)

        # Kontrol butonları
        button_layout = QHBoxLayout()

        self.mute_btn = QPushButton("🔇 Sessiz")
        self.clear_btn = QPushButton("🗑️ Temizle")

        button_layout.addWidget(self.mute_btn)
        button_layout.addWidget(self.clear_btn)

        layout.addLayout(button_layout)

        # Alarm istatistikleri
        self.stats_label = QLabel("📊 İstatistik: 0 alarm")
        layout.addWidget(self.stats_label)

        layout.addStretch()
        self.setLayout(layout)

        # Buton sinyallerini bağla
        self.mute_btn.clicked.connect(self.toggle_mute)
        self.clear_btn.clicked.connect(self.clear_alarms)

        # Başlangıç durumu
        self._set_normal_status()

    def add_alarm(self, alert_type: str, severity: str, message: str):
        """Yeni alarm ekle"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Renk belirleme
        if severity == "CRITICAL":
            color = "red"
            icon = "🔴"
        elif severity == "WARNING":
            color = "orange"
            icon = "🟡"
        else:
            color = "blue"
            icon = "🔵"

        # Liste öğesi oluştur
        item_text = f"{icon} {timestamp} - {message}"
        item = QListWidgetItem(item_text)

        # Renk ayarla
        if severity == "CRITICAL":
            item.setBackground(QColor(255, 200, 200))  # Açık kırmızı
        elif severity == "WARNING":
            item.setBackground(QColor(255, 235, 200))  # Açık turuncu

        # Listeye ekle (en üstte görünmesi için)
        self.alarm_list.insertItem(0, item)

        # Durum güncelle
        self._update_status(severity)
        self._update_stats()

        print(f"🚨 ALARM: {message}")

    def clear_alarms(self):
        """Tüm alarmları temizle"""
        self.alarm_list.clear()
        self._set_normal_status()
        self._update_stats()
        self.clearAlarmsRequested.emit()
        print("✅ Alarmlar temizlendi")

    def toggle_mute(self):
        """Alarm sesini aç/kapat"""
        self.alarms_muted = not self.alarms_muted

        if self.alarms_muted:
            self.mute_btn.setText("🔊 Sesli")
            self.mute_btn.setStyleSheet("background-color: #ffcccc;")
        else:
            self.mute_btn.setText("🔇 Sessiz")
            self.mute_btn.setStyleSheet("")

        self.muteAlarmsRequested.emit()
        print(f"🔇 Alarmlar {'sessize alındı' if self.alarms_muted else 'sesli yapıldı'}")

    def _set_normal_status(self):
        """Normal durum ayarla"""
        self.status_label.setText("✅ Sistem Normal")
        self.status_frame.setStyleSheet("background-color: #ccffcc; border: 2px solid green;")

    def _update_status(self, severity: str):
        """Durum göstergesini güncelle"""
        if severity == "CRITICAL":
            self.status_label.setText("🔴 KRİTİK ALARM!")
            self.status_frame.setStyleSheet("background-color: #ffcccc; border: 2px solid red;")
        elif severity == "WARNING":
            self.status_label.setText("🟡 UYARI!")
            self.status_frame.setStyleSheet("background-color: #fff3cd; border: 2px solid orange;")

    def _update_stats(self):
        """İstatistikleri güncelle"""
        count = self.alarm_list.count()
        self.stats_label.setText(f"📊 İstatistik: {count} alarm")

    def check_telemetry_alarms(self, packet):
        """Telemetri verilerini kontrol et ve alarm üret"""
        # Batarya kontrolü
        if packet.battery_percent <= 15:
            self.add_alarm("BATTERY_CRITICAL", "CRITICAL",
                           f"KRİTİK BATARYA! {packet.battery_percent:.1f}% - Acil iniş gerekli!")
        elif packet.battery_percent <= 30:
            self.add_alarm("BATTERY_LOW", "WARNING",
                           f"Düşük batarya: {packet.battery_percent:.1f}%")

        # GPS kontrolü
        if packet.gps.satellites < 6:
            self.add_alarm("GPS_POOR", "WARNING",
                           f"Zayıf GPS: {packet.gps.satellites} uydu")

        if packet.gps.fix_quality < 3:
            self.add_alarm("GPS_LOST", "CRITICAL",
                           f"GPS kilidi kayboldu! Kalite: {packet.gps.fix_quality}")

        # Rakım kontrolü
        if packet.gps.altitude > 400:
            self.add_alarm("ALTITUDE_HIGH", "WARNING",
                           f"Yüksek rakım: {packet.gps.altitude:.1f}m")
        elif packet.gps.altitude < 5:
            self.add_alarm("ALTITUDE_LOW", "WARNING",
                           f"Düşük rakım: {packet.gps.altitude:.1f}m - Çarpma riski!")

        # Hız kontrolü
        if packet.velocity > 30:
            self.add_alarm("VELOCITY_HIGH", "WARNING",
                           f"Yüksek hız: {packet.velocity:.1f} m/s")