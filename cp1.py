import cv2
import numpy as np

def custom_grayscale(frame):
    return np.dot(frame[..., :3], [0.2989, 0.5870, 0.1140])

def canny_edge_detection(frame, low_threshold=50, high_threshold=150):
    gray = custom_grayscale(frame)
    edges = cv2.Canny(np.uint8(gray), low_threshold, high_threshold)
    frame_with_edges = frame.copy()
    frame_with_edges[edges == 255] = [0, 0, 255]
    return frame_with_edges, edges

def custom_clustering(centroids, epsilon=30):
    clusters = []
    for point in centroids:
        added = False
        for cluster in clusters:
            if np.linalg.norm(np.array(point) - np.array(cluster[0])) < epsilon:
                cluster.append(point)
                added = True
                break
        if not added:
            clusters.append([point])
    return clusters

def calculate_speeds(centroids_current, centroids_previous, fps):
    speeds = []
    for current in centroids_current:
        min_distance = float('inf')
        for previous in centroids_previous:
            distance = np.linalg.norm(np.array(current) - np.array(previous))
            if distance < min_distance:
                min_distance = distance
        speed = min_distance * fps
        speeds.append(speed)
    return speeds

def process_video(video_path):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    prev_frame = None
    prev_centroids = []
    fps = cap.get(cv2.CAP_PROP_FPS)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        edge_frame, edges = canny_edge_detection(frame)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        centroids = []
        for contour in contours:
            if cv2.contourArea(contour) > 100:
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    centroids.append((cX, cY))

        clusters = custom_clustering(centroids, epsilon=30)
        speeds = calculate_speeds([np.mean(cluster, axis=0) for cluster in clusters], 
                                  [np.mean(cluster, axis=0) for cluster in prev_centroids], 
                                  fps)

        for i, cluster in enumerate(clusters):
            cluster_center = np.mean(cluster, axis=0).astype(int)
            cv2.circle(frame, tuple(cluster_center), 5, (0, 0, 255), -1)
            cv2.putText(frame, f"ID {i} Speed: {speeds[i]:.2f} px/s", 
                        tuple(cluster_center - (0, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 
                        (255, 255, 255), 2)

            x, y, w, h = cv2.boundingRect(np.array(cluster))
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        for i, cluster in enumerate(clusters):
            cluster_center = np.mean(cluster, axis=0).astype(int)
            cv2.putText(edge_frame, f"ID {i} Speed: {speeds[i]:.2f} px/s", 
                        tuple(cluster_center - (0, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 
                        (255, 255, 255), 2)

        cv2.imshow("Edge Detection with Speed", edge_frame)
        cv2.imshow("Clustering and Speed", frame)

        prev_centroids = clusters

        if cv2.waitKey(30) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

video_path = "example_video.mp4"
process_video(video_path)
