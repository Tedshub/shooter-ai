# Kode 2

import cv2
import numpy as np
from datetime import datetime
import pytz
from ultralytics import YOLO
import serial
import time
import threading
from queue import Queue

# Frame dimensions
frame_width = 1280
frame_height = 720

# Coordinate scale
x_min, x_max = -15, 15
y_min, y_max = -10, 10
x_range = x_max - x_min
y_range = y_max - y_min
pixels_per_unit_x = frame_width / x_range
pixels_per_unit_y = frame_height / y_range
center_x = frame_width // 2
center_y = frame_height // 2

# Serial Configuration
SERIAL_PORT = "COM5"
SERIAL_BAUDRATE = 115200

# Load YOLOv8 model
model = YOLO("model/best.pt")

# Serial connection
ser = None

# Queue for thread communication
servo_queue = Queue()

# Servo position tracking
current_servo1_angle = 90
current_servo2_angle = 90

# Servo movement configuration - DUAL SPEED SYSTEM
servo_step_fine = 3
servo_step_coarse = 50
precision_threshold = 1.0

# Auto-reset configuration
last_detection_time = time.time()
reset_timeout = 3.0  # 3 seconds timeout for auto-reset
reset_in_progress = False

def init_serial():
    """Initialize serial connection to ESP32"""
    global ser
    try:
        ser = serial.Serial(SERIAL_PORT, SERIAL_BAUDRATE, timeout=0.1)
        time.sleep(2)  # Wait for ESP32 to initialize
        print(f"✅ Serial connected to {SERIAL_PORT} at {SERIAL_BAUDRATE} baud")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to serial: {e}")
        return False

def send_servo_command_serial(x_coord, y_coord):
    """
    Send servo command to ESP32 via Serial - DUAL SPEED SYSTEM
    """
    global current_servo1_angle, current_servo2_angle, ser, precision_threshold, last_detection_time
    
    if ser is None or not ser.is_open:
        return False
    
    try:
        # Update last detection time
        last_detection_time = time.time()
        
        # Determine movement mode based on distance from center
        abs_x = abs(x_coord)
        abs_y = abs(y_coord)
        
        # Select step size based on distance from center
        if abs_x > precision_threshold or abs_y > precision_threshold:
            step_x = servo_step_coarse
            step_y = servo_step_coarse
            movement_mode = "COARSE"
        else:
            step_x = servo_step_fine
            step_y = servo_step_fine
            movement_mode = "FINE"
        
        # Determine servo movement direction based on object position
        if abs(x_coord) < 0.5 and abs(y_coord) < 0.5:
            # Object at center point (0,0) - hold position
            servo1_target = current_servo1_angle
            servo2_target = current_servo2_angle
            movement_mode = "HOLD"
        else:
            # Move servos based on object position with appropriate step
            if x_coord > precision_threshold:
                servo1_target = min(180, current_servo1_angle + servo_step_coarse)
            elif x_coord < -precision_threshold:
                servo1_target = max(0, current_servo1_angle - servo_step_coarse)
            elif x_coord > 0:
                servo1_target = min(180, current_servo1_angle + servo_step_fine)
            elif x_coord < 0:
                servo1_target = max(0, current_servo1_angle - servo_step_fine)
            else:
                servo1_target = current_servo1_angle
                
            if y_coord > precision_threshold:
                servo2_target = min(180, current_servo2_angle + servo_step_coarse)
            elif y_coord < -precision_threshold:
                servo2_target = max(0, current_servo2_angle - servo_step_coarse)
            elif y_coord > 0:
                servo2_target = min(180, current_servo2_angle + servo_step_fine)
            elif y_coord < 0:
                servo2_target = max(0, current_servo2_angle - servo_step_fine)
            else:
                servo2_target = current_servo2_angle
        
        # Format compact serial message
        message = f"S1,{servo1_target},S2,{servo2_target}\n"
        
        # Send via serial
        ser.write(message.encode())
        ser.flush()
        
        # Update servo positions
        current_servo1_angle = servo1_target
        current_servo2_angle = servo2_target
        
        # Calculate steps used for logging
        step_used_x = abs(servo1_target - current_servo1_angle) if servo1_target != current_servo1_angle else 0
        step_used_y = abs(servo2_target - current_servo2_angle) if servo2_target != current_servo2_angle else 0
        
        print(f"⚡ {movement_mode} Mode: S1={servo1_target}° S2={servo2_target}° | Pos=({x_coord:.2f}, {y_coord:.2f}) | Steps=({step_used_x}°, {step_used_y}°)")
        return True
        
    except Exception as e:
        print(f"❌ Serial communication error: {e}")
        return False

def check_reset_condition():
    """
    Check if we need to reset servos due to no detection
    """
    global current_servo1_angle, current_servo2_angle, last_detection_time, reset_in_progress
    
    if time.time() - last_detection_time > reset_timeout and not reset_in_progress:
        if current_servo1_angle != 90 or current_servo2_angle != 90:
            print(f"🔄 No detection for {reset_timeout} seconds - Resetting servos to center...")
            reset_in_progress = True
            servo_queue.put((0, 0))  # This will trigger center position
            current_servo1_angle = 90
            current_servo2_angle = 90
            reset_in_progress = False
            print("✅ Servos reset to center position (90°, 90°)")

