import time
import psutil


def get_network_speed(previous_network_data, preTime):
    currNetData = psutil.net_io_counters()
    currTime = time.perf_counter()

    elapsedTime = currTime - preTime

    dlBytes = currNetData.bytes_recv - previous_network_data.bytes_recv         #compares the current bytes received to the previous
    ulBytes = currNetData.bytes_sent - previous_network_data.bytes_sent         #compares the current bytes sent to the previous

    

    download_mbps = dlBytes * 8 / 1_000_000 / elapsedTime            #calc the  current download and uplad speeds in mbps
    upload_mbps  = ulBytes * 8 / 1_000_000 / elapsedTime

    return currNetData,currTime,  download_mbps, upload_mbps 


def main():

    previous_network_data = psutil.net_io_counters()
    previous_time = time.perf_counter()

    while True:

        cpu_usage_percent = psutil.cpu_percent(interval=None)

        memory_data = psutil.virtual_memory()
        ram_usage_percent = memory_data.percent

        (
            currNetData,
            currTime,
            download_speed_mbps,
            upload_speed_mbps
        ) = get_network_speed(
            previous_network_data,
            previous_time
        )

        previous_network_data = currNetData
        previous_time = currTime

        print(
            f"CPU: {cpu_usage_percent:.1f}% | "
            f"RAM: {ram_usage_percent:.1f}% | "
            f"Download: {download_speed_mbps:.2f} Mbps | "
            f"Upload: {upload_speed_mbps:.2f} Mbps"
        )

        time.sleep(1)


if __name__ == "__main__":
    main()