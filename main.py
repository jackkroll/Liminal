import time, asyncio, os, pytimeparse, datetime, requests, random, math,json, socket, sys, cv2, serial
from datetime import datetime, timedelta
from octorest import OctoRest
from firebase_admin import credentials, initialize_app, storage, firestore
import firebase_admin
from firebase_admin import credentials
import netifaces as ni
import cv2
import numpy as np

if sys.platform == "win32":
    cwd = "C:/Users/jackk/PycharmProjects/Liminal"
else:
    cwd = "/home/jack/Documents/Liminal-master"
try:
    cred = credentials.Certificate(f"{cwd}/ref/liminal-302-749fb908ba9b.json")
    firebase_admin.initialize_app(cred,{'storageBucket': 'liminal-302.appspot.com'})
    db = firestore.client()
    prints_ref = db.collection('prints')
    bucket = storage.bucket()
except Exception as e:
    print("[ERROR] Cannot properly connect to firebase")
def make_client(url, apikey):
    """Creates and returns an instance of the OctoRest client.

    Args:
        url - the url to the OctoPrint server
        apikey - the apikey from the OctoPrint server found in settings
    """
    try:
        client = OctoRest(url=url, apikey=apikey)
        return client
    except ConnectionError as ex:
        # Handle exception as you wish
        print(ex)
class IndividualPrint():
    def __init__(self, file, creator, material, printerCode, nickname):
        self.file = file
        self.creator = creator
        self.material = material
        #gcodeData = parseGCODE(file)[1]
        #TIME TO PRINT IS IN
        #self.timeToPrint = gcodeData[1]
        #self.nozzle = gcodeData[0]
        self.printerCode = printerCode.upper()
        self.nickname = nickname
        #Add implementation to check UUID to ensure it isn't the 0.007% chance they're the same
        passed_check = False
        while not passed_check:
            uuid = printerCode
            letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'j', 'k', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
             'w', 'x', 'y', 'z']
            for i in range(3):
                uuid += random.choice(letters).upper()

            current_year = datetime.now().year
            two_letter_year = str(current_year)[2:]
            uuid += two_letter_year
            query_ref = prints_ref.where('uuid', '==', uuid)

            if len(query_ref.get()) == 0:
                passed_check = True
            else:
                print(query_ref.count)

        self.uuid = uuid




