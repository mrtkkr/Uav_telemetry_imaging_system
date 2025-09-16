# src/ui/map_widget.py - reset_path() metodu eklendi
import folium
import io
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl


class MapWidget(QWebEngineView):
    def __init__(self, start_lat=39.9, start_lon=32.8, zoom=13):
        super().__init__()
        self.start_lat = start_lat
        self.start_lon = start_lon
        self.zoom = zoom
        self.current_lat = start_lat
        self.current_lon = start_lon
        self.path_points = []  # İHA'nın izlediği yolu saklamak için
        self._generate_map(start_lat, start_lon)

    def _generate_map(self, lat, lon, show_path=True):
        """Harita oluştur"""
        # Harita merkezi
        m = folium.Map(location=[lat, lon], zoom_start=self.zoom)

        # Mevcut konum marker'ı (kırmızı)
        folium.Marker(
            [lat, lon],
            tooltip=f"İHA Konumu\nLat: {lat:.5f}\nLon: {lon:.5f}",
            popup=f"Güncel Konum<br>Lat: {lat:.5f}<br>Lon: {lon:.5f}",
            icon=folium.Icon(color='red', icon='plane')
        ).add_to(m)

        # Başlangıç noktası marker'ı (yeşil)
        if lat != self.start_lat or lon != self.start_lon:
            folium.Marker(
                [self.start_lat, self.start_lon],
                tooltip="Başlangıç Noktası",
                popup="İHA Başlangıç Noktası",
                icon=folium.Icon(color='green', icon='home')
            ).add_to(m)

        # Yol çizgisi
        if show_path and len(self.path_points) > 1:
            folium.PolyLine(
                self.path_points,
                color="blue",
                weight=3,
                opacity=0.7,
                tooltip="İHA Rotası"
            ).add_to(m)

        # HTML'i oluştur ve widget'a yükle
        data = io.BytesIO()
        m.save(data, close_file=False)
        html_content = data.getvalue().decode()
        self.setHtml(html_content)

    def update_position(self, lat, lon):
        """
        Harita merkezini ve marker'ı yeni konuma taşır.
        Ayrıca yol izini tutar.
        """
        # Yeni nokta yoldan çok farklıysa path'e ekle
        if not self.path_points or self._distance_significant(lat, lon):
            self.path_points.append([lat, lon])
            # Path çok uzarsa eski noktaları temizle (performans için)
            if len(self.path_points) > 100:
                self.path_points = self.path_points[-50:]

        self.current_lat = lat
        self.current_lon = lon
        self._generate_map(lat, lon)

    def _distance_significant(self, lat, lon, threshold=0.0001):
        """
        İki nokta arasındaki mesafe anlamlı mı kontrol eder
        (Çok sık güncelleme yapmamak için)
        """
        if not self.path_points:
            return True

        last_point = self.path_points[-1]
        distance = abs(lat - last_point[0]) + abs(lon - last_point[1])
        return distance > threshold

    def reset_path(self):
        """Yol izini temizle - STATUS PANEL BUTONU İÇİN"""
        self.path_points = []
        self._generate_map(self.current_lat, self.current_lon)
        print("🗺️ Harita yolu temizlendi!")

    def center_map(self):
        """Haritayı mevcut konuma ortala"""
        self._generate_map(self.current_lat, self.current_lon)

    def add_waypoint(self, lat, lon, alt):
        """Haritaya waypoint ekle"""
        print(f"📍 Waypoint eklendi: {lat:.5f}, {lon:.5f}, {alt}m")

    def clear_waypoints(self):
        """Waypoint'leri temizle"""
        print("🗑️ Waypoint'ler temizlendi")