from flask import Flask, render_template, Response, jsonify, request
import cv2
import serial
import time
import threading
from ultralytics import YOLO
import queue
import math
import os
import glob

app = Flask(__name__)

# Global variables
camera = None
serial_conn = None
current_camera = 0
available_cameras = []
detection_enabled = False
manual_mode = True
auto_mode = False

# Model management
model = None
current_model = None
available_models = []
model_folder = 'model'

# Servo positions
servo_positions = {
    'servo1': 90,  # Y-axis
    'servo2': 90,  # X-axis  
    'servo3': 0    # Trigger
}

# Frame resolution
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
frame_center_x = FRAME_WIDTH // 2
frame_center_y = FRAME_HEIGHT // 2

# Centering control parameters
CENTERING_KP_X = 2.0      # X-axis proportional gain
CENTERING_KP_Y = 1.5      # Y-axis proportional gain  
CENTERING_DEADZONE_X = 1.0  # X-axis deadzone to prevent oscillation
CENTERING_DEADZONE_Y = 1.0  # Y-axis deadzone to prevent oscillation

# Auto mode tracking variables
last_detection_time = 0
no_detection_timeout = 5.0  # 5 seconds timeout
detection_reset_performed = False

# Serial Configuration
SERIAL_PORT = "COM5"
SERIAL_BAUDRATE = 115200

# Command queue for serial communication
command_queue = queue.Queue(maxsize=10)  # Limit queue size to prevent lag
last_command_time = time.time()
last_servo_update_time = time.time()

# Performance optimization
MIN_SERVO_UPDATE_INTERVAL = 0.55  # 100ms between servo updates
MIN_DETECTION_INTERVAL = 0.2     # 200ms between detections
last_detection_run_time = 0

def get_available_models():
    """Get all available .pt model files from the model folder"""
    global available_models, model_folder
    
    if not os.path.exists(model_folder):
        print(f"❌ Model folder '{model_folder}' not found")
        return []
    
    # Find all .pt files in the model folder
    model_pattern = os.path.join(model_folder, '*.pt')
    model_files = glob.glob(model_pattern)
    
    # Extract just the filenames without the path
    available_models = [os.path.basename(f) for f in sorted(model_files)]
    
    print(f"📁 Found models: {available_models}")
    return available_models

def load_model(model_name):
    """Load a specific YOLO model"""
    global model, current_model, model_folder
    
    try:
        model_path = os.path.join(model_folder, model_name)
        
        if not os.path.exists(model_path):
            print(f"❌ Model file not found: {model_path}")
            return False
        
        # Load the new model
        new_model = YOLO(model_path)
        
        # If successful, update global variables
        model = new_model
        current_model = model_name
        
        print(f"✅ Model '{model_name}' loaded successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error loading model '{model_name}': {e}")
        return False

def init_default_model():
    """Initialize the first available model as default"""
    global available_models, current_model
    
    available_models = get_available_models()
    
    if available_models:
        # Load the first model alphabetically
        first_model = available_models[0]
        if load_model(first_model):
            print(f"✅ Default model '{first_model}' initialized")
            return True
        else:
            print(f"❌ Failed to load default model '{first_model}'")
    else:
        print("❌ No models found in the model folder")
    
    return False

# PID Controller class
class PIDController:
    def __init__(self, kp=1.2, ki=0.1, kd=0.05):
        self.kp = kp  # Proportional gain
        self.ki = ki  # Integral gain  
        self.kd = kd  # Derivative gain
        self.previous_error = 0
        self.integral = 0
        self.last_time = time.time()
    
    def calculate(self, error):
        current_time = time.time()
        dt = current_time - self.last_time
        
        if dt <= 0:
            dt = 0.01
        
        # Proportional term
        proportional = error
        
        # Integral term (with windup protection)
        self.integral += error * dt
        self.integral = max(-50, min(50, self.integral))  # Clamp integral
        
        # Derivative term
        derivative = (error - self.previous_error) / dt
        
        # Calculate output
        output = (self.kp * proportional + 
                 self.ki * self.integral + 
                 self.kd * derivative)
        
        self.previous_error = error
        self.last_time = current_time
        
        return output
    
    def reset(self):
        """Reset PID controller state"""
        self.previous_error = 0
        self.integral = 0
        self.last_time = time.time()

