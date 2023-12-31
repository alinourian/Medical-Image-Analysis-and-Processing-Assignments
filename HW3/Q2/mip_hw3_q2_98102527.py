# -*- coding: utf-8 -*-
"""MIP_HW3_Q2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1tXr9S0mK5tPK_HYtBXi8KdUWFC_Xm8X9

## Import Libraries
"""

import numpy as np
import cv2
import matplotlib.pyplot as plt
from sklearn.feature_extraction.image import extract_patches_2d, reconstruct_from_patches_2d
from sklearn.decomposition import MiniBatchDictionaryLearning
np.random.seed(0)

"""## Helping Functions"""

def calcPSNR(image, source):
    L = np.max(image)
    R = L ** 2 / (1 / (image.shape[0] * image.shape[1]) * np.sum((image - source) ** 2))
    return float(10 * np.log10(R))

def load_image(path):
    img = cv2.imread(path)
    img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    if np.max(img_gray) > 1:
        img_gray = img_gray / 255
    return img_gray

def add_gaussian_noise(image, std):
    noise = np.random.normal(scale=std, size=image.shape)
    noisy_img = image + noise
    noisy_img[noisy_img < 0] = 0
    noisy_img[noisy_img > 1] = 1
    return noisy_img, noise

def show_with_diff(image, noisy_image, noise_denoised, isnoise=False):
    plt.figure(figsize=(10, 8))
    plt.subplot(1, 3, 1)
    plt.imshow(image, cmap='gray', vmin=0, vmax=1, interpolation="nearest")
    plt.subplot(1, 3, 2)
    plt.imshow(noisy_image, cmap='gray', vmin=0, vmax=1, interpolation="nearest")
    plt.title('PSNR = ' + str(round(calcPSNR(noisy_image, image), 4)))
    plt.subplot(1, 3, 3)
    if isnoise:
        plt.imshow(noise_denoised, cmap=plt.cm.PuOr, vmin=-0.5, vmax=0.5, interpolation="nearest")
    else:
        plt.imshow(noise_denoised, cmap='gray', vmin=0, vmax=1, interpolation="nearest")
        plt.title('PSNR = ' + str(round(calcPSNR(noise_denoised, image), 4)))
    plt.show()

def extract_patches(image, patch_size):
    dataset = extract_patches_2d(image, patch_size)
    dataset = dataset.reshape(-1, patch_size[0] * patch_size[1])
    dataset -= np.mean(dataset, axis=0)
    dataset /= np.std(dataset, axis=0)
    return dataset

"""## Load Image and Add Gassian Noise"""

image = load_image('mandrill.jpg')
width, height = image.shape
image = cv2.resize(image, (int(width / 2), int(height / 2)), interpolation = cv2.INTER_AREA)
width, height = image.shape

sigma = 0.1
noisy_image, noise = add_gaussian_noise(image, sigma)

show_with_diff(image, noisy_image, noise, True)

"""## Extract Patches & Train Dictionary"""

patch_size = (8, 8)
patches_data = extract_patches(noisy_image, patch_size=patch_size)
print(patches_data.shape)

dico = MiniBatchDictionaryLearning(
    n_components=200,
    batch_size=200,
    alpha=1.0,
    max_iter=10,
    verbose=True
)
comps = dico.fit(patches_data).components_

print(f'Component\'s Shape{comps.shape}')
plt.figure(figsize=(8, 6))
for i, comp in enumerate(comps[:100]):
    plt.subplot(10, 10, i + 1)
    plt.imshow(comp.reshape(patch_size), cmap=plt.cm.gray_r, interpolation="nearest")
    plt.xticks(())
    plt.yticks(())

"""## OPM and LARS Algorithms"""

from time import time

transform_algorithms = [
    ("Orthogonal Matching Pursuit\n2 atoms", "omp", {"transform_n_nonzero_coefs": 2}),
    ("Least-angle regression\n2 atoms", "lars", {"transform_n_nonzero_coefs": 2}),
]

data = extract_patches_2d(noisy_image, patch_size)
data = data.reshape(data.shape[0], -1)
intercept = np.mean(data, axis=0)
data -= intercept

reconstructions = {}
for title, transform_algorithm, kwargs in transform_algorithms:
    print(title + '...')
    t0 = time()
    reconstructions[title] = image.copy()

    dico.set_params(transform_algorithm=transform_algorithm, **kwargs)
    code = dico.transform(data)
    patches = np.dot(code, comps)

    patches += intercept
    patches = patches.reshape(len(data), *patch_size)

    reconstructions[title] = reconstruct_from_patches_2d(patches, (height, width))
    show_with_diff(image, noisy_image, reconstructions[title])
    print(f'time for this algorithm = {time() - t0} s')

plt.show()