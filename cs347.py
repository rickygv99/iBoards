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
            image_feature, image_hog = get_hog(pad_image[i * stepSize : i * stepSize + winH, j * stepSize : j * stepSize + winW])
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
    images = []
    current_scale = 1.0
    images.append((current_scale, image))
    while True:
        if image.shape[0] * scale < minSize[0] or image.shape[1] * scale < minSize[1]:
            break
        current_scale *= scale
        image = rescale(image, scale)
        images.append((current_scale, image))
    return images

def pyramid_score(image, base_score, shape, stepSize=20, scale=0.9):
    max_score = 0
    maxr = 0
    maxc = 0
    max_scale = 1.0
    max_response_map = np.zeros(image.shape)
    images = pyramid(image, scale)
    for i in images:
        ms, mr, mc, mrm = sliding_window(i[1], base_score, stepSize, shape)
        if ms > max_score:
            max_score = ms
            maxr = mr
            maxc = mc
            max_scale = i[0]
            max_response_map = mrm
    return max_score, maxr, maxc, max_scale, max_response_map

def plot_prediction_pyramid(image, max_scale, winW, winH, maxc, maxr):
    fig, ax = plt.subplots(1)
    ax.imshow(rescale(image, max_scale))
    rect = patches.Rectangle((maxc, maxr), winW, winH, linewidth=1, edgecolor='r', facecolor='none')
    ax.add_patch(rect)
    plt.show()
