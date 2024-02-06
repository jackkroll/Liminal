import datetime
import os
import time
import sys

from flask import Flask, render_template, Response, url_for, send_file
import cv2

app = Flask(__name__)

if sys.platform == "win32":
    cwd = "C:/Users/jackk/Desktop/Liminal"
else:
    cwd = "/home/jack/Documents/Liminal-master"
class Camera():
    def __init__(self, cameraNumber):
        self.printer = None
        self.buffer = []
        self.frameRate = 24
        self.rollingTime = 30
        self.camera = cv2.VideoCapture(cameraNumber)
        self.cameraNumber = cameraNumber

    def gen_frames(self):
        print("other")
        while True:
            print("gen")
            success, frame = self.camera.read()
            if not success:
                break
            else:
                self.buffer.append(frame)
                if len(self.buffer) >= (self.frameRate * self.rollingTime):
                    for number in range(0, len(self.buffer) - (self.frameRate * self.rollingTime)):
                        del self.buffer[:number]
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

cameras = [Camera(0)]

@app.route('/camera/raw/<path:cameraNum>')
def video_feed(cameraNum):
    selectedCam = cameras[int(cameraNum)]
    return Response(selectedCam.gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route('/camera/fetchlast30/<path:cameraNum>')
def last30Sec(cameraNum):
    selectedCam = cameras[int(cameraNum)]
    fileName = datetime.datetime.now().strftime("%X%m%d%y")
    result = cv2.VideoWriter(f"/videos/clips/{fileName}.mp4", cv2.VideoWriter_fourcc(*'mp4v'), selectedCam.frameRate, (640, 480))
    for frame in selectedCam.buffer:
        result.write(frame)
    result.release()
    return send_file(f"{cwd}/videos/clips/{fileName}.mp4")

@app.route('/')
def cctv():
    body = "<html><body style = background-color:black>"
    for camera in cameras:
        body += f"""<img src="{url_for("video_feed", cameraNum = camera.cameraNumber)}" alt="Video Stream">
                <a href='{url_for("last30Sec", cameraNum = camera.cameraNumber)}' download>
                <h1> Download last 30 Seconds </h1>
                </a>
        """
    return body



if __name__ == '__main__':
    app.run(debug=True, host= "0.0.0.0", port= 8000)