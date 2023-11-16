import cv2
import os

def convert_avi_to_mp4(input_video, output_video, experiment):
    # Open the input AVI file
    video_directory = os.path.join('video_result', experiment)
    input_path = os.path.join(video_directory, input_video)
    output_path = os.path.join(video_directory, output_video)
    cap = cv2.VideoCapture(input_path)

    # Check if the input video file was opened successfully
    if not cap.isOpened():
        print("Error: Could not open the input video file.")
        return

    # Define the output MP4 file properties
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for MP4 format
    fps = cap.get(cv2.CAP_PROP_FPS)  # Get the frame rate of the input video
    frame_size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

    # Create a video writer object for the MP4 file
    out = cv2.VideoWriter(output_path, fourcc, fps, frame_size)

    while True:
        # Read a frame from the input video
        ret, frame = cap.read()

        # If the end of the video is reached, break the loop
        if not ret:
            break

        # Process the frame here (e.g., apply image processing)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Write the processed frame to the output MP4 file (in this case, it repeats each frame 10 times)
        for _ in range(7):
            out.write(frame)

    # Release the video objects
    cap.release()
    out.release()

    # Display a message indicating successful conversion
    print("Video conversion from AVI to MP4 completed.")

if __name__ == "__main__":
# Usage example:

    experiment = 'exp_500'
    input_video = 'video_2023-11-02_14-27-52.avi'
    output_video = 'video_2023-11-02_14-27-52.mp4'

    convert_avi_to_mp4(input_video, output_video, experiment)
