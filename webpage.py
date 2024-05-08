#https://flask.palletsprojects.com/en/2.2.x/patterns/fileuploads/#a-gentle-introduction
from flask import Flask, request, send_file, Response, url_for
from datetime import datetime
import random, requests
from firebase_admin import credentials, initialize_app, storage
from datetime import datetime
app = Flask(__name__)
thing = 5
@app.route("/", methods=["GET"])
def home():
    body = f'''<form action="{url_for("test")}"; method = post>
  <label for="date">Request:</label>
  <input type="datetime-local" id="date" name="date">
  <input type="submit">
</form>
'''
    return body
@app.route("/flip", methods = ["POST"])
def test():
    print(request.form.get("date"))
    format = "%Y-%m-%dT%H:%M"
    date = datetime.strptime(request.form.get("date"),format)

    return 'yea'

if __name__ == '__main__':
    app.run("0.0.0.0", 8000, True)