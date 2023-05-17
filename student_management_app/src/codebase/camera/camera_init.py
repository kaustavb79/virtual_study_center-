import datetime
import time
import logging
import cv2
import requests
import numpy as np

log = logging.getLogger("redis")


def get_stream_size(url_with=None):
    capture = cv2.VideoCapture(url_with)
    videoWidth = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    videoHeight = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print('videoWidth ---- ', videoWidth)
    print('videoHeight ---- ', videoHeight)
    capture.release()
    return videoWidth, videoHeight


def get_stream_save_frame_or_video(path=None, url=None, user=None, password=None):
    start = datetime.datetime.now()
    print('---get_stream_save_frame_or_video---start---', start)

    if not path:
        path = ""
    if not url:
        url = ""
    if not user:
        user = ""
    if not password:
        password = ""

    url_with = url + "?username=" + user + "&amp;password=" + password + ""

    videoWidth, videoHeight = get_stream_size(url_with=url_with)

    try:
        r = requests.get(url, auth=(user, password), stream=True)
        # video = cv2.VideoWriter("/home/sam/Documents/ip/new_video.mp4", cv2.VideoWriter_fourcc(*"MPEG"), 20.0, (640,840))
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        # height, width, channels = frame.shape
        file_name = 'output_file'
        extension = '.avi'
        path_plus_file_name_plus_extension = path + file_name + extension

        video = cv2.VideoWriter(path_plus_file_name_plus_extension, fourcc, 30.0, (videoWidth, videoHeight))
        print('---video---', video)

        if (r.status_code == 200):
            # bytes = bytes()
            bytes = b''
            j = 0
            for chunk in r.iter_content(chunk_size=1024):
                j += 1
                # print('j----', j)
                bytes += chunk
                a = bytes.find(b'\xff\xd8')
                b = bytes.find(b'\xff\xd9')
                if a != -1 and b != -1:
                    jpg = bytes[a:b + 2]
                    bytes = bytes[b + 2:]
                    i = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)

                    # # show output
                    # cv2.imshow('i', i)

                    # if cv2.waitKey(1) == 27:
                    #     exit(0)

                    ### get and save FRAME to the path
                    # cv2.imwrite(str(path) + str(j) + '.jpg', i)

                    ### get FRAME and save as VIDEO
                    img = cv2.resize(i, (videoWidth, videoHeight))
                    video.write(img)
                    # print('i.shape-----', i.shape)

                    ### stop after second
                    if j > 5000:
                        # exit(0)
                        break
            video.release()
            cv2.destroyAllWindows()
        else:
            print("Received unexpected status code {}".format(r.status_code))

    except Exception as e:
        print('---if camera is not working, no stream found---', e)
        # if camera is not working, no stream found
        return None

    end = datetime.datetime.now()
    print('---get_stream_save_frame_or_video---end---', end)

    return path_plus_file_name_plus_extension


# http://192.168.1.5:6677/index
# http://192.168.1.5:6677/videofeed?username=CCJDLKGMF&amp;password=
# http://192.168.1.xx/mjpeg.cgi

path = "/home/sam/Documents/ip/"
url = "http://192.168.1.4:6677/videofeed"
user = "CCJDLKGMF"
password = ""

# get_stream_save_frame_or_video(path=path, url=url, user=user, password=password)
