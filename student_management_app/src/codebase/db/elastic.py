import json
import logging
from datetime import datetime
from django.conf import settings
from elasticsearch import helpers

log = logging.getLogger("redis")


class ElasticSearch:
    """
    Elastic search utility class

    Write/Upload records to index in elasticsearch index.

    Es index record structure:
        {
            "_index": "<index_name>",
            "_id": "<index_row_id>",
            "profile_id": "",
            "role": "",
            "organization_id": "",
            "organization_type": "",
            "embedding": [vector, vector, ....],
            "bounding_box": {
                "x_min": ...,
                "y_min": ...,
                "x_max": ...,
                "x_max": ...,
            },
            "media_file": "<path_to_media_file>",
            "is_active": True  (Default),
            "creation_datetime": "record_creation_datetime"
        }

    Attributes:
        representations (list): A list of dictionary of representations + face_region + media_file
        school_id (str): (Optional) String field
        role (str): (Optional) String field
        profile_id (str): (Optional) String field
        org_type (str): (Optional) String field
    """

    def __init__(self, representations: list, **kwargs):
        self.organization_id = ""
        self.role = ""
        self.profile_id = ""
        self.org_type = ""
        self.active_status = True

        if 'school_id' in kwargs:
            self.organization_id = kwargs['school_id']
        if 'role' in kwargs:
            self.role = kwargs['role']
        if 'profile_id' in kwargs:
            self.profile_id = kwargs['profile_id']
        if 'org_type' in kwargs:
            self.org_type = kwargs['org_type']
        if 'active_status' in kwargs:
            self.active_status = kwargs['active_status']

        self.representations = representations

    def set_representations(self, representations: list):
        self.representations = representations

    def __add_mapping(self):
        """
        Create mapping / data dictionary for index creation in Elastic search.

        This method is a one time call function. To be run when a singleton index is created to store the records.
        Default index is 'master'.
        For new index, update the value of parameter 'ES_INDEX' in settings.py file.

        Parameters: None

        Returns: None
        """
        es_config = json.load(open(settings.ES_MAPPING_CONFIG))
        settings.ES_INSTANCE.indices.create(index=settings.ES_INDEX_NAME, ignore=400, body=es_config)
        log.info("Mapping created successfully")

    def __generate_record(self):
        for repr in self.representations:
            doc = {
                "_index": settings.ES_INDEX_NAME,
                "_id": str(self.profile_id) + '__' + str(int(datetime.now().microsecond)),
                "_source": {
                    "profile_id": self.profile_id,
                    "role": self.role,
                    "organization_id": self.organization_id,
                    "organization_type": self.org_type,
                    "embedding": repr['embedding'],
                    "bounding_box": repr['face_region'],
                    "media_file": repr['media_file'],
                    "is_active": self.active_status,
                    "creation_datetime": datetime.utcnow().isoformat()
                }
            }
            yield doc

    def bulk_write_to_es(self):
        """
        Bulk record insert method

        Parameters: None

        Returns: None
        """

        start = datetime.now()

        self.__add_mapping()

        log.info("Bulk insertion operation started")
        log.info("Uploading data to %s index in elastic search db...", settings.ES_INDEX_NAME)
        helpers.bulk(client=settings.ES_INSTANCE, actions=self.__generate_record(), request_timeout=settings.ES_REQUEST_TIMEOUT)

        result = settings.ES_INSTANCE.count(index=settings.ES_INDEX_NAME)
        log.info("Records inserted: %s ", result.body['count'])

        end = datetime.now()
        log.info("Bulk insertion operation completed.... Time taken: %s ", (end - start))

    def sequential_write_to_es(self):
        """
        Sequential record insert method

        Parameters: None

        Returns: None
        """

        start = datetime.now()

        self.__add_mapping()

        log.info("Sequential insertion operation started")
        log.info("Uploading data to %s index in elastic search db...", settings.ES_INDEX_NAME)

        count = 0
        for repr in self.representations:
            doc = {
                "profile_id": self.profile_id,
                "role": self.role,
                "organization_id": self.organization_id,
                "organization_type": self.org_type,
                "embedding": repr['embedding'],
                "bounding_box": repr['face_region'],
                "media_file": repr['media_file'],
                "is_active": self.active_status,
                "creation_datetime": datetime.utcnow().isoformat()
            }
            index_row_id = str(self.profile_id) + '__' + str(int(datetime.now().microsecond))
            settings.ES_INSTANCE.index(index=settings.ES_INDEX_NAME, id=index_row_id, document=doc)
            count += 1

        log.info("Records inserted: %s ", count)

        end = datetime.now()
        log.info("Sequential insertion operation completed.... Time taken: %s ", (end - start))

    def get_representations_all(self):
        representations_qs = \
            settings.ES_INSTANCE.search(index=settings.ES_INDEX_NAME, body={"query": {"match_all": {}}})['hits']['hits']
        representations = representations_qs[0]['_source']['representations']
        return representations
