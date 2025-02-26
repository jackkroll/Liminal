import datetime,json,random,time,string,os,sys, threading, cv2, requests

#from google.type.datetime_pb2 import DateTime
#from pyasn1.debug import Printer

import main
#from crypt import methods
from threading import Thread

from flask import Flask, request, send_file, redirect, url_for, Response, render_template, jsonify
from jinja2.filters import FILTERS
from firebase_admin import credentials, initialize_app, storage
from main import IndividualPrint,SinglePrinter, Liminal,PrintLater
import firebase_admin
from firebase_admin import credentials, firestore
import numpy as np
from datetime import datetime
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

from webpage import printers

app = Flask(__name__)
def remove_spaces(input:str) -> str:
    return input.replace(" ","")
FILTERS["remove_spaces"] = remove_spaces
def filter_list(input:list[PrintLater], printer: SinglePrinter) -> list[PrintLater]:
    newList = []
    for job in input:
        if job.printer == printer:
            newList.append(job)
    return newList
FILTERS["filter_list"] = filter_list


#autoUpdateTest2
auth = HTTPBasicAuth()


if sys.platform == "win32":
    cwd = "C:/Users/jackk/PycharmProjects/Liminal"
elif sys.platform == "darwin":
    cwd = "/Users/jackkroll/PycharmProjects/Liminal"
else:
    cwd = "/home/jack/Documents/Liminal-master"
if os.path.exists(f"{cwd}/ref/config.json"):
    liminal = Liminal()
    configExists = True
else:
    configExists = False



@auth.verify_password
def verify_password(username, password):
    if not configExists:
        return username
    try:
        file = open((f"{cwd}/ref/config.json"))
    except FileNotFoundError:
        return username
    jsonValues = json.load(file)
    file.close()
    try:
        users = jsonValues["students"]
    except KeyError:
        users = None
        return "team302"
    usernameLower = username.lower()
    if username == "team302":
        return username
    if users != None and username.capitalize() in users:
        if users[usernameLower.capitalize()]["hash"] == "rat":
            return username
        if users[usernameLower.capitalize()]["hash"] == None:
            with open(f"{cwd}/ref/config.json", "r") as f:
                jsonValues = json.load(f)
                if username in jsonValues["students"]:
                    jsonValues["students"][username]["hash"] = generate_password_hash(password)
            with open(f"{cwd}/ref/config.json", "w") as f:
                json.dump(jsonValues, f, indent=4)
            return username
        if check_password_hash(users[usernameLower.capitalize()]["hash"], password):
            return username
    else:
        print(username.capitalize())

@auth.get_user_roles
def get_user_roles(username):
    if username == "team302":
        return "developer"
    try:
        file = open((f"{cwd}/ref/config.json"))
    except Exception:
        return "developer"
    jsonValues = json.load(file)
    file.close()
    if "students" not in jsonValues:
        return "developer"
    users = jsonValues["students"]
    username = username.lower()
    if username.capitalize() in users:
        return users[username.capitalize()]["role"]
    else:
        return "restricted"

try:
    bucket = storage.bucket()
    db = firestore.client()
    prints_ref = db.collection('prints')
    firebase = True
except Exception:
    firebase = False




