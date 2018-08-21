#!/bin/python3.6
import argparse
import os
import sys
import time
from enum import Enum
from math import floor

import tensorflow as tf


class CellType(Enum):
    """
    Holds integer labels for different blood cell types
    and respective folder names in dataset files
    """
    EOSINOPHIL = {"filename": "EOSINOPHIL", "label": 0}
    LYMPHOCYTE = {"filename": "LYMPHOCYTE", "label": 1}
    MONOCYTE = {"filename": "MONOCYTE", "label": 2}
    NEUTROPHIL = {"filename": "NEUTROPHIL", "label": 3}


def load_image_and_label(filename, label):
    """
    Loads jpeg image file and deccodes it.
    :param filename: Path to image file
    :param label: Image label (needed in dataset.map function)
    :return: tf.image object and its label
    """
    image_string = tf.read_file(filename)
    image_decoded = tf.image.decode_jpeg(image_string, channels=3)
    image_resized = tf.image.resize_images(image_decoded, [320, 240])
    return image_resized, label


def read_image_paths_and_labels(base_path):
    """
    Creates list of image paths and labels, latter based on dataset folder structure
    :param base_path: path dataset images folder
    :return: list of image paths and list of labels
    """
    paths = []
    labels = []
    for cell_type in CellType:
        folder_path = os.path.join(base_path, cell_type.value["filename"])
        image_names = os.listdir(folder_path)
        paths += [os.path.join(folder_path, image_name) for image_name in image_names]
        labels += [cell_type.value["label"]] * len(image_names)
    return paths, labels


def prepare_dataset(base_path, batch_size):
    """
    Loads dataset images and labels into tf.data.Dataset object
    :param base_path: path to dataset images folder
    :return: tf.data.Datset object
    """
    paths, labels = read_image_paths_and_labels(base_path)
    number_of_samples = len(labels)
    paths = tf.constant(paths)
    # Because we are using categorical_crossentropy as loss function
    # labels list is transformed to categorical format (1 dimension for each class for each sample)
    labels = tf.constant(tf.keras.utils.to_categorical(labels, 4))
    dataset = tf.data.Dataset.from_tensor_slices((paths, labels))
    dataset = dataset.map(load_image_and_label)
    dataset = dataset.repeat().batch(batch_size)
    return dataset, number_of_samples


def prepare_argument_parser():
    parser = argparse.ArgumentParser(
        description="Script that runs training of resnet50 on blood-cells dataset"
    )
    parser.add_argument(
        '--epochs',
        help='Number of epochs of learning to be performed',
        dest='epochs',
        default=100,
        type=int
    )
    parser.add_argument(
        '--batch_size',
        help='Size of batch in neural net learning process. Number of images processed in each step',
        dest='batch_size',
        default=1,
        type=int
    )
    parser.add_argument(
        '--dataset_path',
        help='Path to folder that containst dataset2-master folder with the dataset files',
        dest='dataset_path',
        default="./",
        type=str
    )
    return parser


class ImagesProcessed(tf.keras.callbacks.Callback):
    """
    Exposes number of images processed during training (total number of images processed from
    the start) by printing to stdout after the end of each batch of training
    """

    def __init__(self, batch_size: int):
        super().__init__()
        self.images_processed = 0
        self.batch_size = batch_size

    def on_batch_end(self, batch, logs=None):
        self.images_processed += self.batch_size
        print("images_processed={0}".format(self.images_processed), flush=True)


def main():
    arg_parser = prepare_argument_parser()
    args = arg_parser.parse_args()
    dataset_path = os.path.join(args.dataset_path, "dataset2-master/images/TRAIN")
    train_dataset, number_of_samples = prepare_dataset(dataset_path, batch_size=args.batch_size)
    # Calculate nr of steps per epoch to use whole dataset during an epoch of training
    steps_per_epoch = floor(number_of_samples / args.batch_size)
    # Load predefined resnet50 neural net
    resnet_model = tf.keras.applications.ResNet50(
        weights=None,
        include_top=True,
        input_shape=(320, 240, 3),
        classes=4
    )
    resnet_model.compile(optimizer=tf.train.AdamOptimizer(0.001),
                         loss='categorical_crossentropy',
                         metrics=['accuracy'],
                         )
    resnet_model.fit(train_dataset, steps_per_epoch=steps_per_epoch, epochs=args.epochs,
                     shuffle=True, callbacks=[ImagesProcessed(args.batch_size)], verbose=0
                     )


if __name__ == '__main__':
    main()
