from flask import Flask, request, send_file
from firebase_admin import credentials, initialize_app, storage
from main import SinglePrinter, Liminal
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
            #Implement time remaining methods
        else:
            body += f"<h3>Upload your print!<\h3>"
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


if __name__ == '__main__':
    app.run(debug=True, host="localhost", port= 8000)