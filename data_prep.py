import data_utils

class_dict = {"empty": 0, "half": 1, "full": 2}

input_csv_path = 'dataset/aggregated_annotations.csv'
image_directory = 'dataset/image/'
output_directory = 'dataset/annotations/'
train_val_directory = 'dataset/trainval_dataset/'

if __name__ == "__main__":
    data_utils.csv_to_annotation(input_csv_path, 
                            image_directory, 
                            output_directory, 
                            class_dict)

    data_utils.restructure(image_directory, 
                    train_val_directory, 
                    output_directory, 
                    train_ratio=0.8, 
                    random_seed=42)