def servo_communication_thread():
    """Separate thread for handling serial communication"""
    while True:
        try:
            check_reset_condition()  # Check reset condition in the thread
            
            if not servo_queue.empty():
                x_coord, y_coord = servo_queue.get()
                send_servo_command_serial(x_coord, y_coord)
            time.sleep(0.001)  # 1ms delay
        except Exception as e:
            print(f"❌ Error in servo thread: {e}")

def draw_axis_grid(frame):
    """Draw coordinate grid on frame"""
    global precision_threshold
    overlay = frame.copy()
    line_color = (0, 255, 0)
    text_color = (0, 255, 255)
    precision_zone_color = (255, 255, 0)
    thickness = 1
    text_thickness = 1
    font = cv2.FONT_HERSHEY_SIMPLEX

    # X and Y axes
    cv2.line(overlay, (0, center_y), (frame_width, center_y), line_color, 2)
    cv2.line(overlay, (center_x, 0), (center_x, frame_height), line_color, 2)

    # Precision zone
    precision_x_pixels = int(precision_threshold * pixels_per_unit_x)
    precision_y_pixels = int(precision_threshold * pixels_per_unit_y)
    
    cv2.rectangle(overlay, 
                 (center_x - precision_x_pixels, center_y - precision_y_pixels),
                 (center_x + precision_x_pixels, center_y + precision_y_pixels),
                 precision_zone_color, 2)
    
    cv2.putText(overlay, "FINE ZONE", 
               (center_x - precision_x_pixels, center_y - precision_y_pixels - 10),
               font, 0.5, precision_zone_color, 1)

    # Grid lines and labels
    for i in range(x_min, x_max + 1):
        x_pixel = int(center_x + i * pixels_per_unit_x)
        cv2.line(overlay, (x_pixel, center_y - 5), (x_pixel, center_y + 5), line_color, thickness)
        cv2.putText(overlay, str(i), (x_pixel - 10, center_y + 20), font, 0.5, text_color, text_thickness)

    for j in range(y_min, y_max + 1):
        y_pixel = int(center_y - j * pixels_per_unit_y)
        cv2.line(overlay, (center_x - 5, y_pixel), (center_x + 5, y_pixel), line_color, thickness)
        if j != 0:
            cv2.putText(overlay, str(j), (center_x + 10, y_pixel + 5), font, 0.5, text_color, text_thickness)

    return overlay

def draw_labels(frame, detected=0, servo1_angle=90, servo2_angle=90, movement_mode="UNKNOWN"):
    """Draw information labels on frame"""
    overlay = frame.copy()
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    font_thickness = 1
    text_color = (255, 255, 255)
    bg_color = (0, 0, 0)
    padding = 5

    timezone = pytz.timezone('Asia/Jakarta')
    now = datetime.now(timezone)
    time_str = now.strftime('%Y-%m-%d %H:%M:%S')

    # Calculate time since last detection
    time_since_last_detection = time.time() - last_detection_time
    detection_status = "ACTIVE" if time_since_last_detection < reset_timeout else f"INACTIVE ({time_since_last_detection:.1f}s)"

    labels = [
        f"{time_str}",
        f"Target detected = {detected}",
        f"Servo 1: {servo1_angle}°",
        f"Servo 2: {servo2_angle}°",
        f"Movement: {movement_mode}",
        f"Detection: {detection_status}",
        f"Auto-reset: {reset_timeout}s timeout",
        f"Fine Zone: ±{precision_threshold} units",
        f"Fine Step: {servo_step_fine}° | Coarse Step: {servo_step_coarse}°"
    ]

    y_offset = 10
    for label in labels:
        (text_width, text_height), _ = cv2.getTextSize(label, font, font_scale, font_thickness)
        top_left = (10, y_offset)
        bottom_right = (10 + text_width + padding*2, y_offset + text_height + padding*2)
        cv2.rectangle(overlay, top_left, bottom_right, bg_color, -1)
        text_origin = (top_left[0] + padding, top_left[1] + text_height + padding)
        cv2.putText(overlay, label, text_origin, font, font_scale, text_color, font_thickness)
        y_offset += text_height + padding*2 + 5

    return overlay

def pixel_to_coords(x_pixel, y_pixel):
    """Convert pixel coordinates to unit coordinates"""
    x_unit = (x_pixel - center_x) / pixels_per_unit_x
    y_unit = (center_y - y_pixel) / pixels_per_unit_y
    return round(x_unit, 2), round(y_unit, 2)

