import cv2
import torch
import os

# Paths (change these paths as per your system)
exp = "exp2-best"
root_path =  "/Users/richtsai1103/liquid_level_drone"
weights_path = os.path.join(root_path, f"yolov5/runs/train/{exp}/weights/best.pt")
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

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Pass the frame to YOLOv5 for object detection with confidence threshold set to 0.25
    #   results = model(frame_rgb, conf=0.25)  # Set confidence threshold here
    model.conf = 0.10  # Set confidence threshold
    results = model(frame_rgb)


    # Convert results to rendered frame and display
    rendered_frame = results.render()[0]
    cv2.imshow('YOLOv5', rendered_frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
