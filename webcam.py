import time

from flask import Flask, render_template, Response
from PIL import ImageDraw, Image
import numpy as np

from datasets import load_dataset
from huggingface_hub import hf_hub_download
import torch
import cv2

app = Flask(__name__)

camera = cv2.VideoCapture(0)


repo_id = "Javiai/3dprintfails-yolo5vs"
filename= "model_torch.pt"
#https://huggingface.co/Javiai/3dprintfails-yolo5vs
model_path = hf_hub_download(repo_id=repo_id, filename=filename)
dataset = load_dataset('Javiai/failures-3D-print')
model = torch.hub.load('Ultralytics/yolov5', 'custom', model_path, verbose = False)

def gen_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            img = Image.fromarray(np.uint8(frame)).convert('RGB')
            draw = ImageDraw.Draw(img)

            detections = model(frame)

            categories = [
                {'name': 'error', 'color': (0, 0, 255)},
                {'name': 'extruder', 'color': (0, 255, 0)},
                {'name': 'part', 'color': (255, 0, 0)},
                {'name': 'spaghetti', 'color': (0, 0, 255)}
            ]

            for detection in detections.xyxy[0]:
                x1, y1, x2, y2, p, category_id = detection
                x1, y1, x2, y2, category_id = int(x1), int(y1), int(x2), int(y2), int(category_id)
                draw.rectangle((x1, y1, x2, y2),
                               outline=categories[category_id]['color'],
                               width=1)
                draw.text((x1, y1), categories[category_id]['name'],
                          categories[category_id]['color'])


            ret, buffer = cv2.imencode('.jpg', np.array(img))
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')



@app.route('/')
def video_feed():
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')



if __name__ == '__main__':
    app.run(debug=True, host= "0.0.0.0", port= 8000)