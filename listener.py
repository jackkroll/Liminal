from flask import Flask, request, send_file
app = Flask(__name__)

@app.route("/api/printer", methods = ["POST"])
def addedPrinter():
    request.remote_addr