import logging
from deepface.commons import functions

from student_management_app.src.codebase.embeddings.normalize_image import normalize_input
from student_management_app.src.codebase.embeddings.prerprocess import preprocess_face

log = logging.getLogger("api_face_recog_test")


def represent(face, model=None, enforce_detection=True, normalization='base'):
    """
	This function represents facial images as vectors.

	Parameters:
		face: numpy array (BGR) of detected face
		model: Built deepface model. A face recognition model is built every call of verify function. You can pass pre-built face recognition model optionally if you will call verify function several times. Consider to pass model if you are going to call represent function in a for loop.
			model = DeepFace.build_model('VGG-Face')
		enforce_detection (boolean): If any face could not be detected in an image, then verify function will return exception. Set this to False not to have this exception. This might be convenient for low resolution images.
		normalization (string): normalize the input image before feeding to model

	Returns:
		Represent function returns a multidimensional vector. The number of dimensions is changing based on the reference model. E.g. FaceNet returns 128 dimensional vector; VGG-Face returns 2622 dimensional vector.
	"""


    # decide input shape
    input_shape_x, input_shape_y = functions.find_input_shape(model)

    print("target size: ", (input_shape_y, input_shape_x))

    # detect and align
    preprocessed_img = preprocess_face(img=face
                                    , target_size=(input_shape_y, input_shape_x)
                                    , enforce_detection=enforce_detection)

    # ---------------------------------
    # custom normalization

    normalized_face = normalize_input(img=preprocessed_img, normalization=normalization)

    # ---------------------------------

    # represent
    prediction = model.predict(normalized_face)
    embedding = prediction[0].tolist()

    return embedding