# Object tracking class
class ObjectTracker:
    def __init__(self):
        self.last_position = None
        self.position_history = []
        self.max_history = 5
        self.lost_frames = 0
        self.max_lost_frames = 10
    
    def update(self, new_position):
        if new_position is not None:
            self.last_position = new_position
            self.position_history.append(new_position)
            self.lost_frames = 0
            
            # Keep only recent history
            if len(self.position_history) > self.max_history:
                self.position_history.pop(0)
                
            return new_position
        else:
            self.lost_frames += 1
            
            # Use prediction if object is temporarily lost
            if self.lost_frames < self.max_lost_frames and len(self.position_history) >= 2:
                # Simple linear prediction
                if len(self.position_history) >= 2:
                    dx = self.position_history[-1][0] - self.position_history[-2][0]
                    dy = self.position_history[-1][1] - self.position_history[-2][1]
                    
                    predicted_x = self.position_history[-1][0] + dx
                    predicted_y = self.position_history[-1][1] + dy
                    
                    print(f"🔮 Predicted position: ({predicted_x:.0f}, {predicted_y:.0f})")
                    return (predicted_x, predicted_y)
            
            return None
    
    def is_tracking(self):
        return self.lost_frames < self.max_lost_frames
    
    def reset(self):
        """Reset tracker state"""
        self.last_position = None
        self.position_history = []
        self.lost_frames = 0

# Initialize PID controllers and object tracker
pid_x = PIDController(kp=2.0, ki=0.15, kd=0.1)  # Tuned for X-axis
pid_y = PIDController(kp=1.8, ki=0.12, kd=0.08)  # Tuned for Y-axis
object_tracker = ObjectTracker()

def reset_controllers():
    """Reset PID controllers and object tracker"""
    global pid_x, pid_y, object_tracker
    pid_x.reset()
    pid_y.reset()
    object_tracker.reset()
    print("🔄 Controllers reset")

def reset_detection_timeout():
    """Reset detection timeout and flag"""
    global last_detection_time, detection_reset_performed
    last_detection_time = time.time()
    detection_reset_performed = False

def init_serial():
    """Initialize serial connection to ESP32"""
    global serial_conn
    try:
        # Close existing connection if any
        if serial_conn and serial_conn.is_open:
            serial_conn.close()
            time.sleep(0.5)
        
        # Initialize serial connection
        serial_conn = serial.Serial(
            port=SERIAL_PORT,
            baudrate=SERIAL_BAUDRATE,
            timeout=0.05,  # Very short timeout for responsiveness
            write_timeout=0.5
        )
        
        # Wait for ESP32 to initialize
        time.sleep(2)
        
        # Test connection
        test_command = "S1,90,S2,90\n"
        serial_conn.write(test_command.encode())
        serial_conn.flush()
        
        print(f"✅ Serial connection established on {SERIAL_PORT}")
        return True
        
    except serial.SerialException as e:
        print(f"❌ Serial error: {e}")
        serial_conn = None
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        serial_conn = None
        return False

def serial_worker():
    """Background worker to handle serial commands"""
    global serial_conn, command_queue
    
    while True:
        try:
            if not command_queue.empty() and serial_conn and serial_conn.is_open:
                command = command_queue.get(timeout=0.1)
                
                # Send command
                serial_conn.write(command.encode())
                serial_conn.flush()
                
                # Read response (optional, with timeout)
                try:
                    response = serial_conn.readline().decode().strip()
                    if response:
                        print(f"📱 ESP32: {response}")
                except:
                    pass  # Ignore read timeout
                    
            else:
                time.sleep(0.01)  # Small delay when queue is empty
                
        except Exception as e:
            print(f"❌ Serial worker error: {e}")
            time.sleep(0.1)

# Start serial worker thread
serial_thread = threading.Thread(target=serial_worker, daemon=True)
serial_thread.start()

