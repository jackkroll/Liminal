from flask import Flask, request, send_file
import serial
import time, os
import serial.tools.list_ports
app = Flask(__name__)
#git clone https://github.com/libre-computer-project/libretech-wiring-tool.git
#cd libretech-wiring-tool
#sudo make


#M486 - M486: Cancel Object

prusaBaudrate = 115200
ports = serial.tools.list_ports.comports()
for port in ports:
    if "prusa" in port.description.lower():
        mk4PortStr = port

#octoprint serial port = '/dev/ttyAML6'
#mk4Printer = serial.Serial(mk4PortStr.name, baudrate=115200, timeout=5)


class SerialPrinter():
    def __init__(self, portName):
        self.port = portName
        self.serial = serial.Serial(self.port.name, baudrate=115200, timeout=5)
        self.currentPrintObjects = []
        try:
            self.serial.open()
        except Exception:
            print("[NOTICE] Port already open")
            pass
        time.sleep(10)
        print(self.serial.read(256).decode())

    def cmd(self, command):
        self.serial.write(f"{command}\r\n".encode())
        print(self.serial.readline().decode())
    def preheatNozzle(self, type = "both"):
        if type != "bed":
            #Nozzle Temperature
            self.cmd("M104 S215")
        if type != "nozzle":
            #Bed Temperature
            self.cmd("M140 S60")


    def cooldown(self, type = "both"):
        if type != "bed":
            self.cmd("M104 S0")
        if type != "nozzle":
            self.cmd("M140 S0")
    def returnHome(self):
        self.cmd("G28 W")
    def abort(self):
        self.cmd("M112")

printer = SerialPrinter(mk4PortStr)