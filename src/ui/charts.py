# src/ui/charts.py
import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from collections import deque
import time


class ChartsWidget(QWidget):
    def __init__(self, max_points=100):
        super().__init__()
        self.max_points = max_points

        # Veri depoları (son N nokta)
        self.time_data = deque(maxlen=max_points)
        self.altitude_data = deque(maxlen=max_points)
        self.velocity_data = deque(maxlen=max_points)
        self.battery_data = deque(maxlen=max_points)

        # Başlangıç zamanı
        self.start_time = time.time()

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        # Başlık
        title = QLabel("Anlık Telemetri Grafikleri")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        # Grafik alanı - 2x2 düzen
        graphs_layout = QVBoxLayout()

        # Üst satır: İrtifa ve Hız
        top_row = QHBoxLayout()

        # İrtifa grafiği
        self.altitude_plot = pg.PlotWidget(title="İrtifa (m)")
        self.altitude_plot.setLabel('left', 'Rakım', 'm')
        self.altitude_plot.setLabel('bottom', 'Zaman', 's')
        self.altitude_plot.showGrid(x=True, y=True)
        self.altitude_curve = self.altitude_plot.plot(pen='b', width=2)
        top_row.addWidget(self.altitude_plot)

        # Hız grafiği
        self.velocity_plot = pg.PlotWidget(title="Hız (m/s)")
        self.velocity_plot.setLabel('left', 'Hız', 'm/s')
        self.velocity_plot.setLabel('bottom', 'Zaman', 's')
        self.velocity_plot.showGrid(x=True, y=True)
        self.velocity_curve = self.velocity_plot.plot(pen='r', width=2)
        top_row.addWidget(self.velocity_plot)

        graphs_layout.addLayout(top_row)

        # Alt satır: Batarya
        bottom_row = QHBoxLayout()

        # Batarya grafiği
        self.battery_plot = pg.PlotWidget(title="Batarya (%)")
        self.battery_plot.setLabel('left', 'Şarj', '%')
        self.battery_plot.setLabel('bottom', 'Zaman', 's')
        self.battery_plot.setYRange(0, 100)  # Batarya 0-100% arası
        self.battery_plot.showGrid(x=True, y=True)
        self.battery_curve = self.battery_plot.plot(pen='g', width=2)
        bottom_row.addWidget(self.battery_plot)

        # İstatistikler paneli
        stats_widget = self._create_stats_panel()
        bottom_row.addWidget(stats_widget)

        graphs_layout.addLayout(bottom_row)
        layout.addLayout(graphs_layout)

        self.setLayout(layout)

    def _create_stats_panel(self):
        """İstatistik bilgilerini gösteren panel"""
        widget = QWidget()
        widget.setMaximumWidth(200)
        layout = QVBoxLayout()

        # Başlık
        title = QLabel("Anlık Değerler")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Değer etiketleri
        self.current_altitude_label = QLabel("İrtifa: -- m")
        self.current_velocity_label = QLabel("Hız: -- m/s")
        self.current_battery_label = QLabel("Batarya: -- %")
        self.flight_time_label = QLabel("Uçuş Süresi: -- s")

        # Stil
        label_style = "padding: 5px; border: 1px solid gray; margin: 2px; background-color: #f0f0f0;"
        for label in [self.current_altitude_label, self.current_velocity_label,
                      self.current_battery_label, self.flight_time_label]:
            label.setStyleSheet(label_style)
            layout.addWidget(label)

        # Min/Max değerler
        layout.addWidget(QLabel(""))  # Boşluk
        self.max_altitude_label = QLabel("Max İrtifa: -- m")
        self.max_velocity_label = QLabel("Max Hız: -- m/s")
        self.min_battery_label = QLabel("Min Batarya: -- %")

        for label in [self.max_altitude_label, self.max_velocity_label, self.min_battery_label]:
            label.setStyleSheet("padding: 3px; font-size: 10px; color: #666;")
            layout.addWidget(label)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def update_data(self, telemetry_packet):
        """Yeni telemetri verisiyle grafikleri güncelle"""
        current_time = time.time() - self.start_time

        # Veri ekle
        self.time_data.append(current_time)
        self.altitude_data.append(telemetry_packet.gps.altitude)
        self.velocity_data.append(telemetry_packet.velocity)
        self.battery_data.append(telemetry_packet.battery_percent)

        # Grafikleri güncelle
        if len(self.time_data) > 1:
            self.altitude_curve.setData(list(self.time_data), list(self.altitude_data))
            self.velocity_curve.setData(list(self.time_data), list(self.velocity_data))
            self.battery_curve.setData(list(self.time_data), list(self.battery_data))

        # İstatistikleri güncelle
        self._update_stats(telemetry_packet, current_time)

    def _update_stats(self, packet, flight_time):
        """İstatistik panelini güncelle"""
        # Anlık değerler
        self.current_altitude_label.setText(f"İrtifa: {packet.gps.altitude:.1f} m")
        self.current_velocity_label.setText(f"Hız: {packet.velocity:.1f} m/s")
        self.current_battery_label.setText(f"Batarya: {packet.battery_percent:.1f} %")
        self.flight_time_label.setText(f"Uçuş Süresi: {flight_time:.0f} s")

        # Min/Max değerler
        if self.altitude_data:
            max_alt = max(self.altitude_data)
            self.max_altitude_label.setText(f"Max İrtifa: {max_alt:.1f} m")

        if self.velocity_data:
            max_vel = max(self.velocity_data)
            self.max_velocity_label.setText(f"Max Hız: {max_vel:.1f} m/s")

        if self.battery_data:
            min_bat = min(self.battery_data)
            self.min_battery_label.setText(f"Min Batarya: {min_bat:.1f} %")

    def clear_data(self):
        """Tüm grafik verilerini temizle"""
        self.time_data.clear()
        self.altitude_data.clear()
        self.velocity_data.clear()
        self.battery_data.clear()
        self.start_time = time.time()

        # Grafikleri temizle
        self.altitude_curve.clear()
        self.velocity_curve.clear()
        self.battery_curve.clear()