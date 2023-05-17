import base64
import logging
import os
import time
import cv2
from django.conf import settings
from django.core.files.base import ContentFile

log = logging.getLogger("redis")


def base64_file(data, name=None):
    _format, _img_str = data.split(';base64,')
    _name, ext = _format.split('/')
    if not name:
        name = _name.split(":")[-1]
    return ContentFile(base64.b64decode(_img_str), name='{}.{}'.format(name, ext))


def base64_decode(data):
    format, imgstr = data.split(';base64,')
    return imgstr.decode('base64')


def base64_encode(data):
    if data:
        return 'data:image/png;base64,' + data



# from matplotlib import pyplot as plt

def convertScale(img, alpha, beta):
    """Add bias and gain to an image with saturation arithmetics. Unlike
    cv2.convertScaleAbs, it does not take an absolute value, which would lead to
    nonsensical results (e.g., a pixel at 44 with alpha = 3 and beta = -210
    becomes 78 with OpenCV, when in fact it should become 0).
    """

    new_img = img * alpha + beta
    new_img[new_img < 0] = 0
    new_img[new_img > 255] = 255
    return new_img.astype(np.uint8)


# Automatic brightness and contrast optimization with optional histogram clipping
def automatic_brightness_and_contrast(image, clip_hist_percent=25):
    # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = image
    # Calculate grayscale histogram
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist_size = len(hist)

    # Calculate cumulative distribution from the histogram
    accumulator = []
    accumulator.append(float(hist[0]))
    for index in range(1, hist_size):
        accumulator.append(accumulator[index - 1] + float(hist[index]))

    # Locate points to clip
    maximum = accumulator[-1]
    clip_hist_percent *= (maximum / 100.0)
    clip_hist_percent /= 2.0

    # Locate left cut
    minimum_gray = 0
    while accumulator[minimum_gray] < clip_hist_percent:
        minimum_gray += 1

    # Locate right cut
    maximum_gray = hist_size - 1
    while accumulator[maximum_gray] >= (maximum - clip_hist_percent):
        maximum_gray -= 1

    # Calculate alpha and beta values
    alpha = 255 / (maximum_gray - minimum_gray)
    beta = -minimum_gray * alpha

    '''
    # Calculate new histogram with desired range and show histogram 
    new_hist = cv2.calcHist([gray],[0],None,[256],[minimum_gray,maximum_gray])
    plt.plot(hist)
    plt.plot(new_hist)
    plt.xlim([0,256])
    plt.show()
    '''

    auto_result = convertScale(image, alpha=alpha, beta=beta)
    return auto_result, alpha, beta


"""
    Method to save frames to media
    Args:
        - frame_data_dict:
            A dict containing frame count and its image data (np.array)
            {count:np.array}
        - waiting_folder:
            Path to waiting folder where the frames are to be saved
    Returns:
        None
"""


def save_frames(frame_data_dict, waiting_folder):
    const_time = time.strftime("%Y%m%d%H%M%S")
    updated_frames = dict()
    counts = list(frame_data_dict.keys())
    log.info("len(counts) -- total frames extract : %s", len(counts))

    if len(counts) <= settings.MAX_FRAMES_TO_BE_EXTRACTED:
        updated_frames = frame_data_dict

    log.info("len(updated_frames) 1 :  %s", len(updated_frames))
    COUNT_IDX = 0
    for ct in range(0, len(counts)):
        if ct % settings.FRAME_COUNTER == 0:
            if len(updated_frames.keys()) >= settings.MAX_FRAMES_TO_BE_EXTRACTED:
                break
            updated_frames[counts[ct]] = frame_data_dict[counts[ct]]
            COUNT_IDX += 1

    log.info("len(updated_frames) 2 :  %s", len(updated_frames))
    if COUNT_IDX < settings.MAX_FRAMES_TO_BE_EXTRACTED:
        for ctx, img in frame_data_dict.items():
            if len(updated_frames.keys()) >= settings.MAX_FRAMES_TO_BE_EXTRACTED:
                break
            updated_frames[ctx] = img

    log.info("len(updated_frames) 3 :  %s", len(updated_frames))

    for count, img in updated_frames.items():
        adjusted_img_result = img
        if settings.ADJUST_IMAGE_BRIGHTNESS:
            adjusted_img_result, alpha, beta = automatic_brightness_and_contrast(img)
        cv2.imwrite(os.path.join(waiting_folder, "%s_frame_%d.jpg") % (const_time, count), adjusted_img_result)


"""
    Utility method to extract frames from blob to media
    Args:
        - video_file:
            Path to video file (mp4,amv,blob files)
        - waiting_folder:
            Path to waiting folder where the frames are to be saved
    Returns:
        None
"""


def extract_images_from_blobs(waiting_folder, video_file):
    frames = {}

    vidcap = cv2.VideoCapture(video_file)
    every_n_frame = settings.FRAME_EXTRACT_RATE
    fps = vidcap.get(cv2.CAP_PROP_FPS)
    log.warn("FPS : %s", fps)

    after_n_frame = int(every_n_frame * fps)
    log.info('---every_n_frame--- %s', every_n_frame)
    log.info('---fps--- %s', fps)

    success, image = vidcap.read()
    count = 0
    counter = 0
    while success:
        if count % after_n_frame == 0:
            frames[count] = image
            counter += 1
        success, image = vidcap.read()
        count += 1
    # print(frames)
    save_frames(frame_data_dict=frames, waiting_folder=waiting_folder)



# if __name__ == "__main__":
#     image = cv2.imread('E:\\PERSONAL\\LUEIN\\codebases\\facial_recog\\main_app\\luein_smart_attendance\media'
#                        '\\media_file\\temp_20230224150851\\attendance__blob_zcBG5ux\\20230224150851_frame_4.jpg')
#     auto_result, alpha, beta = automatic_brightness_and_contrast(image)
#     print('alpha', alpha)
#     print('beta', beta)
#     cv2.imwrite('auto_result.png', auto_result)