#CWD, current working directory, is the directory that the file is in
@app.route('/')
@auth.login_required()
def index():
    if not configExists:
        return redirect(url_for("setupLandingPage"))
    if request.args.get("later") == "true":
        printLaterEnabled = True
    else:
        printLaterEnabled = False
    addedPrinters = 0
    file =open((f"{cwd}/ref/config.json"))
    jsonValues = json.load(file)
    if "printersDown" not in jsonValues.keys():
        jsonValues["printersDown"] = []
    file.close()
    if "students" not in jsonValues.keys():
        return redirect(url_for("setupLandingPage"))
    configuredPrinters = 0
    for value in jsonValues:
        if "ipAddress" in jsonValues[value] or "Mk4IPAddress" in jsonValues[value]:
            configuredPrinters += 1
    if configuredPrinters == 0:
        return redirect(url_for("setupLandingPage"))

    for printer in liminal.printers + liminal.MK4Printers:
        printer.refreshData()
    for printer in liminal.printers:
        if printer.printer == None:
            liminal.printers.remove(printer)
    return render_template("dashboard.html", printers=liminal.printers, mk4_printers = liminal.MK4Printers, currentUser = auth.current_user(), role = get_user_roles(auth.current_user()), notifications = liminal.notifications, queue=liminal.scheduledPrints)

    body = "<html><body style = background-color:#1f1f1f>"
    body += f'''
    <head>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Inter">
    </head>
    <style>
    body {{
  font-family: "Inter", sans-serif;
    }}
    .button{{
    background-color:{liminal.systemColor};
    color:white;
    padding:10px;
    border-radius:15px;
    text-decoration:none;
    cursor:pointer;
    margin:5px;
    }}
    .interactionButton{{
    align-self:flex-end;
    padding:10px;
    margin:0px;
    color:white;
    border-radius:15px;
    text-decoration:none;
    cursor:pointer;
    }}
    .printerTitle{{
    margin-top:5px;
    margin-bottom:0px;
    cursor:pointer;
    }}
    </style>
    '''
    body += """
    <div style="display:flex">
      <a href="estop" style="background-color:#c43349" class="button">E-STOP</a>
    """
    if "developer" in get_user_roles(auth.current_user()):
        body += """<a href="dev" class="button">Developer Portal</a>"""
    if "developer" in get_user_roles(auth.current_user()) or "manager" in get_user_roles(auth.current_user()):
        body += """<a href="setup/printers" class="button">Add Printers</a>"""
    else:
        print(f"[DEBUG] Not authorized to view dev page: {get_user_roles(auth.current_user())}")
    if get_user_roles(auth.current_user()) in ["developer", "manager"]:
        body += """<a href="account" class="button">Account Management</a>"""
    else:
        print(f"[DEBUG] Not authorized to view dev page: {get_user_roles(auth.current_user())}")
    try:
        prints_ref
        body += '<a href="db" class="button">Database</a>'
    except NameError:
        pass

    if len(liminal.cameras) > 0:
        body += """<a href="cctv" class="button" class="button">Cameras</a>"""

    if printLaterEnabled:
        body += """<a href="/" style="background-color:#165a73" class="button">Return to normal printing</a>"""
    else:
        body += """<a href="?later=true" style="background-color:#165a73" class="button">Print Later [BETA]</a>"""

    if len(liminal.scheduledPrints) > 0:
        body += """
        <a href="printLaterEstop" style="background-color:#c43349" class="button">Cancel All Scheduled Prints</a>"""
    body +="""
    <a href="timelapse" class="button">Download last timelapse</a>
    <a href="/account/reset" style="background-color:#c43349" class="button">Password Reset</a>
    </div>
    """


    for printer in liminal.printers:
        req = requests.get(f"{printer.url}/api/printer", headers={f"X-API-KEY": f"{printer.key}"})
        if not req.ok:
            print("[ERROR] Printer is not operational as reported by Octoprint")
            continue
        if not printer.printer.printer()["state"]["flags"]["operational"]:
            print("[ERROR] Printer is not operational as reported by Octoprint")
            continue
        if printer.printer != None and printer.code not in jsonValues["printersDown"]:
            addedPrinters += 1
            body += '<div style="display:flex;">'
            body += f'<h1 class="printerTitle"> <a href = {printer.url}; style="color:{liminal.systemColor};">{printer.nickname}</a></h1>'
            if printer.fetchNozzleTemp()["actual"] < 200:
                body += f'''
                <form style="margin-top:5px; margin-left:10px;margin-bottom:0px;"action = "{url_for("functions")}" method = post>
                <input type="hidden" name="printer" value="{printer.nickname}">
                <input class="interactionButton" style="background-color:tomato" type = "submit" value = "Preheat"> 
                </form>
                '''
            else:
                body += f'''
                <form  action = "{url_for("cooldown")}" method = post>
                <input type="hidden" name="printer" value="{printer.nickname}">
                <input class="interactionButton" style="background-color:LightSkyBlue" type = "submit" value = "Cooldown"> 
                </form>
                '''
            if "paused" in printer.printer.state().lower():
                body += f'''
                    <form  action = "{url_for("resumePrint")}" method = post>
                    <input type="hidden" name="printer" value="{printer.nickname}">
                    <input class="interactionButton" style="background-color:green" type = "submit" value = "Resume Print"> 
                    </form>
                    '''
            elif "printing" in printer.printer.state().lower():
                body += f'''
                    <form action = "{url_for("pausePrint")}" method = post>
                    <input type="hidden" name="printer" value="{printer.nickname}">
                    <input class="interactionButton" style="background-color:orange" type = "submit" value = "Pause Print"> 
                    </form>
                '''
            body += '</div>'
            for camera in liminal.cameras:
                if camera.printer != None and camera.printer.nickname == printer.nickname:
                    body += f"""<img src="{url_for("video_feed", cameraNum = camera.cameraNumber)}" alt="Video Stream">"""
            body += '<div style="display:flex;">'
            if printer.fetchNozzleTemp() != None:
                body += f'<h3 style="color:white;margin-right: 10px">Nozzle: {printer.fetchNozzleTemp()["actual"]}</h3>'
            if printer.fetchBedTemp() != None:
                body += f'<h3 style="color:white;margin-right: 10px">Bed: {printer.fetchBedTemp()["actual"]}</h3>'
            body += '</div>'
            if "printing" in printer.state.lower() and printer.fetchNozzleTemp()["actual"] >= 200:
                body += f'<h3 style="color:white;">Currently in use | {int(printer.fetchTimeRemaining()/60)} Minutes left</h3>'
                #Implement time remaining methods :)

            elif "restricted" not in get_user_roles(auth.current_user()):
                #Submission requrements:
                # printer : Printer Name ex. Left Printer
                # Gcode : The GCODE file
                # creator: The name of the uploader
                # material: The name of the filament, currently unused
                # printercode: unestablished right now, but is a needed input
                # nickname: The name of the print
                #<input type="hidden" name="creator" placeholder="notSet">
                body += f"""
    <form style="color:white" action="{url_for('printLater') if printLaterEnabled else url_for('uploadPrintURL') }" method="post" enctype="multipart/form-data">
    <input type="hidden" name="printer" value="{printer.nickname}">
    <input type="hidden" name="printercode" value="{printer.code}">
    <input type="hidden" name="creator" value="{auth.current_user()}">
    <input type="hidden" name="material" placeholder="notSet">
    <label for="url">GCODE File:</label>
    <input type="file" id="url" name="gcode" accept=".gcode">
    <label for="nickname">Print Name:</label>
    <input type="text" id="nickname" name="nickname" placeholder="nickname">
    """
                if printLaterEnabled:
                    body +="""
                    <label for="date">Time to print:</label>
                    <input type="datetime-local" id="date" name="date">
                    """
                body += """
                <button type="submit">Upload</button>
                </form>
                """
            else:
                body += '<h2 style = "color:orange"> You do not have proper permissions to print</h2>'

    #Mk4 Printers
    for printer in liminal.MK4Printers:
        if printer.prefix not in jsonValues["printersDown"]:
            try:
                printer.refreshData()
            except Exception:
                if printer in liminal.printers:
                    liminal.printers.remove(printer)
                print(f"[ERROR] Error refreshing data when displaying dashboard for {printer.nickname}")
            else:
                addedPrinters += 1
                body += '<div style="display:flex;">'
                body += f'<h1 class="printerTitle"><a href = "http://{printer.ip}" style="color:{liminal.systemColor}">{printer.nickname}</a> </h1>'
                if printer.serial != None:
                    if printer.fetchNozzleTemp() >= 200:
                        body += f'''
                                <form  action = "{url_for("cooldown")}" method = post>
                                <input type="hidden" name="printer" value="{printer.nickname}">
                                <input class="interactionButton" style="background-color:LightSkyBlue" type = "submit" value = "Cooldown"> 
                                </form>
                        '''
                    else:
                        body += f'''
                                <form style="margin-top:5px; margin-left:10px;margin-bottom:0px;"action = "{url_for("functions")}" method = post>
                                <input type="hidden" name="printer" value="{printer.nickname}">
                                <input class="interactionButton" style="background-color:tomato" type = "submit" value = "Preheat"> 
                                </form>
                                '''
                body += '</div>'

                for camera in liminal.cameras:
                    if camera.printer != None and camera.printer.nickname == printer.nickname:
                        body += f"""<img src="{url_for("video_feed", cameraNum=camera.cameraNumber)}" alt="Video Stream">"""
                body += '<div style="display:flex;">'

                body += f'<h3 style="color:white;margin-right: 10px">Nozzle: {printer.fetchNozzleTemp()}</h3>'
                body += f'<h3 style="color:white;margin-right: 10px">Bed: {printer.fetchBedTemp()}</h3>'
                body += '</div>'
                if "printing" in printer.state.lower() and printer.fetchNozzleTemp() >= 200:
                    body += f'<h3 style="color:white;">Currently in use | {printer.progress}% Complete</h3>'
                else:
                    body += f"""
                    <form style="color:white" action="{url_for('printLater') if printLaterEnabled else url_for('uploadPrintURL') }" method="post" enctype="multipart/form-data">
                    <input type="hidden" name="printer" value="{printer.nickname}">
                    <input type="hidden" name="printercode" value="{printer.prefix}">
                    <input type="hidden" name="creator" value="{auth.current_user()}">
                    <input type="hidden" name="material" placeholder="notSet">
                    <label for="url">GCODE File:</label>
                    <input type="file" id="url" name="gcode" accept=".gcode,.bgcode">
                    <label for="nickname">Print Name:</label>
                    <input type="text" id="nickname" name="nickname" placeholder="nickname">
                    """
                    if printLaterEnabled:
                        body += """
                        <label for="date">Time to print:</label>
                        <input type="datetime-local" id="date" name="date">
                        """
                    body += """
                    <button type="submit">Upload</button>
                    </form>
                    """
    #if addedPrinters == 0:
    if addedPrinters != configuredPrinters and configuredPrinters != 0:
        body += f'<{"p" if addedPrinters > 0 else "h3"} style="color:white;"><small>{addedPrinters}/{configuredPrinters} printers available, consult dev menu for debugging</h3>'
    body += "</body></html>"

    return body
