import cv2
import time
import os
from ultralytics import YOLO

# Model management
model = None
model_path = 'model/red_ball.pt'

# Frame resolution
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Folder paths
IMAGE_FOLDER = 'img'
VIDEO_FOLDER = 'video'
RESULT_FOLDER = 'result'

# Detection parameters
CONFIDENCE_THRESHOLD = 0.5

def create_result_folder():
    """Create result folder if it doesn't exist"""
    if not os.path.exists(RESULT_FOLDER):
        os.makedirs(RESULT_FOLDER)
        print(f"Created result folder: {RESULT_FOLDER}")
    else:
        print(f"Result folder already exists: {RESULT_FOLDER}")

def load_model():
    """Load red_ball.pt model"""
    global model
    
    try:
        if not os.path.exists(model_path):
            print(f"Model file not found: {model_path}")
            return False
        
        # Load the model
        model = YOLO(model_path)
        
        print(f"Model 'red_ball.pt' loaded successfully")
        return True
        
    except Exception as e:
        print(f"Error loading model 'red_ball.pt': {e}")
        return False

def process_detection(frame):
    """
    Process detection on a single frame with multi-object labeling
    Returns the frame with detection results drawn on it
    """
    if model is None:
        print("No model loaded!")
        return frame
    
    height, width = frame.shape[:2]
    center_x, center_y = width // 2, height // 2
    
    # Draw coordinate system
    cv2.line(frame, (center_x - 20, center_y), (center_x + 20, center_y), (0, 255, 0), 2)
    cv2.line(frame, (center_x, center_y - 15), (center_x, center_y + 15), (0, 255, 0), 2)
    
    # Draw coordinate info
    cv2.putText(frame, "X: -15 to +15", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(frame, "Y: -10 to +10", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # Model status
    cv2.putText(frame, "MODEL: red_ball.pt", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    try:
        # Run detection
        results = model(frame, verbose=False)
        
        # Collect all valid detections
        valid_detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = box.conf[0].cpu().numpy()
                    
                    if confidence > CONFIDENCE_THRESHOLD:
                        # Calculate object center
                        obj_center_x = int((x1 + x2) / 2)
                        obj_center_y = int((y1 + y2) / 2)
                        
                        # Calculate area for sorting (larger objects get priority)
                        area = (x2 - x1) * (y2 - y1)
                        
                        valid_detections.append({
                            'bbox': (int(x1), int(y1), int(x2), int(y2)),
                            'center': (obj_center_x, obj_center_y),
                            'confidence': confidence,
                            'area': area
                        })
        
        # Sort detections by area (largest first) to assign priority
        valid_detections.sort(key=lambda x: x['area'], reverse=True)
        
        if valid_detections:
            # Draw all detections with labels
            for i, detection in enumerate(valid_detections):
                bbox = detection['bbox']
                center = detection['center']
                confidence = detection['confidence']
                
                # Color coding: Object 1 (priority) in green, others in yellow
                color = (0, 255, 0) if i == 0 else (0, 255, 255)
                
                # Draw bounding box
                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
                
                # Draw center point
                cv2.circle(frame, center, 5, (0, 0, 255), -1)
                
                # Draw line to frame center (only for priority object)
                if i == 0:
                    cv2.line(frame, (center_x, center_y), center, (255, 0, 0), 2)
                
                # Draw label with number
                label = f"#{i+1} Conf: {confidence:.2f}"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                cv2.rectangle(frame, (bbox[0], bbox[1] - label_size[1] - 10), 
                             (bbox[0] + label_size[0], bbox[1]), color, -1)
                cv2.putText(frame, label, (bbox[0], bbox[1] - 5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            
            print(f"Detected {len(valid_detections)} red ball(s)")
        else:
            print("No red balls detected")
                    
    except Exception as e:
        print(f"Detection error: {e}")
    
    return frame

def process_image(image_path):
    """Process a single image file"""
    print(f"\n{'='*60}")
    print(f"Processing image: {image_path}")
    print(f"{'='*60}")
    
    if not os.path.exists(image_path):
        print(f"Error: Image file not found: {image_path}")
        return False
    
    # Read image
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"Error: Failed to read image: {image_path}")
        return False
    
    print(f"Image loaded: {frame.shape[1]}x{frame.shape[0]}")
    
    # Process detection
    result_frame = process_detection(frame)
    
    # Save result
    filename = os.path.basename(image_path)
    name, ext = os.path.splitext(filename)
    result_filename = f"{name}_result{ext}"
    result_path = os.path.join(RESULT_FOLDER, result_filename)
    
    cv2.imwrite(result_path, result_frame)
    print(f"Result saved to: {result_path}")
    print(f"{'='*60}\n")
    
    return True

def process_video(video_path):
    """Process a video file"""
    print(f"\n{'='*60}")
    print(f"Processing video: {video_path}")
    print(f"{'='*60}")
    
    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        return False
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Failed to open video: {video_path}")
        return False
    
    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"Video properties: {width}x{height} @ {fps} FPS")
    print(f"Total frames: {total_frames}")
    
    # Prepare output video
    filename = os.path.basename(video_path)
    name, ext = os.path.splitext(filename)
    result_filename = f"{name}_result{ext}"
    result_path = os.path.join(RESULT_FOLDER, result_filename)
    
    # Define codec and create VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(result_path, fourcc, fps, (width, height))
    
    if not out.isOpened():
        print(f"Error: Failed to create output video: {result_path}")
        cap.release()
        return False
    
    # Process video frame by frame
    frame_count = 0
    start_time = time.time()
    
    print("Processing frames...")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Process detection
        result_frame = process_detection(frame)
        
        # Write frame to output video
        out.write(result_frame)
        
        # Print progress
        if frame_count % 30 == 0 or frame_count == total_frames:
            elapsed_time = time.time() - start_time
            progress = (frame_count / total_frames) * 100
            fps_current = frame_count / elapsed_time if elapsed_time > 0 else 0
            print(f"Progress: {frame_count}/{total_frames} ({progress:.1f}%) - {fps_current:.1f} FPS")
    
    # Release resources
    cap.release()
    out.release()
    
    elapsed_time = time.time() - start_time
    print(f"\nVideo processing completed in {elapsed_time:.2f} seconds")
    print(f"Average FPS: {frame_count / elapsed_time:.2f}")
    print(f"Result saved to: {result_path}")
    print(f"{'='*60}\n")
    
    return True

def main():
    """Main function"""
    print("="*60)
    print("Red Ball Detection System")
    print("="*60)
    
    # Create result folder
    create_result_folder()
    
    # Load red_ball.pt model
    print("\nLoading red_ball.pt model...")
    if not load_model():
        print("Error: Failed to load red_ball.pt model. Exiting...")
        return
    
    # Process image
    image_path = os.path.join(IMAGE_FOLDER, 'tes.png')
    if os.path.exists(image_path):
        process_image(image_path)
    else:
        print(f"Image not found: {image_path}")
    
    # Process video
    video_path = os.path.join(VIDEO_FOLDER, 'tes.mp4')
    if os.path.exists(video_path):
        process_video(video_path)
    else:
        print(f"Video not found: {video_path}")
    
    print("="*60)
    print("Processing completed!")
    print("="*60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")