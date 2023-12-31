import csv
import os
from PIL import Image
import shutil
import random
from google.cloud import storage

def custom_eval(s):
    try:
        return eval(s.replace('undefined', 'None'))
    except:
        return None

def csv_to_annotation(input_csv_path, image_directory, output_directory, class_dict):
    """
    Convert annotations from a CSV file to YOLO format and save them as .txt files.

    Args:
        input_csv_path (str): Path to the input CSV file containing annotations.
        image_directory (str): Path to the directory containing the images.
        output_directory (str): Path to the directory where YOLO-format annotations will be saved.
        class_dict (dict): A dictionary mapping class names to class IDs.
    """
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    with open(input_csv_path, 'r') as csv_file:
        reader = csv.reader(csv_file)
        next(reader)  # Skip the header
        
        missing_img = []
        for row in reader:
            filename = row[0]
            region_shape_attributes = custom_eval(row[5])
            region_attributes = custom_eval(row[6])

            # Skip rows without the necessary attributes
            if not region_shape_attributes or not region_attributes:
                continue

            if region_attributes['name'] in class_dict:
                class_id = class_dict[region_attributes['name']]
            else:
                continue

            # Open the image to get its size

            try:
                img_path = os.path.join(image_directory, filename)
                with Image.open(img_path) as img:
                    width, height = img.size


                # Extract bounding box
                x = region_shape_attributes["x"]
                y = region_shape_attributes["y"]
                w = region_shape_attributes["width"]
                h = region_shape_attributes["height"]

                # Convert to YOLO format
                x_center = (x + w / 2) / width
                y_center = (y + h / 2) / height
                w_norm = w / width
                h_norm = h / height

                # Save to output .txt file
                output_filename = os.path.splitext(filename)[0] + '.txt'
                with open(os.path.join(output_directory, output_filename), 'a') as out_file:
                    out_file.write(f"{class_id} {x_center} {y_center} {w_norm} {h_norm}\n")
                    
            except FileNotFoundError as e:
                missing_img.append(filename)
                print(f"File not found: {str(e)}")
            
            # remove those missing images from annotations
        print("Missing images:", missing_img)
        for i in missing_img:
            os.remove(os.path.join(image_directory, i))
            


def restructure(image_directory, train_val_dir, output_directory, train_ratio=0.8, random_seed=42):
    """
    Organize a dataset into training and validation sets with corresponding annotations.

    Args:
        input_csv_path (str): Path to the input CSV file containing annotations.
        image_directory (str): Path to the directory containing the images.
        train_val_dir (str): Root directory where the organized dataset will be created.
        output_directory (str): Path to the directory containing YOLO-format annotations.
        train_ratio (float): Ratio of data to use for training (default is 0.8, meaning 80% for training).
        random_seed (int): Random seed for data shuffling (default is 42).
    """
    # Create the required directories if they don't exist
    os.makedirs(os.path.join(train_val_dir, 'images/train/'), exist_ok=True)
    os.makedirs(os.path.join(train_val_dir, 'images/val/'), exist_ok=True)
    os.makedirs(os.path.join(train_val_dir, 'labels/train/'), exist_ok=True)
    os.makedirs(os.path.join(train_val_dir, 'labels/val/'), exist_ok=True)

    # Move the images and labels to the right directories
    # Assuming all images are for training, adjust accordingly if you have validation data
    
    # Data Shuffling
    data_count = len(os.listdir(image_directory))
    random.seed(random_seed)
    train_idx = random.sample(range(0, data_count + 1), int(data_count * train_ratio))

    start = 0
    files = os.listdir(image_directory)
    for filename in files:
        file_name, extension_name = os.path.splitext(filename)
        try:
            if start in train_idx:
                shutil.move(os.path.join(image_directory, file_name + extension_name), os.path.join(train_val_dir, 'images/train/', file_name + '.jpg'))
                shutil.move(os.path.join(output_directory, file_name + '.txt'), os.path.join(train_val_dir, 'labels/train/', file_name + '.txt'))
            else:
                shutil.move(os.path.join(image_directory, file_name + extension_name), os.path.join(train_val_dir, 'images/val/', file_name + '.jpg'))
                shutil.move(os.path.join(output_directory, file_name + '.txt'), os.path.join(train_val_dir, 'labels/val/', file_name + '.txt'))
            start += 1
        except Exception as e:
            print(f"Error occurred: {str(e)}")
        

    print("Directory structure adjusted!")

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