@app.route('/heat', methods = ["GET", "POST"])
@auth.login_required(role = ["student", "manager", "developer"])
#This defines the webpage that will allow you to preheat printers
#You can pass ALL to preheat all of them, and an individual name to preheat that one
def functions():
    if request.method == "GET":
        return "You aren't supposed to be here you silly goose"
    else:
        #Implement API Key validation to ensure legitimate requests
        if request.form.get("printer") == "all":
            for printer in liminal.printers + liminal.MK4Printers:
                printer.preheat()
            return redirect(url_for("index", txt="Preheating all printers", color = "success"))
        else:
            for printer in liminal.printers + liminal.MK4Printers:
                if request.form.get("printer") == printer.nickname:
                    printer.preheat()
                    return redirect(url_for("index", txt=f"{printer.nickname} is now being preheated", color = "success"))
            return redirect(url_for("index", txt="No printer found", color="warning"))

@app.route('/cooldown', methods = ["POST"])
@auth.login_required(role = ["student", "manager", "developer"])
def cooldown():
    for printer in liminal.printers + liminal.MK4Printers:
        if request.form.get("printer") == printer.nickname:
            printer.cooldown()
            return redirect(url_for("index", txt=f"{printer.nickname} is being cooled down", color="success"))

    return redirect(url_for("index", txt="No printer found", color="warning"))
@app.route('/stop', methods = ["POST"])
@auth.login_required(role = ["student", "manager", "developer"])
def stop():
    for printer in liminal.printers + liminal.MK4Printers:
        if request.form.get("printer") == printer.nickname:
            printer.abort()
            return redirect(url_for("index", txt=f"Stopping print on {printer.nickname}", color="success"))
    return redirect(url_for("index", txt="No printer found", color="warning"))

@app.route('/pause', methods = ["POST"])
@auth.login_required(role = ["student", "manager", "developer"])
def pausePrint():
    if request.form.get("printer") == "all":
        for printer in liminal.printers:
            printer.pause()
        return redirect(url_for("index", txt=f"Pausing all printers", color="success"))
    else:
        for printer in liminal.printers:
            if request.form.get("printer") == printer.nickname:
                printer.pause()
                return redirect(url_for("index", txt=f"Pausing print on {printer.nickname}", color="success"))
        for printer in liminal.MK4Printers:
            if request.form.get("printer") == printer.nickname:
                printer.pause()
                return redirect(url_for("index", txt=f"Pausing print on {printer.nickname}", color="success"))
        return redirect(url_for("index", txt=f"No printer found", color="warning"))
@app.route('/resume', methods = ["POST"])
@auth.login_required(role = ["student", "manager", "developer"])
def resumePrint():
    if request.form.get("printer") == "all":
        for printer in liminal.printers:
            printer.resume()
        return redirect(url_for("index", txt=f"Resuming all prints", color="success"))
    else:
        for printer in liminal.printers:
            if request.form.get("printer") == printer.nickname:
                printer.resume()
                return redirect(url_for("index", txt=f"Resuming print on {printer.nickname}", color="success"))
        for printer in liminal.MK4Printers:
            if request.form.get("printer") == printer.nickname:
                printer.resume()
                return redirect(url_for("index", txt=f"Resuming print on {printer.nickname}", color="success"))
        return redirect(url_for("index", txt=f"No printer found", color="warning"))
@app.route('/print', methods = ["GET", "POST"])
@auth.login_required(role = ["student", "manager", "developer"])
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
        for printer in (liminal.printers + liminal.MK4Printers):
            if request.form.get("printer") == printer.nickname:
                print("[OPERATIONAL] Printer selected for printing")
                # Indivdual Print requirements: file (URL String), creator, material, printerCode, nickname
                try:
                    gcodeUpload = request.form.get("gcode")
                    user = request.form.get("creator")
                    material = request.form.get("material")
                    printerCode = request.form.get("printercode")
                    rawNickname = request.form.get("nickname")
                    nickname = rawNickname
                    #for char in rawNickname:
                        #if char.isalnum():
                            #nickname.join(char)
                    print("[OPERATIONAL] Form data successfully gathered")
                except Exception as e:
                    print("[ERROR] Failed to gather form data")
                    return redirect(url_for("index", txt=f"Unable to get form data", color="danger"))


                    #printer.upload(individualPrint)
                    #print(gcodeUpload)

                file_contents = request.files["gcode"].stream.read()

                if nickname == "":
                    nickname = "Untitled"
                if printer in liminal.printers:
                    printer.printer.upload(file=(nickname + ".gcode", file_contents), location="local", print=True)
                    printer.printer.select(location=nickname + ".gcode", print=True)
                    print("[OPERATIONAL] Successfully printed onto a Mk3 printer")
                else:
                    if printer in liminal.MK4Printers:
                        if request.files["gcode"].filename.split(".")[-1] == "bgcode":
                            binaryGcode = True
                        else:
                            binaryGcode = False
                        printer.upload(file_contents, nickname, binaryGcode)
                        print("[OPERATIONAL] Successfully printed onto a Mk4 printer")
                    else:
                        print(f"[ERROR] The printer {request.form.get('printer')} is not registered")
                        return redirect(url_for("index", txt=f"Printer requested does not exist", color="danger"))
                    #Ensures a .00000000000000000000010661449% change of a UUID collision
                try:
                    chars = list(string.ascii_lowercase + string.ascii_uppercase + string.digits)
                    blobName = ""
                    for i in range(0,15):
                        blobName += random.choice(chars)
                    blob = bucket.blob(blobName)
                    blob.upload_from_string(file_contents)
                    blob.make_public()


                    fileURL = blob.public_url
                    individualPrint = IndividualPrint(fileURL, user, material, printerCode, nickname)

                    doc_ref = db.collection('prints').document(individualPrint.uuid)

                    doc_ref.set({
                        'gcode': individualPrint.file,
                        'creator': individualPrint.creator,
                        'material': individualPrint.material,
                        'printerCode': individualPrint.printerCode,
                        'nickname': individualPrint.nickname,
                        'uuid': individualPrint.uuid,
                        'year': individualPrint.uuid[-2::],
                        'created': firestore.SERVER_TIMESTAMP
                    })
                except Exception:
                    print("[WARNING] The print was not logged successfully to Firebase, but was uploaded to the printers")
                    return redirect(url_for("index", txt=f"Print submitted successfully, but was not saved to the cloud", color="warning"))

                return redirect(url_for("index", txt=f"Print submitted successfully, and saved to the cloud with code {individualPrint.uuid}", color = "success"))

        return redirect(url_for("index", txt=f"Printer \"{request.form.get('printer')}\"was not located",
                                        color="danger"))

@app.route('/db')
@auth.login_required()
def database():
    allPrints = prints_ref.get()
    body = ""
    body += """
    <form action="/map" method="post" enctype="multipart/form-data">
  <label for="id">Enter code:</label><br>
  <input type="text" id="id" name="id" value=""><br>
  <input type="submit" value="Submit">
</form> 
    
    """
    for singlePrint in allPrints:
        printData = singlePrint.to_dict()
        try:
            body += f"""
            <h1>{printData["nickname"]} by {printData["creator"]} at {printData["created"].strftime('%Y-%m-%d %H:%M:%S')}</h1>
            <a download href="{printData["gcode"]}">View GCODE</a>
            """
        except KeyError:
            body += f"""
            <h1>Document too old</h1>
            """
    return body