def send_servo_command_optimized(servo1=None, servo2=None, servo3=None):
    """Optimized servo command with extended ranges for auto mode"""
    global servo_positions, command_queue, last_command_time
    
    if not serial_conn or not serial_conn.is_open:
        print("❌ No serial connection")
        return False
    
    # Optimized rate limiting - faster response
    current_time = time.time()
    if current_time - last_command_time < 0.02:  # 50 Hz max
        return False
    last_command_time = current_time
    
    try:
        commands = []
        
        # Update servo positions and build command with extended ranges
        if servo1 is not None:
            if auto_mode:
                # Extended range for auto mode: 25-155 degrees
                servo1 = max(25, min(155, servo1))
            else:
                # Original range for manual mode
                servo1 = max(25, min(155, servo1))
            servo_positions['servo1'] = servo1
            commands.extend(["S1", str(servo1)])
        
        if servo2 is not None:
            if auto_mode:
                # Extended range for auto mode: 15-165 degrees  
                servo2 = max(15, min(165, servo2))
            else:
                # Original range for manual mode
                servo2 = max(15, min(165, servo2))
            servo_positions['servo2'] = servo2
            commands.extend(["S2", str(servo2)])
            
        if servo3 is not None:
            servo3 = max(0, min(43, servo3))
            servo_positions['servo3'] = servo3
            commands.extend(["S3", str(servo3)])
        
        if commands:
            # Format: "S1,90,S2,120\n"
            command_string = ",".join(commands) + "\n"
            
            # Enhanced queue management
            try:
                command_queue.put_nowait(command_string)
                print(f"📤 Queued: {command_string.strip()}")
                return True
            except queue.Full:
                print("⚠️ Command queue full, skipping command")
                return False
            
    except Exception as e:
        print(f"❌ Error preparing command: {e}")
        return False
    
    return False

def get_available_cameras():
    """Detect available cameras"""
    cameras = []
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            cameras.append(i)
            cap.release()
        time.sleep(0.1)
    return cameras

def init_camera(camera_index=0):
    """Initialize camera"""
    global camera
    try:
        if camera:
            camera.release()
            time.sleep(0.5)
        
        camera = cv2.VideoCapture(camera_index)
        if not camera.isOpened():
            print(f"❌ Failed to open camera {camera_index}")
            return False
            
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        camera.set(cv2.CAP_PROP_FPS, 30)
        camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for real-time
        
        # Test camera
        ret, frame = camera.read()
        if ret:
            print(f"✅ Camera {camera_index} initialized")
            return True
        else:
            print(f"❌ Camera {camera_index} cannot read frames")
            camera.release()
            camera = None
            return False
            
    except Exception as e:
        print(f"❌ Camera error: {e}")
        if camera:
            camera.release()
            camera = None
        return False

def calculate_servo_movement(obj_x, obj_y):
    """
    Optimized servo movement calculation using proportional control for effective centering
    """
    global servo_positions
    
    # Convert pixel coordinates to normalized coordinates
    x_normalized = (obj_x - frame_center_x) / (frame_center_x / 15)  # -15 to +15
    y_normalized = (obj_y - frame_center_y) / (frame_center_y / 10)  # -10 to +10
    
    # Clamp values
    x_normalized = max(-15, min(15, x_normalized))
    y_normalized = max(-10, min(10, y_normalized))
    
    # Calculate error (distance from center)
    x_error = x_normalized  # Positive = object on right
    y_error = y_normalized  # Positive = object above center
    
    # Use global parameters for real-time tuning
    global CENTERING_KP_X, CENTERING_KP_Y, CENTERING_DEADZONE_X, CENTERING_DEADZONE_Y
    
    # Calculate proportional correction
    x_correction = CENTERING_KP_X * x_error
    y_correction = CENTERING_KP_Y * y_error
    
    # Apply correction to current servo positions
    # X-axis (Servo 2): Move opposite to error direction
    # If object on right (+x_error), servo should move left (decrease angle)
    new_servo2 = servo_positions['servo2'] - x_correction
    
    # Y-axis (Servo 1): Move opposite to error direction  
    # If object above center (+y_error), servo should move up (increase angle)
    new_servo1 = servo_positions['servo1'] + y_correction
    
    # Apply servo limits based on mode
    if auto_mode:
        # Extended ranges for auto mode
        new_servo1 = max(25, min(155, int(new_servo1)))
        new_servo2 = max(15, min(165, int(new_servo2)))
    else:
        # Original ranges for manual mode
        new_servo1 = max(25, min(155, int(new_servo1)))
        new_servo2 = max(15, min(165, int(new_servo2)))
    
    # Add deadzone to prevent oscillation near center
    if abs(x_error) < CENTERING_DEADZONE_X:
        new_servo2 = servo_positions['servo2']  # Keep current position
    
    if abs(y_error) < CENTERING_DEADZONE_Y:
        new_servo1 = servo_positions['servo1']  # Keep current position
    
    return new_servo1, new_servo2

