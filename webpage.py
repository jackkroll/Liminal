#https://flask.palletsprojects.com/en/2.2.x/patterns/fileuploads/#a-gentle-introduction
from flask import Flask, request, send_file

app = Flask(__name__)

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
    file.save(file.filename)
    return """<html> 
    <body> <h1> yayyyy </h1> </body> </html>"""

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')