class Mk4Printer():
    def __init__(self, nickname, ipAddress, apiKey, prefix, portStr = None):
        self.type = "MK4"
        self.nozzleTemp = None
        self.bedTemp = None
        self.state = None
        self.currentPrintID = None
        self.progress = None
        self.ip = ipAddress
        self.portStr = portStr
        self.key = apiKey
        self.prefix = prefix
        self.nickname = nickname
        self.transfer = None
        if self.portStr != None:
            try:
                self.serial = serial.Serial(self.portStr, baudrate=115200, timeout=5)
                try:
                    self.serial.open()
                except Exception:
                    print(f"[NOTICE] Serial port could not be opened, possibly already open")
                time.sleep(10)
                print(f"[SERIAL STARTUP ON {self.nickname.upper()}]\n{self.serial.read(256).decode()}")
            except Exception:
                self.serial = None
                print(f"[ERROR] Serial could not be configured for {self.nickname} on port {self.portStr}")
        else:
            print(f"[NOTICE] Serial could not be configured on {self.nickname} due to no port being assigned")

    def cmd(self, command):
        self.serial.write(f"{command}\r\n".encode())
        print(f"[SERIAL DEBUG]{self.serial.readline().decode()}")
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
        if serial != None:
            self.cmd("M112")
        else:
            self.stop()

    def refreshData(self):
        headers = {"X-API-KEY": self.key}
        response = requests.get(f"http://{self.ip}/api/v1/status", headers=headers)
        data = response.json()
        self.nozzleTemp = data["printer"]["temp_nozzle"]
        self.bedTemp = data["printer"]["temp_bed"]
        self.state = data["printer"]["state"]
        if "job" in data:
            self.currentPrintID = data["job"]["id"]
            self.progress = data["job"]["progress"]
        else:
            self.currentPrintID = None
            self.progress = None
        if "transfer" in data and "progress" in data["transfer"]:
            self.transfer = data["transfer"]["progress"]
        else:
            self.transfer = None
        print(response.json())
    def checkUpdate(self):
        headers = {"X-API-KEY": self.key}
        returnDict = []
        response = requests.get(f"http://{self.ip}/api/v1/update/prusalink", headers=headers)
        print(f"[DEBUG] Mk4 PrusaLink update request responded: {response.content} with code {response.status_code}")
        if response.status_code == 200:
            returnDict.append(response.content)
        else:
            returnDict.append(None)
        response = requests.get(f"http://{self.ip}/api/v1/update/system", headers=headers)
        print(f"[DEBUG] Mk4 system update request responded: {response.content} with code {response.status_code}")
        if response.status_code == 200:
            returnDict.append(response.content)
        else:
            returnDict.append(None)
        return returnDict

    def pushUpdate(self, type):
        headers = {"X-API-KEY": self.key}
        if type not in ["system", "prusalink"]:
            return False
        response = requests.post(f"http://{self.ip}/api/v1/update/{type}", headers=headers)
        return response


    def fetchNozzleTemp(self):
        self.refreshData()
        return self.nozzleTemp
    def fetchBedTemp(self):
        self.refreshData()
        return self.bedTemp
    def upload(self, fileTxt, nickname, bGcode = False):
        storage = "usb"
        if bGcode:
            path = f"{nickname}.bgcode"
        else:
            path = f"{nickname}.gcode"
        uploadLength = len(fileTxt)
        # ?0 = False, ?1 = True
        headers = {"X-API-KEY": self.key, "Content-Length": str(uploadLength), "Print-After-Upload": "?1",
                   "Overwrite": "?0", "Accept-Language": "en-US", "Accept": "application/json"}
        response = requests.put(f"http://{self.ip}/api/v1/files/{storage}/{path}", headers=headers, data=fileTxt)
        #print(response.text)
        return True
    def transferStatus(self):
        self.refreshData()
        return self.transfer
    def stop(self):
        self.refreshData()
        headers = {"X-API-KEY": self.key}
        response = requests.delete(f"http://{self.ip}/api/v1/job/{self.currentPrintID}", headers=headers)

    def pause(self):
        self.refreshData()
        headers = {"X-API-KEY": self.key}
        response = requests.put(f"http://{self.ip}/api/v1/job/{self.currentPrintID}/pause", headers=headers)

    def resume(self):
        self.refreshData()
        headers = {"X-API-KEY": self.key}
        response = requests.put(f"http://{self.ip}/api/v1/job/{self.currentPrintID}/resume", headers=headers)
    def state(self):
        self.refreshData()
        return self.state


