#© 2020 By The Rector And Visitors Of The University Of Virginia

#Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import os,time
import sys
import requests
from minio import Minio
from minio.error import ResponseError
import json

MINIO_URL = os.environ.get('MINIO_URL','minionas.uvadcos.io/')
MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY')
MINIO_SECRET = os.environ.get('MINIO_SECRET')

ORS_URL = os.environ.get("ORS_URL","http://mds.ors/")

minioClient = Minio(MINIO_URL,
                  access_key=MINIO_ACCESS_KEY,
                  secret_key=MINIO_SECRET,
                  secure=False)

def get_distribution(id):
    """Validates that given identifier exists in Mongo.
        Returns location in minio. """
    if isinstance(id,list):
        locations = []
        names = []
        for i in id:
            location, name = get_distribution(i)
            if location == '':
                continue
            locations.append(location)
            names.append(name)
        return locations, names
    r = requests.get(ORS_URL + id)
    if r.status_code != 200:
        print(ORS_URL + id)
        return False, "Identifier Doesn't Exist."
    try:
        data_dict = r.json()
        if isinstance(data_dict['distribution'],list):
            if data_dict['distribution'][-1].get('@type','') == 'DataDownload':
                data_url = data_dict['distribution'][-1]['contentUrl']
                file_location = '/'.join(data_url.split('/')[1:])
            else:
                dist_r = requests.get(ORS_URL + data_dict['distribution'][-1]['@id'])
                data_url = dist_r.json()['name']
                file_location = data_url
        else:
            if data_dict['distribution'].get('@type','') == 'DataDownload':
                data_url = data_dict['distribution']['contentUrl']
                file_location = '/'.join(data_url.split('/')[1:])
            else:
                dist_r = requests.get(ORS_URL + data_dict['distribution']['@id'])
                data_url = dist_r.json()['name']
                file_location = data_url
    except:
        return '',''
    return file_location, name

def download_all(locations,names,data_ids):
    ids = {}
    for i in range(len(locations)):
        bucket = locations[i].split('/')[0]
        rest = "/".join(locations[i].split('/')[1:])
        try:
            data = minioClient.get_object(bucket, rest)
        except:
            time.sleep(60)
            data = minioClient.get_object(bucket, rest)
        with open('/data/' + locations[i].split('/')[-1], 'wb') as file_data:
            for d in data.stream(32*1024):
                file_data.write(d)
        ids['/data/' +  locations[i].split('/')[-1]] = data_ids[i]
    return ids
data_ids = os.environ.get("DATA")
data_ids = data_ids.replace('[','').replace(']','').split(',')
locations, names = get_distribution(data_ids)
ids = download_all(locations,names,data_ids)
with open('/meta/inputs.json', 'w') as outfile:
    json.dump(ids, outfile)

with open('/meta/outputs.json', 'w') as outfile:
    json.dump(ids, outfile)
