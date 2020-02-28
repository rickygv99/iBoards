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

def conv(image, kernel):
    """ An implementation of convolution filter.

    This function uses element-wise multiplication and np.sum()
    to efficiently compute weighted sum of neighborhood at each
    pixel.

    Args:
        image: numpy array of shape (Hi, Wi).
        kernel: numpy array of shape (Hk, Wk).

    Returns:
        out: numpy array of shape (Hi, Wi).
    """
    Hi, Wi = image.shape
    Hk, Wk = kernel.shape
    out = np.zeros((Hi, Wi))

    # For this assignment, we will use edge values to pad the images.
    # Zero padding will make derivatives at the image boundary very big,
    # whereas we want to ignore the edges at the boundary.
    pad_width0 = Hk // 2
    pad_width1 = Wk // 2
    pad_width = ((pad_width0,pad_width0),(pad_width1,pad_width1))
    padded = np.pad(image, pad_width, mode='edge')

    ### YOUR CODE HERE
    flipped_kernel = np.flip(np.flip(kernel, 0), 1)
    for m in range(Hi):
        for n in range(Wi):
            out[m][n] = np.sum(padded[m : m + Hk, n : n + Wk] * flipped_kernel)
    ### END YOUR CODE

    return out

def gaussian_kernel(size, sigma):
    """ Implementation of Gaussian Kernel.

    This function follows the gaussian kernel formula,
    and creates a kernel matrix.

    Hints:
    - Use np.pi and np.exp to compute pi and exp.

    Args:
        size: int of the size of output matrix.
        sigma: float of sigma to calculate kernel.

    Returns:
        kernel: numpy array of shape (size, size).
    """

    kernel = np.zeros((size, size))

    ### YOUR CODE HERE
    for i in range(size):
        for j in range(size):
            kernel[i][j] = np.exp(((i - (size - 1)/2)**2 + (j - (size - 1)/2)**2) / (-2 * sigma**2)) / (2 * np.pi * sigma**2)
    ### END YOUR CODE

    return kernel

def partial_x(img):
    """ Computes partial x-derivative of input img.

    Hints:
        - You may use the conv function in defined in this file.

    Args:
        img: numpy array of shape (H, W).
    Returns:
        out: x-derivative image.
    """

    out = None

    ### YOUR CODE HERE
    D_x = np.array([[1/2, 0, -1/2]])
    out = conv(img, D_x)
    ### END YOUR CODE

    return out

def partial_y(img):
    """ Computes partial y-derivative of input img.

    Hints:
        - You may use the conv function in defined in this file.

    Args:
        img: numpy array of shape (H, W).
    Returns:
        out: y-derivative image.
    """

    out = None

    ### YOUR CODE HERE
    D_y = np.array([[1/2], [0], [-1/2]])
    out = conv(img, D_y)
    ### END YOUR CODE

    return out

def gradient(img):
    """ Returns gradient magnitude and direction of input img.

    Args:
        img: Grayscale image. Numpy array of shape (H, W).

    Returns:
        G: Magnitude of gradient at each pixel in img.
            Numpy array of shape (H, W).
        theta: Direction(in degrees, 0 <= theta < 360) of gradient
            at each pixel in img. Numpy array of shape (H, W).

    Hints:
        - Use np.sqrt and np.arctan2 to calculate square root and arctan
    """
    G = np.zeros(img.shape)
    theta = np.zeros(img.shape)

    ### YOUR CODE HERE
    G_x = partial_x(img)
    G_y = partial_y(img)
    G = np.sqrt(G_x**2 + G_y**2)
    theta = np.degrees(np.arctan2(G_y, G_x))
    theta[theta < 0] += 360
    ### END YOUR CODE

    return G, theta

def non_maximum_suppression(G, theta):
    """ Performs non-maximum suppression.

    This function performs non-maximum suppression along the direction
    of gradient (theta) on the gradient magnitude image (G).

    Args:
        G: gradient magnitude image with shape of (H, W).
        theta: direction of gradients with shape of (H, W).

    Returns:
        out: non-maxima suppressed image.
    """
    H, W = G.shape
    out = np.zeros((H, W))

    # Round the gradient direction to the nearest 45 degrees
    theta = np.floor((theta + 22.5) / 45) * 45

    ### BEGIN YOUR CODE
    def getGradient(x, y, px, py):
        if x < 0 or x >= H or y < 0 or y >= W:
            return G[px][py]
        return G[x][y]

    for i in range(H):
        for j in range(W):
            forwardPixel = None
            backwardPixel = None
            if theta[i][j] % 180 == 0:
                forwardPixel = getGradient(i, j + 1, i, j)
                backwardPixel = getGradient(i, j - 1, i, j)
            elif theta[i][j] % 180 == 45:
                forwardPixel = getGradient(i + 1, j + 1, i, j)
                backwardPixel = getGradient(i - 1, j - 1, i, j)
            elif theta[i][j] % 180 == 90:
                forwardPixel = getGradient(i + 1, j, i, j)
                backwardPixel = getGradient(i - 1, j, i, j)
            elif theta[i][j] % 180 == 135:
                forwardPixel = getGradient(i + 1, j - 1, i, j)
                backwardPixel = getGradient(i - 1, j + 1, i, j)
            if max(forwardPixel, backwardPixel, G[i][j]) == G[i][j]:
                out[i][j] = G[i][j]
    ### END YOUR CODE

    return out

