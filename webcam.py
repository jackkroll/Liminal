import os
import time

from flask import Flask, render_template, Response, url_for, send_file
from PIL import ImageDraw, Image
import numpy as np

from datasets import load_dataset
from huggingface_hub import hf_hub_download
import torch
import cv2

app = Flask(__name__)

camera = cv2.VideoCapture(0)
bufferVid = []
frameRate = 24
rollingTime = 30

def gen_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            bufferVid.append(frame)
            if len(bufferVid) >= (frameRate * rollingTime):
                for number in range(0, len(bufferVid) - (frameRate * rollingTime)):
                    del bufferVid[:number]
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')



@app.route('/videoRaw')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route('/last30Sec')
def last30Sec():
    result = cv2.VideoWriter("OutputVideo.mp4", cv2.VideoWriter_fourcc(*'mp4v'), frameRate, (640, 480))
    for frame in bufferVid:
        result.write(frame)
    result.release()
    return send_file(r"C:\Users\jackk\Desktop\Liminal\OutputVideo.mp4")
@app.route('/')
def main():

    return f"""
     <img src='{url_for("video_feed") }'width="640" height="480">
     <a href='{url_for("last30Sec")}' download>
          <h1> Download last 30 Seconds </h1>
     </a>
    """


if __name__ == '__main__':
    app.run(debug=True, host= "0.0.0.0", port= 8000)