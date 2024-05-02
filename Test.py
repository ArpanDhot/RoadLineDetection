import cv2
import numpy as np
import time

# Constants
FRAME_RATE = 60  # Frame rate of the video, adjust according to your video
DISTANCE_BETWEEN_STRIPS = 0.5  # Distance between strips in meters, adjust as needed


def canny(image):
    """Applies Canny edge detection to an image."""
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)
    return edges


def get_roi_and_detection_line_y(frame):
    """Applies an ROI mask to the frame and returns the y-coordinate for the detection line."""
    height, width = frame.shape[:2]
    # Define the ROI; adjust these points based on your actual ROI
    top_left = (450, height)
    top_right = (700, int(height * 0.79))
    bottom_right = (700, int(height * 0.73))
    bottom_left = (25, height)

    polygons = np.array([
        [bottom_left, bottom_right, top_right, top_left]
    ])
    mask = np.zeros_like(frame)
    cv2.fillPoly(mask, polygons, 255)
    masked_image = cv2.bitwise_and(frame, mask)

    # Calculate the middle y-coordinate of the ROI for the detection line
    top_y = int(height * 0.7)
    bottom_y = height
    detection_line_y = (top_y + bottom_y) // 2

    return masked_image, detection_line_y, top_left[0], bottom_right[0]


def detect_crossing(edges, line_y):
    """Checks if there are any edges crossing the detection line."""
    crossings = np.any(edges[line_y, :] > 0)
    return crossings


def calculate_speed(distance, time_seconds):
    """Calculates speed given distance and time."""
    if time_seconds > 0:
        speed = distance / time_seconds
        return speed * 3.6  # Convert from m/s to km/h
    return 0


def overlay_edges_on_image(original_image, edge_image):
    """Creates a color overlay of the detected edges on the original image."""
    edge_colored = cv2.cvtColor(edge_image, cv2.COLOR_GRAY2BGR)
    edge_colored[edge_image == 255] = [0, 0, 255]  # Edge pixels marked in red
    overlay_image = cv2.addWeighted(original_image, 0.8, edge_colored, 0.2, 0)
    return overlay_image


def process_video(video_path):
    cap = cv2.VideoCapture(video_path)
    last_crossing_time = None

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        edges = canny(frame)
        roi_edges, detection_line_y, roi_start_x, roi_end_x = get_roi_and_detection_line_y(edges)

        if detect_crossing(roi_edges, detection_line_y):
            current_time = time.time()
            if last_crossing_time is not None:
                time_interval = current_time - last_crossing_time
                speed = calculate_speed(DISTANCE_BETWEEN_STRIPS, time_interval)
                print(f"Speed: {speed:.2f} km/h")
            last_crossing_time = current_time

        # Overlay edges on the original image
        overlay_image = overlay_edges_on_image(frame, roi_edges)

        # Draw the detection line across the width of the ROI
        cv2.line(overlay_image, (roi_start_x, detection_line_y), (roi_end_x, detection_line_y), (0, 255, 0), 2)
        cv2.imshow('Edges with Detection Line', overlay_image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


# Example usage
process_video('test_video.mp4')  # Replace with the path to your video
