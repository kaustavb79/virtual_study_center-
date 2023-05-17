import logging
from app_root.models import Profile, AttendanceModel, StaffAttendanceModel, MediaCapturedModel, PeriodModel
from student_management_app.src.codebase.inference.inference_utils import get_representation_df
from student_management_app.src.codebase.inference.inference_video import InferenceVideo
from student_management_app.src.codebase.redis_utils.model_utils.model_func import create_attendance_row, \
    update_camera_response_row
from student_management_app.src.codebase.redis_utils.redis_utils import delete_media_file
from student_management_app.views import set_attendance_under_process

log = logging.getLogger("redis")


def recognise_face(logged_in_user_uuid, taken_by_user_uuid, taken_for_user_uuid, period_number, section, class_name,
                   day, school_id, attendance_date, pickle_folder, file_path,
                   media_id, role, staff_attendance_type, attendance_type, staff_attendance_geolocation,
                   camera_response_id, attendance_choice):
    is_completed = False

    log.info(" ATTENDANCE STARTED ")

    logged_in_user = Profile.objects.none()
    attendance_get_qs = AttendanceModel.objects.none()
    staff_attendance_get_qs = StaffAttendanceModel.objects.none()
    taken_by = Profile.objects.none()
    taken_for = Profile.objects.none()

    media_id = MediaCapturedModel.objects.get(media_id=media_id)
    message = ""

    representations_df = get_representation_df(pickle_folder=pickle_folder)

    infer_obj = InferenceVideo(
        representations_df=representations_df,
        role=role,
        attendance_type=attendance_type,
        taken_for_user_uuid=taken_for_user_uuid,
        school_id=school_id
    )

    print('---attendance_type---', attendance_type)

    if attendance_type == "class":
        period_id = PeriodModel.objects.get(period_number=period_number, section=section,
                                            class_name=class_name,
                                            day=day, school_id=school_id)
        attendance_list = AttendanceModel.objects.filter(period_id=period_id,
                                                         attendance_date=attendance_date)
        logged_in_user = Profile.objects.get(profile_id=logged_in_user_uuid)
        students = Profile.objects.filter(role=role, class_name=class_name, section=section, school_id=school_id)
        taken_by = Profile.objects.get(profile_id=taken_by_user_uuid)

        # set organization type
        org_type = logged_in_user.school_id.organisation_type
        infer_obj.set_organization_type(org_type=org_type)
        # set organization type

        # if attendance list is empty i.e. no attendance is taken yet
        if attendance_list and attendance_list[0].attempt_status == "success":
            message = "Attendance Already taken for given period and date!!!"
        else:
            attempt_status = "failure"
            message = f"{role} attendance failed"
            if students:
                print('---pickle_folder---', pickle_folder)
                print('---role---', role)
                video_data = []  # sample response data
                try:
                    video_data = infer_obj.inference_video(video_file=file_path)
                except:
                    log.exception("Exception occurred during Attendence")

                attendance_status = []

                if video_data and video_data['set_of_users_identified']:
                    for user in students:
                        if str(user.profile_id) in video_data['set_of_users_identified']:
                            attendance_status.append({
                                "status": "present",
                                "profile_id": str(user.profile_id)
                            })
                        else:
                            attendance_status.append({
                                "status": "absent",
                                "profile_id": str(user.profile_id)
                            })

                    if attendance_list:
                        log.info("---- UPDATE ----")
                        attendance_obj = attendance_list[0]
                        prev_media_id = attendance_obj.media_id
                        attendance_obj.media_id = media_id
                        attendance_obj.attempt_status = "success"
                        attendance_obj.attendance_status = attendance_status
                        attendance_obj.save()
                        attendance_get_qs = attendance_obj
                        delete_media_file(prev_media_id)
                    else:
                        log.info("---- CREATING ATTENDANCE ROW ----")
                        attendance_get_qs = create_attendance_row(
                            user=logged_in_user,
                            attendance_taker=taken_by,
                            attempt_status="success",
                            period_id=period_id,
                            media_id=media_id,
                            attendance_status=attendance_status,
                            attendance_date=attendance_date,
                            attendance_choice=attendance_choice)
                        log.info("---- CREATING ATTENDANCE ROW COMPLETED ----")
                    message = "Attendance Completed"
                    is_completed = True
                    attempt_status = "success"
                else:
                    message = "No faces identified"
                    # Handle case when all students absent/ No face recognised / Mass bunk
                    if attendance_list:
                        log.info("---- FAILURE MEDIA UPDATE ----")
                        attendance_obj = attendance_list[0]
                        prev_media_id = attendance_obj.media_id
                        attendance_obj.media_id = media_id
                        attendance_obj.save()
                        attendance_get_qs = attendance_obj

                        delete_media_file(prev_media_id)
                    else:
                        log.info("---- FAILURE ROW CREATE ----")
                        attendance_get_qs = create_attendance_row(
                            user=logged_in_user,
                            attendance_taker=taken_by,
                            attempt_status="failure",
                            period_id=period_id,
                            media_id=media_id,
                            attendance_status=attendance_status,
                            attendance_date=attendance_date,
                            attendance_choice=attendance_choice)
                        log.info("---- FAILURE ROW CREATE COMPLETED----")
            else:
                message = "No student registered"

            log.info("---- CREATE STAFF ATTENDANCE ROW ----")
            StaffAttendanceModel.objects.create(
                attendance_type=staff_attendance_type,
                attempt_status=attempt_status,
                loggedin_user=logged_in_user,
                taken_by=taken_by,
                media_id=media_id,
                # attendance_status=attendance_status,
                attendance_date=attendance_date
            )

            log.info("---- CREATE STAFF ATTENDANCE ROW COMPLETED----")
    elif attendance_type == "cctv":
        logged_in_user = Profile.objects.get(profile_id=logged_in_user_uuid)
        taken_by = Profile.objects.get(profile_id=taken_by_user_uuid)

        print('---pickle_folder---', pickle_folder)
        print('---role---', role)

        log.info("--- TAKING ATTENDANCE ---")
        video_data = []
        try:
            video_data = infer_obj.inference_video(video_file=file_path)
        except:
            log.exception("Exception occurred during %s Attendance", attendance_type)

        attendance_status = []
        attempt_status = "failure"

        # video_data = {
        # 	'faces_identified': [{
        # 		'class': '7ee74383-9eb9-4eb4-a20b-858f860ac00a',
        # 		'role': 'school_admin',
        # 		'bbox': {
        # 			'x_min': 555,
        # 			'y_min': 329,
        # 			'x_max': 746,
        # 			'y_max': 563
        # 		},
        # 		'match': True
        # 	}],
        # 	'set_of_users_identified': ['7ee74383-9eb9-4eb4-a20b-858f860ac00a']
        # }
        print('---video_data---', video_data)

        if video_data and video_data['faces_identified']:

            for item in video_data['faces_identified']:
                profile_id = item["class"]
                recognised_role = item["role"]
                recognised_profile_qs = Profile.objects.filter(profile_id=profile_id, role=recognised_role)[0]

                print('---recognised_profile_qs---', recognised_profile_qs)
                attendance_status.append({
                    "status": "present",
                    "profile_id": str(recognised_profile_qs.profile_id)
                })
                attempt_status = "success"

            attendance_get_qs = update_camera_response_row(camera_response_id=camera_response_id,
                                                           media_id=media_id,
                                                           cctv_attempt_status="success",
                                                           cctv_attendance_status=attendance_status,
                                                           attendance_date=attendance_date)
        else:
            attendance_get_qs = update_camera_response_row(camera_response_id=camera_response_id,
                                                           media_id=media_id,
                                                           cctv_attempt_status="failure",
                                                           cctv_attendance_status=attendance_status,
                                                           attendance_date=attendance_date)

        print("--- attendance_status ---", attendance_status)

        log.info("--- TAKING ATTENDANCE COMPLETED ---")
    else:
        if attendance_type == "self":
            logged_in_user = Profile.objects.get(profile_id=logged_in_user_uuid)
            taken_by = logged_in_user
            taken_for = logged_in_user
        elif attendance_type == "other":
            logged_in_user = Profile.objects.get(profile_id=logged_in_user_uuid)
            taken_by = Profile.objects.get(profile_id=taken_by_user_uuid)
            taken_for = Profile.objects.get(profile_id=taken_for_user_uuid)

        # set organization type
        org_type = logged_in_user.school_id.organisation_type
        infer_obj.set_organization_type(org_type=org_type)
        # set organization type

        print('---taken_for---', taken_for)
        print('---attendance_date---', attendance_date)
        print('---staff_attendance_type---', staff_attendance_type)

        # UNCOMMENT START #
        # staff_attendance_list = StaffAttendanceModel.objects.filter(
        #     taken_for=taken_for,
        #     attendance_date__date=attendance_date,
        #     attempt_status="success",
        #     attendance_type=staff_attendance_type
        # )
        # print('---staff_attendance_list---', staff_attendance_list)
        #
        # if staff_attendance_list:
        #     log.info("---- STAFF ATTENDANCE ALREADY TAKEN FOR GIVEN DATE ----")
        #     message = "Attendance already taken for given date: " + attendance_date.strftime("%d-%m-%Y")
        #     staff_attendance_get_qs = staff_attendance_list
        # else:

        log.info("--- TAKING ATTENDANCE ---")
        video_data = []
        try:

            video_data = infer_obj.inference_video(video_file=file_path)
        except:
            log.exception("Exception occurred during %s Attendance", attendance_type)

        print('---video_data---', video_data)

        attendance_status = []
        message = f"{role} attendance failed"
        attempt_status = "failure"
        if video_data and video_data['set_of_users_identified']:
            if taken_for_user_uuid in video_data['set_of_users_identified']:
                attendance_status.append({
                    "status": "present",
                    "profile_id": str(taken_for.profile_id)
                })
                attempt_status = "success"
                message = f"{role} attendance completed"
                is_completed = True
                set_attendance_under_process(taken_for.profile_id, False, staff_attendance_type)
            else:
                # attendance_status.append({
                #     "status": "absent",
                #     "profile_id": str(taken_for.profile_id)
                # })
                set_attendance_under_process(taken_for.profile_id, False)
        else:
            set_attendance_under_process(taken_for.profile_id, False)

        log.info("--- TAKING ATTENDANCE COMPLETED ---")

        log.info("---- CREATE STAFF ATTENDANCE ROW ----")
        staff_attendance_get_qs = StaffAttendanceModel.objects.create(
            attendance_type=staff_attendance_type,
            attempt_status=attempt_status,
            loggedin_user=logged_in_user,
            taken_by=taken_by,
            taken_for=taken_for,
            media_id=media_id,
            attendance_status=attendance_status,
            attendance_date=attendance_date,
            staff_attendance_geolocation=staff_attendance_geolocation,
        )
        log.info("---- CREATE STAFF ATTENDANCE ROW COMPLETED----")

    # if self/other --- staff,non-staff attendance
    if staff_attendance_get_qs:
        return is_completed, message, staff_attendance_get_qs
    else:  # else class attendance
        return is_completed, message, attendance_get_qs
