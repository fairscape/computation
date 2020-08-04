import time,requests,json, sys, random, os, warnings, logging, threading
from datetime import datetime
from flask import Flask, render_template, request, redirect,jsonify
from funcs import *

MINIO_URL = os.environ.get('MINIO_URL','minionas.uvadcos.io/')
MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY')
MINIO_SECRET = os.environ.get('MINIO_SECRET')
ORS_URL = os.environ.get("ORS_URL","ors.uvadco.io/")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def homepage():

    return "Tracker: Working"


@app.route('/nitrack',methods = ['POST','GET'])
def track_nipy():
    '''
    POST:
        {"job_id":abc1234}
        Tracks given job_id to completion
        Returns True if tracking began sucessfully
        Mints outputs and updates job Identifier as needed
    '''

    logger.info('Job endpoint handling request %s', request)

    valid, inputs = gather_inputs(request)
    track_id = inputs['job_id']
    job_type = inputs['job_type']
    ns = inputs['namespace']

    pod_name = job_type + '-' + track_id

    prefix = inputs['output_location']
    bucket = prefix.split('/')[0]
    in_bucket_location = '/'.join(prefix.split('/')[1:])

    full_id = 'ark:' + ns + '/' + track_id

    logger.info('Tracking Job ID: %s', track_id)
    exists = find_pod(pod_name)

    if not exists:

        logger.error('Pod does not exsist for job : %s', track_id)
        return "No Pod"

    def track(track_id,pod_name):

        logger.info('Thread following Job ID %s started.', track_id)

        while pod_running(pod_name):
            logger.info('Tracking running Job ID %s.', track_id)
            time.sleep(30)


        job_status = get_pod_status(pod_name)

        # if job_status == 'Failed':
        #     failed_pod, message = whyd_pod_fail('sparkjob-' + track_id)
        #
        #     if failed_pod != 'JobRunner':
        #
        #         logs = get_pod_logs('sparkjob-' + track_id)
        #         logger.info('Job %s completed with status: ' + str(job_status), track_id)
        #
        #         success = update_job_id('ark:99999/' + track_id,job_status,logs,[])
        #         try:
        #             clean_up_pods(track_id)
        #         except:
        #             logger.error('Failed to clean up after job.', exc_info=True)
        #
        #         return

        logs = get_pod_logs(pod_name)
        logger.info('Job %s completed with status: ' + str(job_status), track_id)


        #Something near here about if failed
        #Below gets error from first initContainer
        #result.status.init_container_statuses[0].state.terminated.message
        #result = v1.read_namespaced_pod('pod-name','default')
        #Nipype Container Handles all id minting

        logger.info('Updating Job ID: %s', track_id)
        success = update_job_id('ark:' +  ns + '/' + track_id,job_status,logs,[])

        try:
            clean_up_pods(pod_name)
        except:
            logger.error('Failed to clean up after job.', exc_info=True)


    thread = threading.Thread(target=track, kwargs={'track_id':track_id,'pod_name':pod_name})
    thread.start()

    return "Tracking " + track_id


@app.route('/track',methods = ['POST','GET'])
def add_id_to_track():
    '''
    POST:
        {"job_id":abc1234}
        Tracks given job_id to completion
        Returns True if tracking began sucessfully
        Mints outputs and updates job Identifier as needed
    '''

    logger.info('Job endpoint handling request %s', request)

    valid, inputs = gather_inputs(request)
    track_id = inputs['job_id']
    job_type = inputs['job_type']
    ns = inputs['namespace']
    qualifer = inputs['qualifer']

    pod_name = job_type + '-' + track_id

    prefix = inputs['output_location']
    bucket = prefix.split('/')[0]
    in_bucket_location = '/'.join(prefix.split('/')[1:])

    full_id = 'ark:' + ns + '/' + track_id

    logger.info('Tracking Job ID: %s', track_id)
    exists = find_pod(pod_name)

    if not exists:

        logger.error('Pod does not exsist for job : %s', track_id)
        return "No Pod"

    def track(track_id,pod_name):

        logger.info('Thread following Job ID %s started.', track_id)

        while pod_running(pod_name):
            logger.info('Tracking running Job ID %s.', track_id)
            time.sleep(30)

        job_status = get_pod_status(pod_name)
        logs = get_pod_logs(pod_name)

        logger.info('Job %s completed with status: ' + str(job_status), track_id)

        outputs = gather_job_outputs(track_id,bucket,in_bucket_location)
        output_ids, all_minted = mint_output_ids(outputs,'ark:' + ns + '/' + track_id,ns,qualifer)

        if not all_minted:
            logger.error('Failed to mint all output ids for job %s.', track_id)

        logger.info('Updating Job ID: %s', track_id)
        success = update_job_id('ark:' + ns + '/' + track_id,job_status,logs,output_ids)

        for output_id in output_ids:
            built = build_eg('ark:' + ns + '/' + track_id)
            if not built:
                logger.error('Failed to create eg for job %s',output_id)

        try:
            clean_up_pods(pod_name)
        except:
            logger.error('Failed to clean up after job.', exc_info=True)


    thread = threading.Thread(target=track, kwargs={'track_id':track_id,'pod_name':pod_name})
    thread.start()

    return "Tracking " + track_id

if __name__ == "__main__":
    app.run(port = 5001)