class SinglePrinter():
    """"
    This creates a basic printer class with additional information
    """
    def __init__(self, nickname, url, key, code):
        self.type = "MK3"
        self.nickname = nickname
        self.code = code
        self.url = url
        self.key = key
        self.state = None
        #Idle, Printing, Offline
       #self.color = color
        try:
            self.printer = make_client(url = url, apikey= key)
            self.printer.connect()
            #ipAddr = socket.gethostbyname(socket.gethostname())
            #self.printer.gcode(f"M117 {ipAddr}")
        except Exception:
            self.printer = None
        #self.printer.home()
        self.user = None
        self.currentFile = None
        if self.printer != None:
            self.state = self.printer.state()

        else:
            self.state = "offline"
        #operational
        #paused
        #printing
        #pausing
        #cancelling
        #sdReady means the printer’s SD card is available and initialized
        #error
        #ready
        #closedOrError means the printer is disconnected (possibly due to an error)
        self.queue = []

    def pause(self):
        self.printer.pause()
        return True
    def resume(self):
        self.printer.resume()
        return True
    def updateState(self):
        state = self.printer.state
        self.state = state
        return state

    def preheat(self):
        """
        Preheats to PLAs target temp
        """
        self.printer.bed_target(60)
        self.printer.tool_target(210)
    def cooldown(self):
        """
        Cools down the printer
        """
        self.printer.bed_target(0)
        self.printer.tool_target(0)

    def uploadLocal(self, filepath, fileName : str, uploader):
        """
        Only useful for testing. Will not work/will be useless in full implementation
        """
        file = open(filepath, "rb")
        file_contents = file.read()
        self.printer.upload(file = (fileName, file_contents), location= "local",print= True)
        self.printer.select(location= fileName, print= True)
        self.currentFile = file_contents
        self.user = uploader

    def displayMSG(self, message):
        """
        Allows you to display text onto the printer
        """
        if self.printer != None:
            self.printer.gcode(f"M117 {message}")

        
    def upload(self, print : IndividualPrint):
        """
        Uploads using a IndividualPrint Object
        """

        file_contents = requests.get(print.file).text
        self.printer.upload(file = (print.nickname + ".gcode", file_contents), location= "local",print= True)
        time.sleep(1)
        self.printer.select(location= print.nickname + ".gcode", print= True)
        self.currentFile = file_contents
        self.user = print.creator

    def abort(self):
        self.printer.cancel()
        #Used for implementing LED Methods + Sending notifications
    def fetchNozzleTemp(self):
        return self.printer.tool(history = True, limit = 1)["tool0"]
    def fetchBedTemp(self):
        return self.printer.bed(history = True, limit = 1)["bed"]
    def fetchTimeRemaining(self):
        '''
        Returns time remaining in seconds
        '''
        if self.printer.job_info()["progress"]["printTimeLeft"] != None:
            return self.printer.job_info()["progress"]["printTimeLeft"]
        else:
            return -60

    def scheduler(self, gcode: IndividualPrint, requestedTime):
        times = []
        gaps = []
        for print in self.queue:
            times.append(print.estimatedStartTime)
            times.append(print.estimatedEndTime)
        times.pop(0)
        times.pop(-1)
        for item in range(0, len(times), 2):
            gaps += (times[item], times[item + 1], times[item + 1] - times [item])
            #Appends a tuple containing the gaps start, and the gaps end, and a timedelta object of the time between


    def addToQueueOld(self, gcode: IndividualPrint):
        officeHours = [(datetime.time(hour= 18), datetime.time(hour= 21))]

        info = self.printer.job_info()
        startTime = datetime.now()
        nextAvilableStart = 0
        printTime = gcode.timeToPrint
        if info["state"] == "Printing":
            remaining = info["progress"]["printTimeLeft"]
            remaining += (10 * 60) #Adds to minute buffer in seconds
            nextAvilableStart += remaining
        startTime += datetime.timedelta(seconds=nextAvilableStart)
        for set in officeHours:
            if datetime.time > set[0] and datetime < set[1] and startTime >= set[1]:
                print("yuh")
        #If we're within this set off office hours and the current print will end outside of them

        #Gap optimization algorithm
        for singlePrint in self.queue:
            #Calculating the timedelta between the requested print time and the current estimated next avilable start time
            #If that gap is greater than the time to print, slot that print in.
            if (singlePrint.estimatedStartTime - startTime) > gcode.timeToPrint:
                self.queue.insert(self.queue.index(singlePrint), gcode)
                #Setting the object it's estimated start time
                gcode.estimatedStartTime = startTime
                break



#class PrintUpload():
 #   def __init__(self, gcode, uploader):
  #      self.gcode = gcode
   #     self.uploader = uploader

