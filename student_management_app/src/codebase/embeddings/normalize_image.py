import logging

log = logging.getLogger("redis")


def normalize_input(img, normalization='base'):
    # issue 131 declares that some normalization techniques improves the accuracy

    if normalization == 'base':
        return img
    else:
        # @trevorgribble and @davedgd contributed this feature

        img *= 255  # restore input in scale of [0, 255] because it was normalized in scale of  [0, 1] in preprocess_face

        if normalization == 'raw':
            pass  # return just restored pixels

        elif normalization == 'Facenet':
            mean, std = img.mean(), img.std()
            img = (img - mean) / std

        elif normalization == "Facenet2018":
            # simply / 127.5 - 1 (similar to facenet 2018 model preprocessing step as @iamrishab posted)
            img /= 127.5
            img -= 1

        elif normalization == 'VGGFace':
            # mean subtraction based on VGGFace1 training data
            img[..., 0] -= 93.5940
            img[..., 1] -= 104.7624
            img[..., 2] -= 129.1863

        elif normalization == 'VGGFace2':
            # mean subtraction based on VGGFace2 training data
            img[..., 0] -= 91.4953
            img[..., 1] -= 103.8827
            img[..., 2] -= 131.0912

        elif normalization == 'ArcFace':
            # Reference study: The faces are cropped and resized to 112×112,
            # and each pixel (ranged between [0, 255]) in RGB images is normalised
            # by subtracting 127.5 then divided by 128.
            img -= 127.5
            img /= 128

    # -----------------------------

    return img