def check_detection_timeout():
    """Check if no detection timeout has been reached and reset servos if needed"""
    global last_detection_time, detection_reset_performed, no_detection_timeout
    
    if not auto_mode:
        return
    
    current_time = time.time()
    time_since_detection = current_time - last_detection_time
    
    if time_since_detection >= no_detection_timeout and not detection_reset_performed:
        print(f"⏰ No detection for {no_detection_timeout}s - Resetting servos to 90°")
        send_servo_command_optimized(servo1=90, servo2=90)
        detection_reset_performed = True
        print("🔄 Servos reset to initial position (90°, 90°)")

def process_detection_optimized(frame, results):
    """
    Optimized detection processing with multi-object labeling and priority tracking
    """
    global auto_mode, last_servo_update_time, last_detection_time, detection_reset_performed
    global last_detection_run_time
    
    if not auto_mode:
        return
    
    height, width = frame.shape[:2]
    center_x, center_y = width // 2, height // 2
    
    # Check if we should run detection (rate limiting)
    current_time = time.time()
    if current_time - last_detection_run_time < MIN_DETECTION_INTERVAL:
        return
    last_detection_run_time = current_time
    
    # Collect all valid detections
    valid_detections = []
    
    for result in results:
        boxes = result.boxes
        if boxes is not None:
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = box.conf[0].cpu().numpy()
                
                if confidence > 0.5:
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
        # Update detection time and reset flag
        last_detection_time = time.time()
        detection_reset_performed = False
        
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
        
        # Only track and move servos based on Object #1 (priority object)
        priority_object = valid_detections[0]
        
        # Check if enough time has passed since last servo update
        if current_time - last_servo_update_time >= MIN_SERVO_UPDATE_INTERVAL:
            # Calculate target servo positions using the priority object
            target_servo1, target_servo2 = calculate_servo_movement(
                priority_object['center'][0], priority_object['center'][1]
            )
            
            # Send commands if positions changed
            if target_servo1 != servo_positions['servo1'] or target_servo2 != servo_positions['servo2']:
                send_servo_command_optimized(servo1=target_servo1, servo2=target_servo2)
                last_servo_update_time = current_time
                print(f"🎯 Servos updated for Object #1 at {current_time:.2f}s")
    
    else:
        # No detections - check timeout
        check_detection_timeout()

