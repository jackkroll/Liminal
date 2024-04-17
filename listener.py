from flask import Flask, request, send_file
import serial
app = Flask(__name__)
#git clone https://github.com/libre-computer-project/libretech-wiring-tool.git
#cd libretech-wiring-tool
#sudo make


#M486 - M486: Cancel Object

prusaBaudrate = 115200
#octoprint serial port = '/dev/ttyAML6'
mk4Printer = serial.Serial('/dev/ttyAML6', baudrate=115200, timeout=5)
mk4Printer.open()
mk4Printer.write("G28".encode())
response = mk4Printer.readline()
print(response.decode())
mk4Printer.close()