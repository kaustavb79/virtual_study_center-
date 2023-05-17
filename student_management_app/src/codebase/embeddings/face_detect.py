import logging
from datetime import datetime
import cv2
from deepface.detectors import FaceDetector
from django.conf import settings

log = logging.getLogger("redis")


def detect_faces_from_image(image):
    """
    Detect multiple faces from a single image

    Parameters:
        image (str): image path

    Returns:
        A list of tuple containing detected face array and the region
    """

    start_face_detect = datetime.now()

    detected_faces = list()
    try:
        img = cv2.imread(image)
        detected_faces = FaceDetector.detect_faces(settings.RECOGNIION_DETECTOR_MODEL, settings.RECOGNIION_DETECTOR,
                                                   img)
    except:
        log.exception("Exception occurred during face detection")

    end_face_detect = datetime.now()
    log.info(" --- Face detection TIME TAKEN : %s ----", end_face_detect - start_face_detect)
    return detected_faces