def generate_frames():
    """Generate video frames with object detection"""
    global detection_enabled, auto_mode
    
    while True:
        if not camera or not camera.isOpened():
            time.sleep(1)
            continue
            
        success, frame = camera.read()
        if not success:
            print("❌ Failed to read frame")
            time.sleep(0.1)
            continue
        
        height, width = frame.shape[:2]
        center_x, center_y = width // 2, height // 2
        
        # Draw coordinate system
        cv2.line(frame, (center_x - 20, center_y), (center_x + 20, center_y), (0, 255, 0), 2)
        cv2.line(frame, (center_x, center_y - 15), (center_x, center_y + 15), (0, 255, 0), 2)
        
        # Draw coordinate info
        cv2.putText(frame, "X: -15 to +15", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, "Y: -10 to +10", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Mode indicator
        mode_text = "AUTO MODE" if auto_mode else "MANUAL MODE"
        mode_color = (0, 255, 255) if auto_mode else (255, 255, 255)
        cv2.putText(frame, mode_text, (width - 150, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, mode_color, 2)
        
        # Serial status
        serial_status = "SERIAL: OK" if (serial_conn and serial_conn.is_open) else "SERIAL: ERROR"
        serial_color = (0, 255, 0) if (serial_conn and serial_conn.is_open) else (0, 0, 255)
        cv2.putText(frame, serial_status, (width - 150, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, serial_color, 2)
        
        # Model status
        model_status = f"MODEL: {current_model}" if current_model else "MODEL: NONE"
        model_color = (0, 255, 0) if model else (255, 0, 0)
        cv2.putText(frame, model_status, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, model_color, 2)
        
        # Object detection with optimized processing
        if detection_enabled and auto_mode and model:
            try:
                results = model(frame, verbose=False)
                process_detection_optimized(frame, results)
                                
            except Exception as e:
                print(f"❌ Detection error: {e}")
        
        # Display servo positions with extended angle ranges
        if auto_mode:
            pos_text = f"S1:{servo_positions['servo1']}° (25-155°) S2:{servo_positions['servo2']}° (15-165°) S3:{servo_positions['servo3']}°"
        else:
            pos_text = f"S1:{servo_positions['servo1']}° (25-155°) S2:{servo_positions['servo2']}° (15-165°) S3:{servo_positions['servo3']}°"
        cv2.putText(frame, pos_text, (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # Encode frame
        try:
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ret:
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except Exception as e:
            print(f"❌ Frame encoding error: {e}")
            continue

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', 
                         available_cameras=available_cameras,
                         current_camera=current_camera,
                         available_models=available_models,
                         current_model=current_model)

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/change_camera', methods=['POST'])
def change_camera():
    """Change camera input"""
    global current_camera
    try:
        data = request.get_json()
        new_camera = int(data['camera'])
        if new_camera in available_cameras:
            current_camera = new_camera
            if init_camera(current_camera):
                return jsonify({'success': True, 'camera': current_camera})
    except Exception as e:
        print(f"Error changing camera: {e}")
    return jsonify({'success': False})

@app.route('/change_model', methods=['POST'])
def change_model():
    """Change YOLO model"""
    global current_model
    try:
        data = request.get_json()
        new_model = data['model']
        if new_model in available_models:
            if load_model(new_model):
                return jsonify({'success': True, 'model': current_model})
            else:
                return jsonify({'success': False, 'error': f'Failed to load model: {new_model}'})
        else:
            return jsonify({'success': False, 'error': f'Model not found: {new_model}'})
    except Exception as e:
        print(f"Error changing model: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/set_mode', methods=['POST'])
def set_mode():
    """Set control mode (manual/auto)"""
    global manual_mode, auto_mode, detection_enabled, last_servo_update_time
    
    try:
        data = request.get_json()
        mode = data.get('mode')
        
        if mode == 'manual':
            manual_mode = True
            auto_mode = False
            detection_enabled = False
            # Reset controllers when switching to manual
            reset_controllers()
        elif mode == 'auto':
            manual_mode = False
            auto_mode = True
            detection_enabled = True
            # Reset controllers, timing, and detection timeout when switching to auto
            reset_controllers()
            reset_detection_timeout()
            last_servo_update_time = time.time()
        
        return jsonify({
            'success': True,
            'manual_mode': manual_mode,
            'auto_mode': auto_mode,
            'detection_enabled': detection_enabled
        })
        
    except Exception as e:
        print(f"Error setting mode: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/tune_centering', methods=['POST'])
def tune_centering():
    """Tune centering parameters in real-time"""
    global CENTERING_KP_X, CENTERING_KP_Y, CENTERING_DEADZONE_X, CENTERING_DEADZONE_Y
    
    try:
        data = request.get_json()
        
        if 'kp_x' in data:
            CENTERING_KP_X = float(data['kp_x'])
        if 'kp_y' in data:
            CENTERING_KP_Y = float(data['kp_y'])
        if 'deadzone_x' in data:
            CENTERING_DEADZONE_X = float(data['deadzone_x'])
        if 'deadzone_y' in data:
            CENTERING_DEADZONE_Y = float(data['deadzone_y'])
        
        return jsonify({
            'success': True,
            'kp_x': CENTERING_KP_X,
            'kp_y': CENTERING_KP_Y,
            'deadzone_x': CENTERING_DEADZONE_X,
            'deadzone_y': CENTERING_DEADZONE_Y
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/manual_control', methods=['POST'])
def manual_control():
    """Manual servo control"""
    if not manual_mode:
        return jsonify({'success': False, 'error': 'Manual mode not active'})
    
    try:
        data = request.get_json()
        servo1 = data.get('servo1')
        servo2 = data.get('servo2')
        servo3 = data.get('servo3')
        
        success = send_servo_command_optimized(servo1=servo1, servo2=servo2, servo3=servo3)
        return jsonify({'success': success, 'positions': servo_positions})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/trigger', methods=['POST'])
def trigger():
    """Control trigger servo"""
    try:
        data = request.get_json()
        action = data.get('action')
        
        if action == 'press':
            success = send_servo_command_optimized(servo3=90)
        elif action == 'release':
            success = send_servo_command_optimized(servo3=0)
        else:
            success = False
            
        return jsonify({'success': success, 'positions': servo_positions})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/reset_servos', methods=['POST'])
def reset_servos():
    """Reset all servos to initial positions"""
    global last_servo_update_time
    success = send_servo_command_optimized(servo1=90, servo2=90, servo3=0)
    # Also reset controllers, timing, and detection timeout
    reset_controllers()
    reset_detection_timeout()
    last_servo_update_time = time.time()
    return jsonify({'success': success, 'positions': servo_positions})

@app.route('/status')
def status():
    """Get system status"""
    global last_servo_update_time, last_detection_time, detection_reset_performed
    current_time = time.time()
    time_since_last_update = current_time - last_servo_update_time
    time_since_detection = current_time - last_detection_time
    
    return jsonify({
        'servo_positions': servo_positions,
        'detection_enabled': detection_enabled,
        'manual_mode': manual_mode,
        'auto_mode': auto_mode,
        'current_camera': current_camera,
        'current_model': current_model,
        'serial_connected': serial_conn is not None and serial_conn.is_open,
        'available_cameras': available_cameras,
        'available_models': available_models,
        'command_queue_size': command_queue.qsize(),
        'tracking_active': object_tracker.is_tracking() if 'object_tracker' in globals() else False,
        'time_since_last_servo_update': time_since_last_update,
        'next_update_in': max(0, MIN_SERVO_UPDATE_INTERVAL - time_since_last_update),
        'time_since_detection': time_since_detection,
        'detection_timeout': no_detection_timeout,
        'detection_reset_performed': detection_reset_performed,
        'servo_ranges': {
            'servo1': {'min': 25, 'max': 155},
            'servo2': {'min': 15, 'max': 165}
        },
        'centering_params': {
            'kp_x': CENTERING_KP_X,
            'kp_y': CENTERING_KP_Y,
            'deadzone_x': CENTERING_DEADZONE_X,
            'deadzone_y': CENTERING_DEADZONE_Y
        }
    })

def cleanup():
    """Cleanup resources"""
    global camera, serial_conn
    
    if camera:
        camera.release()
        print("✅ Camera released")
    
    if serial_conn and serial_conn.is_open:
        serial_conn.close()
        print("✅ Serial connection closed")

if __name__ == '__main__':
    print("🚀 Starting Flask Servo Controller (Optimized Version)...")
    
    # Initialize serial connection
    retry_count = 0
    max_retries = 3
    
    while retry_count < max_retries:
        if init_serial():
            break
        else:
            retry_count += 1
            if retry_count < max_retries:
                print(f"⚠️ Retrying serial connection... ({retry_count}/{max_retries})")
                time.sleep(2)
    
    if not serial_conn:
        print("⚠️ Continuing without serial connection")
    
    # Initialize models
    print("🤖 Scanning for YOLO models...")
    if not init_default_model():
        print("⚠️ Continuing without model - detection will be disabled")
    
    # Initialize cameras
    print("📹 Scanning for cameras...")
    available_cameras = get_available_cameras()
    print(f"📹 Available cameras: {available_cameras}")
    
    if available_cameras:
        if init_camera(available_cameras[0]):
            current_camera = available_cameras[0]
            print(f"✅ Camera {current_camera} ready")
    
    # Setup cleanup
    import atexit
    atexit.register(cleanup)
    
    # Initialize controllers and detection timeout
    reset_controllers()
    reset_detection_timeout()
    
    try:
        print("✅ Flask server starting on http://localhost:5000")
        print(f"   📁 Available models: {available_models}")
        print(f"   🔧 Current model: {current_model}")
        app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    finally:
        cleanup()


        # okee