# src/ui/status_panel.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QGroupBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class StatusPanel(QWidget):
    # ---- Yeni Sinyaller ----
    clearGraphsRequested = Signal()
    clearPathRequested = Signal()
    emergencyStopRequested = Signal()

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self._connect_signals()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Başlık
        title = QLabel("İHA Durum Paneli")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # ---------------- Sistem Durumu ----------------
        system_group = QGroupBox("Sistem Durumu")
        system_layout = QVBoxLayout()

        self.connection_status = QLabel("🔴 Bağlantı: Kesildi")
        self.flight_mode = QLabel("✈️ Uçuş Modu: Bekleme")
        self.gps_status = QLabel("🛰️ GPS: Aranıyor...")

        for w in (self.connection_status, self.flight_mode, self.gps_status):
            system_layout.addWidget(w)

        system_group.setLayout(system_layout)
        layout.addWidget(system_group)

        # ---------------- Batarya Durumu ----------------
        battery_group = QGroupBox("Güç Sistemi")
        battery_layout = QVBoxLayout()

        self.battery_bar = QProgressBar()
        self.battery_bar.setRange(0, 100)
        self.battery_voltage_label = QLabel("Voltaj: -- V")

        battery_layout.addWidget(QLabel("Batarya Seviyesi:"))
        battery_layout.addWidget(self.battery_bar)
        battery_layout.addWidget(self.battery_voltage_label)
        battery_group.setLayout(battery_layout)
        layout.addWidget(battery_group)

        # ---------------- Kontrol Butonları ----------------
        control_group = QGroupBox("Kontroller")
        control_layout = QVBoxLayout()

        self.clear_path_btn = QPushButton("🗺️ Harita Yolunu Temizle")
        self.clear_graphs_btn = QPushButton("📊 Grafikleri Temizle")
        self.emergency_btn = QPushButton("🚨 ACİL DURDUR")
        self.emergency_btn.setStyleSheet(
            "background-color: red; color: white; font-weight: bold;"
        )

        control_layout.addWidget(self.clear_path_btn)
        control_layout.addWidget(self.clear_graphs_btn)
        control_layout.addWidget(self.emergency_btn)
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        layout.addStretch()
        self.setLayout(layout)

    def _connect_signals(self):
        """Butonları kendi sinyallerine bağla"""
        self.clear_graphs_btn.clicked.connect(self.clearGraphsRequested.emit)
        self.clear_path_btn.clicked.connect(self.clearPathRequested.emit)
        self.emergency_btn.clicked.connect(self.emergencyStopRequested.emit)

    # ----------------------------------------------------
    # Telemetri Güncelleme
    # ----------------------------------------------------
    def update_status(self, packet):
        """Telemetri paketiyle paneli güncelle."""
        # Bağlantı durumu
        self.connection_status.setText("🟢 Bağlantı: Aktif")

        # GPS durumu
        if packet.gps.latitude != 0 and packet.gps.longitude != 0:
            self.gps_status.setText("🟢 GPS: Kilitli")
        else:
            self.gps_status.setText("🟡 GPS: Aranıyor...")

        # Uçuş modu
        self.flight_mode.setText(f"✈️ Uçuş Modu: {packet.status}")

        # Batarya seviyesi
        self.battery_bar.setValue(int(packet.battery_percent))
        self.battery_voltage_label.setText(f"Voltaj: {packet.battery_voltage:.1f} V")

        # Batarya rengi
        if packet.battery_percent > 50:
            color = "green"
        elif packet.battery_percent > 20:
            color = "orange"
        else:
            color = "red"

        self.battery_bar.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {color};
            }}
        """)