import os
import subprocess
# Check if google-cloud-storage is installed, and install it if not
try:
    import google.cloud.storage
except ImportError:
    print("Installing google-cloud-storage...")
    subprocess.call(["pip", "install", "google-cloud-storage"])

# import google
from google.cloud import storage

def download_images_to_folder(gcs_bucket_path, source_folder_name, target_folder):
    client = storage.Client()
    bucket = client.get_bucket(gcs_bucket_path)
    blobs = list(bucket.list_blobs(prefix=source_folder_name + "/"))
    image_blobs = [blob for blob in blobs if not blob.name.startswith("._")]

    # Check if the target folder exists; if not, create it
    os.makedirs(target_folder, exist_ok=True)

    for blob in image_blobs:
        image_data = blob.download_as_bytes()
        image_filename = os.path.join(target_folder, os.path.basename(blob.name))

        # Save the downloaded image to the target folder
        with open(image_filename, "wb") as image_file:
            image_file.write(image_data)
            
        print(f"Image '{blob.name}' downloaded and saved to '{target_folder}'")

if __name__ == "__main__":
    gcs_bucket_path = "bottle_image"
    source_folder_name = "new_images"
    target_folder = "/home/jupyter/liquid_level_drone/dataset/image"  # Keep consistent with the naming requirement

    download_images_to_folder(gcs_bucket_path, source_folder_name, target_folder)
