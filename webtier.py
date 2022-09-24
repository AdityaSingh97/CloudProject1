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
from constants import *
from helper import *
import boto3
import json
import time
import base64

def process_image(request_queue_url, b64_string, filename, job_id):
    message_attr = {}
    body_object = {
        'image': b64_string,
        'name': filename,
        'job_id': job_id
    }
    body = json.dumps(body_object)
    send_message(request_queue_url, message_attr, job_id, body)

def spawn_processing_apps(request_queue_url, job_id):
    q_length = int(get_one_queue_attribute(request_queue_url))

    running = get_running_app_tiers_ids()
    max_new = MAX_APP_TIERS - running
    num_instances = min(q_length, max_new)

    create_instance(
        KEY_NAME,
        SECURITY_GROUP_ID,
        image_id=AMI_IMAGE_ID,
        min_count=num_instances,
        max_count=num_instances
    )
    
def get_running_app_tiers_ids():
    curr_ins_id = get_instance_id()
    ec2_res = boto3.resource('ec2')
    instances = ec2_res.instances.filter(
        Filters =[
            {
                'Name':'instance-state-name',
                'Values': ['running']
            }
        ]
    )
    instance_ids = []
    for instance in instances:
        if instance.id != curr_ins_id:
            instance_ids.append(instance.id)
    return len(instance_ids)

def listen_for_results(socketio, response_queue_irl, job_id, job_dictionary):
    res_rec = 0
    j_length = job_dictionary[job_id]
    socketio.emit('processing_start', j_length)
    while res_rec != j_length:
        resp = receive_message(response_queue_irl, 1)
        if 'Messages' in resp:
            message = resp['Messages'][0]
            result = message['Body']
            body = json.loads(result)
            print(body['image_classification_result'])
            res_rec += 1
            response = {
                'result': result,
                'total': j_length
            }
            socketio.emit(
                'partial_result', json.dumps(response)
            )
            receipt_handle = message['ResceiptHandle']
            delete_message(response_queue_irl, receipt_handle)
    socketio.emit('processing_end', '')

def setup_aws_resources():
    create_bucket(BUCKET_NAME_INPUT)
    create_bucket(BUCKET_NAME_OUTPUT)

    request_queue_url = create_queue(REQUEST_QUEUE_NAME, QUEUE_ATTRIBUTES)

    response_queue_url = create_queue(RESPONSE_QUEUE_NAME, QUEUE_ATTRIBUTES)

    return request_queue_url, response_queue_url

def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
            print("checking before allowed filename")
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                with open(file,"rb") as img_file:
                    b64_string = base64.b64encode(img_file.read())
                images.append(file)
                print("file uploaded", filename)
            process_image(request_queue_url, b64_string,filename, job_id)
        jobs[job_id] = len(images)
        print("images", images)

        #need to set new threads and listen for results
        spawn = Thread(target=spawn_processing_apps, args =(request_queue_url,job_id,))
        spawn.start()

        listen = Thread(target=listen_for_results, args=(socket, response_queue_url,job_id,jobs,))
        listen.start()


    return "done"

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