class Camera():
    def __init__(self, cameraNumber, cameraIndex):
        self.printer = None
        self.buffer = []
        self.timelapse = []
        self.frameRate = 24
        self.rollingTime = 30
        self.resolution = None
        self.camera = cv2.VideoCapture(cameraIndex)
        self.index = cameraIndex
        self.cameraNumber = cameraNumber

    def stream(self):
        while True:
            if len(self.buffer) > 0:
                yield (b'--frame\r\n'
                                       b'Content-Type: image/jpeg\r\n\r\n' + self.buffer[-1] + b'\r\n')
            else:
                yield ("None")

    def timelapseLogger(self):
        while True:
            if self.printer != None and len(self.buffer)>0:
                if ((self.printer.type == "MK3" and "printing" in self.printer.printer.state().lower()) or (self.printer.type == "MK4" and "printing" in self.printer.state().lower())) and ((self.printer.type == "MK3" and self.printer.fetchNozzleTemp()["actual"] >= 200) or (self.printer.type == "MK4" and self.printer.fetchNozzleTemp() >= 200)):
                    self.timelapse.append(self.buffer[-1])
                    time.sleep(60)
                elif len(self.timelapse) > 0:
                    resolution = cv2.imdecode(np.frombuffer(self.buffer[-1], np.uint8), cv2.IMREAD_COLOR).shape
                    result = cv2.VideoWriter(f"{cwd}/Clip.mp4", cv2.VideoWriter_fourcc(*'mp4v'), 10,
                                             (resolution[1], resolution[0]))
                    for frame in self.timelapse:
                        result.write(cv2.imdecode(np.frombuffer(frame, np.uint8), cv2.IMREAD_COLOR))
                    result.release()

                    self.timelapse = []
                else:
                    time.sleep(120)
            elif len(self.buffer) == 0:
                time.sleep(10)
            else:
                time.sleep(300)
    def backgroundLogger(self):
        retrys = 0
        while True:
            success, frame = self.camera.read()
            if not success:
                print("[ERROR] Issue reading data from camera, attempting to reinit...")
                self.camera.release()
                self.camera = cv2.VideoCapture(self.index)
                retrys+=1
                if retrys <= 5:
                    time.sleep(5)
                elif retrys <= 10:
                    time.sleep(15)
                elif retrys <= 20:
                    time.sleep(60)
                elif retrys <= 50:
                    time.sleep(300)
            else:
                ret, buffer = cv2.imencode('.jpg', frame)
                if self.resolution == None:
                    try:
                        self.resolution = (frame.shape[1],frame.shape[0])
                    except Exception:
                        print("[WARNING] Resolution unable to be set, defaulted to 680x480")
                        self.resolution = (680,480)
                frame = buffer.tobytes()
                self.buffer.append(frame)
                if len(self.buffer) >= (self.frameRate * self.rollingTime):
                    for number in range(0, len(self.buffer) - (self.frameRate * self.rollingTime)):
                        del self.buffer[:number]
                time.sleep(1/self.frameRate)

