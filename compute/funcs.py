import requests
import time
import os
from datetime import datetime
import random
import string
import yaml
import kubernetes as k
import json

MINIO_URL = os.environ.get('MINIO_URL','minionas.uvadcos.io/')
MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY')
MINIO_SECRET = os.environ.get('MINIO_SECRET')

ORS_URL = os.environ.get("ORS_URL","ors.uvadco.io/")

def track(job_id):

    r = requests.post('http://localhost:5001/track',json = {'job_id':job_id})

    if r.status_code != 200:

        return r.status_code

    return r.content.decode()

def mint_ouput_ids(job_id):

    pass

def delete_service(service_def):

    pass

def create_service(service_def):

    k.config.load_incluster_config()

    v1 = k.client.CoreV1Api()

    try:
        resp = v1.create_namespaced_service(
                    body = service_def,namespace="default")

    except:

        return False

    return True

def create_pod(pod_def):

    k.config.load_incluster_config()

    v1 = k.client.CoreV1Api()

    try:
        resp = v1.create_namespaced_pod(
                    body = pod_def,namespace="default")

    except:

        return False

    return True

def update_pod_service_yaml(data_location,script_location,job_id):

    with open("pod.yaml") as f:

        pod = yaml.safe_load(f)

    with open("service.yaml") as f:

        service = yaml.safe_load(f)

    service['metadata']['name'] = "sparkjob-" + job_id

    service['spec']['selector']['app'] = "sparkjob-" + job_id

    pod['metadata']['name'] = "sparkjob-" + job_id

    pod['spec']['containers'][0]['name'] = "sparkjob-" + job_id

    pod['metadata']['labels']['app'] = "sparkjob-" + job_id

    pod['spec']['containers'][0]['command'].append("--conf")

    pod['spec']['containers'][0]['command'].append("spark.hadoop.fs.s3a.endpoint=" + MINIO_URL)

    pod['spec']['containers'][0]['command'].append("--conf")

    pod['spec']['containers'][0]['command'].append("spark.hadoop.fs.s3a.access.key=" + MINIO_ACCESS_KEY)

    pod['spec']['containers'][0]['command'].append("--conf")

    pod['spec']['containers'][0]['command'].append("spark.hadoop.fs.s3a.secret.key=" + MINIO_SECRET)

    pod['spec']['containers'][0]['command'].append(script_location)

    pod['spec']['containers'][0]['command'].append(data_location)

    pod['spec']['containers'][0]['command'].append(job_id)

    return pod, service

def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

def gather_inputs(request):

    if request.data == b'':

        return False, "Please POST json with keys, Dataset Identifier,\
                Job Identifier, and Main Function"
        (jsonify({'error':"Please POST json with keys, Dataset Identifier,\
                Job Identifier, and Main Function",'valid':False}))

    try:

        inputs = json.loads(request.data.decode('utf-8'))

    except:

        return False,"Please POST JSON file"
        (jsonify({'error':"Please POST JSON file",'valid':False}))

    return True, inputs

def validate_input(id):
    """Validates that given identifier exists in Mongo.
        Returns location in minio. """
    r = requests.get(ORS_URL + datasetid)

    if r.status_code != 200:

        return False, "Identifier Doesn't Exist"

    try:

        data_dict = r.json()

        data_url = data_dict['distribution'][0]['contentUrl']

        file_location = '/'.join(data_url.split('/')[1:])

    except:

        return False, "Distribution not in right spot"

    return True, file_location

def mint_job_id(data_id,script_id):

    return True, randomString(10)

    base_meta = {
        "@type":"eg:Computation",
        "began":datetime.fromtimestamp(time.time()).strftime("%A, %B %d, %Y %I:%M:%S"),
        "eg:usedDataset":data_id,
        "eg:usedSoftware":script_id
    }

    url = ORS_URL + "shoulder/ark:99999"

    r = requests.post(url, data=json.dumps(base_meta))
    returned = r.json()

    if 'created' in returned:

        return True, returned['id']

    return False, 0