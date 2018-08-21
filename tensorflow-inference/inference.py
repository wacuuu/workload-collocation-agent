#!/bin/python3.6
import argparse
import itertools
from typing import List

import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications.resnet50 import preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image


def prepare_image(loaded_image):
    return preprocess_input(np.expand_dims(image.img_to_array(loaded_image), axis=0))


def load_images(base_path: str) -> List[np.ndarray]:
    image_paths = [os.path.join(base_path, image_path) for image_path in os.listdir(base_path)]
    images = [image.load_img(image_path, target_size=(224, 224, 3)) for image_path in image_paths]
    image_arrays = [prepare_image(loaded_image) for loaded_image in images]
    return image_arrays


def prepare_argument_parser():
    parser = argparse.ArgumentParser(
        description="Script that runs inference/prediction using pre-trained resnet50, on images "
                    "from the fruit photos dataset."
    )
    parser.add_argument(
        '--dataset_path',
        help='Path to folder that contains images from the dataset',
        dest='dataset_path',
        default="./",
        type=str
    )
    return parser


def main():
    arg_parser = prepare_argument_parser()
    args = arg_parser.parse_args()

    resnet_model = tf.keras.applications.ResNet50(
        weights='imagenet',
    )
    image_folder_path = os.path.join(args.dataset_path, "fruits-360/test-multiple_fruits")
    images = load_images(image_folder_path)

    images_processed = 0
    for dataset_image in itertools.cycle(images):
        predictions = resnet_model.predict(dataset_image)
        images_processed += 1
        print('images_processed={0}'.format(images_processed), flush=True)
        print('Predicted:', decode_predictions(predictions, top=3)[0], flush=True)


if __name__ == '__main__':
    main()