@app.route('/search/<id>')
@auth.login_required()
def search(id):
    print(id)
    query_ref = prints_ref.where('uuid', '==', id).get()
    body = ""
    for singlePrint in query_ref:
        printData = singlePrint.to_dict()
        print(singlePrint.to_dict())
        try:
            body += f"""
            <h1>{printData["nickname"]} by {printData["creator"]} at {printData["created"].strftime('%Y-%m-%d %H:%M:%S')}</h1>
            <a download href="{printData["gcode"]}">View GCODE</a>
            """
        except KeyError:
            body += f"""
            <h1>Document too old</h1>
            """
    return body

@app.route('/map', methods = ["POST"])
@auth.login_required()
def map():
    id = request.form.get("id")
    return redirect(f"/search/{id}")

@app.route('/dev/online',methods = ["GET", "POST"])
@auth.login_required(role="developer")
def setPrinterOnline():
    if request.method == "GET":
        return redirect(url_for("setPrinterStatus"))
    else:
        with open(f"{cwd}/ref/config.json", "r") as f:
            setOnline = request.form.get("printer")
            jsonValues = json.load(f)
            if "printersDown" not in jsonValues:
                jsonValues["printersDown"] = []
            jsonValues["printersDown"].remove(setOnline)
        with open(f"{cwd}/ref/config.json", "w") as f:
            json.dump(jsonValues,f,indent=4)
        return redirect(url_for("setPrinterStatus"))

@app.route('/dev/ip',methods = ["GET", "POST"])
@auth.login_required(role="developer")
def changeIPAddr():
    if request.method == "GET":
        return redirect(url_for("setPrinterStatus"))
    else:
        with (open(f"{cwd}/ref/config.json", "r") as f):
            changedIP = request.form.get("printer")
            newAddress = request.form.get("addr")
            ismk4 = request.form.get("isMk4").lower() == "true"
            jsonValues = json.load(f)
            field = "Mk4IPAddress" if ismk4 else "ipAddress"
            jsonValues[changedIP][field] = "http://" + newAddress
        with open(f"{cwd}/ref/config.json", "w") as f:
            json.dump(jsonValues,f,indent=4)
        return redirect(url_for("setPrinterStatus"))
@app.route('/dev/key',methods = ["GET", "POST"])
@auth.login_required(role="developer")
def changeAPIKey():
    if request.method == "GET":
        return redirect(url_for("setPrinterStatus"))
    else:
        with open(f"{cwd}/ref/config.json", "r") as f:
            changedKey = request.form.get("printer")
            newKey = request.form.get("key")
            jsonValues = json.load(f)
            jsonValues[changedKey]["apiKey"] = newKey
        with open(f"{cwd}/ref/config.json", "w") as f:
            json.dump(jsonValues,f,indent=4)
        return redirect(url_for("setPrinterStatus"))
@app.route('/dev/camera',methods = ["GET", "POST"])
@auth.login_required(role="developer")
def changeCamMemory():
    if request.method == "GET":
        return redirect(url_for("setPrinterStatus"))
    else:
        with open(f"{cwd}/ref/config.json", "r") as f:
            changedPrinter = request.form.get("printer")
            newIndex = request.form.get("index")
            jsonValues = json.load(f)
            for item in jsonValues:
                if item["cameraIndex"] == newIndex:
                    jsonValues[item]["cameraIndex"] = None
            jsonValues[changedPrinter]["cameraIndex"] = newIndex
            for camera in liminal.cameras:
                if camera.index == newIndex:
                    for printer in liminal.printers + liminal.MK4Printers:
                        if printer.nickname == changedPrinter:
                            camera.printer = printer
        with open(f"{cwd}/ref/config.json", "w") as f:
            json.dump(jsonValues,f,indent=4)
        return redirect(url_for("setPrinterStatus"))
@app.route('/dev/ipMK4',methods = ["GET", "POST"])
@auth.login_required(role="developer")
def changeIPAddrMK4():
    if request.method == "GET":
        return redirect(url_for("setPrinterStatus"))
    else:
        with open(f"{cwd}/ref/config.json", "r") as f:
            changedIP = request.form.get("printer")
            newAddress = request.form.get("addr")
            jsonValues = json.load(f)
            jsonValues[changedIP]["Mk4IPAddress"] = newAddress
        with open(f"{cwd}/ref/config.json", "w") as f:
            json.dump(jsonValues,f,indent=4)
        return redirect(url_for("setPrinterStatus"))
        
@app.route('/dev/offline',methods = ["GET", "POST"])
@auth.login_required(role="developer")
def setPrinterOffline():

    if request.method == "GET":
        return redirect(url_for("setPrinterStatus"))
    else:
        with open(f"{cwd}/ref/config.json", "r") as f:
            setOnline = request.form.get("printer")
            jsonValues = json.load(f)
            if "printersDown" not in jsonValues:
                jsonValues["printersDown"] = []
            jsonValues["printersDown"].append(setOnline)
        with open(f"{cwd}/ref/config.json", "w") as f:
            json.dump(jsonValues, f, indent=4)
        return redirect(url_for("setPrinterStatus"))
@app.route('/dev/scan', methods = ["GET", "POST"])
@auth.login_required(role="developer" )
def scanForPrinter():
    if request.method == "GET":
        return render_template(f"portscan.html", scanning = liminal.searchingForHosts, host = liminal.possibleHosts)
    elif request.method == "POST":
        hardware = request.form.get("hardware")
        suffix = request.form.get("suffix")
        agree = request.form.get("agree")
        if agree == "on":
            agree = True
        else:
            agree = False
        if not agree:
            return "You did not confirm agreeing to the terms of port scanning"
        scanThread = threading.Thread(target=liminal.portScan, args=(hardware, suffix))
        threads.append(scanThread)
        scanThread.start()
        return redirect(url_for("scanForPrinter"))

@app.route('/estop', methods = ["GET"])
@auth.login_required()
def emergencyStopWeb():
    liminal.estop()
    return "All printers stopping"
@app.route('/2FA')
@auth.login_required()
def TwoFA():
    liminal.genNewApprovalCode()
    expTime = (liminal.lastGenerated + datetime.timedelta(minutes = 5))
    for printer in liminal.printers:
        printer.displayMSG(f"{liminal.approvalCode} EXP: {(expTime.time())}")
    return redirect(url_for("index"))

@app.route('/clearDisplays')
@auth.login_required()
def clean():
    for printer in liminal.printers:
        printer.displayMSG(f"")
    return redirect(url_for("index"))
@app.route('/ip')
@auth.login_required(role="developer")
def debugReRoute():
    return redirect(url_for("ipManagement"))
