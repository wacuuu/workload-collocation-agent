##################################################################################
This software is pre-production and should not be deployed to production servers.
##################################################################################

Tensorflow training workload
============================

Runs training of a neural net with the resnet50 architecture. Exposes a metric of the total number
of images processed during the training from the start of the workload.
Used dataset comes from https://www.kaggle.com/paultimothymooney/blood-cells/


Building docker image
---------------------

All commands and scripts should be run from the top directory of the repository. File `kaggle.json` needs to be available in this directory too (it is necessary to download image dataset from Kaggle). To obtain the file you will need to create an account at Kaggle and download API credentials as described in `documentation`_.

.. _documentation: https://github.com/Kaggle/kaggle-api#api-credentials
