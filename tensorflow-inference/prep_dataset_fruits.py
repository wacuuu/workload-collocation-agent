#!/bin/python3.6
import os.path
import kaggle

'''
Downloads Moltean's fruits dataset using kaggle module (install with 'pip install -r requirements.txt')
if dataset zip file is not found.
'''

dataset = 'moltean/fruits'
dataset_dir = 'tensorflow-inference/fruits-360'
if os.path.isdir(dataset_dir):
    print("Found dataset directory, exiting")
    exit(0)
print("Dataset not found, using kaggle-api tool for download")
kaggle.api.dataset_download_files(dataset, path="./tensorflow-inference/", unzip=True)