def harris_corners(img, window_size=3, k=0.04):
    """
    Compute Harris corner response map. Follow the math equation
    R=Det(M)-k(Trace(M)^2).

    Hint:
        You may use the function scipy.ndimage.filters.convolve,
        which is already imported above.

    Args:
        img: Grayscale image of shape (H, W)
        window_size: size of the window function
        k: sensitivity parameter

    Returns:
        response: Harris response image of shape (H, W)
    """

    H, W = img.shape
    window = np.ones((window_size, window_size))

    response = np.zeros((H, W))

    dx = filters.sobel_v(img)
    dy = filters.sobel_h(img)

    ### YOUR CODE HERE
    I_x2 = np.zeros((H, W))
    I_y2 = np.zeros((H, W))
    I_xy = np.zeros((H, W))
    for i in range(H):
        for j in range(W):
            I_x2[i][j] = dx[i][j] * dx[i][j]
            I_y2[i][j] = dy[i][j] * dy[i][j]
            I_xy[i][j] = dx[i][j] * dy[i][j]

    for i in range(H):
        for j in range(W):
            M = np.zeros((2, 2))
            for y in range(window_size):
                for x in range(window_size):
                    m = i + window_size // 2 - y
                    n = j + window_size // 2 - x
                    if m < 0 or n < 0 or m >= H or n >= W:
                        continue
                    M = M + np.array([[I_x2[m][n], I_xy[m][n]], [I_xy[m][n], I_y2[m][n]]])
            response[i][j] = np.linalg.det(M) - k * np.trace(M)**2
    ### END YOUR CODE

    return response

def hog_feature(image, pixel_per_cell=8):
    """
    Compute hog feature for a given image.

    Important: use the hog function provided by skimage to generate both the
    feature vector and the visualization image. **For block normalization, use L1.**

    Args:
        image: an image with object that we want to detect.
        pixel_per_cell: number of pixels in each cell, an argument for hog descriptor.

    Returns:
        score: a vector of hog representation.
        hogImage: an image representation of hog provided by skimage.
    """
    ### YOUR CODE HERE
    hogFeature, hogImage = feature.hog(image, pixels_per_cell=(pixel_per_cell, pixel_per_cell), block_norm='L1', visualize=True)
    ### END YOUR CODE
    return (hogFeature, hogImage)

def sliding_window(image, base_score, stepSize, windowSize, pixel_per_cell=8):
    """ A sliding window that checks each different location in the image,
        and finds which location has the highest hog score. The hog score is computed
        as the dot product between the hog feature of the sliding window and the hog feature
        of the template. It generates a response map where each location of the
        response map is a corresponding score. And you will need to resize the response map
        so that it has the same shape as the image.

    Hint: use the resize function provided by skimage.

    Args:
        image: an np array of size (h,w).
        base_score: hog representation of the object you want to find, an array of size (m,).
        stepSize: an int of the step size to move the window.
        windowSize: a pair of ints that is the height and width of the window.
    Returns:
        max_score: float of the highest hog score.
        maxr: int of row where the max_score is found (top-left of window).
        maxc: int of column where the max_score is found (top-left of window).
        response_map: an np array of size (h,w).
    """
    # slide a window across the image
    (max_score, maxr, maxc) = (0, 0, 0)
    winH, winW = windowSize
    H, W = image.shape
    pad_image = np.lib.pad(
        image,
        ((winH // 2,
          winH - winH // 2),
         (winW // 2,
          winW - winW // 2)),
        mode='constant')
    response_map = np.zeros((H // stepSize + 1, W // stepSize + 1))
    ### YOUR CODE HERE
    for i in range(H // stepSize + 1):
        for j in range(W // stepSize + 1):
            if i * stepSize >= H or j * stepSize >= W:
                continue
            image_feature, image_hog = hog_feature(pad_image[i * stepSize : i * stepSize + winH, j * stepSize : j * stepSize + winW], pixel_per_cell)
            response_map[i][j] = np.dot(image_feature, base_score)
            if response_map[i][j] > max_score:
                max_score = response_map[i][j]
                maxr = i * stepSize - winH // 2
                maxc = j * stepSize - winW // 2
    response_map = resize(response_map, image.shape, mode="constant")
    ### END YOUR CODE

    return (max_score, maxr, maxc, response_map)

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

def plot_part1(avg_face, face_hog):
    """plot average face and hog representatitons of face."""
    plt.subplot(1, 2, 1)
    plt.imshow(avg_face)
    plt.axis('off')
    plt.title('average face image')

    plt.subplot(1, 2, 2)
    plt.imshow(face_hog)
    plt.title('hog representation of face')
    plt.axis('off')

    plt.show()

def plot_part2(image, r, c, response_map, winW, winH):
    """plot window with highest hog score and heatmap."""
    fig, ax = plt.subplots(1)
    ax.imshow(image)
    rect = patches.Rectangle((c, r),
                             winW,
                             winH,
                             linewidth=1,
                             edgecolor='r',
                             facecolor='none')
    ax.add_patch(rect)
    plt.show()

    plt.imshow(response_map, cmap='viridis', interpolation='nearest')
    plt.title('sliding window')
    plt.show()

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