import os
from django.conf import settings
import glob, shutil
import logging
from tqdm import tqdm

from student_management_app.src.codebase.db.elastic import ElasticSearch
from student_management_app.src.codebase.db.es_upload_handler import handle_es_upload
from student_management_app.src.codebase.db.pickle_func import PickleUtility
from student_management_app.src.codebase.embeddings.image_embeddings import get_embeddings

log = logging.getLogger("redis")


class TrainImages:
    """
    Save embeddings of faces from image/video.

    Attributes:
        classes_to_train_folder_path (str): waiting folder path.
        pickle_folder (str): path to save representations pickle file.
        metadata (dict): dictionary containing meta information.
            Allowed fields:
                - school_id
                - role
                - profile_id
                - org_type
    """

    def __init__(self, classes_to_train_folder_path: str, pickle_folder: str, metadata: dict):
        self.school_id = ""
        self.role = ""
        self.profile_id = ""
        self.org_type = ""
        if 'metadata':
            if 'school_id' in metadata:
                self.school_id = metadata['school_id']
            if 'role' in metadata:
                self.role = metadata['role']
            if 'profile_id' in metadata:
                self.profile_id = metadata['profile_id']
            if 'org_type' in metadata:
                self.org_type = metadata['org_type']

        self.pickle_folder = pickle_folder
        self.classes_to_train_folder_path = classes_to_train_folder_path
        self.pickle_util_obj = PickleUtility()
        self.es_util_obj = ElasticSearch(
            school_id=self.school_id,
            role=self.role,
            profile_id=self.profile_id,
            org_type=self.org_type,
            representations=[]
        )

    def __remove_files_from_waiting_folder(self):
        log.info("--- removing files in waiting folder---")
        if '\\' in self.classes_to_train_folder_path:
            waiting_data_folder_path = '/'.join(self.classes_to_train_folder_path.split("\\")[:-1])
        else:
            waiting_data_folder_path = '/'.join(self.classes_to_train_folder_path.split("/")[:-1])
        for f in glob.glob(os.path.join(waiting_data_folder_path, '*')):
            shutil.rmtree(f)
        log.info("--- removing files in waiting folder completed---")

    def __copy_training_images(self):
        list_of_images = []

        print("waiting_data_folder_path: ", self.classes_to_train_folder_path)

        if len(os.listdir(self.classes_to_train_folder_path)) == 0:
            raise ValueError("No data in 'waiting_folder'!!!")
        training_images_path = self.classes_to_train_folder_path.replace('waiting_folder', 'training_folder')

        log.info("--- coping files to training_images_path : %s started ---", training_images_path)
        for file in os.listdir(self.classes_to_train_folder_path):
            shutil.copy(os.path.join(self.classes_to_train_folder_path, file), os.path.join(training_images_path, file),
                        follow_symlinks=True)
            list_of_images.append(os.path.join(training_images_path, file))
        log.info("--- coping files to training_images_path : %s  completed ---", training_images_path)

        return list_of_images, training_images_path

    def __get_bulk_representations(self, list_of_images, training_images_path, disable_prog_bar=True):
        if os.path.isdir(training_images_path):
            if len(list_of_images) == 0:
                raise ValueError("'list_of_images' list is empty.........No image available for training!!!")

            pbar = tqdm(range(0, len(list_of_images)), desc='Finding representations...', disable=disable_prog_bar)

            representations_struct_update = list()

            for index in pbar:
                image = list_of_images[index]
                representations = get_embeddings(image=image)
                if representations:
                    for rep in representations:
                        representations_struct_update.append(rep)
                else:
                    log.warning("No representations found in image <<< %s >>>", image)

            return representations_struct_update

        else:
            raise IOError("Passed trained_images_path does not exist!")

    def train_images(self):
        status = "failure"
        message = ""
        representations = list()

        try:
            list_of_images, training_images_path = self.__copy_training_images()
        except Exception as e:
            log.exception("Exception occurred during train --- file copy from wait to train folder!!!")
            message = str(e)
        else:
            log.info("--- training started ---")
            print("total list_of_images: ", len(list_of_images))
            try:
                representations = self.__get_bulk_representations(
                    list_of_images=list_of_images,
                    training_images_path=training_images_path,
                    disable_prog_bar=False
                )
            except Exception as e:
                log.exception("EXCEPTION OCCURRED during train!!! ")
                message = str(e)
            else:
                self.pickle_util_obj.write_to_pickle(representations=representations, pickle_folder=self.pickle_folder)

                self.es_util_obj.set_representations(representations=representations)
                try:
                    self.es_util_obj.sequential_write_to_es()
                except Exception as e:
                    log.error("Exception occurred during write to es index ")
                    handle_es_upload(
                        representations=representations,
                        school_id=self.school_id,
                        profile_id=self.profile_id,
                        role=self.role,
                        org_type=self.org_type,
                    )

                status = "success"
                message = "Model updated Successfully!!!"
            log.info("--- training started completed---")

            self.__remove_files_from_waiting_folder()

        return {
            "status": status,
            "message": message,
            "face_model": settings.RECOGNIION_MODEL_NAME,
            "detector": settings.RECOGNIION_DETECTOR,
            "distance_similarity_metric": settings.RECOGNIION_METRICS,
            "representations": representations
        }
