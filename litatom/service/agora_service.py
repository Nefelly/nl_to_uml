import requests
import time
import json
from copy import deepcopy
from flask import request
import base64
from ..util import (
    low_high_pair
)
from ..const import (
    ONE_MIN
)
from ..key import (
    REDIS_VOICE_RECORD_CACHE
)
from ..model import (
    VoiceMatchRecord
)
from ..service import (
    AliLogService
)

from ..redis import RedisClient
redis_client = RedisClient()['lit']


class AgoraService(object):
    RECORD_EXPIRE_TIME = 10 * ONE_MIN
    TIMEOUT = 60
    '''
    docs:
    https://docs.agora.io/cn/cloud-recording/cloud_recording_api_rest?platform=All%20Platforms#a-namestorageconfiga%E4%BA%91%E5%AD%98%E5%82%A8%E8%AE%BE%E7%BD%AE
    https://docs.agora.io/cn/cloud-recording/cloud_recording_rest?platform=All%20Platforms
    '''
    #TODO: Fill in AppId, Basic Auth string, Cname (channel name), and cloud storage information
    APPID = "a0baede033384361a307dbf9e28b571d"
    CUSTOMERID ="3613e4cdf16246a9888e870eb8317fb5"
    APP_SECRET = "74654ca439ac420c9b2b2e57ff474abf"
    Auth="Basic " + base64.encodestring('%s:%s' % (CUSTOMERID, APP_SECRET)).replace('\n', '')
    Cname="love127618040528489love126505602587986"
    ACCESS_KEY="LTAIxjghAKbw6DrM"
    SECRET_KEY="QpvYuzO2X5QwxYaZwgpsjjkBDEYFNP"
    VENDOR = 2
    REGION = 0
    BUCKET = "testlowvisit"

    url="https://api.agora.io/v1/apps/%s/cloud_recording/" % APPID

    acquire_body={
        "uid": "957947",
        "cname": Cname,
        "clientRequest": {}
    }

    start_body={
        "uid": "957947",
        "cname": Cname,
        "clientRequest": {
            "storageConfig": {
                "secretKey": SECRET_KEY,
                "region": REGION,
                "accessKey": ACCESS_KEY,
                "bucket": BUCKET,
                "vendor": VENDOR
            },
            "recordingConfig": {
                "audioProfile": 0,
                "channelType": 0,
                "maxIdleTime": 5,
                "transcodingConfig": {
                        "width": 640,
                        "height": 360,
                        "fps": 15,
                        "bitrate": 500
                }
            }
        }
    }

    stop_body={
        "uid": "957947",
        "cname": Cname,
        "clientRequest": {}
    }

    @classmethod
    def cloud_post(cls, url, data=None,timeout=TIMEOUT):
        print cls.Auth
        headers = {'Content-type': "application/json", "Authorization": cls.Auth}

        try:
            response = requests.post(url, json=data, headers=headers, timeout=timeout, verify=False)
            # print("url: %s, request body:%s response: %s" %(url, response.request.body,response.json()))
            return response
        except requests.exceptions.ConnectTimeout:
            raise Exception("CONNECTION_TIMEOUT")
        except requests.exceptions.ConnectionError:
            raise Exception("CONNECTION_ERROR")

    @classmethod
    def cloud_get(cls, url, timeout=TIMEOUT):
        headers = {'Content-type':"application/json", "Authorization": cls.Auth}
        try:
            response = requests.get(url, headers=headers, timeout=timeout, verify=False)
            # print("url: %s,request:%s response: %s" % (url, response.request.body, response.json()))
            return response
        except requests.exceptions.ConnectTimeout:
            raise Exception("CONNECTION_TIMEOUT")
        except requests.exceptions.ConnectionError:
            raise Exception("CONNECTION_ERROR")

    @classmethod
    def get_resource_id(cls, cname):
        acquire_url = cls.url + "acquire"
        acquire_body = {
            "uid": "957947",
            "cname": cname,
            "clientRequest": {}
        }
        r_acquire = cls.cloud_post(acquire_url, acquire_body)
        if r_acquire.status_code == 200:
            resourceId = r_acquire.json()["resourceId"]
            return resourceId
        else:
            print("Acquire error! Code: %s Info: %s" % (r_acquire.status_code, r_acquire.json()))
            return False

    @classmethod
    def get_cache_key(cls, cname):
        return REDIS_VOICE_RECORD_CACHE.format(cname=cname)

    @classmethod
    def outer_record(cls, loveid1, loveid2):
        cname = low_high_pair(loveid1, loveid2)
        key = cls.get_cache_key(cname)
        if redis_client.get(key):
            # cls.outer_stop_record(key)
            AliLogService.put_err_log({"name": "voice_record_dup", "cname": cname})
            return
            # redis_client.delete(key)
        resourceId, sid = cls._start_record(cname)
        save_add = '%s_%s.m3u8' % (sid, cname)
        region = request.region
        save_record = VoiceMatchRecord.create(loveid1, loveid2, save_add, region)
        if not save_record:
            print 'no save record', '!' * 100
            return
        to_save = {
            'resource_id': resourceId,
            'sid': sid,
            'rid': str(save_record.id)
        }
        redis_client.set(key, json.dumps(to_save), cls.RECORD_EXPIRE_TIME)
        return


    @classmethod
    def outer_stop_record(cls, loveid1, loveid2):
        cname = low_high_pair(loveid1, loveid2)
        key = cls.get_cache_key(cname)
        cache_res = redis_client.get(key)
        if cache_res:
            cache_res = json.loads(cache_res)
            rid = cache_res['rid']
            resourceId = cache_res['resource_id']
            sid = cache_res['sid']
            VoiceMatchRecord.stop(rid)
            cls.stop_record(resourceId, sid)
            redis_client.delete(key)

    @classmethod
    def _start_record(cls, cname):
        resourceId = cls.get_resource_id(cname)
        if not resourceId:
            return '', ''
        start_url = cls.url + "resourceid/%s/mode/mix/start" % resourceId
        start_body = deepcopy(cls.start_body)
        start_body['cname'] = cname
        r_start = cls.cloud_post(start_url, start_body)
        print start_body
        if r_start.status_code == 200:
            print r_start.json(), '*' * 100
            sid = r_start.json()["sid"]
            return resourceId, sid
        else:
            print("Start error! Code:%s Info:%s" % (r_start.status_code, r_start.json()))
            return '', ''

    @classmethod
    def stop_record(cls, resourceId, sid):
        stop_url = cls.url + "resourceid/%s/sid/%s/mode/mix/stop" % (resourceId, sid)
        r_stop = cls.cloud_post(stop_url, cls.stop_body)
        if r_stop.status_code == 200:
            # print("Stop cloud recording success. FileList : %s, uploading status: %s"
            #       %(r_stop.json()["serverResponse"]["fileList"], r_stop.json()["serverResponse"]["uploadingStatus"]))
            return
        else:
            # print("Stop failed! Code: %s Info: %s" % r_stop.status_code, r_stop.json())
            return True

    @classmethod
    def start_record(cls, cname=None):
        if not cname:
            cname = "love127618040528489love126505602587986"
        resourceId, sid = cls._start_record(cname)
        print '%s_%s.m3u8' % (sid, cname)
        # time.sleep(10)
        # cls.stop_record(resourceId, sid)
        return
        acquire_url = cls.url + "acquire"
        acquire_body = {
            "uid": "957947",
            "cname": cname,
            "clientRequest": {}
        }
        r_acquire = cls.cloud_post(acquire_url, acquire_body)
        if r_acquire.status_code == 200:
            resourceId = r_acquire.json()["resourceId"]
        else:
            print("Acquire error! Code: %s Info: %s" %(r_acquire.status_code, r_acquire.json()))
            return False
        start_url = cls.url + "resourceid/%s/mode/mix/start" % resourceId
        start_body = deepcopy(cls.start_body)
        start_body['Cname'] = cname
        r_start = cls.cloud_post(start_url, start_body)
        if r_start.status_code == 200:
            sid = r_start.json()["sid"]
            print sid, '!!!!!!' * 10
        else:
            print("Start error! Code:%s Info:%s" %(r_start.status_code, r_start.json()))
            return False

        time.sleep(1)
        query_url = cls.url + "resourceid/%s/sid/%s/mode/mix/query" %(resourceId, sid)
        r_query = cls.cloud_get(query_url)
        if r_query.status_code == 200:
            print("The recording status: %s" % r_query.json())
        else:
            print("Query failed. Code %s, info: %s" % (r_query.status_code, r_query.json()))

        time.sleep(10)
        stop_url = cls.url+"resourceid/%s/sid/%s/mode/mix/stop" % (resourceId, sid)
        r_stop = cls.cloud_post(stop_url, cls.stop_body)
        print r_stop.json()
        if r_stop.status_code == 200:
            print("Stop cloud recording success. FileList : %s, uploading status: %s"
                  %(r_stop.json()["serverResponse"]["fileList"], r_stop.json()["serverResponse"]["uploadingStatus"]))
        else:
            print("Stop failed! Code: %s Info: %s" % r_stop.status_code, r_stop.json())


# AgoraService.start_record()
