#https://flask.palletsprojects.com/en/2.2.x/patterns/fileuploads/#a-gentle-introduction
from flask import Flask, request, send_file, Response, url_for
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
@app.route("/", methods=["GET"])
def home():
    body = '''<head>
    <link href=
"https://cdn.jsdelivr.net/npm/bootstrap@5.1.1/dist/css/bootstrap.min.css"
          rel="stylesheet">
    <script src=
"https://cdn.jsdelivr.net/npm/bootstrap@5.1.1/dist/js/bootstrap.bundle.min.js">
    </script>
</head>'''
    if showNotif:
        body += f'''
        <div class="alert alert-{alertType} alert-dismissible" role="alert">
        <strong>{notificationTitle}</strong> {notificationBody}
        <button type="button" class="btn-close" 
          data-bs-dismiss="alert"
          aria-label="Close">
        </button>
        </div>
        '''
    return body

if __name__ == '__main__':
    app.run("0.0.0.0", 8000, True)