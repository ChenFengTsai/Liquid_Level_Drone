import os
import subprocess
try:
    import google.cloud.storage
except ImportError:
    print("Installing google-cloud-storage...")
    subprocess.call(["pip", "install", "google-cloud-storage"])
import os
from google.cloud import storage
from datetime import datetime

def upload_directory_to_gcs(local_folder_path, bucket_name, destination_path):
    # Instantiates a client
    storage_client = storage.Client()

    # Get the bucket
    bucket = storage_client.get_bucket(bucket_name)
    new_folder_path = destination_path

    # Walk through the directory structure
    for root, _, files in os.walk(local_folder_path):
        for file in files:
            local_file_path = os.path.join(root, file)
            # Calculate the relative path to maintain the directory structure
            relative_path = os.path.relpath(local_file_path, local_folder_path)
            gcs_blob_path = os.path.join(new_folder_path, relative_path).replace("\\", "/")
            blob = bucket.blob(gcs_blob_path)
            blob.upload_from_filename(local_file_path)

    print(f"Files from {local_folder_path} moved to GCS bucket {bucket_name} in folder {new_folder_path}")

if __name__ == "__main__":
    # Provide workbench directory, bucket name, and destination path within the bucket
    local_folder_path = '/home/jupyter/liquid_level_drone/yolov5/runs/train'
    bucket_name = 'bottle_image'
    destination_path = 'model_outputs'

    upload_directory_to_gcs(local_folder_path, bucket_name, destination_path)