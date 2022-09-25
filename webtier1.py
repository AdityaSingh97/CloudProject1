from contextlib import nullcontext
from crypt import methods
from fileinput import filename
import uuid
import os
from flask import Flask, request
from flask_socketio import SocketIO
from threading import Thread
#from werkzeug.utils import secure_filename
from threading import Thread
from constants import *
from helper import *
import boto3
import json
import time
import base64

