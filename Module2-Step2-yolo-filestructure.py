import os
import shutil
import random

# Define your paths
root_directory = os.getcwd()
input_csv_path = os.path.join(root_directory, 'aggregated_annotations.csv')
image_directory = os.path.join(root_directory, 'img_dataset/')
train_val_dir = os.path.join(root_directory, 'trainval_dataset/')
output_directory = os.path.join(root_directory, 'annotations/')

# Create the required directories if they don't exist
os.makedirs(os.path.join(train_val_dir, 'images/train/'), exist_ok=True)
os.makedirs(os.path.join(train_val_dir, 'images/val/'), exist_ok=True)
os.makedirs(os.path.join(train_val_dir, 'labels/train/'), exist_ok=True)
os.makedirs(os.path.join(train_val_dir, 'labels/val/'), exist_ok=True)

# Move the images and labels to the right directories
# Assuming all images are for training, adjust accordingly if you have validation data
## Data Shuffling
data_count = len(os.listdir(image_directory))
random.seed(42)
train_idx = random.sample(range(0, data_count + 1), int(data_count*0.8))

# for img
start = 0
files = os.listdir(image_directory)
for filename in files:
    filename = os.path.splitext(filename)[0]
    if start in train_idx:
        shutil.move(os.path.join(image_directory, filename+'.jpg'), os.path.join(train_val_dir, 'images/train/', filename+'.jpg'))
        shutil.move(os.path.join(output_directory, filename+'.txt'), os.path.join(train_val_dir, 'labels/train/', filename+'.txt'))
    else:
        shutil.move(os.path.join(image_directory, filename+'.jpg'), os.path.join(train_val_dir, 'images/val/', filename+'.jpg'))
        shutil.move(os.path.join(output_directory, filename+'.txt'), os.path.join(train_val_dir, 'labels/val/', filename+'.txt'))
    start += 1

print("Directory structure adjusted!")
