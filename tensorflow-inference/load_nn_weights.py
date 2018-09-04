import tensorflow as tf


def main():
    # Creating this model will download resnet50 weights
    resnet_model = tf.keras.applications.ResNet50(
        weights='imagenet',
    )


if __name__ == '__main__':
    main()
