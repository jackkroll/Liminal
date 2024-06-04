import datetime,json,random,time,string,os,sys, threading, cv2, requests
from flask import Flask, request, send_file, redirect, url_for, Response
from firebase_admin import credentials, initialize_app, storage
from main import IndividualPrint,SinglePrinter, Liminal,PrintLater
import firebase_admin
from firebase_admin import credentials, firestore
import numpy as np
from datetime import datetime
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
liminal = Liminal()
#autoUpdateTest2
auth = HTTPBasicAuth()

if sys.platform == "win32":
    cwd = "C:/Users/jackk/PycharmProjects/Liminal"
else:
    cwd = "/home/jack/Documents/Liminal-master"



@auth.verify_password
def verify_password(username, password):
    file = open((f"{cwd}/ref/config.json"))
    jsonValues = json.load(file)
    file.close()
    users = jsonValues["students"]
    username = username.lower()
    if username.capitalize in users:
        if users[username.capitalize()]["hash"] == password:
            return True
    return True

@auth.get_user_roles
def get_user_roles(username):
    #if user in ["jack", "luke"]:
    #    return ["developer"]
    #elif user in ["spencer", "katia"]:
    #    return ["manager"]
    #else:
    #    return ["student"]
    file = open((f"{cwd}/ref/config.json"))
    jsonValues = json.load(file)
    file.close()
    users = jsonValues["students"]
    username = username.lower()
    return jsonValues["students"][username.capitalize()]["role"]

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
    file = open((f"{cwd}/ref/values.json"))
    jsonValues = json.load(file)
    file.close()
    if request.args.get("later") == "true":
        printLaterEnabled = True
    else:
        printLaterEnabled = False
    print(printLaterEnabled)
    addedPrinters = 0
    file =open((f"{cwd}/ref/config.json"))
    config = json.load(file)
    file.close()
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
                body += '<div style="display:flex;">'
                body += f'<h1 class="printerTitle"><a href = http://{printer.ip};style="color:{liminal.systemColor}">{printer.nickname}</a> </h1>'
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
    if addedPrinters == 0:
        body += f'<h3 style="color:white;">No printers available/online, consult dev menu for debugging</h3>'
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
            return redirect(url_for("index"))
        else:
            print(request.form.get(""))
            for printer in liminal.printers + liminal.MK4Printers:
                if request.form.get("printer") == printer.nickname:
                    printer.preheat()
            return redirect(url_for("index"))

@app.route('/cooldown', methods = ["POST"])
@auth.login_required(role = ["student", "manager", "developer"])
def cooldown():
    for printer in liminal.printers + liminal.MK4Printers:
        if request.form.get("printer") == printer.nickname:
            printer.cooldown()
            return True

@app.route('/pause', methods = ["POST"])
@auth.login_required(role = ["student", "manager", "developer"])
def pausePrint():
    if request.form.get("printer") == "all":
        for printer in liminal.printers:
            printer.pause()
        return redirect(url_for("index"))
    else:
        for printer in liminal.printers:
            if request.form.get("printer") == printer.nickname:
                printer.pause()
                return redirect(url_for("index"))
        for printer in liminal.MK4Printers:
            if request.form.get("printer") == printer.nickname:
                printer.pause()

@app.route('/resume', methods = ["POST"])
@auth.login_required(role = ["student", "manager", "developer"])
def resumePrint():
    if request.form.get("printer") == "all":
        for printer in liminal.printers:
            printer.resume()
        return redirect(url_for("index"))
    else:
        for printer in liminal.printers:
            if request.form.get("printer") == printer.nickname:
                printer.resume()
                return redirect(url_for("index"))
        for printer in liminal.MK4Printers:
            if request.form.get("printer") == printer.nickname:
                printer.resume()
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
                    return "Unable to get HTTP form data"


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
                        return redirect(url_for("mk4LoadingScreen", printerNickname = printer.nickname))
                        print("[OPERATIONAL] Successfully printed onto a Mk4 printer")
                    else:
                        print(f"[ERROR] The printer {request.form.get('printer')} is not registered")
                        return f"The printer {request.form.get('printer')} is not registered"
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
                    return "Your print was successfully uploaded to the printer but was not saved to the cloud."

                return f"Your print was successfully uploaded and documented. The unique code for your print is: {individualPrint.uuid}"
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
        with open(f"{cwd}/ref/values.json", "r") as f:
            setOnline = request.form.get("printer")
            jsonValues = json.load(f)
            jsonValues["printersDown"].remove(setOnline)
        with open(f"{cwd}/ref/values.json", "w") as f:
            json.dump(jsonValues,f,indent=4)
        return redirect(url_for("setPrinterStatus"))

