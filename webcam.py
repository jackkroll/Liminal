import datetime
import os
import time
import sys
import asyncio
import threading

import numpy
import numpy as np
from flask import Flask, render_template, Response, url_for, send_file
import cv2

app = Flask(__name__)

if sys.platform == "win32":
    cwd = "C:/Users/jackk/Desktop/Liminal"
else:
    cwd = "/home/jack/Documents/Liminal-master"
class Camera():
    def __init__(self, cameraNumber, cameraIndex):
        self.printer = None
        self.buffer = []
        self.frameRate = 24
        self.rollingTime = 30
        self.resolution = (640,480)
        self.resolution = (1920,1080)
        self.camera = cv2.VideoCapture(cameraIndex)
        self.index = cameraIndex
        self.cameraNumber = cameraNumber

    def stream(self):
        while True:
            if len(self.buffer) > 0:
                yield (b'--frame\r\n'
                                       b'Content-Type: image/jpeg\r\n\r\n' + self.buffer[-1] + b'\r\n')
            else:
                yield ("None")
    def backgroundLogger(self):
        while True:
            success, frame = self.camera.read()
            if not success:
                print("[ERROR] Issue reading data from camera")
                break
            else:
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                self.buffer.append(frame)
                if len(self.buffer) >= (self.frameRate * self.rollingTime):
                    for number in range(0, len(self.buffer) - (self.frameRate * self.rollingTime)):
                        del self.buffer[:number]
                time.sleep(1/self.frameRate)

class CCTV():
    def __init__(self):
        self.cameras = []
        initalized = -1
        for i in range (10):
            initalized+=1
            self.cameras.append(Camera(initalized, i))
            if not self.cameras[-1].camera.read()[0]:
                initalized -= 1
                self.cameras.pop()
                print(f"Camera on port {i} unreachable")
            else:
                print(f"Camera Initalized on port {i}")

# for camera in cctv.cameras:
#     asyncio.run(camera.backgroundLogger())
@app.route('/camera/raw/<path:cameraNum>')
def video_feed(cameraNum):
    selectedCam = cctv.cameras[int(cameraNum)]
    return Response(selectedCam.stream(), mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route('/camera/fetchlast30/<path:cameraNum>')
def last30Sec(cameraNum):
    selectedCam = cctv.cameras[int(cameraNum)]
    fileName = datetime.datetime.now().strftime("%X%m%d%y")
    result = cv2.VideoWriter(f"{cwd}/videos/clips/{fileName}.mp4", cv2.VideoWriter_fourcc(*'mp4v'), selectedCam.frameRate,(1920,1080))
    for frame in selectedCam.buffer:
        result.write(cv2.imdecode(np.frombuffer(frame, np.uint8), cv2.IMREAD_COLOR))
    result.release()
    print("released")
    time.sleep(2)
    return send_file(f"{cwd}/videos/clips/{fileName}.mp4")

@app.route('/')
def cctvView():
    body = "<html><body style = background-color:black>"
    for camera in cctv.cameras:
        body += f"""<img src="{url_for("video_feed", cameraNum = camera.cameraNumber)}" alt="Video Stream">
                <a href='{url_for("last30Sec", cameraNum = camera.cameraNumber)}' download>
                <h1> Download last 30 Seconds </h1>
                </a>
        """
    return body


if __name__ == '__main__':
    threads = []
    cctv = CCTV()
    for camera in cctv.cameras:
        camThread = threading.Thread(target=camera.backgroundLogger)
        threads.append(camThread)
    for thread in threads:
        thread.start()
    app.run("0.0.0.0", 8000, False)

    # for camera in cctv.cameras:
    #     asyncio.run(camera.backgroundLogger())
