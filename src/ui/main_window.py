# src/ui/main_window.py - DATABASE ENTEGRASYONU
import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QLabel, QTabWidget, QMessageBox, QPushButton, QHBoxLayout)
from PySide6.QtCore import Qt

# Import'lar
from src.telemetry.data_generator import TelemetryWorker
from src.telemetry.data_models import TelemetryPacket
from src.ui.map_widget import MapWidget
from src.ui.charts import ChartsWidget
from src.ui.status_panel import StatusPanel
from src.ui.alarm_panel import AlarmPanel
from src.database.database_manager import DatabaseManager # YENİ!


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("İHA Telemetri Görüntüleyici - Database v3.0")
        self.setMinimumSize(1200, 800)

        # DATABASE MANAGER BAŞLAT
        try:
            self.db_manager = DatabaseManager("iha_telemetry.db")
            print("Veritabanı bağlantısı başarılı!")
        except Exception as e:
            print(f"Veritabanı hatası: {e}")
            QMessageBox.critical(self, "Veritabanı Hatası",
                                 f"Veritabanı başlatılamadı:\n{e}")
            self.db_manager = None

        # Widget'ları oluştur
        self.telemetry_label = QLabel("Henüz veri yok")
        self.telemetry_label.setAlignment(Qt.AlignCenter)

        self.map_widget = MapWidget()
        self.charts_widget = ChartsWidget()

        # Status panel
        try:
            self.status_panel = StatusPanel()
        except Exception as e:
            print(f"Status panel oluşturulamadı: {e}")
            self.status_panel = None

        try:
            # Status panel'den sonra ekleyin
            self.alarm_panel = AlarmPanel()
        except:
            print(f"Alarm Panel Oluşturulamadı:{e}")
            self.alarm_panel=None

        # Tab düzeni
        self._setup_tabs()

        # Status panel sinyallerini bağla
        self._connect_status_panel_signals()

        # Worker başlat (DATABASE MANAGER İLE!)
        self.worker = TelemetryWorker(database_manager=self.db_manager)
        self.worker.new_data.connect(self.update_telemetry)
        self.worker.start()

    def _setup_tabs(self):
        """Tab düzenini oluştur"""
        tabs = QTabWidget()

        # 1. Harita Tab
        tabs.addTab(self._create_map_tab(), "🗺️ Harita")

        # 2. Grafikler Tab
        tabs.addTab(self._create_charts_tab(), "📊 Grafikler")

        # 3. Telemetri Tab
        tabs.addTab(self._create_telemetry_tab(), "📡 Telemetri")

        # 4. Status Tab (eğer varsa)
        if self.status_panel:
            tabs.addTab(self._create_status_tab(), "⚙️ Durum")

        # Status tab'dan sonra ekleyin
        tabs.addTab(self._create_alarm_tab(), "🚨 Alarmlar")

        # 5. VERİTABANI TAB - YENİ!
        tabs.addTab(self._create_database_tab(), "💾 Veritabanı")

        self.setCentralWidget(tabs)

    def _create_map_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.map_widget)
        widget.setLayout(layout)
        return widget

    def _create_alarm_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.alarm_panel)
        widget.setLayout(layout)
        return widget

    def _create_charts_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.charts_widget)
        widget.setLayout(layout)
        return widget

    def _create_telemetry_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.telemetry_label)
        widget.setLayout(layout)
        return widget

    def _create_status_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.status_panel)
        widget.setLayout(layout)
        return widget

    def _create_database_tab(self):  # YENİ VERİTABANI SEKMESİ
        """Veritabanı yönetim sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Başlık
        title = QLabel("Veritabanı Yönetimi")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        # İstatistikler
        self.db_stats_label = QLabel("Veritabanı bilgileri yükleniyor...")
        layout.addWidget(self.db_stats_label)

        # Butonlar
        button_layout = QHBoxLayout()

        self.refresh_db_btn = QPushButton("🔄 Bilgileri Yenile")
        self.new_session_btn = QPushButton("🆕 Yeni Oturum Başlat")
        self.end_session_btn = QPushButton("🏁 Oturumu Sonlandır")
        self.export_csv_btn = QPushButton("📤 CSV Dışa Aktar")

        button_layout.addWidget(self.refresh_db_btn)
        button_layout.addWidget(self.new_session_btn)
        button_layout.addWidget(self.end_session_btn)
        button_layout.addWidget(self.export_csv_btn)

        layout.addLayout(button_layout)

        # Uçuş oturumları listesi
        self.sessions_label = QLabel("Son Uçuş Oturumları:")
        layout.addWidget(self.sessions_label)

        self.sessions_list_label = QLabel("Liste yükleniyor...")
        layout.addWidget(self.sessions_list_label)

        layout.addStretch()
        widget.setLayout(layout)

        # Buton sinyalleri
        self.refresh_db_btn.clicked.connect(self.refresh_database_info)
        self.new_session_btn.clicked.connect(self.start_new_session)
        self.end_session_btn.clicked.connect(self.end_current_session)
        self.export_csv_btn.clicked.connect(self.export_current_session)

        # İlk yükleme
        self.refresh_database_info()

        return widget

    def refresh_database_info(self):
        """Veritabanı bilgilerini yenile"""
        if not self.db_manager:
            self.db_stats_label.setText("Veritabanı bağlantısı yok!")
            return

        try:
            # Genel bilgiler
            info = self.db_manager.get_database_info()
            stats_text = (
                f"Veritabanı: {info['database_path']}\n"
                f"Dosya boyutu: {info['database_size'] / 1024:.1f} KB\n"
                f"Toplam oturum: {info['total_sessions']}\n"
                f"Toplam kayıt: {info['total_records']}\n"
                f"Aktif oturum: {info['active_sessions']}"
            )
            self.db_stats_label.setText(stats_text)

            # Son oturumlar
            sessions = self.db_manager.get_flight_sessions()
            if sessions:
                session_text = "\n".join([
                    f"• {s['session_name']} - {s['start_time'].strftime('%Y-%m-%d %H:%M')} "
                    f"({s['status']})" for s in sessions[:10]  # Son 10 oturum
                ])
            else:
                session_text = "Henüz oturum bulunmuyor"

            self.sessions_list_label.setText(session_text)

        except Exception as e:
            self.db_stats_label.setText(f"Veritabanı bilgi hatası: {e}")

    def start_new_session(self):
        """Yeni uçuş oturumu başlat"""
        if not self.db_manager:
            QMessageBox.warning(self, "Hata", "Veritabanı bağlantısı yok!")
            return

        # Mevcut worker'ı durdur
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()

        # Yeni oturum başlat
        session_id = self.db_manager.start_flight_session()

        # Yeni worker başlat
        self.worker = TelemetryWorker(database_manager=self.db_manager)
        self.worker.new_data.connect(self.update_telemetry)
        self.worker.start()

        QMessageBox.information(self, "Başarılı", f"Yeni oturum başlatıldı: {session_id}")
        self.refresh_database_info()

    def end_current_session(self):
        """Mevcut oturumu sonlandır"""
        if not self.db_manager:
            QMessageBox.warning(self, "Hata", "Veritabanı bağlantısı yok!")
            return

        if hasattr(self, 'worker'):
            self.worker.stop_session()

        QMessageBox.information(self, "Başarılı", "Oturum sonlandırıldı")
        self.refresh_database_info()

    def export_current_session(self):
        """Mevcut oturumu CSV olarak dışa aktar"""
        if not self.db_manager or not self.db_manager.current_session_id:
            QMessageBox.warning(self, "Hata", "Aktif oturum bulunamadı!")
            return

        from datetime import datetime
        filename = f"flight_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        try:
            self.db_manager.export_session_csv(
                self.db_manager.current_session_id,
                filename
            )
            QMessageBox.information(self, "Başarılı", f"Veriler dışa aktarıldı: {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Dışa aktarma hatası: {e}")

    def update_telemetry(self, packet: TelemetryPacket):
        """Worker'dan gelen veriyi tüm widget'lara dağıt"""
        # 1. Telemetri text güncelle
        txt = (
            f"🕐 Zaman: {packet.timestamp.strftime('%H:%M:%S')}\n"
            f"📍 GPS: {packet.gps.latitude:.5f}, {packet.gps.longitude:.5f}\n"
            f"⛰️ Rakım: {packet.gps.altitude:.1f} m\n"
            f"🚀 Hız: {packet.velocity:.1f} m/s\n"
            f"🔋 Batarya: {packet.battery_percent:.1f}% ({packet.battery_voltage:.1f} V)\n"
            f"📊 Durum: {packet.status}"
        )
        self.telemetry_label.setText(txt)

        # 2. Haritayı güncelle
        self.map_widget.update_position(packet.gps.latitude, packet.gps.longitude)

        # 3. Grafikleri güncelle
        self.charts_widget.update_data(packet)

        # 5. Alarm kontrolü
        self.alarm_panel.check_telemetry_alarms(packet)

        # 4. Status paneli güncelle (eğer varsa)
        if self.status_panel:
            try:
                self.status_panel.update_status(packet)
            except Exception as e:
                print(f"Status panel güncelleme hatası: {e}")

    def _connect_status_panel_signals(self):
        """Status panel butonlarını işlevlere bağla"""
        if self.status_panel:
            print("Status panel sinyalleri bağlanıyor...")

            # Grafikleri temizle
            self.status_panel.clearGraphsRequested.connect(self.clear_graphs)

            # Harita yolunu temizle
            self.status_panel.clearPathRequested.connect(self.clear_map_path)

            # Acil durdur
            self.status_panel.emergencyStopRequested.connect(self.emergency_stop)

            print("✅ Tüm sinyaller bağlandı!")

    def clear_graphs(self):
        """Tüm grafikleri temizle"""
        print("🔄 Grafikler temizleniyor...")
        self.charts_widget.clear_data()
        print("✅ Grafikler temizlendi!")

    def clear_map_path(self):
        """Harita yolunu temizle"""
        print("🔄 Harita yolu temizleniyor...")
        self.map_widget.reset_path()
        print("✅ Harita yolu temizlendi!")

    def emergency_stop(self):
        """Acil durdur - Worker'ı durdur"""
        print("🚨 ACİL DURDUR başlatıldı!")

        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
            print("🚨 ACİL DURDUR: Veri akışı durduruldu!")

            # Tekrar başlatma butonu
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                'Acil Durdur',
                'Veri akışı durduruldu!\n\nTekrar başlatmak istiyor musunuz?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.restart_worker()

    def restart_worker(self):
        """Worker'ı yeniden başlat"""
        try:
            print("🔄 Worker yeniden başlatılıyor...")
            self.worker = TelemetryWorker(database_manager=self.db_manager)
            self.worker.new_data.connect(self.update_telemetry)
            self.worker.start()
            print("✅ Veri akışı yeniden başlatıldı!")
        except Exception as e:
            print(f"❌ Worker başlatılamadı: {e}")

    def closeEvent(self, event):
        """Uygulama kapanırken temizlik"""
        if hasattr(self, 'worker'):
            self.worker.quit()
            self.worker.wait()

        # Veritabanı bağlantısını kapat
        if hasattr(self, 'db_manager') and self.db_manager:
            self.db_manager.close_connection()

        event.accept()

    # Bu kısım dosyanın en sonunda olmalı ve düzeltilmeli:

def main():
        app = QApplication(sys.argv)
        win = MainWindow()
        win.show()
        sys.exit(app.exec())

if __name__ == "__main__":
    main()

    # NOT: main() fonksiyonu sınıfın içinde değil, dosyanın en sonunda olmalı!