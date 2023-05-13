import time, asyncio, os, pytimeparse, datetime, requests, random
from datetime import datetime, timedelta
from octorest import OctoRest


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

class SinglePrinter():
    """"
    This creates a basic printer class with additional information
    """
    def __init__(self, nickname, url, key):
        self.nickname = nickname
        self.url = url
        self.key = key
       #self.color = color
        self.printer = make_client(url = url, apikey= key)
        self.printer.connect()
        #self.printer.home()
        self.user = None
        self.currentFile = None


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
    def upload(self, link, fileName : str, uploader):
        """
        Only useful for testing. Will not work/will be useless in full implementation
        """

        file_contents = requests.get(link).text
        print(file_contents)
        self.printer.upload(file = (fileName + ".gcode", file_contents), location= "local",print= True)
        time.sleep(1)
        self.printer.select(location= fileName + ".gcode", print= True)
        self.currentFile = file_contents
        self.user = uploader

    def abort(self):
        self.printer.cancel()
        #Used for implementing LED Methods + Sending notifications
    def fetchNozzleTemp(self):
        return self.printer.tool(history = True, limit = 1)["tool0"]
    def fetchBedTemp(self):
        return self.printer.bed(history = True, limit = 1)["bed"]

#class PrintUpload():
 #   def __init__(self, gcode, uploader):
  #      self.gcode = gcode
   #     self.uploader = uploader
class IndividualPrint():
    def __init__(self, file, creator, material, printerCode):
        self.file = file
        self.creator = creator
        self.material = material
        gcodeData = parseGCODE(file)[1]
        self.timeToPrint = gcodeData[1]
        self.nozzle = gcodeData[0]
        self.printerCode = printerCode.upper()
        #Add implementation to check UUID to ensure it isn't the 0.007% chance they're the same
        uuid = ""
        letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'j', 'k', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
         'w', 'x', 'y', 'z']
        for i in range(3):
            uuid += random.choice(letters).upper()
        self.uuid = printerCode.upper() + uuid
class Liminal():

    def __init__(self):
        self.printers = [
            SinglePrinter("Left", "http://10.110.8.77", "FCDAE0344C424542B80117AF896B62F6"),
            SinglePrinter("Middle", "http://10.110.8.110","6273C0628B8B47E397CA4554C94F6CD5"),
            SinglePrinter("Right", "http://10.110.8.100", "33A782146A5A48A7B3B9873217BD19AC")]
        self.state = "idle"
        #State Map
        #Idle: All printers are OK, nothing printing
        #Printing: One or more printers are ongoing, printers OK
        #Error: The printers detected an issue, no connection or other
        #Stop: All printers have been immediately e-stopped
        self.optimizeDuring= (datetime.time(hour=18), datetime.time(hour=21))
        self.queue = []

    def estop(self):
        for printer in self.printers:
            printer.abort()
        #Implement methods for display & mobile notifications to dispatch
    def addToQueue(self, optimize : bool, position : int, gcode):
        currentTime = datetime.now().time()


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
    file = requests.get(link).text
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
#Left Printer,http://10.110.8.77 ,FCDAE0344C424542B80117AF896B62F6
#Middle Printer, http://10.110.8.110, 6273C0628B8B47E397CA4554C94F6CD5
#Right Printer,http://10.110.8.100 ,33A782146A5A48A7B3B9873217BD19AC

#spencer = SinglePrinter("Middle", "http://10.110.8.110","6273C0628B8B47E397CA4554C94F6CD5")
#spencer.printer.jog(x=5)

#myPrinter.printer.disconnect()


