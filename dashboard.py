import time

from flask import Flask, request, send_file, redirect, url_for
from firebase_admin import credentials, initialize_app, storage
from main import IndividualPrint,SinglePrinter, Liminal
import requests
app = Flask(__name__)
#Left Printer,http://10.110.8.77 ,FCDAE0344C424542B80117AF896B62F6
#Middle Printer, http://10.110.8.110, 6273C0628B8B47E397CA4554C94F6CD5
#Right Printer,http://10.110.8.100 ,33A782146A5A48A7B3B9873217BD19AC
#printers = [SinglePrinter("Left Printer", "http://10.110.8.77","FCDAE0344C424542B80117AF896B62F6"),SinglePrinter("Middle Printer", "http://10.110.8.110","6273C0628B8B47E397CA4554C94F6CD5"),SinglePrinter("Right Printer", "http://10.110.8.100","33A782146A5A48A7B3B9873217BD19AC")]
liminal = Liminal()
@app.route('/')
def index():
    body = "<html><body>"
    for printer in liminal.printers:
        body += f"<h1>{printer.nickname}</h1>"
        body += f"<h3>Nozzle: {printer.fetchNozzleTemp()['actual']}</h3>"
        body += f"<h3>Bed: {printer.fetchBedTemp()['actual']}</h3>"
        if printer.currentFile != None:
            body += f"<h3>Currently in use by {printer.user}</h3>"
            #Implement time remaining methods :)
        else:
            #Submission requrements:
            # printer : Printer Name ex. Left Printer
            # Gcode : The GCODE file
            # creator: The name of the uploader
            # material: The name of the filament, currently unused
            # printercode: unestablished right now, but is a needed input
            # nickname: The name of the print
            body += f"<h3>Upload your print!</h3>"
            body += f"""
<form action="{url_for('uploadPrintURL')}" method="post", enctype="multipart/form-data">
<input type="hidden" name="printer" value="{printer.nickname}">
<input type="hidden" name="printercode" placeholder="{printer.nickname}">
<label for="url">GCODE File:</label>
<input type="file" id="url" name="gcode" accept=".gcode">
<label for="nickname">Print Name:</label>
<input type="text" id="nickname" name="nickname" placeholder="nickname">
<button type="submit">Upload</button>
            """
            #Add upload form here


    body += "</html></body>"

    return body

@app.route('/heat', methods = ["GET", "POST"])
#This defines the webpage that will allow you to preheat printers
#You can pass ALL to preheat all of them, and an individual name to preheat that one
def functions():
    if request.method == "GET":
        return "You aren't supposed to be here you silly goose"
    else:
        #Implement API Key validation to ensure legitimate requests
        if request.form.get("preheat") == "all":
            for printer in liminal.printers:
                printer.preheat()
        else:
            for printer in liminal.printers:
                if request.form.get("preheat") == printer.nickname:
                    printer.preheat()
@app.route('/print', methods = ["GET", "POST"])
#Form components nessesary:
#printer : Printer Name ex. Left Printer
#url : The GCODE URL (from firebase)
#creator: The name of the uploader
#material: The name of the filament, currently unused
#printercode: unestablished right now, but is a needed input
#nickname: The name of the print
def uploadPrintURL():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        for printer in liminal.printers:
            if request.form.get("printer") == printer.nickname:
                # Indivdual Print requirements: file (URL String), creator, material, printerCode, nickname
                gcodeUpload = request.form.get("gcode")
                user = request.form.get("creator")
                material = request.form.get("material")
                printerCode = request.form.get("printercode")
                nickname = request.form.get("nickname")
                #fileURL = Set this to a firebase upload
                fileURL = None
                #individualPrint = IndividualPrint(fileURL, user, material, printerCode, nickname)
                #printer.upload(individualPrint)
                #print(gcodeUpload)
                for file in request.files:
                    print(file)
                file_contents = request.files["gcode"].stream.read()
                if nickname == "":
                    nickname = "Untitled"
                printer.printer.upload(file=(nickname + ".gcode", file_contents), location="local", print=True)
                printer.printer.select(location=nickname + ".gcode", print=True)
                return "Success!"

if __name__ == '__main__':
    app.run(debug=True, host="localhost", port= 8000)