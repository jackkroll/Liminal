#https://flask.palletsprojects.com/en/2.2.x/patterns/fileuploads/#a-gentle-introduction
from flask import Flask, request, send_file, Response, url_for
from datetime import datetime
import random, requests
from firebase_admin import credentials, initialize_app, storage

app = Flask(__name__)
thing = 5
@app.route("/", methods=["GET"])
def home():
    #print(requests.get(url_for("coinflip")))
    thing = 3
    if thing <= 5:
        return """
    <meta http-equiv="refresh" content="1" /> 
    Hello World!<br>The current time is {}.""".format(datetime.strftime(datetime.now(), "%d %B %Y %X"))
    else:
        return "<h1>YIPPEEEE</h1>"
@app.route("/flip")
def coinflip():
    return random.choice(["heads", "tails"])

if __name__ == '__main__':
    app.run("0.0.0.0", 8000, True)