@app.route('/debug',methods = ["GET"])
@auth.login_required(role="developer")
def ipManagement():
    file = open(f"{cwd}/ref/config.json")
    jsonValues = json.load(file)
    file.close()
    flags = {}
    advice = {}
    for item in jsonValues:
        subflags = []
        if "ipAddress" in jsonValues[item]:
            try:
                req = requests.get(f'{jsonValues[item]["ipAddress"]}/api/printer', headers={"X-API-KEY": f'{jsonValues[item]["apiKey"]}'})
                #body += '<h3 style="color:green"> Printer is reachable via HTTP</h3>'
                octoprint = True
                if not req.ok:
                    #body += '<h3 style="color:orange"> Printer is not operational on Octoprint </h3>'
                    subflags.append(["Printer is not operational on Octoprint", "no-op","danger"])
                else:
                    if not req.json()["state"]["flags"]["operational"]:
                        subflags.append(["Printer is not operational on Octoprint via flags", "no-op","danger"])
                        #body += '<h3 style="color:orange"> Printer is not operational on Octoprint via flags</h3>'
                    else:
                        subflags.append(["Printer is operational on Octoprint","op", "success"])
                        #body += '<h3 style="color:green"> Printer is operational via Octoprint</h3>'
            except Exception as e:
                print(e)
                octoprint = False
                subflags.append(["Printer is not reachable via HTTP", "no-reach", "danger"])

            nicknames = []
            for printer in liminal.printers + liminal.MK4Printers:
                nicknames.append(printer.nickname)
                if printer.nickname == item and octoprint:
                    percentUsed = printer.percentUsed()
                    if percentUsed > 90:
                        color = "danger"
                    elif percentUsed > 60:
                        color = "warning"
                    else:
                        color = "success"
                    subflags.append([f"{round(percentUsed,2)}% of onboard storage used", "good-storage" if color == "danger" else "bad-storage", color])
            if item in nicknames:
                subflags.append(["Printer registered by system", "registered", "success"])
            else:
                subflags.append(["Printer not registered by system", "not-registered", "danger"])

        if "Mk4IPAddress" in jsonValues[item]:
            for printer in liminal.MK4Printers:
                if printer.nickname == item:
                    if printer.serial != None:
                        subflags.append(["Connected via serial connection", "serial", "success"])
                    else:
                        subflags.append(["Serial Connection not available", "serial", "primary"])
                    if printer.freeSpace != None:
                        subflags.append([f"{round(printer.freeSpace/1_000_000_000,2)}gb free on {printer.storageName}", "storage", "primary"])
                    else:
                        subflags.append([f"Could not determine free storage on {printer.storageName}", "null-storage",
                                     "primary"])
        if "Mk4IPAddress" in jsonValues[item] or "ipAddress" in jsonValues[item]:
            flags[item] = subflags


    return render_template("debug.html", flags=flags)

@app.route('/dev/mk4Update/<printer>/<type>', methods = ["POST"])
@auth.login_required(role="developer")
def updatePrinter(printer, type):
    for Mk4printer in liminal.MK4Printers:
        if Mk4printer.nickname == printer:
            Mk4printer.pushUpdate(type)
    return url_for("setPrinterStatus")
@app.route('/dev',methods = ["GET"])
@auth.login_required(role="developer")
def setPrinterStatus():
    file = open(f"{cwd}/ref/config.json")
    jsonValues = json.load(file)
    file.close()
    printerOptions = []
    if "printersDown" not in jsonValues:
        jsonValues["printersDown"] = []
    for printer in liminal.printers + liminal.MK4Printers:
        printerOptions.append(printer.nickname)
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
        body += """
                <div class="topnav">
              <a href="ip">Edit IP Addresses</a>
            </div>
                """
        body += f'<h1 style="color:{liminal.systemColor}"> Currently Online </h1>'
        for printer in liminal.printers:
            if printer.code not in jsonValues["printersDown"]:
                body += f'<h3 style="color:white"> {printer.nickname} </h3>'
                body += f"""
                        <form style="color:white" action="{url_for('setPrinterOffline')}" method="post", enctype="multipart/form-data">
                        <input type="hidden" name="printer" value="{printer.code}">
                        <button type="submit">Switch Offline</button>
                        </form>
                        """
        body += f'<h1 style="color:{liminal.systemColor}"> Currently Offline </h1>'
        for printer in liminal.printers:
            if printer.code in jsonValues["printersDown"]:
                body += f'<h3 style="color:white"> {printer.nickname} </h3>'
                body += f"""
                    <form style="color:white" action="{url_for('setPrinterOnline')}" method="post" enctype="multipart/form-data">
                    <input type="hidden" name="printer" value="{printer.code}">
                    <button type="submit">Switch Online</button>
                    </form>
                                """

        body += f'<h1 style="color:{liminal.systemColor}"> Change Printer Camera </h1>'
        for camera in liminal.cameras:
            body += f"""<img src="{url_for("video_feed", cameraNum=camera.cameraNumber)}" alt="Video Stream">"""
            body += f"""
            <form style="color:white" action="{url_for('changeCamMemory')}" method="post" enctype="multipart/form-data">
            <input type="hidden" name="index" value="{camera.index}">
            <select name="printer">"""
            for printerOption in printerOptions:
                body+= f"""
                <option value="{printerOption}"> {printerOption} </option>
                """
            body += f"""
            </select>
            <button type="submit">Switch Camera to Printer</button>
            </form>
            """
        body += f'<a href="{url_for("clean")}">Clear all displays</a>'

        if len(liminal.MK4Printers) > 0:
            body += f'<h1 style="{liminal.systemColor}"> Mk Printers </h1>'
            for Mk4Printer in liminal.MK4Printers:
                body += f'<h2 style="color:white"> {Mk4Printer.nickname} </h2>'
                prusalinkUpdate, systemUpdate = Mk4Printer.checkUpdate()
                if not prusalinkUpdate:
                    body += '<button disabled> PrusaLink is up to date </button>'
                elif prusalinkUpdate:
                    body += f"""
                    <form style="color:white" action="{url_for('updatePrinter')}" method="post" enctype="multipart/form-data">
                    <input type="hidden" name="type" value="prusalink">
                    <button type="submit">Update Prusalink</button>
                    </form>
                    """
                else:
                    body += '<button disabled> Unable to get Prusalink version status </button>'

                if not systemUpdate:
                    body += '<button disabled> System is up to date </button>'
                elif systemUpdate:
                    body += f"""
                    <form style="color:white" action="{url_for('updatePrinter')}" method="post" enctype="multipart/form-data">
                    <input type="hidden" name="type" value="prusalink">
                    <button type="submit">Update Prusalink</button>
                    </form>
                    """
                else:
                    body += '<button disabled> Unable to get system version status </button>'


        return body

@app.errorhandler(401)
def notauthorized(error):
    return render_template("401.html")
@app.errorhandler(403)
@auth.login_required()
def forbidden(error):
    return render_template("403.html", role = get_user_roles(auth.current_user()))
@app.errorhandler(404)
@auth.login_required()
def notFound(error):
    return render_template("404.html", role = get_user_roles(auth.current_user()))
@app.route('/timelapse')
@auth.login_required()
def timelapse():
    try:
        return send_file(f"Clip.mp4")
    except:
        return "Error downloading last timelapse..."

