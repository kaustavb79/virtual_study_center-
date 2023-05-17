import logging
import os
import time
import warnings
import tensorflow as tf
from deepface.commons import functions
from django.conf import settings
from tqdm import tqdm

from student_management_app.src.codebase.embeddings.image_embeddings import get_embeddings
from student_management_app.src.codebase.inference.similarity_check.similarity import get_similarity, get_similarity_es

warnings.filterwarnings("ignore")

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

tf_version = int(tf.__version__.split(".")[0])
if tf_version == 2:
    import logging

    tf.get_logger().setLevel(logging.ERROR)

log = logging.getLogger("redis")


class InferenceImage:
    """
    Detect, Verify and Recognize faces from an image.

    Attributes:
        representations_df (pd.DataFrame): DataFrame consisting of representations of trained faces.
        role (str): Role of the user.
        prog_bar (bool): Default is True
    """

    def __init__(self, representations_df, **kwargs):
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
        self.prog_bar = True

    def set_organization_type(self, org_type):
        self.org_type = org_type

    def __find_match_pickle(self, image):
        results = []

        if not self.representations_df.empty:
            df = self.representations_df

            # role based filter
            if self.role:
                if '\\' in df['media_file'].values.tolist()[0]:
                    df['role'] = df['media_file'].apply(lambda x: x.split("\\")[-3])
                else:
                    df['role'] = df['media_file'].apply(lambda x: x.split("/")[-3])
                # print(df)
                df = df[df['role'] == self.role]
                # print(df)
                df.drop(columns=["role"])
            df_base = df.copy()  # df will be filtered in each img. we will restore it for the next item.

            embeddings = get_embeddings(image=image)

            for face in embeddings:
                detected_face = {}
                target_representation = face['embedding']

                df_updt = get_similarity(database_df=df, target_representation=target_representation)

                df_dict = df_updt.to_dict('records')
                if df_dict and not detected_face:
                    profile_id = "Unknown"

                    data_split = df_dict[0]['media_file'].split("/")[-3:]
                    if '\\' in data_split[-1]:
                        temp = data_split[-1].split('\\')
                        data_split.pop(-1)
                        for x in temp: data_split.append(x)

                    # print("Data split: ", data_split)

                    if data_split:
                        profile_id = data_split[-2]

                    detected_face = {
                        "id": profile_id,
                        "role": self.role,
                        "face_region": face['face_region']
                    }
                    results.append(detected_face)
                df = df_base.copy()  # restore df for the next iteration
        else:
            log.error("No data in representations pickle file!!!")
        return results

    def __find_match_es(self, image):
        results = []

        embeddings = get_embeddings(image=image)

        for face in embeddings:
            target_representation = face['embedding']

            response = get_similarity_es(
                target_representation=target_representation,
                organization_id=self.school_id,
                organization_type=self.org_type,
                role=self.role,
                is_active="true",
            )

            for X in response:
                dct = X['_source']
                detected_face = {
                    "id": dct['profile_id'],
                    "role": self.role,
                    "face_region": face['face_region']
                }
                results.append(detected_face)

        return results

    def _find_match(self, img_path):
        """
        Wrapper function to detect faces in an image.

        Parameters:
            img_path (str): path to image file

        Returns: A list of dictionaries

        """

        tic = time.time()
        results = list()
        if settings.RECOGNITION_SIMILARITY_MATCH == "pickle":
            results = self.__find_match_pickle(image=img_path)
            # if not results:
            #     results = self.__find_match_es(image=img_path)
        elif settings.RECOGNITION_SIMILARITY_MATCH == "elastic":
            results = self.__find_match_es(image=img_path)
        else:
            log.error("Invalid RECOGNITION_SIMILARITY_MATCH --- %s  provided!!!", settings.RECOGNITION_SIMILARITY_MATCH)

        toc = time.time()

        log.info("find function lasts %s seconds", toc - tic)
        log.info("Results:  %s", results)
        print("---results---", results)

        return results

    def inference_image(self, image_path):
        """
        Main function to detect faces from an image.

        Parameters:
            image_path (str): path to image

        Returns: A tuple of list of responses from  find_match and a dictionary
        """

        results = self._find_match(img_path=image_path)
        response = {"faces_identified": results, "set_of_users_identified": [x['id'] for x in results]}
        return results, response
