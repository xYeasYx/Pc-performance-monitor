"""PySide6 dashboard for the PC performance monitor."""

from PySide6.QtCore import QPoint, QTimer, Qt, QSettings
import ctypes,ctypes.wintypes
from PySide6.QtCore import QAbstractNativeEventFilter
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QSlider
)

from monitor import Metrics, SystemMonitor


class MetricCard(QWidget):
    """Display one metric and its overlay visibility preference."""

    def __init__(self, title: str, unit: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("metricCard")
        self.metric_name = title
        self.unit = unit

        self.visibility_checkbox = QCheckBox("Show in overlay")
        self.visibility_checkbox.setChecked(True)
        self.title_label = QLabel(title.upper())
        self.title_label.setObjectName("metricTitle")
        self.value_label = QLabel("--")
        self.value_label.setObjectName("metricValue")
        self.unit_label = QLabel(unit)
        self.unit_label.setObjectName("metricUnit")

        value_layout = QHBoxLayout()
        value_layout.setContentsMargins(0, 0, 0, 0)
        value_layout.setSpacing(6)
        value_layout.addWidget(self.value_label)
        value_layout.addWidget(self.unit_label, alignment=Qt.AlignmentFlag.AlignBottom)
        value_layout.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        layout.addWidget(self.title_label)
        layout.addLayout(value_layout)
        layout.addWidget(self.visibility_checkbox)

    def set_value(self, value: float, decimals: int) -> None:
        self.value_label.setText(f"{value:.{decimals}f}")

    def is_overlay_visible(self) -> bool:
        return self.visibility_checkbox.isChecked()

class HotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, callback) -> None:
        super().__init__()
        self.callback = callback

    def nativeEventFilter(self, event_type, message):
        msg = ctypes.wintypes.MSG.from_address(int(message))

        WM_HOTKEY = 0x0312

        if msg.message == WM_HOTKEY:
            self.callback()
            return True, 0

        return False, 0

    