class Liminal():

    def __init__(self):
        self.config = json.load(open(f"{cwd}/ref/config.json"))
        self.printers = []
        self.MK4Printers = []
        self.accounts = list(self.config["students"].keys())
        self.cameras = []
        initalized = -1
        for i in range (10):
            initalized+=1
            self.cameras.append(Camera(initalized, i))
            if not self.cameras[-1].camera.read()[0]:
                initalized -= 1
                self.cameras.pop()
                print(f"Camera on port {i} unreachable")
            else:
                print(f"Camera Initalized on port {i}")
        for item in self.config:
            if "ipAddress" in self.config[item]:
                tempPrinter = SinglePrinter(item, self.config[item]["ipAddress"], self.config[item]["apiKey"], self.config[item]["prefix"])
                req = requests.get(f"{tempPrinter.url}/api/printer", headers={f"X-API-KEY": f"{tempPrinter.key}"})
                if not req.ok:
                    print("[ERROR] Printer is not operational as reported by Octoprint")
                if tempPrinter.printer.printer()["state"]["flags"]["operational"]:
                    print("[OPERATIONAL] Mk3 Printer has been successfully added")
                    self.printers.append(tempPrinter)
                    for camera in self.cameras:
                        try:
                            if camera.index == int(self.config[item]["cameraIndex"]):
                                camera.printer = tempPrinter
                                print("Camera Matched with Printer")
                        except:
                            print("[NOTICE] Camera config not added for printer")
                else:
                    print("[ERROR] Printer is offline and cannot be added to LMNL")
                    print(f'[DEBUG] {tempPrinter.printer.printer()["state"]["flags"]}')


        for item in self.config:
            if "Mk4IPAddress" in self.config[item]:
                #nickname, ipAddress, apiKey, prefix
                print("[OPERATIONAL] Mk4 Printer has been successfully added")
                self.MK4Printers.append(Mk4Printer(item, self.config[item]["Mk4IPAddress"], self.config[item]["apiKey"], self.config[item]["prefix"]))
                for camera in self.cameras:
                    try:
                        if camera.index == int(self.config[item]["cameraIndex"]):
                            camera.printer = self.MK4Printers[-1]
                            print("[OPERATIONAL] Camera matched with Mk4 Printer")
                    except:
                        print("[NOTICE] Camera config not added for printer")
        self.state = "idle"
        self.estimatedBufferTime = 10
        self.approvalCode = "null"
        self.lastGenerated = None
        try:
            self.ipAddress = ni.ifaddresses('eth0')[ni.AF_INET][0]['addr']
        except ValueError:
            self.ipAddress = socket.gethostbyname(socket.gethostname())
        except Exception:
            self.ipAddress = None
            print("[ERROR] IP Address unreachable")
        print(f"[INFO] The system IP address is: {self.ipAddress}")
        for printer in self.printers:
            printer.displayMSG(f"LMNL: {self.ipAddress}")




        #State Map
        #Idle: All printers are OK, nothing printing
        #Printing: One or more printers are ongoing, printers OK
        #Error: The printers detected an issue, no connection or other
        #Stop: All printers have been immediately e-stopped
        #self.officeHours = [(datetime.hour(hour=18), datetime.time(hour=21))]
    def genNewApprovalCode(self):

        uuid = ""
        letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'j', 'k', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v','w', 'x', 'y', 'z']
        for i in range(4):
            uuid += random.choice(letters).upper()
        self.approvalCode = uuid
        self.lastGenerated = datetime.now()
        print(uuid)

    def estop(self):
        for printer in self.printers:
            printer.abort()
        for printer in self.MK4Printers:
            printer.abort()
        #Implement methods for display & mobile notifications to dispatch





def parseGCODELocal(filepath):
    file = open(filepath, "r")
    file_contents = file.read()
    file_contents = file_contents.split(";")
    printTime = [item for item in file_contents if item.startswith(" estimated printing time (normal mode)")][0]
    #Above, getting the print time from the GCODE. Below, parsing the string to extract the timing
    printTime = printTime.strip(" estimated printing time (normal mode) = ")
    printTime = printTime.strip("\n")
    timeInSec = pytimeparse.parse(printTime)
    timeDelta = timedelta(seconds= timeInSec)
    #Below, getting nozzle diameter for print
    nozzleDiameter = [item for item in file_contents if item.startswith(" nozzle_diameter = ")][0]
    nozzleDiameter = nozzleDiameter.strip(" nozzle_diameter = ")
    nozzleDiameter = nozzleDiameter.strip("\n")

    return [nozzleDiameter, timedelta.seconds]
def parseGCODE(link):
    try:
        file = requests.get(link).text
        file_contents = file
        file_contents = file_contents.split(";")
        printTime = [item for item in file_contents if item.startswith(" estimated printing time (normal mode)")][0]
        #Above, getting the print time from the GCODE. Below, parsing the string to extract the timing
        printTime = printTime.strip(" estimated printing time (normal mode) = ")
        printTime = printTime.strip("\n")
        timeInSec = pytimeparse.parse(printTime)
        timeDelta = timedelta(seconds= timeInSec)
        #Below, getting nozzle diameter for print
        nozzleDiameter = [item for item in file_contents if item.startswith(" nozzle_diameter = ")][0]
        nozzleDiameter = nozzleDiameter.strip(" nozzle_diameter = ")
        nozzleDiameter = nozzleDiameter.strip("\n")

        return [nozzleDiameter, timedelta.seconds]
    except:
        return None