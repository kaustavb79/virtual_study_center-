import logging
from datetime import datetime

from deepface.commons import distance as dst
from django.conf import settings

log = logging.getLogger("redis")


def get_similarity(database_df, target_representation):
    start_face_recog = datetime.now()
    df = database_df

    distances = []

    for index, instance in df.iterrows():
        source_representation = instance["embedding"]

        if settings.RECOGNIION_METRICS == 'cosine':
            distance = dst.findCosineDistance(source_representation, target_representation)
        elif settings.RECOGNIION_METRICS == 'euclidean':
            distance = dst.findEuclideanDistance(source_representation, target_representation)
        elif settings.RECOGNIION_METRICS == 'euclidean_l2':
            distance = dst.findEuclideanDistance(dst.l2_normalize(source_representation),
                                                 dst.l2_normalize(target_representation))

        distances.append(distance)

    # ---------------------------

    df["distances"] = distances

    threshold = dst.findThreshold(model_name=settings.RECOGNIION_MODEL_NAME,
                                  distance_metric=settings.RECOGNIION_METRICS)
    print("default threshold: ", threshold)
    df = df.drop(columns=["embedding"])
    df = df[df["distances"] <= threshold]

    df = df.sort_values(by=["distances"], ascending=True).reset_index(drop=True)

    end_face_recog = datetime.now()
    log.warning("Similarity check took %s time", end_face_recog - start_face_recog)
    return df


def get_similarity_es(target_representation, organization_id, organization_type, role, is_active):
    query = {
        "size": 10,
        "query": {
            "script_score": {
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"organization_id": organization_id}}
                        ],
                        "filter": [
                            {"term": {"is_active": is_active}},
                            {"term": {"role": role}},
                            {"term": {"organization_type": organization_type}}
                        ]
                    }
                },
                "script": {
                    "source": "1 / (1 + l2norm(params.queryVector, 'embedding'))",
                    "params": {
                        "queryVector": target_representation
                    }
                }
            }
        }
    }

    res = settings.ES_INSTANCE.search(index=settings.ES_INDEX_NAME, body=query)
    return res['hits']['hits']
