# PC Performance Monitor

A lightweight Windows desktop monitor for CPU, RAM, download, and upload usage.
The interface uses PySide6 and refreshes once per second with a Qt timer.

## Run

Activate the virtual environment, install dependencies, and start the app:

```powershell
pip install -r requirements.txt
python main.py
```

## Project Structure

* `monitor.py` collects system metrics and owns network timing state.
* `gui.py` contains the dashboard, metric cards, timer, and the always-on-top overlay.
* `main.py` creates the Qt application and connects the monitor to the dashboard.

The overlay preview opens as a frameless tool window that stays above other
applications. Hotkey, transparency, and click-through behavior can be added to
`OverlayWindow` without coupling those details to the dashboard.

## Dependencies

* PySide6
* psutil
