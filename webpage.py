#https://flask.palletsprojects.com/en/2.2.x/patterns/fileuploads/#a-gentle-introduction
from flask import Flask, request, send_file
from firebase_admin import credentials, initialize_app, storage

app = Flask(__name__)

@app.route('/')
def index():
    while True:
        yield( '''
            <html>
                <body>
                    <h1>File Uploader</h1>
                    <form method="POST" action="/upload" enctype="multipart/form-data">
                        <input type="file" name="file">
                        <input type="submit" value="Upload">
                    </form>
                </body>
            </html>
        ''')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']

    blob = bucket.blob(file)
    blob.upload_from_filename(file)
    blob.make_public()
    #print("your file url", blob.public_url)
    return """<html> 
    <body> <h1> yayyyy </h1> </body> </html>"""

if __name__ == '__main__':
    app.run("0.0.0.0", 8000, False)