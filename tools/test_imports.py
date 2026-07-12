import sys
import traceback
try:
    from UI.main_window import MainWindow
    print("MainWindow imported successfully!")
except Exception as e:
    print(f"Import failed: {e}")
    traceback.print_exc()
