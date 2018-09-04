#!/bin/python3.6
import os.path
import kaggle

'''
Downloads blood-cells dataset using kaggle module (install with 'pip install -r requirements.txt')
if dataset zip file is not found.
'''

dataset = 'paultimothymooney/blood-cells'
dataset_file = 'tensorflow-train/dataset2-master.zip'
if os.path.isfile(dataset_file):
    print("Found dataset archive, exiting")
    exit(0)
print("Dataset not found, using kaggle-api tool for download")
kaggle.api.dataset_download_files(dataset, path="./tensorflow-train/", unzip=True)
