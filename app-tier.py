import app-helper
import base64
from image_classification import *
import os


def image_classification(img_encode):
    with open("imageToSave.jpg", "wb") as decoded_img:
        decoded_img.write(base64.decodebytes(img_encode))
    #img = Image.open(r"{x}".format(x=job_id))
    if object_name is None:
        object_name = os.path.basename("imageToSave.jpg")
    try:
        response = upload_file(file_to_store, BUCKET_NAME, '{}{}'.format("imageToSave.jpg",S3_INPUT_FOLDER))
    except ClientError as e:
        logging.error(e)
    print('uploaded file to bucket')
    result = classify("imageToSave.jpg")
    os.remove("./imageToSave.jpg")
    return(result)

# GET REQUEST & RESPONSE QUEUE URLS
request_queue_url = get_queue_url(REQUEST_QUEUE_NAME)
response_queue_url = get_queue_url(RESPONSE_QUEUE_NAME)

jobs_processed = 0

MAX_RETRIES = 12
CURR_RETRIES = 0
while (CURR_RETRIES < MAX_RETRIES):
    # 1) receive message from request queue
    imageid_from_request_queue_url = receive_message(request_queue_url, 1)
    if 'Messages' in imageid_from_request_queue_url:
        message = imageid_from_request_queue_url['Messages'][0]
        body_string = message['Body']
        # print('message was -> {}'.format(body_string))
        body = json.loads(body_string)
        image_enc = body['image']
        job_id = body['job_id']
        img_name = body['name']
#         print('reading from bucket {}'.format(BUCKET_NAME))
# # 2) get image from s3
#         read_from_bucket(BUCKET_NAME, '{}{}'.format(S3_INPUT_FOLDER, image_id))

# 3) process image and return result
        #image_classification_output = image_classification(body_string)
        image_classification_output = image_classification(image_enc)
        response_queue_message = '({}, {})'.format(
            "imagereceived", image_classification_output)
        print('result classification was {}'.format(response_queue_message))

# 4) store result in s3 and put in response queue
        file_to_store = '{}_Result.txt'.format(image_id)
        s3_writetofile = open(file_to_store, "w+")
        s3_writetofile.write(response_queue_message)
        s3_writetofile.close()

        upload_file(file_to_store, BUCKET_NAME, '{}{}'.format(S3_OUTPUT_FOLDER, file_to_store))
        print('uploaded file to bucket')
        send_message(response_queue_url, {}, job_id, response_queue_message)
        print('sent message to queue')

# 5) delete message from request queue
        receipt_handle = message['ReceiptHandle']
        delete_message(request_queue_url, receipt_handle)
        print('deleted message from queue')

# 6) Listen for requests before terminating
        CURR_RETRIES = 0
        jobs_processed += 1
    else:
        CURR_RETRIES += 1

# 7) Add logic to terminate instance
# instanceid_to_kill = get_instance_id()
# print('instance id - {}, processed {} jobs and will be terminated now'.format(
#     instanceid_to_kill, jobs_processed))
# terminate_instance(instanceid_to_kisll)

