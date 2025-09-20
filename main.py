# main.py
import sys
import os

# Mevcut dizini Python path'ine ekle
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Proje klasör adını da ekle
project_name = "Uav_telemetry_imaging_system"
sys.path.insert(0, os.path.join(current_dir, project_name))

from src.ui.main_window import main

if __name__ == "__main__":
    main()
