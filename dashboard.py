import datetime
import json
import random
import time
import string

from flask import Flask, request, send_file, redirect, url_for
from firebase_admin import credentials, initialize_app, storage
from main import IndividualPrint,SinglePrinter, Liminal
import firebase_admin
from firebase_admin import credentials, firestore
import requests
app = Flask(__name__)
liminal = Liminal()


bucket = storage.bucket()
db = firestore.client()
prints_ref = db.collection('prints')
@app.route('/')
def index():
    file = open("values.json")
    jsonValues = json.load(file)
    file.close()

    file = open("config.json")
    config = json.load(file)
    file.close()
    body = "<html><body style = background-color:black>"
    body += """
    <head>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Inter">
    </head>
    <style>
    body {
  font-family: "Inter", sans-serif;
    }
    </style>
    """
    for printer in liminal.printers:
        if printer.printer != None and printer.code not in jsonValues["printersDown"]:
            body += f'<h1 style="color:coral;">{printer.nickname}</h1>'
            if config[printer.nickname]["camActive"]:
                body += f'<img src="{config[printer.nickname]["webcamURL"]}" alt="Video Stream">'
            if printer.fetchNozzleTemp() != None:
                body += f'<h3 style="color:white;">Nozzle: {printer.fetchNozzleTemp()["actual"]}</h3>'
            if printer.fetchBedTemp() != None:
                body += f'<h3 style="color:white;">Bed: {printer.fetchBedTemp()["actual"]}</h3>'
            body += f'{printer.state}'
            if "printing" in printer.state.lower():
                body += f'<h3 style="color:white;">Currently in use | {int(printer.fetchTimeRemaining()/60)} Minutes left</h3>'
                #Implement time remaining methods :)
            else:
                #Submission requrements:
                # printer : Printer Name ex. Left Printer
                # Gcode : The GCODE file
                # creator: The name of the uploader
                # material: The name of the filament, currently unused
                # printercode: unestablished right now, but is a needed input
                # nickname: The name of the print
                body += f"""
    <form style="color:white" action="{url_for('uploadPrintURL')}" method="post" enctype="multipart/form-data">
    <input type="hidden" name="printer" value="{printer.nickname}">
    <input type="hidden" name="printercode" value="{printer.code}">
    <input type="hidden" name="creator" placeholder="notSet">
    <input type="hidden" name="material" placeholder="notSet">
    <label for="url">GCODE File:</label>
    <input type="file" id="url" name="gcode" accept=".gcode">
    <label for="nickname">Print Name:</label>
    <input type="text" id="nickname" name="nickname" placeholder="nickname">
    <button type="submit">Upload</button></form>
                """


        body += "</body></html>"

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


                #printer.upload(individualPrint)
                #print(gcodeUpload)

                file_contents = request.files["gcode"].stream.read()
                print(request.files.get("gcode"))

                print(file_contents)
                if nickname == "":
                    nickname = "Untitled"
                printer.printer.upload(file=(nickname + ".gcode", file_contents), location="local", print=True)
                printer.printer.select(location=nickname + ".gcode", print=True)
                #Ensures a .00000000000000000000010661449% change of a UUID collision
                chars = list(string.ascii_lowercase + string.ascii_uppercase + string.digits)
                blobName = ""
                for i in range(0,15):
                    blobName += random.choice(chars)
                blob = bucket.blob(blobName)
                blob.upload_from_string(file_contents)
                blob.make_public()

                print(blob.public_url)
                fileURL = blob.public_url
                individualPrint = IndividualPrint(fileURL, user, material, printerCode, nickname)
                print("made it here")
                doc_ref = db.collection('prints').document(individualPrint.uuid)
                print("made it further")
                doc_ref.set({
                    'gcode': individualPrint.file,
                    'creator': individualPrint.creator,
                    'material': individualPrint.material,
                    'printerCode': individualPrint.printerCode,
                    'nickname': individualPrint.nickname,
                    'uuid': individualPrint.uuid
                })
                print("made it all the way")
                return "Success!"
@app.route('/dev/online',methods = ["GET", "POST"])
def setPrinterOnline():
    if request.method == "GET":
        return redirect(url_for("setPrinterStatus"))
    else:
        with open("values.json", "r") as f:
            setOnline = request.form.get("printer")
            jsonValues = json.load(f)
            jsonValues["printersDown"].remove(setOnline)
        with open("values.json", "w") as f:
            json.dump(jsonValues,f,indent=4)
        return redirect(url_for("setPrinterStatus"))

@app.route('/dev/offline',methods = ["GET", "POST"])
def setPrinterOffline():
    if request.method == "GET":
        return redirect(url_for("setPrinterStatus"))
    else:
        with open("values.json", "r") as f:
            setOnline = request.form.get("printer")
            jsonValues = json.load(f)
            jsonValues["printersDown"].append(setOnline)
        with open("values.json", "w") as f:
            json.dump(jsonValues, f, indent=4)
        return redirect(url_for("setPrinterStatus"))
@app.route('/dev',methods = ["GET"])
def setPrinterStatus():
    file = open("values.json")
    jsonValues = json.load(file)
    file.close()
    if request.method == "GET":
        body = "<html><body style = background-color:black>"
        body += """
                    <head>
                    <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Inter">
                    </head>
                    <style>
                    body {
                  font-family: "Inter", sans-serif;
                    }
                    </style>
                    """
        body += '<h1 style="color:coral"> Currently Online </h1>'
        for printer in liminal.printers:
            if printer.code not in jsonValues["printersDown"]:
                body += f'<h3 style="color:white"> {printer.nickname} </h3>'
                body += f"""
                        <form style="color:white" action="{url_for('setPrinterOffline')}" method="post", enctype="multipart/form-data">
                        <input type="hidden" name="printer" value="{printer.code}">
                        <button type="submit">Switch Offline</button>
                        </form>
                        """
        body += '<h1 style="color:coral"> Currently Offline </h1>'
        for printer in liminal.printers:
            if printer.code in jsonValues["printersDown"]:
                body += f'<h3 style="color:white"> {printer.nickname} </h3>'
                body += f"""
                    <form style="color:white" action="{url_for('setPrinterOnline')}" method="post" enctype="multipart/form-data">
                    <input type="hidden" name="printer" value="{printer.code}">
                    <button type="submit">Switch Online</button>
                    </form>
                                """
        return body
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port= 8000)
