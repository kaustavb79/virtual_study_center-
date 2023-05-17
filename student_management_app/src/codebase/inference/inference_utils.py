from student_management_app.src.codebase.db.pickle_func import PickleUtility


def get_representation_df(pickle_folder: str):
    df = None
    if pickle_folder:
        obj = PickleUtility()
        df = obj.load_pickle_data_to_df(pickle_folder=pickle_folder)
    return df