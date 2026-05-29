import sys
import truststore
truststore.inject_into_ssl()

from PySide6.QtWidgets import QApplication
import api
from windows.main_window import MainWindow


def main():
    dev_mode = "--dev" in sys.argv
    if dev_mode:
        api.configure("http://localhost:8001/doglog")

    app = QApplication(sys.argv)
    window = MainWindow(dev_mode=dev_mode)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
