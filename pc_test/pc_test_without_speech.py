import cv2
import torch
import os

# Paths (change these paths as per your system)
exp = "exp_500"
root_path =  "/Users/richtsai1103/liquid_level_drone"
weights_path = os.path.join(root_path, f"yolov5/runs/train/{exp}/weights/best_small.pt")
model_path = os.path.join(root_path, "yolov5/")

# Setup YOLOv5 with custom model weights
model = torch.hub.load(model_path, 'custom', path=weights_path, source='local')

# Start video capture from the default computer's camera
cap = cv2.VideoCapture(0)

while True:
    # Get the current frame from the video capture
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    frame = cv2.flip(frame, 1)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    model.conf = 0.25  # Set confidence threshold
    
    # Crop the image to make it more focued on smaller portion of the frame
    height, width, channel = frame.shape
    crop_x1 = width // 8  # Adjust the cropping region as needed
    crop_x2 = 7 * width // 8
    crop_y1 = height // 8
    crop_y2 = 7 * height // 8
    cropped_image = frame[crop_y1:crop_y2, crop_x1:crop_x2]

    results = model(cropped_image)


    # Convert results to rendered frame and display
    rendered_frame = results.render()[0]
    rendered_frame = cv2.resize(rendered_frame, (1280, 720)) 
    rendered_frame = cv2.cvtColor(rendered_frame, cv2.COLOR_BGR2RGB)
    cv2.imshow('YOLOv5', rendered_frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
