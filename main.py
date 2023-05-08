import time, asyncio, os, pytimeparse, datetime
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

    def abort(self):
        self.printer.cancel()
        #Used for implementing LED Methods + Sending notifications

#class PrintUpload():
 #   def __init__(self, gcode, uploader):
  #      self.gcode = gcode
   #     self.uploader = uploader
def parseGCODE(filepath):
    file = open(filepath, "r")
    file_contents = file.read()
    file_contents = file_contents.split(";")
    printTime = [item for item in file_contents if item.startswith(" estimated printing time (normal mode)")][0]
    #Above, getting the print time from the GCODE. Below, parsing the string to extract the timing
    printTime = printTime.strip(" estimated printing time (normal mode) = ")
    printTime = printTime.strip("\n")
    timeInSec = pytimeparse.parse(printTime)
    timeDelta = timedelta(seconds= timeInSec)
    print(datetime.now() + timeDelta)
#Left Printer,http://10.110.8.77 ,FCDAE0344C424542B80117AF896B62F6
#Right Printer,http://10.110.8.100 ,33A782146A5A48A7B3B9873217BD19AC

#(self, nickname, url, key
printers = [SinglePrinter("left", "http://10.110.8.77", "FCDAE0344C424542B80117AF896B62F6"),SinglePrinter("right", "http://10.110.8.100", "33A782146A5A48A7B3B9873217BD19AC")]
for printer in printers:
    printer.printer.jog(x = 10)

#myPrinter = SinglePrinter("josef", "http://prusaprinter.local", "572323F7CF4749F4BD2DCC610E443C0E")
#myPrinter.printer.disconnect()


