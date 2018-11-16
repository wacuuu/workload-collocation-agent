##################################################################################
This software is pre-production and should not be deployed to production servers.
##################################################################################

Tensorflow inference workload
=============================

Runs prediction on images using the resnet50 neural net with pre-trained weights.
Used dataset comes from https://www.kaggle.com/moltean/fruits

Building docker image
---------------------

All commands and scripts should be run from the top directory of the repository. File `kaggle.json` needs to be available in this directory too (it is necessary to download image dataset from Kaggle). To obtain the file you will need to create an account at Kaggle and download API credentials as described in `documentation`_.

.. _documentation: https://github.com/Kaggle/kaggle-api#api-credentials
