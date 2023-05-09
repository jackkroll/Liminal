#https://flask.palletsprojects.com/en/2.2.x/patterns/fileuploads/#a-gentle-introduction
from flask import Flask, request, send_file
from firebase_admin import credentials, initialize_app, storage

app = Flask(__name__)
cred = credentials.Certificate('C:\\Users\\HS.Robotics\\Downloads\\liminal-302-cred.json')
initialize_app(cred, {'storageBucket': 'liminal-302.appspot.com'})

bucket = storage.bucket()
@app.route('/')
def index():
    return '''
        <html>
            <body>
                <h1>File Uploader</h1>
                <form method="POST" action="/upload" enctype="multipart/form-data">
                    <input type="file" name="file">
                    <input type="submit" value="Upload">
                </form>
            </body>
        </html>
    '''

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    fileName = ("C:\\Users\\HS.Robotics\\Downloads\\SpEnCer.PNG")
    blob = bucket.blob(fileName)
    blob.upload_from_filename(fileName)
    blob.make_public()
    #print("your file url", blob.public_url)
    return """<html> 
    <body> <h1> yayyyy </h1> </body> </html>"""

if __name__ == '__main__':
    app.run(debug=True, host='localhost')