import logging
import os
import pickle

import pandas as pd

log = logging.getLogger("redis")


class PickleUtility:
    def __init__(self):
        self.REPRESENTATIONS_FILE_NAME = "representations.pkl"

    def write_to_pickle(self, representations: list, pickle_folder: str):
        prev_representations = list()
        if os.path.exists(os.path.join(pickle_folder, self.REPRESENTATIONS_FILE_NAME)):
            with open(os.path.join(pickle_folder, self.REPRESENTATIONS_FILE_NAME), 'rb+') as f:
                prev_representations = pickle.load(f)

        with open(os.path.join(pickle_folder, self.REPRESENTATIONS_FILE_NAME), 'wb') as f:
            combined_data = prev_representations
            for x in representations:
                combined_data.append(x)
            pickle.dump(combined_data, f)

    def read_representations_from_pickle(self, pickle_folder: str):
        if os.path.exists(os.path.join(pickle_folder, self.REPRESENTATIONS_FILE_NAME)):
            with open(os.path.join(pickle_folder, self.REPRESENTATIONS_FILE_NAME), 'rb+') as f:
                representations = pickle.load(f)
            return representations
        else:
            raise IOError(f"File -- {pickle_folder}/{self.REPRESENTATIONS_FILE_NAME} doesn't exists!!")

    def load_pickle_data_to_df(self, pickle_folder: str):
        df = None
        try:
            representations = self.read_representations_from_pickle(pickle_folder=pickle_folder)
        except:
            log.exception("Exception during pickle load!!!")
        else:
            log.info("There are %s represeentations...", len(representations))
            df = pd.DataFrame(representations)
            # print(df)
        return df