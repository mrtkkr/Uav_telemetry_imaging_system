# run.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ui.main_window import main

if __name__ == "__main__":
    main()