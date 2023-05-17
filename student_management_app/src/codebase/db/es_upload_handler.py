import csv
import json
import logging
import os
import pandas as pd
from student_management_app.src.codebase.db.elastic import ElasticSearch

ES_FILE_WAITING = "resources/elastic_waiting_representations_redis.csv"

log = logging.getLogger("redis")


def handle_es_upload(representations, school_id, role, profile_id, org_type):
    log.warning("Failed to push representation : %s ",representations)
    file_exists = os.path.isfile(ES_FILE_WAITING)

    with open(ES_FILE_WAITING, 'a') as csvfile:
        headers = ['school_id', 'org_type', 'role', 'profile_id', 'is_active', 'representations']
        writer = csv.DictWriter(csvfile, delimiter=',', lineterminator='\n', fieldnames=headers)

        if not file_exists:
            writer.writeheader()  # file doesn't exist yet, write a header

        writer.writerow({
            'school_id': school_id,
            'org_type': org_type,
            'role': role,
            'profile_id': profile_id,
            'is_active': True,
            'representations': representations
        })


def upload_pending_representations():
    log.warning("Uploading failed to push representation!!!")

    if not os.path.exists(ES_FILE_WAITING):
        f = open(ES_FILE_WAITING, 'w')
        headers = ['school_id', 'org_type', 'role', 'profile_id', 'is_active', 'representations']
        writer = csv.DictWriter(f, delimiter=',', lineterminator='\n', fieldnames=headers)
        writer.writeheader()
        f.close()

    df = None
    try:
        df = pd.read_csv(ES_FILE_WAITING)
    except:
        log.error("Empty sheet... no data to push to es!!!")

    if not df.empty:
        df_dict = df.to_dict('records')

        if df_dict:
            df_dict_updated = df_dict
            for idx, X in enumerate(df_dict):
                X['representations'] = X['representations'].replace('\\','/')
                X['representations'] = X['representations'].replace("\'", "\"")
                # print(json.loads(X['representations']))

                obj = ElasticSearch(
                    organization_id=X['school_id'],
                    role=X['role'],
                    profile_id=X['profile_id'],
                    org_type=X['org_type'],
                    is_active=X['is_active'],
                    representations=json.loads(X['representations'])
                )
                # obj.bulk_write_to_es()
                obj.sequential_write_to_es()
                del df_dict_updated[idx]

            f = open(ES_FILE_WAITING, 'w')
            headers = ['school_id', 'org_type', 'role', 'profile_id', 'is_active', 'representations']
            writer = csv.DictWriter(f, delimiter=',', lineterminator='\n', fieldnames=headers)
            writer.writeheader()
            writer.writerows(df_dict_updated)
            f.close()
