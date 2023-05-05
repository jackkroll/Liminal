import time

from octorest import OctoRest
import asyncio
import os

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

class SingelePrinter():
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
        Preheats to PLA's target temp
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
        self.printer.select(location= fileNamename, print= True)
        self.currentFile = file_contents
        self.user = uploader


    def abort(self):
        self.printer.cancel()
        #Used for implementing LED Methods + Sending notifications


myPrinter = SingelePrinter("josef", "http://prusaprinter.local", "572323F7CF4749F4BD2DCC610E443C0E")
myPrinter.printer.disconnect()
