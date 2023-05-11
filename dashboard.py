from flask import Flask, request, send_file
from firebase_admin import credentials, initialize_app, storage
from main import SinglePrinter
app = Flask(__name__)
#Left Printer,http://10.110.8.77 ,FCDAE0344C424542B80117AF896B62F6
#Middle Printer, http://10.110.8.110, 6273C0628B8B47E397CA4554C94F6CD5
#Right Printer,http://10.110.8.100 ,33A782146A5A48A7B3B9873217BD19AC
printers = [SinglePrinter("Left Printer", "http://10.110.8.77","FCDAE0344C424542B80117AF896B62F6"),SinglePrinter("Middle Printer", "http://10.110.8.110","6273C0628B8B47E397CA4554C94F6CD5"),SinglePrinter("Right Printer", "http://10.110.8.100","33A782146A5A48A7B3B9873217BD19AC")]
@app.route('/')
def index():
    body = "<html><body>"
    for printer in printers:
        body += f"<h1>{printer.nickname}</h1>"
        body += f"<h3>{printer.temps()}"
        print(printer.temps[1]
    body += "</html></body>"

    return body

if __name__ == '__main__':
    app.run(debug=True, host='localhost')