def get_movement_mode(x_coord, y_coord):
    """Determine movement mode based on object position"""
    global precision_threshold
    abs_x = abs(x_coord)
    abs_y = abs(y_coord)
    
    if abs(x_coord) < 0.5 and abs(y_coord) < 0.5:
        return "HOLD"
    elif abs_x > precision_threshold or abs_y > precision_threshold:
        return "COARSE"
    else:
        return "FINE"

def main():
    global current_servo1_angle, current_servo2_angle, ser, precision_threshold, last_detection_time
    
    # Initialize serial connection
    serial_connected = init_serial()
    if not serial_connected:
        print("❌ Cannot continue without serial connection")
        return
    
    # Start servo communication thread
    servo_thread = threading.Thread(target=servo_communication_thread, daemon=True)
    servo_thread.start()
    
    # Initialize video capture
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    cap.set(cv2.CAP_PROP_FPS, 60)

    if not cap.isOpened():
        print("❌ Cannot open camera.")
        return

    cv2.namedWindow("Kamera Fullscreen", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Kamera Fullscreen", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    print("✅ DUAL SPEED SERVO MODE ACTIVE!")
    print(f"✅ Fine movement zone: ±{precision_threshold} units ({servo_step_fine}° steps)")
    print(f"✅ Coarse movement zone: beyond ±{precision_threshold} units ({servo_step_coarse}° steps)")
    print(f"✅ Auto-reset timeout: {reset_timeout} seconds")
    print("✅ Press 'q' to quit.")
    print("✅ Press 'r' to manually reset servos to center.")
    print("✅ Press '+' to increase precision threshold.")
    print("✅ Press '-' to decrease precision threshold.")

    target1_coords = None
    last_command_time = 0
    command_interval = 0.01
    current_movement_mode = "UNKNOWN"

    frame_count = 0
    fps_start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to read frame.")
            break

        frame = cv2.resize(frame, (frame_width, frame_height))
        results = model.predict(frame, imgsz=640, conf=0.5, verbose=False)
        detections = results[0].boxes.xyxy.cpu().numpy() if results[0].boxes else []

        frame_with_axis = draw_axis_grid(frame)

        target1_found = False
        for i, box in enumerate(detections):
            x1, y1, x2, y2 = box[:4].astype(int)
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)

            # Convert to unit coordinates
            coord_x, coord_y = pixel_to_coords(cx, cy)

            # Save coordinates for Target 1 (first detected object)
            if i == 0:
                target1_coords = (coord_x, coord_y)
                target1_found = True
                current_movement_mode = get_movement_mode(coord_x, coord_y)
                last_detection_time = time.time()  # Update detection time

            # Draw bounding box and center point
            color = (0, 0, 255) if i == 0 else (255, 0, 0)
            cv2.rectangle(frame_with_axis, (x1, y1), (x2, y2), color, 2)
            cv2.circle(frame_with_axis, (cx, cy), 4, (255, 255, 0), -1)

            # Display coordinates and movement mode
            movement_info = get_movement_mode(coord_x, coord_y)
            cv2.putText(
                frame_with_axis,
                f"({coord_x}, {coord_y}) - {movement_info}",
                (cx + 10, cy - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )

            # Add object label
            label_text = f"Target {i+1}"
            label_color = (255, 255, 255) if i == 0 else (200, 200, 200)
            cv2.putText(
                frame_with_axis,
                label_text,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                label_color,
                2
            )

        # Send servo commands if target found
        current_time = time.time()
        if target1_found and serial_connected and (current_time - last_command_time) > command_interval:
            if servo_queue.empty():
                servo_queue.put(target1_coords)
                last_command_time = current_time

        # Calculate and display FPS
        frame_count += 1
        if frame_count % 30 == 0:
            fps = 30 / (time.time() - fps_start_time)
            time_since_detection = time.time() - last_detection_time
            print(f"🚀 FPS: {fps:.1f} | Servo latency: ~{command_interval*1000:.1f}ms | Mode: {current_movement_mode} | Last detection: {time_since_detection:.1f}s ago")
            fps_start_time = time.time()

        frame_with_labels = draw_labels(
            frame_with_axis, 
            detected=len(detections), 
            servo1_angle=current_servo1_angle,
            servo2_angle=current_servo2_angle,
            movement_mode=current_movement_mode
        )
        
        cv2.imshow("Kamera Fullscreen", frame_with_labels)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            # Manual reset to center
            current_servo1_angle = 90
            current_servo2_angle = 90
            if serial_connected:
                servo_queue.put((0, 0))
            last_detection_time = time.time()  # Reset detection timer
            print("🔄 Manual servo reset to center (90°, 90°)")
        elif key == ord('+') or key == ord('='):
            # Increase precision threshold
            precision_threshold = min(5.0, precision_threshold + 0.5)
            print(f"📈 Precision threshold increased to ±{precision_threshold}")
        elif key == ord('-'):
            # Decrease precision threshold
            precision_threshold = max(0.5, precision_threshold - 0.5)
            print(f"📉 Precision threshold decreased to ±{precision_threshold}")

    # Cleanup
    if ser and ser.is_open:
        ser.close()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()