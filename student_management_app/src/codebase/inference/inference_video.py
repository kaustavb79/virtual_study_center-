import concurrent.futures
import logging
import os
import shutil
import time

import pandas as pd
from django.conf import settings

from student_management_app.src.codebase.inference.inference_image import InferenceImage
from student_management_app.src.codebase.utility import extract_images_from_blobs

log = logging.getLogger("redis")

"""
    ---- video inference ---
"""


class InferenceVideo:
    """
    Detect, Verify and Recognize faces from a video file.

    Attributes:
        representations_df (pd.DataFrame): DataFrame consisting of representations of trained faces.
        role (str): Role of the user.
    """

    def __init__(self, representations_df, attendance_type, taken_for_user_uuid, **kwargs):
        self.school_id = ""
        self.role = ""
        self.org_type = ""

        if 'school_id' in kwargs:
            self.school_id = kwargs['school_id']
        if 'role' in kwargs:
            self.role = kwargs['role']
        if 'org_type' in kwargs:
            self.org_type = kwargs['org_type']

        self.frame_folder = None
        self.representations_df = representations_df
        self.img_infer = InferenceImage(
            representations_df=self.representations_df,
            role=self.role,
            school_id=self.school_id,
            org_type=self.org_type,
        )

        self.attendance_type = attendance_type
        self.taken_for_user_uuid = taken_for_user_uuid

    def set_organization_type(self, org_type):
        self.org_type = org_type
        self.img_infer.set_organization_type(org_type=org_type)


    def __save_temp_folder(self):
        """
        Method to save the extracted frames for inference.

        Parameters: None

        Returns: None
        """

        if not settings.SAVE_TEMP_FOLDER_INFERENCE:
            if os.path.exists(self.frame_folder):
                shutil.rmtree(self.frame_folder)
                if '\\' in self.frame_folder:
                    os.rmdir('\\'.join(self.frame_folder.split('\\')[:-1]))
                else:
                    os.rmdir('/'.join(self.frame_folder.split('/')[:-1]))

    def __extract_images_for_inference(self, video_file_path: str):
        """
        Extract frames from video.

        Parameters:
            video_file_path (str): Path to video file.

        Returns: None
        """

        file_name = os.path.splitext(video_file_path)[0]

        # if "\\" in video_file_path:
        #     video_folder = "/".join(video_file_path.split("\\")[:-1])
        #     file_name = file_name.split("\\")[-1]
        # else:
        video_folder = "/".join(video_file_path.split("/")[:-1])
        file_name = file_name.split("/")[-1]

        temp_folder_name = "temp_" + time.strftime("%Y%m%d%H%M%S")
        temp_folder = os.path.join(video_folder, temp_folder_name)
        log.info("Attendance Temp extract folder: %s", temp_folder)
        log.info("Attendance video_file_path: %s", video_file_path)

        if not os.path.exists(temp_folder):
            os.mkdir(temp_folder)
        temp_folder = os.path.join(temp_folder, file_name)
        if not os.path.exists(temp_folder):
            os.mkdir(temp_folder)

        log.info('EXTRACTING IMAGES FROM INFERENCE')
        extract_images_from_blobs(waiting_folder=temp_folder, video_file=video_file_path)
        log.info('EXTRACTING IMAGES FROM INFERENCE >>> COMPLETED')

        self.frame_folder = temp_folder

    def __call_inference_api(self, count, set_of_images):
        """
        Executor method to do inference on a list of frames.

        Parameters:
            count (integer): Counter variable.
            set_of_images (list): Set of images to do inference on.

        Returns: A list of dictionary
        """

        results = []

        for x in set_of_images:
            log.info('List Count: %s --- image: %s', count, x)
            inference_result = self.img_infer.inference_image(image_path=os.path.join(self.frame_folder, x))
            results.append(inference_result[0])

            if self.attendance_type in ['self', 'other'] and self.taken_for_user_uuid in inference_result[1][
                'set_of_users_identified']:
                break
        return results

    def inference_video(self, video_file: str):
        """
        Method to process a video file and a return a set of detected faces with their face regions and matching id's

        Parameters:
            video_file (str): Path to uploaded video file

        Returns: A dictionary.

        """

        faces_identified = []
        set_of_classes_identified = set()

        self.__extract_images_for_inference(video_file_path=video_file)

        frames_extracted = os.listdir(self.frame_folder)
        sublists = list()
        chunk_size = 10

        for i in range(0, len(frames_extracted), chunk_size):
            sublists.append(frames_extracted[i:i + chunk_size])

        response = list()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            futures = {
                executor.submit(self.__call_inference_api, count, lst) for count, lst in
                enumerate(sublists)}
            for future in concurrent.futures.as_completed(futures):
                response = future.result()

        if response:
            for lst in response:
                if lst:
                    for x in lst:
                        if x['id'] not in set_of_classes_identified:
                            faces_identified.append(x)
                            set_of_classes_identified.add(x['id'])

        self.__save_temp_folder()

        return {"faces_identified": faces_identified, "set_of_users_identified": list(set_of_classes_identified)}
