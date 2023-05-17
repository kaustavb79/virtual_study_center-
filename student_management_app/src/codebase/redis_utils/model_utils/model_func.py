import logging
from app_root.models import StaffAttendanceModel, AttendanceModel, CameraResponseModel

log = logging.getLogger("redis")


def create_staff_attendance_row(staff_attendance_type, attempt_status, logged_in_user, taken_by, media_id,
                                attendance_date, taken_for, attendance_status, staff_attendance_geolocation):
    """
        Create row in staff attendance model

        Parameters:
            staff_attendance_type (str): staff_attendance_type
            attempt_status (str): success or failure
            logged_in_user (Object): Logged in user profile
            taken_by (Object): Attendance taken by user profile
            media_id (str): Attendance media id
            attendance_date (datetime): Date and time for attendance taken
            taken_for (Object): Attendance taken for user profile
            attendance_status (list): success or failure
            staff_attendance_geolocation (str):

        Returns:
            staff_attendance_get_qs: (Object) StaffAttendanceModel object
    """

    staff_attendance_get_qs = StaffAttendanceModel.objects.create(
        attendance_type=staff_attendance_type,
        attempt_status=attempt_status,
        loggedin_user=logged_in_user,
        taken_by=taken_by,
        media_id=media_id,
        attendance_date=attendance_date,
        taken_for=taken_for,
        attendance_status=attendance_status,
        staff_attendance_geolocation=staff_attendance_geolocation,
    )
    return staff_attendance_get_qs


def create_attendance_row(user, attendance_taker, attempt_status, period_id, media_id, attendance_status,
                          attendance_date, attendance_choice):
    """
            Create row in attendance model

            Parameters:
                attempt_status (str): success or failure
                user (Object): Logged in user profile
                attendance_taker (Object): Attendance taken by user profile
                media_id (str): Attendance media id
                attendance_date (datetime): Date and time for attendance taken
                attendance_choice (str): Attendance taken for user profile
                attendance_status (list): success or failure
                period_id (str): period uuid

            Returns:
                attendance_get_qs: (Object) AttendanceModel object
        """

    attendance_get_qs = AttendanceModel.objects.create(
        loggedin_user=user,
        attendance_taker=attendance_taker,
        attempt_status=attempt_status,
        period_id=period_id,
        media_id=media_id,
        attendance_status=attendance_status,
        attendance_date=attendance_date,
        attendance_choice=attendance_choice
    )
    return attendance_get_qs


"""
    --------------------------
    Add Camera response row in attendance model
    --------------------------
    Args:
        - user: (str) logged in user
        - attendance_taker: (str)
        - attempt_status: (str) 
        - period_id: (str) 
        - media_id: (str) 
        - attendance_date: (datetime) 
        - attendance_status: (list) 
    Return: 
        - attendance_get_qs: (Object) AttendanceModel object
"""


def create_camera_response_row(user, attendance_taker, attempt_status, period_id, media_id, attendance_status,
                               attendance_date):
    attendance_get_qs = AttendanceModel.objects.create(
        loggedin_user=user,
        attendance_taker=attendance_taker,
        attempt_status=attempt_status,
        period_id=period_id,
        media_id=media_id,
        attendance_status=attendance_status,
        attendance_date=attendance_date
    )
    return attendance_get_qs


"""
    --------------------------
    Update Camera response row in attendance model
    --------------------------
    Args:
        - camera_response_id: (str) 
        - media_id: (str)
        - cctv_attempt_status: (str) 
        - cctv_attendance_status: (str)  
        - attendance_date: (datetime) 
    Return: 
        - camera_response_get_qs: (Object) CameraResponseModel object
"""


def update_camera_response_row(camera_response_id, media_id, cctv_attempt_status,
                               cctv_attendance_status, attendance_date):
    camera_response_get_qs = CameraResponseModel.objects.filter(camera_response_id=camera_response_id)
    camera_response_get_qs.update(
        media_id=media_id,
        cctv_attempt_status=cctv_attempt_status,
        cctv_attendance_status=cctv_attendance_status,
        attendance_date=attendance_date,
    )

    return camera_response_get_qs[0]