@app.route('/dev/ip',methods = ["GET", "POST"])
@auth.login_required(role="developer")
def changeIPAddr():
    if request.method == "GET":
        return redirect(url_for("setPrinterStatus"))
    else:
        with open(f"{cwd}/ref/config.json", "r") as f:
            changedIP = request.form.get("printer")
            newAddress = request.form.get("addr")
            jsonValues = json.load(f)
            jsonValues[changedIP]["ipAddress"] = newAddress
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
        with open(f"{cwd}/ref/values.json", "r") as f:
            setOnline = request.form.get("printer")
            jsonValues = json.load(f)
            jsonValues["printersDown"].append(setOnline)
        with open(f"{cwd}/ref/values.json", "w") as f:
            json.dump(jsonValues, f, indent=4)
        return redirect(url_for("setPrinterStatus"))

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
    for item in jsonValues:
        if "ipAddress" in jsonValues[item]:
            body += f'<h1 style="color:{liminal.systemColor}"> {item} </h1>'
            try:
                req = requests.get(f'{jsonValues[item]["ipAddress"]}/api/printer', headers={"X-API-KEY": f'{jsonValues[item]["apiKey"]}'})
                body += '<h3 style="color:green"> Printer is reachable via HTTP</h3>'
                octoprint = True
                if not req.ok:
                    body += '<h3 style="color:orange"> Printer is not operational on Octoprint </h3>'
                else:
                    if not req.json()["state"]["flags"]["operational"]:
                        body += '<h3 style="color:orange"> Printer is not operational on Octoprint via flags</h3>'
                    else:
                        body += '<h3 style="color:green"> Printer is operational via Octoprint</h3>'
            except Exception as e:
                print(e)
                octoprint = False
                body += '<h3 style="color:red"> Printer is not reachable via HTTP</h3>'
            nicknames = []
            for printer in liminal.printers + liminal.MK4Printers:
                nicknames.append(printer.nickname)
                if printer.nickname == item and octoprint:
                    percentUsed = printer.percentUsed()
                    if percentUsed > 90:
                        color = "red"
                    elif percentUsed > 75:
                        color = "orange"
                    elif percentUsed > 60:
                        color = "yellow"
                    else:
                        color = "green"
                    body += f'<h3 style="color:{color}"> {int(percentUsed)}% of onboard storage used</h3>'
            if item in nicknames:
                body += '<h3 style="color:green"> Printer registered in LMNL</h3>'
            else:
                body += '<h3 style="color:red"> Printer is not registered in LMNL</h3>'


            body += f"""
            <form style="color:white" action="{url_for('changeIPAddr')}" method="post", enctype="multipart/form-data">
            <input type="hidden" name="printer" value="{item}">
            <input type="text" name="addr" value="{jsonValues[item]["ipAddress"]}">
            <button type="submit">Update IP Address</button>
            </form>
            """
        if "Mk4IPAddress" in jsonValues[item]:
            body += f'<h1 style="color:{liminal.systemColor}"> {item} </h1>'
            body += f"""
            <form style="color:white" action="{url_for('changeIPAddrMK4')}" method="post", enctype="multipart/form-data">
            <input type="hidden" name="printer" value="{item}">
            <input type="text" name="addr" value="{jsonValues[item]["Mk4IPAddress"]}">
            <button type="submit">Update IP Address</button>
            </form>
            """
            for printer in liminal.MK4Printers:
                if printer.nickname == item:
                    if printer.serial != None:
                        body += '<h3 style="color:green">Connected via serial</h3>'
                    else:
                        body += '<h3 style="color:orange">Serial connection failed</h3>'
                    if printer.freeSpace != None:
                        body += f'<h3 style="color:blue">{printer.freeSpace/1_000_000_000}gb free on {printer.storageName}</h3>'
                    else:
                        body += f'<h3 style="color:orange">Could not determine free storage on {printer.storageName}, likely due to no Prusa API support</h3>'
    body += """
    <h1 style="color:red"> WARNING: Changing these values may result in this software not recognizing printers, only do this if you know what you're doing </h1>
    """
    return body

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
    file = open(f"{cwd}/ref/values.json")
    jsonValues = json.load(file)
    file.close()
    printerOptions = []
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
    body = f"You don't have access to this page, you likely don't need it. Talk to a lead or a developer about this error"
    return body
@app.errorhandler(403)
def forbidden(error):
    body = f"You don't have access to this page, you likely don't need it. Talk to a lead or a developer about this error"
    return body
@app.errorhandler(404)
def notFound(error):
    body = f'<img src= "https://i.redd.it/x3tgtg5hniyb1.jpeg" alt = "THEREWASAMISINPUT">'
    body += "<h3>This page doesn't exist, either me or you misinput something</h3>"
    return body
@app.route('/timelapse')
@auth.login_required()
def timelapse():
    try:
        return send_file(f"Clip.mp4")
    except:
        return "Error downloading last timelapse..."
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
def troubleMakrer():
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
        return "Print has been scheduled!"
    else:
        return f'Printer "{request.form.get("printer")}" not found'

@app.route('/account/reset/<username>')
@auth.login_required(role=["developer", "manager"])
def resetPassword(username):
    return f"Incomeplete method for account reset for user {username}"
@app.route('/account/remove/<username>')
@auth.login_required(role=["developer", "manager"])
def removeUser(username):
    return f"Incomeplete method for account deletion for user {username}"

@app.route('/account/modify/<username>')
@auth.login_required(role=["developer", "manager"])
def updateUser(username):
    return f"Incomeplete method for account modification for user {username} to be set to {request.args.get('role')}"
@app.route('/account/add')
@auth.login_required(role=["developer", "manager"])
def addUser():
    return f"Incomeplete method for account addition for new user {request.args.get('name')} to be set to {request.args.get('role')}"
@app.route('/account')
@auth.login_required(role=["developer", "manager"])
def accountManger():
    file = open((f"{cwd}/ref/config.json"))
    jsonValues = json.load(file)
    file.close()
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
        body += f'<div style="display:flex"> <h2 style="color:white; padding:5px">{account} - {jsonValues["students"][account]} </h3>'
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
        body += f'<a href="{url_for("resetPassword", username = account)}" class="interactionButton" style = "background-color:orange">Reset Password</a>'
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


@auth.error_handler
def auth_error(status):
    return "You don't have access to this page. You likely don't need it. These pages are often restricted to leads and developers as they contain important database management tools, system configuration,account management, and debug information. If you think this is a mistake, talk to a developer or lead", status
if __name__ == '__main__':
    threads = []
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
    app.run("0.0.0.0", 8000, True)
