import logging
from django.conf import settings
from datetime import datetime

from student_management_app.src.codebase.embeddings.embedding_predict import represent
from student_management_app.src.codebase.embeddings.face_detect import detect_faces_from_image

log = logging.getLogger("redis")


def get_embeddings(image: str):
    """
    Get face region and embeddings from an image

    Parameters:
        image (str): path to image

    Returns:
         list of dict [{'media_file':'...','face_region':{},'embedding':[<vector>,<vector>,...]}]
    """

    log.info("Input image: << %s >>",image)

    representations = list()

    detected_faces = detect_faces_from_image(image=image)

    if detected_faces:
        for face in detected_faces:
            start_embedding_gen_gl = datetime.now()

            representation_predict = represent(
                face=face[0],
                model=settings.RECOGNIION_MODEL,
                enforce_detection=settings.RECOGNITION_DETECTION_ENFORCE,
                normalization=settings.RECOGNITION_NORMALIZATION
            )

            end_embedding_gen_gl = datetime.now()
            log.info(" --- Embedding creation TIME TAKEN : %s ----", end_embedding_gen_gl - start_embedding_gen_gl)

            if representation_predict:
                representations.append(
                    {
                        "media_file": image,
                        "face_region": {
                            "x_min": face[1][0],
                            "y_min": face[1][1],
                            "x_max": face[1][2] + face[1][0],
                            "y_max": face[1][3] + face[1][1],
                        },
                        "embedding": representation_predict
                    }
                )
    else:
        log.error("No face detected for given image!!!")
    return representations
