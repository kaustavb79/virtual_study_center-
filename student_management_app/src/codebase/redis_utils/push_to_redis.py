import logging
from django.conf import settings

log = logging.getLogger("app_smart_attendance")


def push_request_for_face_recog(request_data):
    log.info("---- Adding job to redis queue ----")
    print(request_data)
    cg_current = settings.REDIS_DB.consumer_group(settings.REDIS_CONSUMER_GROUP, settings.REDIS_STREAM_KEYS)
    cg_current.face_recog.add(request_data)
    log.info("---- Redis job created successfully ----")

