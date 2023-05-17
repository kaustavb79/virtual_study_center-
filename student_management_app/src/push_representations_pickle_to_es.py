import logging as log_print
import sys, os, django

STUDY_CENTER_PROJ_PATH = os.getenv("STUDY_CENTER_PROJ_PATH")
print("STUDY_CENTER_PROJ_PATH : ", STUDY_CENTER_PROJ_PATH)
sys.path.append(STUDY_CENTER_PROJ_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = 'student_management_system.settings'
django.setup()

from django.conf import settings
from student_management_app.src.codebase.db.elastic import ElasticSearch
from student_management_app.src.codebase.inference.inference_utils import get_representation_df


def setup_custom_logger(name):
    formatter = log_print.Formatter(fmt='%(asctime)s - %(process)d - %(levelname)s - %(message)s')
    fh = log_print.FileHandler(settings.LOGS_DIR + '/es_static_test.log')
    fh.setFormatter(formatter)
    logger = log_print.getLogger(name)
    logger.setLevel(log_print.INFO)
    logger.addHandler(fh)
    return logger


log = setup_custom_logger("es_static")

if __name__ == "__main__":

    pickle_root_folder = "resources/attendance_prod_models/face_recog_db"
    for X in os.listdir(pickle_root_folder):
        school_id = X
        pickle_folder = os.path.join(STUDY_CENTER_PROJ_PATH, pickle_root_folder, school_id)
        log.info("---- PICKLE_FOLDER: %s ", pickle_folder)

        df = get_representation_df(pickle_folder=pickle_folder)
        df['school_id'] = df['media_file'].apply(lambda x: x.split("\\")[-4])
        df['role'] = df['media_file'].apply(lambda x: x.split("\\")[-3])
        df['profile_id'] = df['media_file'].apply(lambda x: x.split("\\")[-2])

        is_active = True

        print("------ df.shape: ", df.shape)

        df_group = df.groupby(by=['role'])
        for role in df_group.groups:
            print("role: ", role)
            df_x_group = df_group.get_group(role).groupby(by=['profile_id'])
            for profile in df_x_group.groups:
                print("profile_id: ", profile)
                profile_get_qs = Profile.objects.get(pk=profile)
                org_type = profile_get_qs.school_id.organisation_type
                print("org_type: ", org_type)
                df_x_1 = df_x_group.get_group(profile)
                df_x_1_dict = df_x_1.to_dict('records')

                obj = ElasticSearch(
                    school_id=school_id,
                    role=role,
                    profile_id=profile,
                    org_type=org_type,
                    is_active=is_active,
                    representations=df_x_1_dict
                )
                # obj.bulk_write_to_es()
                obj.sequential_write_to_es()
