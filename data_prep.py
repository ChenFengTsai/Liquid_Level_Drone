import data_utils


class_dict = {"empty": 0, "half": 1, "full": 2}

input_csv_path = 'dataset/aggregated_annotations.csv'
image_directory = 'dataset/image/'
output_directory = 'dataset/annotations/'
train_val_directory = 'dataset/trainval_dataset/'

# gcp storage
gcs_bucket_path = "bottle_image"
source_folder_name = "new_images"
target_folder = "/home/jupyter/liquid_level_drone/dataset/image"
gcp_storage_option = False

if __name__ == "__main__":
    
    # get data from gcp storage if needed
    if gcp_storage_option:
        data_utils.download_images_to_folder(gcs_bucket_path, source_folder_name, target_folder)
        
    data_utils.csv_to_annotation(input_csv_path, 
                            image_directory, 
                            output_directory, 
                            class_dict)

    data_utils.restructure(image_directory, 
                    train_val_directory, 
                    output_directory, 
                    train_ratio=0.8, 
                    random_seed=42)





