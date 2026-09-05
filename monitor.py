"""System metric collection, kept independent from the Qt interface."""

from dataclasses import dataclass
import time

import psutil


@dataclass(frozen=True)
class Metrics:
    cpu_percent: float
    ram_percent: float
    download_mbps: float
    upload_mbps: float


class SystemMonitor:
    """Collect CPU, memory, and network metrics from the local computer."""

    def __init__(self) -> None:
        self._previous_network_data = psutil.net_io_counters()
        self._previous_time = time.perf_counter()
        psutil.cpu_percent(interval=None)

    def read_metrics(self) -> Metrics:
        """Read one sample and use elapsed time for network speed."""
        cpu_percent = psutil.cpu_percent(interval=None)
        ram_percent = psutil.virtual_memory().percent

        current_network_data = psutil.net_io_counters()
        current_time = time.perf_counter()
        elapsed_time = current_time - self._previous_time

        download_bytes = (
            current_network_data.bytes_recv
            - self._previous_network_data.bytes_recv
        )
        upload_bytes = (
            current_network_data.bytes_sent
            - self._previous_network_data.bytes_sent
        )

        self._previous_network_data = current_network_data
        self._previous_time = current_time

        if elapsed_time <= 0:
            download_mbps = 0.0
            upload_mbps = 0.0
        else:
            download_mbps = download_bytes * 8 / 1_000_000 / elapsed_time
            upload_mbps = upload_bytes * 8 / 1_000_000 / elapsed_time

        return Metrics(
            cpu_percent=cpu_percent,
            ram_percent=ram_percent,
            download_mbps=max(0.0, download_mbps),
            upload_mbps=max(0.0, upload_mbps),
        )


# Kept as a small compatibility helper for code that used the original function.
def get_network_speed(previous_network_data, previous_time):
    current_network_data = psutil.net_io_counters()
    current_time = time.perf_counter()
    elapsed_time = current_time - previous_time

    if elapsed_time <= 0:
        return current_network_data, current_time, 0.0, 0.0

    download_bytes = current_network_data.bytes_recv - previous_network_data.bytes_recv
    upload_bytes = current_network_data.bytes_sent - previous_network_data.bytes_sent
    download_mbps = download_bytes * 8 / 1_000_000 / elapsed_time
    upload_mbps = upload_bytes * 8 / 1_000_000 / elapsed_time

    return current_network_data, current_time, max(0.0, download_mbps), max(0.0, upload_mbps)
