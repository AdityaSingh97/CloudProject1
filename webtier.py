from contextlib import nullcontext
from crypt import methods
from fileinput import filename
import uuid
import os
from flask import Flask, render_template, request
from flask_socketio import SocketIO
from threading import Thread
from werkzeug.utils import secure_filename
from threading import Thread
from webtier_helper import * 
from constants import *
from helper import *

#defining some required variables
request_queue_url = ''
response_queue_url = ''
images = []
jobs= {}
is_get = True

app= Flask(__name__)

socket = SocketIO(app)
socket.init_app(app,cors_allowed_origins = "*")     #allows cross origin

@app.route('/',methods=['GET','POST'])
def home_page():
    is_get = (request.method == 'GET')
    job_id = str(uuid.uuid4())

    images = []
    received =[]
    if not is_get:
        received = request.files.getlist("file")
        for file in received:
            if file and allowed_file(file.filename):
                with open(file,"rb") as img_file:
                    b64_string = base64.b64encode(img_file.read())
                images.append(file)
                print("file uploaded", filename)
            process_image(request_queue_url, b64_string, job_id)
        jobs[job_id] = len(images)
        print("images", images)

        #need to set new threads and listen for results
        spawn = Thread(target=spawn_processing_apps, args =(request_queue_url,job_id,))
        spawn.start()

        listen-Thread(target=listen_for_results, args=(socket, response_queue_url,job_id,jobs,))
        listen.start()

    return nullcontext

@socket.on('connect')
def connected():
    print('connected')
    socket.emit('on_connect', is_get)

@socket.on('disconnect')
def disconnected():
    print('disconnected')

request_queue_url,response_queue_url = setup_aws_resources()

if __name__ == '__main__':
    print("listening")
    socket.run(
        app,
        host = "0.0.0.0",
        port=5000
    )

