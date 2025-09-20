# tests/test_ui.py
import unittest
import sys
import os
from datetime import datetime
from unittest.mock import Mock, patch

# Qt test framework
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication,QMessageBox

# Proje kök dizinini Python path'ine ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ui.alarm_panel import AlarmPanel
from src.ui.waypoint_panel import WaypointPanel
from src.ui.status_panel import StatusPanel
from src.telemetry.data_models import TelemetryPacket, GPSData, AttitudeData


class TestAlarmPanel(unittest.TestCase):
    """Alarm paneli UI testleri"""

    @classmethod
    def setUpClass(cls):
        """Test sınıfı başlatma"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """Her test öncesi hazırlık"""
        self.alarm_panel = AlarmPanel()

    def test_alarm_panel_creation(self):
        """Alarm paneli oluşturma testi"""
        self.assertIsNotNone(self.alarm_panel)
        self.assertFalse(self.alarm_panel.alarms_muted)
        self.assertEqual(self.alarm_panel.alarm_list.count(), 0)

    def test_add_warning_alarm(self):
        """Uyarı alarmı ekleme testi"""
        initial_count = self.alarm_panel.alarm_list.count()

        self.alarm_panel.add_alarm("TEST_WARNING", "WARNING", "Test uyarı mesajı")

        self.assertEqual(self.alarm_panel.alarm_list.count(), initial_count + 1)
        item_text = self.alarm_panel.alarm_list.item(0).text()
        self.assertIn("Test uyarı mesajı", item_text)
        self.assertIn("🟡", item_text)

    def test_add_critical_alarm(self):
        """Kritik alarm ekleme testi"""
        self.alarm_panel.add_alarm("TEST_CRITICAL", "CRITICAL", "Test kritik mesajı")

        item = self.alarm_panel.alarm_list.item(0)
        self.assertIn("Test kritik mesajı", item.text())
        self.assertIn("🔴", item.text())

    def test_clear_alarms(self):
        """Alarm temizleme testi"""
        # Önce alarm ekle
        self.alarm_panel.add_alarm("TEST", "WARNING", "Test mesajı")
        self.assertEqual(self.alarm_panel.alarm_list.count(), 1)

        # Temizle
        self.alarm_panel.clear_alarms()
        self.assertEqual(self.alarm_panel.alarm_list.count(), 0)

    def test_mute_toggle(self):
        """Sessiz modu toggle testi"""
        # Başlangıçta sesli olmalı
        self.assertFalse(self.alarm_panel.alarms_muted)

        # Sessize al
        self.alarm_panel.toggle_mute()
        self.assertTrue(self.alarm_panel.alarms_muted)

        # Tekrar sesli yap
        self.alarm_panel.toggle_mute()
        self.assertFalse(self.alarm_panel.alarms_muted)

    def test_telemetry_alarm_check(self):
        """Telemetri alarm kontrolü testi"""
        # Kritik batarya seviyesi
        gps = GPSData(latitude=40.0, longitude=33.0, altitude=100.0, satellites=10)
        packet = TelemetryPacket(
            timestamp=datetime.now(),
            gps=gps,
            velocity=15.0,
            battery_percent=10.0,  # Kritik seviye
            battery_voltage=22.0,
            status="LOW_BATTERY"
        )

        initial_count = self.alarm_panel.alarm_list.count()
        self.alarm_panel.check_telemetry_alarms(packet)

        # Alarm eklenmiş olmalı
        self.assertGreater(self.alarm_panel.alarm_list.count(), initial_count)


class TestWaypointPanel(unittest.TestCase):
    """Waypoint paneli UI testleri"""

    @classmethod
    def setUpClass(cls):
        """Test sınıfı başlatma"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """Her test öncesi hazırlık"""
        self.waypoint_panel = WaypointPanel()

    def test_waypoint_panel_creation(self):
        """Waypoint paneli oluşturma testi"""
        self.assertIsNotNone(self.waypoint_panel)
        self.assertEqual(len(self.waypoint_panel.waypoints), 0)
        self.assertEqual(self.waypoint_panel.waypoint_list.count(), 0)

    def test_add_waypoint(self):
        """Waypoint ekleme testi"""
        # Form değerlerini ayarla
        self.waypoint_panel.lat_spin.setValue(40.0)
        self.waypoint_panel.lon_spin.setValue(33.0)
        self.waypoint_panel.alt_spin.setValue(150.0)
        self.waypoint_panel.action_combo.setCurrentText("FLY_TO")

        # Waypoint ekle
        initial_count = len(self.waypoint_panel.waypoints)
        self.waypoint_panel.add_waypoint()

        # Kontrol et
        self.assertEqual(len(self.waypoint_panel.waypoints), initial_count + 1)
        self.assertEqual(self.waypoint_panel.waypoint_list.count(), initial_count + 1)

        # Eklenen waypoint'i kontrol et
        waypoint = self.waypoint_panel.waypoints[0]
        self.assertEqual(waypoint['latitude'], 40.0)
        self.assertEqual(waypoint['longitude'], 33.0)
        self.assertEqual(waypoint['altitude'], 150.0)
        self.assertEqual(waypoint['action'], 'FLY_TO')

    def test_remove_waypoint(self):
        """Waypoint kaldırma testi"""
        # Önce waypoint ekle
        self.waypoint_panel.lat_spin.setValue(40.0)
        self.waypoint_panel.lon_spin.setValue(33.0)
        self.waypoint_panel.add_waypoint()

        self.assertEqual(len(self.waypoint_panel.waypoints), 1)

        # İlk öğeyi seç ve kaldır
        self.waypoint_panel.waypoint_list.setCurrentRow(0)
        self.waypoint_panel.remove_waypoint()

        self.assertEqual(len(self.waypoint_panel.waypoints), 0)
        self.assertEqual(self.waypoint_panel.waypoint_list.count(), 0)

    def test_waypoint_order_up(self):
        """Waypoint yukarı taşıma testi"""
        # İki waypoint ekle
        self.waypoint_panel.lat_spin.setValue(40.0)
        self.waypoint_panel.lon_spin.setValue(33.0)
        self.waypoint_panel.add_waypoint()

        self.waypoint_panel.lat_spin.setValue(41.0)
        self.waypoint_panel.lon_spin.setValue(34.0)
        self.waypoint_panel.add_waypoint()

        # İkinci waypoint'i seç ve yukarı taşı
        self.waypoint_panel.waypoint_list.setCurrentRow(1)
        original_lat = self.waypoint_panel.waypoints[1]['latitude']

        self.waypoint_panel.move_waypoint_up()

        # Sıralama değişmiş olmalı
        self.assertEqual(self.waypoint_panel.waypoints[0]['latitude'], original_lat)

    def test_clear_mission(self):
        """Görev temizleme testi"""
        # Waypoint ekle
        self.waypoint_panel.add_waypoint()
        self.assertEqual(len(self.waypoint_panel.waypoints), 1)

        # Mock dialog response - Yes seçeneği (DÜZELTME)
        with patch('PySide6.QtWidgets.QMessageBox.question') as mock_question:
            mock_question.return_value = QMessageBox.StandardButton.Yes  # Bu satırı değiştirin

            self.waypoint_panel.clear_mission()

            self.assertEqual(len(self.waypoint_panel.waypoints), 0)

    def test_mission_statistics(self):
        """Görev istatistikleri testi"""
        # İki waypoint ekle (mesafe hesaplanabilir)
        self.waypoint_panel.lat_spin.setValue(40.0000)
        self.waypoint_panel.lon_spin.setValue(33.0000)
        self.waypoint_panel.add_waypoint()

        self.waypoint_panel.lat_spin.setValue(40.0010)  # Küçük değişiklik
        self.waypoint_panel.lon_spin.setValue(33.0010)
        self.waypoint_panel.add_waypoint()

        # İstatistiklerin güncellenmiş olması gerekir
        stats_text = self.waypoint_panel.stats_label.text()
        self.assertIn("2 waypoint", stats_text)
        self.assertIn("km", stats_text)
        self.assertIn("dk", stats_text)


class TestStatusPanel(unittest.TestCase):
    """Status paneli UI testleri"""

    @classmethod
    def setUpClass(cls):
        """Test sınıfı başlatma"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """Her test öncesi hazırlık"""
        self.status_panel = StatusPanel()

    def test_status_panel_creation(self):
        """Status paneli oluşturma testi"""
        self.assertIsNotNone(self.status_panel)
        self.assertIsNotNone(self.status_panel.battery_bar)
        self.assertIsNotNone(self.status_panel.connection_status)

    def test_telemetry_update(self):
        """Telemetri güncelleme testi"""
        gps = GPSData(latitude=40.0, longitude=33.0, altitude=150.0, satellites=12)
        attitude = AttitudeData(roll=5.0, pitch=-2.0, yaw=45.0)

        packet = TelemetryPacket(
            timestamp=datetime.now(),
            gps=gps,
            attitude=attitude,
            velocity=20.0,
            battery_percent=75.0,
            battery_voltage=24.5,
            status="FLYING"
        )

        # Status güncelle
        self.status_panel.update_status(packet)

        # Kontrol et
        self.assertEqual(self.status_panel.battery_bar.value(), 75)
        self.assertIn("24.5", self.status_panel.battery_voltage_label.text())
        self.assertIn("FLYING", self.status_panel.flight_mode.text())

    def test_battery_color_critical(self):
        """Kritik batarya rengi testi"""
        gps = GPSData(latitude=40.0, longitude=33.0, altitude=100.0)
        packet = TelemetryPacket(
            timestamp=datetime.now(),
            gps=gps,
            velocity=15.0,
            battery_percent=15.0,  # Kritik seviye
            battery_voltage=22.0,
            status="LOW_BATTERY"
        )

        self.status_panel.update_status(packet)

        # Batarya çubuğu kırmızı olmalı
        stylesheet = self.status_panel.battery_bar.styleSheet()
        self.assertIn("red", stylesheet)

    def test_signal_connections(self):
        """Sinyal bağlantıları testi"""
        # Sinyallerin bağlanmış olduğunu kontrol et
        self.assertTrue(self.status_panel.clearGraphsRequested)
        self.assertTrue(self.status_panel.clearPathRequested)
        self.assertTrue(self.status_panel.emergencyStopRequested)


if __name__ == '__main__':
    # Test suite oluştur
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Test sınıflarını ekle
    suite.addTests(loader.loadTestsFromTestCase(TestAlarmPanel))
    suite.addTests(loader.loadTestsFromTestCase(TestWaypointPanel))
    suite.addTests(loader.loadTestsFromTestCase(TestStatusPanel))

    # Testleri çalıştır
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Sonuçları yazdır
    print(f"\nUI Test Sonuçları:")
    print(f"Toplam test: {result.testsRun}")
    print(f"Başarısız: {len(result.failures)}")
    print(f"Hata: {len(result.errors)}")

    if result.failures:
        print("\nBaşarısız testler:")
        for test, error in result.failures:
            print(f"- {test}: {error}")

    if result.errors:
        print("\nHata alan testler:")
        for test, error in result.errors:
            print(f"- {test}: {error}")

    success_rate = ((result.testsRun - len(result.failures) - len(
        result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    print(f"Başarı oranı: {success_rate:.1f}%")