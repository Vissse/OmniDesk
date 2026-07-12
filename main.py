import sys
import os
import time 

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QEvent
from PyQt6.QtGui import QIcon

# Globální zachytávač chyb - pokud cokoliv spadne, ukáže se chybová tabulka
def global_exception_handler(exctype, value, tb):
    import traceback
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    print(error_msg)
    if QApplication.instance():
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Kritická chyba")
        msg.setText("Aplikace narazila na kritickou chybu.")
        msg.setDetailedText(error_msg)
        msg.exec()
    sys.exit(1)

sys.excepthook = global_exception_handler

class SnippingToolFilter(QObject):
    def eventFilter(self, obj, event):
        # Print Screen generuje v Qt na Windows událost KeyRelease, nikoliv KeyPress!
        if event.type() == QEvent.Type.KeyRelease:
            if event.key() == Qt.Key.Key_Print or event.key() == 16777222:
                import os
                os.system("start ms-screenclip:")
                return True
        return super().eventFilter(obj, event)

# Importy
from core.config import resource_path
from core.i18n import _
from UI.splash import SplashScreen
from UI.pages.view_specs import get_pc_specs
from UI.main_window import MainWindow

window = None
final_specs = None 

class InitWorker(QThread):
    progress_update = pyqtSignal(int, str)
    
    def run(self):
        global final_specs
        try:
            self.progress_update.emit(10, _("splash_config"))
            time.sleep(0.2)
            
            self.progress_update.emit(20, _("splash_hw"))
            def hw_progress(msg):
                self.progress_update.emit(50, msg)
                
            final_specs = get_pc_specs(progress_callback=hw_progress) 
            
            self.progress_update.emit(90, _("splash_ui"))
            time.sleep(0.2)
        except Exception as e:
            print(f"Chyba při inicializaci HW: {e}")
        finally:
            self.progress_update.emit(100, _("splash_start"))

def show_main_window():
    QApplication.instance().setQuitOnLastWindowClosed(True)
    window.show()

def start_program():
    global window, final_specs
    window = MainWindow(specs=final_specs)
    
    window.updater.check_for_updates(silent=True, on_continue=show_main_window)

if __name__ == "__main__":
    if os.name == 'nt': 
        import ctypes
        myappid = u'vissse.OmniDesk.v1' 
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QApplication(sys.argv)

    # Globální zachytávač Print Screen
    snip_filter = SnippingToolFilter()
    app.installEventFilter(snip_filter)

    # Nevypínej celou aplikaci jen proto, že zmizel Splash Screen
    app.setQuitOnLastWindowClosed(False)
    
    icon_path = resource_path("assets/icons/program_icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    splash = SplashScreen()
    splash.show()
    
    worker = InitWorker()
    worker.progress_update.connect(splash.update_progress)
    splash.finished.connect(start_program)
    worker.start()
    
    sys.exit(app.exec())
