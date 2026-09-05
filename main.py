import sys

from PySide6.QtWidgets import QApplication

from gui import DashboardWindow
from monitor import SystemMonitor


def main() -> int:
    application = QApplication(sys.argv)
    application.setStyleSheet(
        """
        QMainWindow, QWidget {
            background-color: #12161d;
            color: #e8edf2;
            font-family: Segoe UI;
        }
        QLabel#windowTitle {
            color: #f4f7fa;
            font-size: 24px;
            font-weight: 700;
            letter-spacing: 1px;
        }
        QLabel#subtitle, QLabel#status, QLabel#hotkey {
            color: #8794a3;
            font-size: 13px;
        }
        QLabel#status {
            color: #66d9a5;
        }
        QWidget#metricCard {
            background-color: #1a212b;
            border: 1px solid #293442;
            border-radius: 10px;
        }
        QWidget#metricCard QLabel {
            border: none;
            color: #f4f7fa;
        }
        QLabel#metricTitle {
            color: #aeb9c5;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 1px;
        }
        QLabel#metricValue {
            color: #f4f7fa;
            font-size: 30px;
            font-weight: 700;
        }
        QLabel#metricUnit {
            color: #8794a3;
            font-size: 12px;
        }
        QLabel {
            background: transparent;
        }
        QCheckBox {
            color: #aeb9c5;
            font-size: 12px;
        }
        QCheckBox::indicator {
            width: 15px;
            height: 15px;
        }
        QCheckBox::indicator:unchecked {
            border: 1px solid #526070;
            border-radius: 4px;
            background: #1a212b;
        }
        QCheckBox::indicator:checked {
            border: 1px solid #5dd39e;
            border-radius: 4px;
            background: #5dd39e;
        }
        QPushButton {
            background-color: #5dd39e;
            color: #0f1916;
            border: none;
            border-radius: 6px;
            padding: 10px 18px;
            font-weight: 700;
        }
        QPushButton:hover {
            background-color: #f59e42;
        }
        """
    )

    monitor = SystemMonitor()
    window = DashboardWindow(monitor)
    window.show()
    return application.exec()


if __name__ == "__main__":
    main()