import json
import logging
from webpush.utils import _send_notification
from app_root.models import Profile
from notifications.signals import notify

log = logging.getLogger("redis")

"""
    ---------------------------------------------------------------
        Utility method to create pwa wepush notification body
    ---------------------------------------------------------------
    Args:
        - request_type: (str) <<'train','attendance'>>
        - request_type: (str) <<'train','attendance'>>
        - request_type: (str) <<'train','attendance'>>
        - request_type: (str) <<'train','attendance'>>
        - request_type: (str) <<'train','attendance'>>
        - request_type: (str) <<'train','attendance'>>
        - request_type: (str) <<'train','attendance'>>
        - request_type: (str) <<'train','attendance'>>
        - request_type: (str) <<'train','attendance'>>
        - request_type: (str) <<'train','attendance'>>
        - request_type: (str) <<'train','attendance'>>
        - request_type: (str) <<'train','attendance'>>
        - request_type: (str) <<'train','attendance'>>
        - request_type: (str) <<'train','attendance'>>
"""


def create_push_notification_body(request_type, registration_type, verb, recipient, action_object, profile,
                                  profile_role, sender, date_str, taken_for, taken_by, class_name, section, period):
    body = ""
    if request_type == "train":
        if registration_type == "new_user":
            if verb == "new_user_registration_completed":
                body = f"Hi {recipient.first_name + ' ' + recipient.last_name}.\n" \
                       "Registration Successful \n"
                if profile_role == "student":
                    body += f"Name: {action_object.first_name + ' ' + action_object.last_name} \nClass: {profile.class_name} --- Section: {profile.section.capitalize()} \nTaken By: {sender.first_name + ' ' + sender.last_name}"
                else:
                    body += f"Name: {action_object.first_name + ' ' + action_object.last_name} \nTaken By: {sender.first_name + ' ' + sender.last_name}"
            elif verb == "new_user_registration_failed":
                body = f"Hi {recipient.first_name + ' ' + recipient.last_name}. \n " \
                       f"New User Registration Failed!!! \n"
                if profile_role == "student":
                    body += f"Name: {action_object.first_name + ' ' + action_object.last_name} " \
                            f"\nClass: {profile.class_name} --- Section: {profile.section.capitalize()} " \
                            f"\nTaken By: {sender.first_name + ' ' + sender.last_name}"
                else:
                    body += f"Name: {action_object.first_name + ' ' + action_object.last_name} " \
                            f"\nTaken By: {sender.first_name + ' ' + sender.last_name}"
        elif registration_type == "face":
            if verb == "face_registration_completed":
                body = f"Hi {recipient.first_name + ' ' + recipient.last_name}. \n"
                if profile_role == "student":
                    body += f"Name: {action_object.first_name + ' ' + action_object.last_name} \nClass: {profile.class_name} \nSection: {profile.section.capitalize()} \nTaken By: {sender.first_name + ' ' + sender.last_name}"
                else:
                    body += f"Name: {action_object.first_name + ' ' + action_object.last_name} \nTaken By: {sender.first_name + ' ' + sender.last_name}"
            elif verb == "face_registration_failed":
                body = f"Hi {recipient.first_name + ' ' + recipient.last_name} \n"
                if profile_role == "student":
                    body += f"Name: {action_object.first_name + ' ' + action_object.last_name} " \
                            f"\nClass: {profile.class_name} \nSection: {profile.section.capitalize()} " \
                            f"\nTaken By: {sender.first_name + ' ' + sender.last_name}"
                else:
                    body += f"Name: {action_object.first_name + ' ' + action_object.last_name} " \
                            f"\nTaken By: {sender.first_name + ' ' + sender.last_name}"
    elif request_type == "attendance":
        # if attendance type == self/other
        if taken_for:
            body = f"Date: {date_str}" \
                   f"\nTaken By: {taken_by.user.first_name + ' ' + taken_by.user.last_name}" \
                   f"\nTaken For: {taken_for.user.first_name + ' ' + taken_for.user.last_name}"
        else:
            body = f"Date: {date_str}" \
                   f"\nTaken By: {taken_by.user.first_name + ' ' + taken_by.user.last_name}" \
                   f"\nTaken for class : \nClass: {class_name} \nSection: {section.capitalize()} \nPeriod: {period}"
    return body


