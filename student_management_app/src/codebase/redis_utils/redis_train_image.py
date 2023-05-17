import logging
import os
from app_root.models import Profile
from student_management_app.src.codebase.train.train_image import TrainImages

log = logging.getLogger("redis")

LUEIN_SM_ATT_PROJ_PATH = os.getenv("LUEIN_SM_ATT_PROJ_PATH")

"""
    ---------------------------------------------------------------
        TRAINING HANDLER METHOD
    ---------------------------------------------------------------
"""


def train_face_recognition_model(wait_folder, pickle_folder):
    """
    Pass a list of images and then detect faces and generate embeddings and save/update representations for a given profile.

    Parameters:
        wait_folder (str): Path to folder containing to be trained set of images
        pickle_folder (Str): Path to representations.pkl file where the representations for each image need to be serialized

    Returns:
         - is_completed (boolean): status of the process
         - profile_id (str): Profile uuid of the user whose images where sent for training
         - response_data (json): response from the <train_images function>
                {
                    "status": status,
                    "message": message,
                    "face_model": settings.RECOGNIION_MODEL_NAME,
                    "detector": settings.RECOGNIION_DETECTOR,
                    "distance_similarity_metric": settings.RECOGNIION_METRICS,
                    "representations": representations
                }

    """
    is_completed = False
    profile_id = ""
    response_data = None
    waiting_folder = os.path.join(LUEIN_SM_ATT_PROJ_PATH, wait_folder)

    if os.path.exists(waiting_folder):
        if "\\" in waiting_folder:
            data_spit = waiting_folder.split("\\")
        else:
            data_spit = waiting_folder.split("/")

        profile_id = data_spit[-1]
        school_id = data_spit[-3]
        role = data_spit[-2]
        metadata = {
            'school_id': school_id,
            'role': role,
            'profile_id': profile_id,
            'org_type': ''
        }

        try:
            profile_qs = Profile.objects.get(pk=profile_id)
            org_type = profile_qs.school_id.organisation_type
            metadata['org_type'] = org_type
        except:
            log.exception("No profile found!!!")

        try:
            log.info("WAITING_FOLDER: %s", waiting_folder)
            obj = TrainImages(
                classes_to_train_folder_path=waiting_folder,
                pickle_folder=pickle_folder,
                metadata=metadata
            )
            response_data = obj.train_images()
        except:
            log.exception("Exception Occurred in Training API!!!")
        else:
            print("---- response_data--message: ", response_data['message'])
            if response_data['status'] == "success":
                log.info("TRAINING COMPLETED")
                is_completed = True
                print("----- profile_id : ", profile_id)
                profile_obj = Profile.objects.get(pk=profile_id)
                print("----- profile_obj : ", profile_obj)
                profile_obj.is_registered = is_completed
                profile_obj.save()
            else:
                log.error("TRAINING FAILED....CHECK LOGS FOR MORE DETAILS")
    else:
        log.error("Either Waiting Folder or Training folder doesn't exists yet!!!")
    return is_completed, profile_id, response_data
