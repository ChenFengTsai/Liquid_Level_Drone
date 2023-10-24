import cv2

# Replace 'input_video.avi' with the path to your input AVI file
input_video_path = 'video_result/exp2-best/video_2023-10-24_02-40-16.avi'
cap = cv2.VideoCapture(input_video_path)

# Define the output MP4 file properties
output_video_path = 'video_result/exp2-best/video_2023-10-24_02-40-16.mp4'
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for MP4 format
fps = cap.get(cv2.CAP_PROP_FPS)  # Get the frame rate of the input video
frame_size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

# Create a video writer object for the MP4 file
out = cv2.VideoWriter(output_video_path, fourcc, fps, frame_size)

if not cap.isOpened():
    print("Error: Could not open the input video file.")
    exit()
    
while True:
    # Read a frame from the input video
    ret, frame = cap.read()

    # If the end of the video is reached, break the loop
    if not ret:
        break

    # Process the frame here (e.g., apply image processing)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # Write the processed frame to the output MP4 file
    for _ in range(10):
        out.write(frame)
    
# Release the video objects
cap.release()
out.release()

# Display a message indicating successful conversion
print("Video conversion from AVI to MP4 completed.")