class OverlayWindow(QWidget):
    """Small always-on-top overlay window."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        #self.setWindowOpacity(0.5)

        self.settings = QSettings("PcPerformanceMonitor", "Overlay")

        self.adjustSize()
        self.load_position()

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)              ##overlay transparent settings
        self.setStyleSheet("background: transparent;")

        self._drag_position: QPoint | None = None               #mosue drag orignial postion

        self.setWindowTitle("PC Performance Overlay")
        outer_layout = QVBoxLayout(self)

        self.panel = QWidget()
        self.panel.setObjectName("overlayPanel")

        self.panel.setStyleSheet(
            """
            QWidget#overlayPanel {
                background-color: rgba(18, 22, 29, 160);
                border-radius: 10px;
            }
            """
        )

        self._layout = QVBoxLayout(self.panel)

        self._layout.setContentsMargins(14, 10, 14, 10)
        self._layout.setSpacing(6)

        outer_layout.addWidget(self.panel)




        self._metric_labels: dict[str, QLabel] = {}

    def set_panel_opacity(self, percent: int) -> None:
        alpha = int(255 * (percent / 100))

        self.panel.setStyleSheet(
            f"""
            QWidget#overlayPanel {{
                background-color: rgba(18, 22, 29, {alpha});
                border-radius: 10px;
            }}
            """
        )
        self.settings.setValue("opacity", percent)

    def load_opacity(self) -> int:
        saved_opacity = self.settings.value("opacity", 60)

        return int(saved_opacity)
    
    def save_position(self) -> None:
        x = self.x()
        y = self.y()

        self.settings.setValue("x", x)
        self.settings.setValue("y", y)

        print(f"Saved overlay position: x={x}, y={y}")


    def load_position(self) -> None:
        saved_x = self.settings.value("x")
        saved_y = self.settings.value("y")

        if saved_x is not None and saved_y is not None:
            x = int(saved_x)
            y = int(saved_y)

            if self.position_is_valid(x, y):
                self.move(x, y)
                return

        self.move_to_default_position()


    def position_is_valid(self, x: int, y: int) -> bool:
        for screen in QApplication.screens():
            screen_area = screen.availableGeometry()

            if screen_area.contains(QPoint(x, y)):
                return True

        return False


    def move_to_default_position(self) -> None:
        screen = QApplication.primaryScreen()

        if screen is None:
            return

        screen_area = screen.availableGeometry()

        margin = 20

        x = (
            screen_area.right()
            - self.width()
            - margin
        )

        y = screen_area.top() + margin

        self.move(x, y)

    def set_edit_mode(self, edit_mode: bool) -> None:
        hwnd = int(self.winId())

        GWL_EXSTYLE = -20
        WS_EX_TRANSPARENT = 0x00000020
        WS_EX_LAYERED = 0x00080000

        current_style = ctypes.windll.user32.GetWindowLongW(
            hwnd,
            GWL_EXSTYLE
        )

        if edit_mode:
            # Remove click-through
            new_style = current_style & ~WS_EX_TRANSPARENT

        else:
            # Enable click-through
            new_style = (
                current_style
                | WS_EX_TRANSPARENT
                | WS_EX_LAYERED
            )

        ctypes.windll.user32.SetWindowLongW(
            hwnd,
            GWL_EXSTYLE,
            new_style
        )

    def update_metrics(self, metrics: Metrics, visible_metrics: set[str]) -> None:
        values = {
            "CPU": f"CPU  {metrics.cpu_percent:.1f}%",
            "RAM": f"RAM  {metrics.ram_percent:.1f}%",
            "Download": f"Download  {metrics.download_mbps:.2f} Mbps",
            "Upload": f"Upload  {metrics.upload_mbps:.2f} Mbps",
        }
        for metric_name, text in values.items():
            label = self._metric_labels.get(metric_name)
            if label is None:
                label = QLabel()
                self._metric_labels[metric_name] = label
                self._layout.addWidget(label)
            label.setText(text)
            label.setVisible(metric_name in visible_metrics)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = (
                event.globalPosition().toPoint()
                - self.frameGeometry().topLeft()
        )


    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if (
            self._drag_position is not None
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            self.move(
                event.globalPosition().toPoint()
                - self._drag_position
            )


    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_position = None
        self.save_position()


class DashboardWindow(QMainWindow):
    """Main dashboard window and timer-driven view of SystemMonitor."""

    def __init__(self, monitor: SystemMonitor) -> None:
        super().__init__()
        self.monitor = monitor
        self.overlay_window = OverlayWindow()   #creates overlay window called self
        self.overlay_edit_mode = True           #sets editing mode to true by defualt 
        self.metric_cards = {
            "CPU": MetricCard("CPU", "%"),
            "RAM": MetricCard("RAM", "%"),
            "Download": MetricCard("Download", "Mbps"),
            "Upload": MetricCard("Upload", "Mbps"),
        }

        self.setWindowTitle("PC Performance Monitor")
        self.setMinimumSize(560, 430)
        self._build_ui()
        self.register_hotkey()

        self.update_timer = QTimer(self)
        self.update_timer.setInterval(1000)
        self.update_timer.timeout.connect(self.update_metrics)
        self.update_timer.start()
        self.update_metrics()

    def register_hotkey(self) -> None:
        MOD_CONTROL = 0x0002
        MOD_SHIFT = 0x0004
        VK_O = 0x4F

        self.hotkey_id = 1

        success = ctypes.windll.user32.RegisterHotKey(
            None,
            self.hotkey_id,
            MOD_CONTROL | MOD_SHIFT,
            VK_O
        )

        if not success:
            self.overlay_status_label.setText(
                "Could not register Ctrl + Shift + O"
            )
            return

        self.hotkey_filter = HotkeyFilter(self.toggle_overlay)

        QApplication.instance().installNativeEventFilter(
            self.hotkey_filter
        )

    def closeEvent(self, event) -> None:
        ctypes.windll.user32.UnregisterHotKey(
            None,
            self.hotkey_id
        )

        event.accept()
    def _build_ui(self) -> None:
        title_label = QLabel("PC PERFORMANCE MONITOR")
        title_label.setObjectName("windowTitle")

        subtitle_label = QLabel("Live system telemetry")
        subtitle_label.setObjectName("subtitle")

        cards_layout = QGridLayout()
        cards_layout.setSpacing(14)
        for index, card in enumerate(self.metric_cards.values()):
            cards_layout.addWidget(card, index // 2, index % 2)

        hotkey_label = QLabel("Overlay Hotkey: Ctrl + Shift + O")
        hotkey_label.setObjectName("hotkey")

        self.overlay_status_label = QLabel("Overlay window ready for future controls")
        self.overlay_status_label.setObjectName("status")

        self.overlay_button = QPushButton("Start Overlay")
        self.overlay_button.clicked.connect(self.toggle_overlay)

        self.overlay_mode_button = QPushButton("Enter Game Mode")
        self.overlay_mode_button.clicked.connect(self.toggle_overlay_mode)

        opacity_label = QLabel("Overlay Opacity")

        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setMinimum(20)
        self.opacity_slider.setMaximum(100)
        saved_opacity = self.overlay_window.load_opacity()
        self.opacity_slider.setValue(saved_opacity)

        self.opacity_slider.valueChanged.connect(
            self.overlay_window.set_panel_opacity
        )


        footer_layout = QHBoxLayout()
        footer_layout.addWidget(hotkey_label)
        footer_layout.addStretch()
        footer_layout.addWidget(self.overlay_mode_button)
        footer_layout.addWidget(self.overlay_button)

        central_widget = QWidget()

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(28, 26, 28, 28)
        layout.setSpacing(6)

        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        layout.addSpacing(16)

        layout.addLayout(cards_layout)

        layout.addSpacing(12)
        layout.addWidget(opacity_label)
        layout.addWidget(self.opacity_slider)

        layout.addStretch()

        layout.addWidget(self.overlay_status_label)
        layout.addLayout(footer_layout)

        self.setCentralWidget(central_widget)

    def update_metrics(self) -> None:
        metrics = self.monitor.read_metrics()
        self.metric_cards["CPU"].set_value(metrics.cpu_percent, 1)
        self.metric_cards["RAM"].set_value(metrics.ram_percent, 1)
        self.metric_cards["Download"].set_value(metrics.download_mbps, 2)
        self.metric_cards["Upload"].set_value(metrics.upload_mbps, 2)

        visible_metrics = {
            name
            for name, card in self.metric_cards.items()
            if card.is_overlay_visible()
        }
        self.overlay_window.update_metrics(metrics, visible_metrics)


    def toggle_overlay(self) -> None:
        if self.overlay_window.isVisible():
            self.overlay_window.hide()
            self.overlay_button.setText("Start Overlay")
            self.overlay_status_label.setText("Overlay hidden")
        else:
            self.overlay_window.show()
            self.overlay_button.setText("Hide Overlay")
            self.overlay_status_label.setText("Overlay visible")


    def toggle_overlay_mode(self) -> None:
        if self.overlay_edit_mode:
            self.overlay_edit_mode = False
            self.overlay_window.set_edit_mode(False)

            self.overlay_mode_button.setText("Enter Edit Mode")
            self.overlay_status_label.setText("Game mode enabled")
        else:
            self.overlay_edit_mode = True
            self.overlay_window.set_edit_mode(True)

            self.overlay_mode_button.setText("Enter Game Mode")
            self.overlay_status_label.setText("Edit mode enabled")