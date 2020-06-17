import requests
import time
import base64
TIMEOUT=60


class AgoraService(object):
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
                "maxIdleTime": 30,
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
            print("url: %s, request body:%s response: %s" %(url, response.request.body,response.json()))
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
            print("url: %s,request:%s response: %s" % (url, response.request.body, response.json()))
            return response
        except requests.exceptions.ConnectTimeout:
            raise Exception("CONNECTION_TIMEOUT")
        except requests.exceptions.ConnectionError:
            raise Exception("CONNECTION_ERROR")

    @classmethod
    def start_record(cls):
        acquire_url = cls.url + "acquire"
        print acquire_url,  cls.acquire_body
        r_acquire = cls.cloud_post(acquire_url, cls.acquire_body)
        if r_acquire.status_code == 200:
            resourceId = r_acquire.json()["resourceId"]
        else:
            print("Acquire error! Code: %s Info: %s" %(r_acquire.status_code, r_acquire.json()))
            return False
        print resourceId, ''
        start_url = cls.url + "resourceid/%s/mode/mix/start" % resourceId
        r_start = cls.cloud_post(start_url, cls.start_body)
        if r_start.status_code == 200:
            sid = r_start.json()["sid"]
        else:
            print("Start error! Code:%s Info:%s" %(r_start.status_code, r_start.json()))
            return False

        time.sleep(10)
        query_url = cls.url + "resourceid/%s/sid/%s/mode/mix/query" %(resourceId, sid)
        r_query = cls.cloud_get(query_url)
        if r_query.status_code == 200:
            print("The recording status: %s" % r_query.json())
        else:
            print("Query failed. Code %s, info: %s" % (r_query.status_code, r_query.json()))

        time.sleep(30)
        stop_url = cls.url+"resourceid/%s/sid/%s/mode/mix/stop" % (resourceId, sid)
        r_stop = cls.cloud_post(stop_url, cls.stop_body)
        if r_stop.status_code == 200:
            print("Stop cloud recording success. FileList : %s, uploading status: %s"
                  %(r_stop.json()["serverResponse"]["fileList"], r_stop.json()["serverResponse"]["uploadingStatus"]))
        else:
            print("Stop failed! Code: %s Info: %s" % r_stop.status_code, r_stop.json())


# AgoraService.start_record()
