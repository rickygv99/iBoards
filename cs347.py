import math
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from skimage import filters, feature, data, color, exposure, io
from skimage.feature import corner_peaks
from skimage.filters import gaussian
from skimage.transform import rescale, resize, downscale_local_mean
from skimage.util.shape import view_as_blocks
from scipy import signal
from scipy.ndimage import interpolation
from scipy.spatial.distance import cdist
from scipy.ndimage.filters import convolve

def get_hog(image):
    return feature.hog(image, pixels_per_cell=(8, 8), block_norm='L1', visualize=True)

def plot_hog(image, hog):
    plt.subplot(1, 2, 1)
    plt.imshow(image)
    plt.axis('off')

    plt.subplot(1, 2, 2)
    plt.imshow(hog)
    plt.axis('off')

    plt.show()

def sliding_window(image, base_score, stepSize, windowSize):
    (max_score, maxr, maxc) = (0, 0, 0)
    winH, winW = windowSize
    H, W = image.shape
    pad_image = np.lib.pad(image, ((winH // 2, winH - winH // 2), (winW // 2, winW - winW // 2)), mode='constant')
    response_map = np.zeros((H // stepSize + 1, W // stepSize + 1))

    for i in range(H // stepSize + 1):
        for j in range(W // stepSize + 1):
            if i * stepSize >= H or j * stepSize >= W:
                continue
            image_feature, image_hog = hog_feature(pad_image[i * stepSize : i * stepSize + winH, j * stepSize : j * stepSize + winW], 8)
            response_map[i][j] = np.dot(image_feature, base_score)
            if response_map[i][j] > max_score:
                max_score = response_map[i][j]
                maxr = i * stepSize - winH // 2
                maxc = j * stepSize - winW // 2
    response_map = resize(response_map, image.shape, mode="constant")

    return (max_score, maxr, maxc, response_map)

def plot_prediction(image, r, c, winW, winH):
    fig, ax = plt.subplots(1)
    ax.imshow(image)
    rect = patches.Rectangle((c, r), winW, winH, linewidth=1, edgecolor='r', facecolor='none')
    ax.add_patch(rect)
    plt.show()

def plot_heatmap(response_map):
    plt.imshow(response_map, cmap='viridis', interpolation='nearest')
    plt.title('sliding window')
    plt.show()

def pyramid(image, scale=0.9, minSize=(200, 100)):
    """
    Generate image pyramid using the given image and scale.
    Reducing the size of the image until either the height or
    width reaches the minimum limit. In the ith iteration,
    the image is resized to scale^i of the original image.

    This function is mostly completed for you -- only a termination
    condition is needed.

    Args:
        image: np array of (h,w), an image to scale.
        scale: float of how much to rescale the image each time.
        minSize: pair of ints showing the minimum height and width.

    Returns:
        images: a list containing pair of
            (the current scale of the image, resized image).
    """
    images = []

    # Yield the original image
    current_scale = 1.0
    images.append((current_scale, image))

    while True:
        # Use "break" to exit this loop if the next image will be smaller than
        # the supplied minimium size
        ### YOUR CODE HERE
        if image.shape[0] * scale < minSize[0] or image.shape[1] * scale < minSize[1]:
            break
        ### END YOUR CODE

        # Compute the new dimensions of the image and resize it
        current_scale *= scale
        image = rescale(image, scale)

        # Yield the next image in the pyramid
        images.append((current_scale, image))

    return images


def pyramid_score(image, base_score, shape, stepSize=20,
                  scale=0.9, pixel_per_cell=8):
    """
    Calculate the maximum score found in the image pyramid using sliding window.

    Args:
        image: np array of (h,w).
        base_score: the hog representation of the object you want to detect.
        shape: shape of window you want to use for the sliding_window.

    Returns:
        max_score: float of the highest hog score.
        maxr: int of row where the max_score is found.
        maxc: int of column where the max_score is found.
        max_scale: float of scale when the max_score is found.
        max_response_map: np array of the response map when max_score is found.
    """
    max_score = 0
    maxr = 0
    maxc = 0
    max_scale = 1.0
    max_response_map = np.zeros(image.shape)
    images = pyramid(image, scale)
    ### YOUR CODE HERE
    for i in images:
        ms, mr, mc, mrm = sliding_window(i[1], base_score, stepSize, shape, pixel_per_cell)
        if ms > max_score:
            max_score = ms
            maxr = mr
            maxc = mc
            max_scale = i[0]
            max_response_map = mrm
    ### END YOUR CODE
    return max_score, maxr, maxc, max_scale, max_response_map

def plot_part3_1(images):
    """plot image pyramid."""
    sum_r = 0
    sum_c = 0
    for i, result in enumerate(images):
        (scale, image) = result
        if i == 0:
            sum_c = image.shape[1]
        sum_r += image.shape[0]

    composite_image = np.zeros((sum_r, sum_c))

    pointer = 0
    for i, result in enumerate(images):
        (scale, image) = result
        composite_image[pointer:pointer +
                        image.shape[0], :image.shape[1]] = image
        pointer += image.shape[0]

    plt.imshow(composite_image)
    plt.axis('off')
    plt.title('image pyramid')
    plt.show()

def plot_part3_2(image, max_scale, winW, winH, maxc, maxr, max_response_map):
    """plot window with highest hog score and heatmap."""
    fig, ax = plt.subplots(1)
    ax.imshow(rescale(image, max_scale))
    rect = patches.Rectangle((maxc, maxr),
                             winW,
                             winH,
                             linewidth=1,
                             edgecolor='r',
                             facecolor='none')
    ax.add_patch(rect)
    plt.show()

    plt.imshow(max_response_map, cmap='viridis', interpolation='nearest')
    plt.axis('off')
    plt.show()
