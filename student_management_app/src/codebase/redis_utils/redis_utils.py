import logging
import os

from django.conf import settings

log = logging.getLogger("redis")


def delete_key_from_stream(id):
    """
        Delete key from redis stream

        Parameters:
            id (str): Redis job queue id

        Returns:
            None

    """
    cg_current = settings.REDIS_DB.consumer_group(settings.REDIS_CONSUMER_GROUP, settings.REDIS_STREAM_KEYS)
    cg_current.face_recog.delete(id)
    log.warning("<< %s >> queue deleted from redis db.", id)


def delete_media_file(prev_media_id):
    """
    Delete previous media file after new media file insertion

    Parameters:
        prev_media_id (Object): MediaCapturedModel object

    Returns:
        None

    """
    if settings.REMOVE_ORPHAN_MEDIA:
        log.info("prev_media_id: %s", prev_media_id)
        if prev_media_id.media_file and os.path.isfile(
                os.path.join(os.getcwd(), prev_media_id.media_file.url.lstrip("/"))):
            os.remove(os.path.join(os.getcwd(), prev_media_id.media_file.url.lstrip("/")))
        prev_media_id.delete()