if not liminal.debugging:
    @app.errorhandler(500)
    @auth.login_required()
    def fallback(error):
        body = ""
        body += f'<h1> There was an error somewhere, here is a fallback to printer URLS: </h1>'
        for printer in liminal.printers:
            try:
                body += f'<h1 style="color:{liminal.systemColor};"><a href = http://{printer.url}>{printer.nickname}</a> </h1>'
            except Exception:
                print(f"[ERROR] Error adding printer to fallback")
        for printer in liminal.MK4Printers:
            try:
                body += f'<h1 style="color:{liminal.systemColor};"><a href = http://{printer.ip}>{printer.nickname}</a> </h1>'
            except Exception:
                print("[ERROR] Error adding printer to falback")
        body += f'<h1>Debug details: </h1>'
        for printer in liminal.printers:
            body += f'<h5>{printer.nickname}</h5>'
        for printer in liminal.MK4Printers:
            if printer.serial != None:
                body += f'<h5>{printer.nickname} w/ serial</h5>'
            else:
                body += f'<h5>{printer.nickname} w/o serial</h5>'
        return body
@app.route('/error')
@auth.login_required()
def troubleMaker():
    return 500
@app.route('/camera/raw/<path:cameraNum>')
@auth.login_required()
def video_feed(cameraNum):
    selectedCam = liminal.cameras[int(cameraNum)]
    return Response(selectedCam.stream(), mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route('/camera/fetchlast30/<path:cameraNum>')
@auth.login_required()
def last30Sec(cameraNum):
    selectedCam = liminal.cameras[int(cameraNum)]
    resolution = cv2.imdecode(np.frombuffer(selectedCam.buffer[-1], np.uint8), cv2.IMREAD_COLOR).shape
    result = cv2.VideoWriter(f"{cwd}/Clip.mp4", cv2.VideoWriter_fourcc(*'mp4v'), selectedCam.frameRate,(resolution[1],resolution[0]))
    for frame in selectedCam.buffer:
        result.write(cv2.imdecode(np.frombuffer(frame, np.uint8), cv2.IMREAD_COLOR))
    result.release()
    return send_file(f"Clip.mp4")

@app.route('/cctv')
@auth.login_required()
def cctvView():
    body = "<html><body style = background-color:black>"
    for camera in liminal.cameras:
        if camera.printer == None:
            cameraTxt = "No printer Assigned"
        else:
            cameraTxt = camera.printer.nickname
        body += f"""<img src="{url_for("video_feed", cameraNum = camera.cameraNumber)}" alt="Video Stream">
                <h1> {cameraTxt} </h1>
                <a href='{url_for("last30Sec", cameraNum = camera.cameraNumber)}' download>
                <h1> Download last 30 Seconds </h1>
                </a>
        """
    return body
@app.route('/mk4Load/<printerNickname>')
@auth.login_required()
def mk4LoadingScreen(printerNickname):
    for printer in liminal.MK4Printers:
        if printer.nickname == printerNickname:
            printer.refreshData()

            if printer.transfer != None:
                return f"""
                <meta http-equiv="refresh" content="1" /> 
                Mk4 Transfer status:<br>{printer.transfer}% Complete"""
            else:
                return "<h1>Transfer status Complete?</h1>"

@app.route('/nukeFiles/<printerNickname>')
@auth.login_required()
def nukeFiles(printerNickname):
    for printer in liminal.printers:
        if printer.nickname == printerNickname:
            printer.nukeFiles()
            return f"Success, percent storage is now: {printer.percentUsed()}"

@app.route('/printLater/cancel', methods=["POST"])
@auth.login_required(role=["student", "manager", "developer"])
def removeItemFromQueue():
    for printer in liminal.printers + liminal.MK4Printers:
        if request.form.get("printer") == printer.nickname:
            for job in liminal.scheduledPrints:
                if job.nickname == request.form.get("nickname"):
                    if (job.preheating):
                        printer.cooldown()
                    liminal.scheduledPrints.remove(job)
                    return redirect(url_for("index", txt=f"{job.nickname} has been cancelled on {printer.nickname}", color="success"))
    return redirect(url_for("index", txt=f"The job count not be located in the queue", color="warning"))


@app.route('/printLater', methods = ["POST"])
@auth.login_required(role = ["student", "manager", "developer"])
def printLater():
    #printer : Printer Name ex. Left Printer
    #url : The GCODE URL (from firebase)
    #creator: The name of the uploader
    #material: The name of the filament, currently unused
    #printercode: unestablished right now, but is a needed input
    #nickname: The name of the print
    printerToPrint = None
    for printer in liminal.printers + liminal.MK4Printers:
        if request.form.get("printer") == printer.nickname:
            printerToPrint = printer
    if printerToPrint != None:
        
        #time, fileContents, nickname, printer, bgcode = False
        file_contents = request.files["gcode"].stream.read()

        if request.files["gcode"].filename.split(".")[-1] == "bgcode":
            binaryGcode = True
        else:
            binaryGcode = False

        format = "%Y-%m-%dT%H:%M"
        rawNickname = request.form.get("nickname")
        nickname = rawNickname
        #for char in rawNickname:
            #if char.isalnum():
                #nickname.join(char)
        if nickname == "":
            nickname = "Untitled"
        time = datetime.strptime(request.form.get("date"), format)
        printLaterobj = PrintLater(time,file_contents,nickname,printerToPrint,binaryGcode)

        liminal.scheduledPrints.append(printLaterobj)
        print(f"[OPERATIONAL] Print has been scheduled on {printerToPrint.nickname} for {time.strftime('%Y-%m-%d %H:%M:%S')}")
        return redirect(url_for("index", txt=f"Print has been scheduled!", color="success"))
    else:
        return redirect(url_for("index", txt=f"{request.form.get('printer')} was not found", color="warning"))

@app.route('/account/reset/<username>')
@auth.login_required(role=["developer", "manager"])
def resetPassword(username):
    with open(f"{cwd}/ref/config.json", "r") as f:
        jsonValues = json.load(f)
        jsonValues["students"][username]["hash"] = None
    with open(f"{cwd}/ref/config.json", "w") as f:
        json.dump(jsonValues, f, indent=4)
    return "Password reset, upon next login the password they enter will become their new password :)"
@app.route('/account/reset')
@auth.login_required()
def passwordResetSelf():
    username = auth.current_user()
    with open(f"{cwd}/ref/config.json", "r") as f:
        jsonValues = json.load(f)
        jsonValues["students"][username.capitalize()]["hash"] = None
    with open(f"{cwd}/ref/config.json", "w") as f:
        json.dump(jsonValues, f, indent=4)
    return "Password reset, next login will determine your password"
@app.route('/account/remove/<username>')
@auth.login_required(role=["developer", "manager"])
def removeUser(username):
    with open(f"{cwd}/ref/config.json", "r") as f:
        jsonValues = json.load(f)
        if username in jsonValues["students"]:
            del jsonValues["students"][username]
    with open(f"{cwd}/ref/config.json", "w") as f:
        json.dump(jsonValues, f, indent=4)
    return f"Account Removed"

@app.route('/account/modify/<username>')
@auth.login_required(role=["developer", "manager"])
def updateUser(username):
    with open(f"{cwd}/ref/config.json", "r") as f:
        jsonValues = json.load(f)
        if username in jsonValues["students"]:
            jsonValues["students"][username]["role"] = request.args.get('role')
    with open(f"{cwd}/ref/config.json", "w") as f:
        json.dump(jsonValues, f, indent=4)
    return f"{username} is now {request.args.get('role')}"
@app.route('/account/add')
@auth.login_required(role=["developer", "manager"])
def addUser():
    name = request.args.get('name')
    role = request.args.get('role')
    with open(f"{cwd}/ref/config.json", "r") as f:
        jsonValues = json.load(f)
        jsonValues["students"][name.capitalize()]= {"hash": None, "role":role}
    with open(f"{cwd}/ref/config.json", "w") as f:
        json.dump(jsonValues, f, indent=4)
    return f"Added {request.args.get('name')} as {request.args.get('role')}. Their password will be set automatically upon first login"
@app.route('/account')
@auth.login_required(role=["developer", "manager"])
def accountManger():
    file = open((f"{cwd}/ref/config.json"))
    jsonValues = json.load(file)
    file.close()
    return render_template("manage-accounts.html", accounts = jsonValues["students"], role = get_user_roles(auth.current_user()))
    #Developer, access to developer settings + debug
    #Manager, configure roles
    #Student, basic printing capabilities
    body = "<html><body style = background-color:#1f1f1f>"
    body += f'''
      <head>
      <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Inter">
      </head>
      <style>
      body {{
    font-family: "Inter", sans-serif;
      }}
      .button{{
      background-color:{liminal.systemColor};
      color:white;
      padding:10px;
      border-radius:15px;
      text-decoration:none;
      cursor:pointer;
      }}
      .interactionButton{{
      align-self:center;
      padding:10px;
      margin:0px;
      color:white;
      border-radius:15px;
      text-decoration:none;
      cursor:pointer;
      margin:5px;
      }}
      .printerTitle{{
      margin-top:5px;
      margin-bottom:0px;
      cursor:pointer;
      }}
      </style>
      '''
    for account in jsonValues["students"]:
        body += f'<div style="display:flex"> <h2 style="color:white; padding:5px">{account} - {jsonValues["students"][account]["role"]} </h3>'
        body += f'''
                <form style= "align-self:center"action="{url_for('updateUser', username=account)}">
                  <select name="role" id="role">
                <option value="none" selected disabled hidden>Select a role</option>
                    <option value="restricted">Restricted</option>
                    <option value="student">Student</option>
                    <option value="manager">Manager</option>
                    <option value="developer">Developer</option>
                  </select>
                  <input type="submit" value="Update Role">
                </form>
                '''
        if jsonValues["students"][account]["hash"] != None:
            body += f'<a href="{url_for("resetPassword", username = account)}" class="interactionButton" style = "background-color:orange">Reset Password</a>'
        else:
            body += f'<a class="interactionButton">Password Awaiting Reset by User</a>'
        body += f'<a href="{url_for("removeUser", username = account)}" class="interactionButton" style = "background-color:#c43349">Remove User</a>'
        body += '</div>'
    #Add new account
    body += '<h1 style = "color:green">Create New User:</h1>'
    body += f'''
    <form action="{url_for('addUser')}">
        <label style="color:white" for="name">Name:</label>
        <input type="text" id="name" name="name">
          <select name="role" id="role">
          <option value="Restricted">Restricted</option>
            <option value="student">Student</option>
            <option value="manager">Manager</option>
            <option value="developer">Developer</option>
          </select>
          <input type="submit" value="Create User">
        </form>
    '''
    return body
@app.route('/printLaterEstop', methods = ["GET"])
@auth.login_required()
def printLaterEstop():
    liminal.scheduledPrints = []
    return "Removed all scheduled prints"
@app.route('/reminders', methods = ["GET"])
@auth.login_required()
def reminderMGMT():
    body = "<h1>Reminder Management</h1>"
    for reminder in liminal.reminders:
        body += f'''
        <h3>{reminder.title} - {reminder.body}<h3>
        <h3>Next Date: {(reminder.lastDate + reminder.interval).strftime("%d %b %Y")}
        <h3>Interval: {reminder.interval.days} days
        <h3> Visible to {" ,".join(reminder.groups)}
        <br>
        '''
    if len(liminal.reminders) == 0:
        body += "<h3>No reminders added :(</h3>"

    body += '<h1 style = "color:green">Create New Reminder:</h1>'
    body += f'''
        <form action="{url_for('reminderAdd')}">
            <label for="title">Reminder Title:</label>
            <input type="text" id="title" name="title">
                
            <label for="body">Reminder Body:</label>
            <input type="text" id="body" name="body">
            '''
    body += "<p>Select the roles this reminder applies to:</p>"
    for role in liminal.groups:
        body += f'''
                <input type="radio" id="{role}" name="{role}">
                <label for="{role}"> {role} </label>
        '''

    body += '''
            <label for="lastDate">Reminder Start Date:</label>
            <input type="datetime-local" id="lastDate" name="lastDate">
            
            <label for="interval">Reminder Interval Date:</label>
            <input type="datetime-local" id="interval" name="interval">
            <p>The distance between the start date and the interval date will be the set interval</p>
            
            <input type="submit" value="Create Reminder">
            </form>
        '''
    return body
@app.route("/reminders/add", methods =["GET"])
@auth.login_required()
def reminderAdd():
    title = request.args.get('title')
    if title == "":
        title = "Untitled"
    body = request.args.get('body')
    format = "%Y-%m-%dT%H:%M"
    lastDate = datetime.strptime(request.args.get("lastDate"), format)
    nextDate = datetime.strptime(request.args.get("interval"), format)
    interval = (nextDate - lastDate)
    print(interval)
    print(interval.total_seconds())
    groups = []
    for role in liminal.groups:
        if request.args.get(role) == "on":
            groups.append(role)
    if len(groups) == 0:
        groups = ["student"]

    with open(f"{cwd}/ref/config.json", "r") as f:
        jsonValues = json.load(f)
        newReminder = {
            "body": body,
            "lastDate": time.mktime(lastDate.timetuple()),
            "interval": interval.total_seconds(),
            "groups": groups
        }
        if "reminders" not in jsonValues:
            jsonValues["reminders"] = {}
        jsonValues["reminders"][title] = newReminder

    with open(f"{cwd}/ref/config.json", "w") as f:
        json.dump(jsonValues, f, indent=4)
    return "added?"

@app.route('/setup')
def setupLandingPage():
    accounts = False
    printers = False
    fileExists = os.path.isfile(f"{cwd}/ref/config.json")
    if fileExists:
        file = open((f"{cwd}/ref/config.json"))
        jsonValues = json.load(file)
        file.close()
        if "students" in jsonValues:
            accounts = True
        for item in jsonValues:
            if "ipAddress" in jsonValues[item] or "Mk4IPAddress" in jsonValues[item]:
                printers = True
                break
    else:
        with open(f"{cwd}/ref/config.json", "w") as outfile:
            outfile.write("{}")
    body = f'''
        <h1>Setup Progress</h1>
        <p>Root user account:{"✅" if accounts else "❌"}</p>
        <p>1 printer added: {"✅" if printers else "❌"}</p>
        '''
    if not accounts:
        body += f'<br><a href={url_for("setupRootUser")}> Click here to setup root user'
    if not printers:
        body += f'<br><a href={url_for("setupPrinters")}> Click here to setup a printer'
    if accounts and printers:
        body += f'<br><a href="/"> Let\'s get printing!'
    return body


@app.route('/setup/user', methods = ["GET", "POST"])
def setupRootUser():
    fileExists = os.path.isfile(f"{cwd}/ref/config.json")
    if fileExists:
        file = open((f"{cwd}/ref/config.json"))
        jsonValues = json.load(file)
        file.close()
        if "students" in jsonValues:
            return "Accounts already exist"
    if request.method.lower() == "get":
        body = f'''
        <h1>Configure Root User</h1>
        <p>This user will be set up as an admin will full access, upon setup the next time the user logs in that password will be set</p>
        <form method="post">
            <label for="">Username:</label>
            <input type="text" id="name" name="name">
            <br>
            <input type="submit" value="Confirm user setup">
        </form>
        '''
        return body
    elif request.method.lower() == "post":
        name = request.form.get("name")
        with open(f"{cwd}/ref/config.json", "r") as f:
            jsonValues = json.load(f)
            jsonValues["students"] = {}
            jsonValues["students"][name.capitalize()] = {"hash": None, "role": "manager"}
        with open(f"{cwd}/ref/config.json", "w") as f:
            json.dump(jsonValues, f, indent=4)
        return redirect(url_for("setupLandingPage"))


@app.route('/setup/printers', methods = ["GET", "POST"])
@auth.login_required(role = ["manager", "developer"])
def setupPrinters():
    if request.method.lower() == "get":
        body = f'''
        <h1>Add Printer</h1>
        <form method="post">
            <label for="">Printer Nickname:</label>
            <input type="text" id="nickname" name="nickname">
            <br>
            <label for="ip">IP Address:</label>
            <input type="text" id="ip" name="ip">
            <br>
            <label for="apiKey">API Key:</label>
            <input type="text" id="apiKey" name="apiKey">
            <br>
            <label for="printer">Printer Type:</label>
            <br>
            <label for="mk3">Mk3S (Octoprint)</label>
            <input type="radio" id="mk3" name="printer" value="mk3">
            <br>
            <label for="mk4">Mk4 (PrusaConnect)</label>
            <input type="radio" id="mk4" name="printer" value="mk4">
            <br>
            <label for="prefix">Two Character Prefix:</label>
            <input type="text" id="prefix" name="prefix">
            <br>
            <input type="hidden" id="final" value="false" name="final">
            <input type="submit" value="Add printer">
        </form>
        '''
        return body
    elif request.method.lower() == "post" and request.form.get("final").lower() == "false":
        body = ""
        nickname = request.form.get("nickname")
        ipAddr = request.form.get("ip")
        if not ipAddr.startswith("http://") or not ipAddr.startswith("https://"):
            ipAddr = "http://" + ipAddr
        apiKey = request.form.get("apiKey")
        isMk3 = request.form.get("printer").lower() == "mk3"
        prefix = request.form.get("prefix")
        if isMk3:
            try:
                req = requests.get(f'{ipAddr}/api/printer',
                                   headers={"X-API-KEY": f'{apiKey}'})
                body += f'<h3 style="color:green"> {nickname} is reachable via HTTP</h3>'
                octoprint = True
                if not req.ok:
                    body += f'<h3 style="color:orange"> {nickname} is not operational on Octoprint </h3>'
                else:
                    if not req.json()["state"]["flags"]["operational"]:
                        body += f'<h3 style="color:orange"> {nickname} is not operational on Octoprint via flags</h3>'
                    else:
                        body += f'<h3 style="color:green"> {nickname} is operational via Octoprint</h3>'
            except Exception as e:
                print(e)
                octoprint = False
                body += f'<h3 style="color:red"> {nickname} is not reachable via HTTP</h3>'
        else:
            try:
                req = requests.get(f'{ipAddr}/api/v1/status',
                                   headers={"X-API-KEY": f'{apiKey}'})

                body += f'<h3 style="color:green"> {nickname} is reachable via HTTP</h3>'
                if req.ok:
                    body += f'<h3 style="color:green"> {nickname} API Key is functional</h3>'
                else:
                    body += f'<h3 style="color:red"> {nickname} API Key is NOT functional</h3>'
            except Exception as e:
                print(e)
                body += f'<h3 style="color:red"> {nickname} is not reachable via HTTP</h3>'
        body += f'''
        <form method="post">
            <input type="hidden" id="nickname" value="{nickname}" name="nickname">
            <input type="hidden" id="ip" value="{ipAddr}" name="ip">
            <input type="hidden" id="apiKey" value="{apiKey}" name="apiKey">
            <input type="hidden" id="{'mk3' if isMk3 else 'mk4'}" name="printer" value="{'mk3' if isMk3 else 'mk4'}">
            <input type="hidden" id="prefix" value="{prefix}"name="prefix">
            <input type="hidden" id="final" value="true" name="final">
            <input type="submit" value="Confirm addition">
        </form>
        '''
        return body
    elif request.method.lower() == "post" and request.form.get("final").lower() == "true":
        nickname = request.form.get("nickname")
        ipAddr = request.form.get("ip")
        if not ipAddr.startswith("http://") or not ipAddr.startswith("https://"):
            ipAddr = "http://" + ipAddr
        apiKey = request.form.get("apiKey")
        isMk3 = request.form.get("printer").lower() == "mk3"
        prefix = request.form.get("prefix")

        jsonAddition = {
            f'{nickname}' : {
            "ipAddress" if isMk3 else "Mk4IPAddress": ipAddr,
            "apiKey": apiKey,
            "prefix": prefix
            }
        }
        with open(f"{cwd}/ref/config.json", "r") as f:
            jsonValues = json.load(f)
            jsonValues[nickname] = {
            "ipAddress" if isMk3 else "Mk4IPAddress": apiKey,
            "apiKey": apiKey,
            "prefix":prefix
            }
        with open(f"{cwd}/ref/config.json", "w") as f:
            json.dump(jsonValues, f, indent=4)
        return redirect(url_for("setupLandingPage"))

@app.route("/download/config")
@auth.login_required(role = ["developer"])
def downloadConfig():
    return send_file(f"{cwd}/ref/config.json")

@auth.error_handler
def auth_error(status):
    return "You don't have access to this page. You likely don't need it. These pages are often restricted to leads and developers as they contain important database management tools, system configuration,account management, and debug information. If you think this is a mistake, talk to a developer or lead", status
if __name__ == '__main__':
    threads = []
    if configExists:
        for camera in liminal.cameras:
            #Camera buffer
            camThread = threading.Thread(target=camera.backgroundLogger)
            threads.append(camThread)
            #Timelapse logger
            camThread = threading.Thread(target=camera.timelapseLogger)
            threads.append(camThread)

        threads.append(threading.Thread(target=liminal.printWatcher))

    for thread in threads:
        thread.start()
    app.run("0.0.0.0", 8000, liminal.debugging)
