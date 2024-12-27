#https://flask.palletsprojects.com/en/2.2.x/patterns/fileuploads/#a-gentle-introduction
from flask import Flask, request, send_file, Response, url_for, render_template

from main import SinglePrinter
from datetime import datetime
import random, requests
from firebase_admin import credentials, initialize_app, storage
from datetime import datetime
app = Flask(__name__)
thing = 5
notificationTitle = "Printer Maintenance"
notificationBody = "Please consult the manual :)"
alertType = "danger"
showNotif = True
printers = [SinglePrinter("Home Printer", "http://octopi.local", "ZKduVdsbbh92GGv06Xt_sen89sNTbNdgKkzDeu4RAac", "HP")]

@app.route("/", methods=["GET"])
def home():
    for printer in printers:
        printer.refreshData()
    return render_template("dashboard.html", printers=printers, currentUser = "yo mama")

if __name__ == '__main__':
    app.run("0.0.0.0", 8080, True)