def send_notifications(request_type, all_recipient, sender, verb, description, notification_type, target, action_object,
                       class_name, section, media_type, recipient_role, school_id, registration_type, attendance_type,
                       period=None,
                       date=None, date_str=None,
                       profile_role=None,
                       taken_by_user_uuid=None, taken_for_user_uuid=None):
    print("-- request_type: ", request_type)
    print("-- all_recipient: ", all_recipient)
    print("-- classs: ", class_name)
    print("-- section : ", section)
    print("-- verb: ", verb)
    print("-- profile_role: ", profile_role)
    print("-- action_object: ", action_object)
    print("-- taken_by_user_uuid: ", taken_by_user_uuid)
    print("-- taken_for_user_uuid: ", taken_for_user_uuid)
    print("-- attendance_date: ", date)
    print("-- registration_type: ", registration_type)

    taken_by = Profile.objects.none()
    taken_for = Profile.objects.none()
    profile = Profile.objects.none()
    if taken_by_user_uuid:
        taken_by = Profile.objects.get(pk=taken_by_user_uuid)
    else:
        log.warning("No taken_by_user_uuid passed")

    if taken_for_user_uuid:
        taken_for = Profile.objects.get(pk=taken_for_user_uuid)
    else:
        log.warning("No taken_for_user_uuid passed")

    try:
        for assignee in all_recipient:
            title = ""
            recipient = assignee.user
            if request_type == "train":
                profile = Profile.objects.get(user=action_object)
                print("-- profile: ", profile)
                title = verb

                notify.send(
                    sender,
                    recipient=recipient,
                    verb=verb,
                    description=description,
                    notification_type=notification_type,
                    target=target,
                    action_object=action_object,
                    class_name=profile.class_name,
                    section=profile.section,
                    media_type=media_type)
            elif request_type == "attendance":
                notify.send(
                    sender,
                    recipient=recipient,
                    verb=verb,
                    description=description,
                    notification_type=notification_type,
                    target=target,
                    action_object=action_object,
                    class_name=class_name,
                    section=section,
                    period=period,
                    date=date,
                    media_type=media_type,
                    attendance_type=attendance_type)

                if verb == "attendance_completed_v1":
                    if attendance_type == "class":
                        title = "class_attendance_taken"
                    if attendance_type == "cctv":
                        title = "cctv_attendance_taken"
                    if attendance_type == "self":
                        title = "self_attendance_taken"
                    if attendance_type == "other":
                        title = "other_attendance_taken"
                elif verb == "attendance_failed_v1":
                    if attendance_type == "class":
                        title = "class_attendance_failed"
                    if attendance_type == "cctv":
                        title = "cctv_attendance_failed"
                    if attendance_type == "self":
                        title = "self_attendance_failed"
                    if attendance_type == "other":
                        title = "other_attendance_failed"

            body = create_push_notification_body(
                request_type=request_type,
                registration_type=registration_type,
                verb=title,
                recipient=recipient,
                action_object=action_object,
                profile=profile,
                profile_role=profile_role,
                sender=sender,
                date_str=date_str,
                taken_for=taken_for,
                taken_by=taken_by,
                class_name=class_name,
                section=section,
                period=period)
            send_device_notification(verb=title, body=body, recipient_roles=recipient_role, school_id=school_id,
                                     recipient=recipient)
    except:
        log.exception("Exception Occurred During send notification")

    # body = ""
    # if request_type == "train":
    #     if "completed" in verb:
    #         body = "New User Got Successfully Registered!!!"
    #     elif "failed" in verb:
    #         body = "Registration Failed!!!"
    #
    #     body += f"Name: {action_object.first_name + ' ' + action_object.last_name} \n \t Class: {class_name} \n \t Section: {section.capitalize()} \n\t Taken By: {sender.first_name + ' ' + sender.last_name}"
    # elif request_type == "attendance":
    #     if "completed" in verb:
    #         body = "Attendance Taken for "
    #     elif "failed" in verb:
    #         body = "Attendance Failed for "
    #     body += f"{date} \n \t Class: {class_name} \n \t Section: {section.capitalize()} \n\t Period: {period} \n\t Taken By: {sender.first_name + sender.last_name}"
    # send_device_notification(verb=verb, body=body, recipient_roles=recipient_role, school_id=school_id, recipient=recipient)


"""
    Group notification utility
"""


def send_notification_to_group(group_names, school_id, payload, ttl=0):
    # Get all the subscription related to the group
    payload = json.dumps(payload)

    users = Profile.objects.filter(role__in=group_names, school_id=school_id)
    print("users: ", users)

    for usr in users:
        push_infos = usr.user.webpush_info.select_related("subscription")
        print("push_infos: ", push_infos)
        for push_info in push_infos:
            _send_notification(push_info.subscription, payload, ttl)


def send_device_notification(verb, body, recipient_roles, school_id, recipient):
    from webpush import send_user_notification

    log.info("Sending device notification")
    try:
        body = body
        head = " ".join(wrd.capitalize() for wrd in verb.split('_'))

        payload = {'head': head, 'body': body}
        print(payload)
        # # Single user
        send_user_notification(user=recipient, payload=payload, ttl=1000)
        # # Group notification
        # send_notification_to_group(recipient_roles, school_id, payload, ttl=1000)
    except:
        log.exception("Exception occurred during push notification")
    else:
        log.info("Sending device notification completed")


"""
    ---------------------------------------------------------------
        Send notifications method end
    ---------------------------------------------------------------
"""
