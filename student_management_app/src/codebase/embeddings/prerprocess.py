import logging
import cv2
import numpy as np
from deepface.commons.functions import load_image
import tensorflow as tf

tf_version = tf.__version__
tf_major_version = int(tf_version.split(".")[0])
tf_minor_version = int(tf_version.split(".")[1])

if tf_major_version == 1:
    from keras.preprocessing import image
elif tf_major_version == 2:
    from tensorflow.keras.preprocessing import image


log = logging.getLogger("redis")


def preprocess_face(img, target_size=(224, 224), grayscale=False, enforce_detection=True):

    img = load_image(img)
    base_img = img.copy()

    # img, region = detect_face(img=img, detector_backend=detector_backend, grayscale=grayscale,
    #                           enforce_detection=enforce_detection, align=align)

    # --------------------------

    if img.shape[0] == 0 or img.shape[1] == 0:
        if enforce_detection == True:
            raise ValueError("Detected face shape is ", img.shape,
                             ". Consider to set enforce_detection argument to False.")
        else:  # restore base image
            img = base_img.copy()

    # --------------------------

    # post-processing
    if grayscale == True:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # ---------------------------------------------------
    # resize image to expected shape

    # img = cv2.resize(img, target_size) #resize causes transformation on base image, adding black pixels to resize will not deform the base image

    if img.shape[0] > 0 and img.shape[1] > 0:
        factor_0 = target_size[0] / img.shape[0]
        factor_1 = target_size[1] / img.shape[1]
        factor = min(factor_0, factor_1)

        dsize = (int(img.shape[1] * factor), int(img.shape[0] * factor))
        img = cv2.resize(img, dsize)

        # Then pad the other side to the target size by adding black pixels
        diff_0 = target_size[0] - img.shape[0]
        diff_1 = target_size[1] - img.shape[1]
        if grayscale == False:
            # Put the base image in the middle of the padded image
            img = np.pad(img, ((diff_0 // 2, diff_0 - diff_0 // 2), (diff_1 // 2, diff_1 - diff_1 // 2), (0, 0)),
                         'constant')
        else:
            img = np.pad(img, ((diff_0 // 2, diff_0 - diff_0 // 2), (diff_1 // 2, diff_1 - diff_1 // 2)), 'constant')

    # ------------------------------------------

    # double check: if target image is not still the same size with target.
    if img.shape[0:2] != target_size:
        img = cv2.resize(img, target_size)

    # ---------------------------------------------------

    # cv2.imwrite("C:\\Users\\Kaustav\\Downloads\\istockphoto-1364222624-170667a__preprocessed___{face_count}.jpg",img)

    # normalizing the image pixels

    img_pixels = image.img_to_array(img)  # what this line doing? must?
    img_pixels = np.expand_dims(img_pixels, axis=0)
    img_pixels /= 255  # normalize input in [0, 1]

    # ---------------------------------------------------

    return img_pixels
