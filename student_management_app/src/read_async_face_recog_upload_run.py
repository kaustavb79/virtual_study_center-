import concurrent.futures
import json
import logging as log_print
import os
import sys
from datetime import datetime

import django


"""
    --------------------------
    django setup load
    --------------------------
"""
STUDY_CENTER_PROJ_PATH = os.getenv("STUDY_CENTER_PROJ_PATH")
print("STUDY_CENTER_PROJ_PATH: ", STUDY_CENTER_PROJ_PATH)
sys.path.append(STUDY_CENTER_PROJ_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = 'student_management_system.settings'
django.setup()

from django.conf import settings
from django.utils.dateparse import parse_datetime
from student_management_app.src.codebase.camera.camera_init import get_stream_save_frame_or_video
from student_management_app.src.codebase.redis_utils.model_utils.model_func import update_camera_response_row
from student_management_app.src.codebase.redis_utils.notifications.push_notify import send_notifications
from student_management_app.src.codebase.redis_utils.redis_inference import recognise_face
from student_management_app.src.codebase.redis_utils.redis_train_image import train_face_recognition_model
from student_management_app.src.codebase.redis_utils.redis_utils import delete_key_from_stream
from student_management_app.src.codebase.db.es_upload_handler import upload_pending_representations

"""
    --------------------------
    django setup load end
    --------------------------
"""

"""
    --------------------------
        logger segment
    --------------------------
"""


def setup_custom_logger(name):
    formatter = log_print.Formatter(fmt='%(asctime)s - %(process)d - %(levelname)s - %(message)s')
    fh = log_print.FileHandler(settings.LOGS_DIR + '/redis.log')
    fh.setFormatter(formatter)
    logger = log_print.getLogger(name)
    logger.setLevel(log_print.INFO)
    logger.addHandler(fh)
    return logger


log = setup_custom_logger("redis")

"""
    --------------------------
        logger segment end
    --------------------------
"""


def wrapper_function(request_dict):
    """
    REDIS WRAPPER METHOD - HANDLE ALL REQUESTS IN POOL

    Parameters:
        request_dict (dict): request json from redis db pool

    Returns:
        None
    """

    redis_start = datetime.now()

    """
        ---- CHECK IF RESOURCES AND SUB DIRECTORIES EXISTS ---
    """
    log.info("--- MODEL/REPRESENTATION VALIDATION CHECK IN PROGRESS ---")
    settings.FACE_RECOG_UTILS.check_resources_exists(root_folder=STUDY_CENTER_PROJ_PATH)
    log.info("--- MODEL/REPRESENTATION VALIDATION CHECK COMPLETED ---")

    log.info("--- MODEL/REPRESENTATION VALIDATION CHECK IN PROGRESS ---")
    if settings.ES_INSTANCE.ping():
        upload_pending_representations()
    log.info("--- MODEL/REPRESENTATION VALIDATION CHECK IN COMPLETED ---")

    request_id = request_dict[0]
    request_data = request_dict[1]
    encoding = 'utf-8'

    request_id_decoded = request_id.decode(encoding)
    request_type = request_data[b'request_type']
    request_type = request_type.decode(encoding)

    sender_uuid = request_data[b'sender_uuid']
    sender_uuid = sender_uuid.decode(encoding)
    notification_type = request_data[b'notification_type']
    notification_type = notification_type.decode(encoding)
    description = request_data[b'description']
    description = description.decode(encoding)
    media_type = request_data[b'media_type']
    media_type = media_type.decode(encoding)
    school_id = request_data[b'school_id']
    school_id = school_id.decode(encoding)
    recipient_role = request_data[b'recipient_role']
    recipient_role = recipient_role.decode(encoding)
    recipient_role = json.loads(recipient_role)

    period_number = ""
    action_object = None
    attendance_date = None
    attendance_date_str = None
    section = ""
    class_name = ""
    day = ""
    profile_role = ""
    taken_by_user_uuid = ""
    taken_for_user_uuid = ""
    staff_attendance_geolocation = None
    registration_type = ""
    attendance_type = ""
    camera_response_id = ""
    attendance_choice = ""

    pickle_folder = settings.FACE_RECOG_UTILS.create_pickle_folder(school_id=str(school_id),
                                                                   root_folder=STUDY_CENTER_PROJ_PATH)
    print("---pickle_folder---: ", pickle_folder)

    sender_profile_qs = Profile.objects.get(profile_id=sender_uuid)
    sender = sender_profile_qs.user
    target = SchoolModel.objects.get(school_id=school_id)
    all_recipient_profile = Profile.objects.none()

    try:
        log.info("Started JOB: %s", request_id_decoded)
        verb = ""
        if request_type == "train":
            log.info("Registration inprogress JOB-ID: %s", request_id_decoded)

            action_object_uuid = request_data[b'action_object_uuid']
            action_object_uuid = action_object_uuid.decode(encoding)
            action_object = Profile.objects.get(profile_id=action_object_uuid).user
            wait_folder = request_data[b'wait_folder']
            wait_folder = wait_folder.decode(encoding)

            registration_type = request_data[b'registration_type']
            registration_type = registration_type.decode(encoding)

            is_completed, profile_id, response_data = train_face_recognition_model(wait_folder=wait_folder,
                                                                                   pickle_folder=pickle_folder)
            if is_completed:
                if registration_type == "new_user":
                    verb = "new_user_registration_completed"
                else:
                    verb = "face_registration_completed"
                delete_key_from_stream(request_id)
                log.info("Finished JOB: %s", request_id_decoded)
            else:
                if registration_type == "new_user":
                    verb = "new_user_registration_failed"
                else:
                    verb = "face_registration_failed"
                log.warning("Execution Failed -- JOB: %s", request_id_decoded)
            all_recipient_profile = Profile.objects.filter(school_id=school_id,
                                                           profile_id__in=[profile_id, sender_uuid])
            profile_role = Profile.objects.get(pk=profile_id).role
        elif request_type == "attendance":
            log.info("Attendance inprogress -- JOB-ID: %s", request_id_decoded)

            attendance_type = request_data[b'attendance_type']
            attendance_type = attendance_type.decode(encoding)

            staff_attendance_type = request_data[b'staff_attendance_type']
            staff_attendance_type = staff_attendance_type.decode(encoding)

            attendance_date = request_data[b'attendance_date']
            attendance_date_str = attendance_date.decode(encoding)
            attendance_date = parse_datetime(attendance_date_str)

            file_path = request_data[b'file_path']
            file_path = file_path.decode(encoding)

            media_id = request_data[b'media_id']
            media_id = media_id.decode(encoding)

            role = request_data[b'role']
            role = role.decode(encoding)

            logged_in_user_uuid = sender_uuid

            if attendance_type == 'class':
                period_number = request_data[b'period']
                period_number = period_number.decode(encoding)

                class_name = request_data[b'class_name']
                class_name = class_name.decode(encoding)

                section = request_data[b'section']
                section = section.decode(encoding)

                day = request_data[b'day']
                day = day.decode(encoding)

                taken_by_user_uuid = request_data[b'taken_by_user_uuid']
                taken_by_user_uuid = taken_by_user_uuid.decode(encoding)

                attendance_choice = request_data[b'attendance_choice']
                attendance_choice = attendance_choice.decode(encoding)

                all_recipient_profile = Profile.objects.filter(school_id=school_id,
                                                               profile_id__in=[logged_in_user_uuid])
            elif attendance_type == "cctv":
                path = request_data[b'path']
                path = path.decode(encoding)

                url = request_data[b'url']
                url = url.decode(encoding)

                taken_by_user_uuid = request_data[b'taken_by_user_uuid']
                taken_by_user_uuid = taken_by_user_uuid.decode(encoding)

                extra_data = {
                    "request_type": "attendance",
                    "attendance_type": attendance_type,
                    "sender_uuid": sender_uuid,
                    'taken_by_user_uuid': taken_by_user_uuid,
                    "notification_type": notification_type,
                    "description": description,
                    "media_type": media_type,
                    "recipient_role": json.dumps(recipient_role),
                    "attendance_date": attendance_date_str,
                    "role": role
                }

                file_key = "media_file"
                path_plus_file_name_plus_extension = get_stream_save_frame_or_video(path=path, url=url, user=None,
                                                                                    password=None)

                camera_response_id = request_data[b'camera_response_id']
                camera_response_id = camera_response_id.decode(encoding)

                if path_plus_file_name_plus_extension:
                    media_path = path_plus_file_name_plus_extension.split(settings.BROWSE_FOLDER_ROOT)[1]

                    print('---path_plus_file_name_plus_extension---', path_plus_file_name_plus_extension)
                    filename = "file_name"
                    # override file name with prefixes
                    filename = media_type + "__" + filename

                    obj = MediaCapturedModel.objects.create(
                        media_type=media_type,
                        extra_data=extra_data
                    )

                    obj.media_file = media_path
                    obj.save()

                    file_path = path_plus_file_name_plus_extension
                    media_id = obj.media_id
                else:
                    logged_in_user = Profile.objects.get(profile_id=logged_in_user_uuid)
                    taken_by = Profile.objects.get(profile_id=taken_by_user_uuid)

                    attendance_get_qs = update_camera_response_row(camera_response_id=camera_response_id,
                                                                   media_id=None,
                                                                   cctv_attempt_status="failure",
                                                                   cctv_attendance_status=[],
                                                                   attendance_date=attendance_date)

                    action_object = attendance_get_qs
            elif attendance_type == "self":
                taken_by_user_uuid = logged_in_user_uuid
                taken_for_user_uuid = logged_in_user_uuid
                all_recipient_profile = Profile.objects.filter(school_id=school_id,
                                                               profile_id__in=[taken_for_user_uuid])

                staff_attendance_geolocation = request_data[b'staff_attendance_geolocation']
                staff_attendance_geolocation = staff_attendance_geolocation.decode(encoding)
                staff_attendance_geolocation = json.loads(staff_attendance_geolocation)
            elif attendance_type == "other":
                taken_by_user_uuid = request_data[b'taken_by_user_uuid']
                taken_by_user_uuid = taken_by_user_uuid.decode(encoding)
                taken_for_user_uuid = request_data[b'taken_for_user_uuid']
                taken_for_user_uuid = taken_for_user_uuid.decode(encoding)
                all_recipient_profile = Profile.objects.filter(school_id=school_id,
                                                               profile_id__in=[logged_in_user_uuid,
                                                                               taken_for_user_uuid])

                # todo uncomment when other geolocation enable
                # staff_attendance_geolocation = request_data[b'staff_attendance_geolocation']
                # staff_attendance_geolocation = staff_attendance_geolocation.decode(encoding)
                # staff_attendance_geolocation = json.loads(staff_attendance_geolocation)

            if media_id:
                is_completed, message, action_object = recognise_face(logged_in_user_uuid=logged_in_user_uuid,
                                                                      taken_by_user_uuid=taken_by_user_uuid,
                                                                      taken_for_user_uuid=taken_for_user_uuid,
                                                                      period_number=period_number,
                                                                      section=section,
                                                                      class_name=class_name,
                                                                      day=day,
                                                                      school_id=school_id,
                                                                      attendance_date=attendance_date,
                                                                      pickle_folder=pickle_folder,
                                                                      file_path=file_path,
                                                                      media_id=media_id,
                                                                      role=role,
                                                                      staff_attendance_type=staff_attendance_type,
                                                                      attendance_type=attendance_type,
                                                                      staff_attendance_geolocation=staff_attendance_geolocation,
                                                                      camera_response_id=camera_response_id,
                                                                      attendance_choice=attendance_choice
                                                                      )
            else:
                is_completed = False
                message = "Camera is not working, no stream found"
                # action_object = ""

            log.info(" MESSAGE: %s", message)
            if is_completed:
                verb = "attendance_completed_v1"
                delete_key_from_stream(id=request_id)
                log.info("Finished JOB: %s", request_id_decoded)
            else:
                verb = 'attendance_failed_v1'
                log.warning("Execution Failed -- JOB: %s", request_id_decoded)

        school_admin_qs = Profile.objects.none()
        if target.organisation_type == "school":
            school_admin_qs = Profile.objects.filter(school_id=school_id, role="school_admin")
        elif target.organisation_type == "company":
            school_admin_qs = Profile.objects.filter(school_id=school_id, role="admin")

        all_recipient = all_recipient_profile | school_admin_qs
        all_recipient = all_recipient.distinct()

        log.info("SENDING NOTIFICATIONS")
        send_notifications(request_type=request_type,
                           all_recipient=all_recipient,
                           sender=sender,
                           verb=verb,
                           description=description,
                           notification_type=notification_type,
                           target=target,
                           action_object=action_object,
                           class_name=class_name,
                           section=section,
                           media_type=media_type,
                           recipient_role=recipient_role,
                           school_id=school_id,
                           period=period_number,
                           date=attendance_date,
                           date_str=attendance_date_str,
                           profile_role=profile_role,
                           taken_by_user_uuid=taken_by_user_uuid,
                           taken_for_user_uuid=taken_for_user_uuid,
                           registration_type=registration_type,
                           attendance_type=attendance_type)
        log.info("SENDING NOTIFICATIONS COMPLETED")
    except:
        log.exception("Exception occurred during redis call")

    redis_end = datetime.now()

    log.info("Redis << %s >> job total time taken : %s", request_type, redis_end - redis_start)


def main():
    """
    Redis job executor
    """

    cg_current = settings.REDIS_DB.consumer_group(settings.REDIS_CONSUMER_GROUP, settings.REDIS_STREAM_KEYS)
    jobs = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        while True:
            result = cg_current.read(block=0, count=1)
            job = executor.map(wrapper_function, [result[0][1][0]])
            jobs[job] = result
            keys = [k for k, v in jobs.items()]
            for x in keys:
                del jobs[x]


if __name__ == "__main__":
    main()
