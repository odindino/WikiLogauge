import json
import serial.tools.list_ports
import time
import threading
import webview


class Api:
    def __init__(self):
        # self.keithley = Keithley2400()

        return

    def get_ports(self):
        print("get_com_list")
        port_list = list(serial.tools.list_ports.comports())
        com_list = [port[0] for port in port_list]
        print(f"Available COM ports: {com_list}")
        return com_list

    def connect(self, port):
        print(f"Connecting to port: {port}")

    def disconnect(self):

        return

    def start_measurement(self):

        return

    def pause_measurement(self):

        return

    def stop_measurement(self):

        return


if __name__ == '__main__':
    api = Api()

    t = threading.Thread(target=api.measure_current)
    t.daemon = True
    t.start()

# set the size of the window to 1020x680
    window = webview.create_window(
        'Keithley 2400 Control', url="http://localhost:5173/", js_api=api, width=1020, height=720)
    webview.start(debug=True)
