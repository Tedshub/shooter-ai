// Global variables
let manualMode = true;
let autoMode = false;
let detectionEnabled = false;
let isDragging = false;
let currentServo1 = 90, currentServo2 = 90; // Renamed for clarity
let triggerPressed = false;
let voiceFireTimeout = null; // New variable for voice fire timeout
let voiceCooldownTimeout = null; // New variable for voice command cooldown
let isVoiceCooldown = false; // Flag to track if voice system is in cooldown

// DOM elements
const joystick = document.getElementById('joystick');
const joystickContainer = document.getElementById('joystickContainer');
const triggerButton = document.getElementById('triggerButton');
const manualModeBtn = document.getElementById('manualModeBtn');
const autoModeBtn = document.getElementById('autoModeBtn');
const manualControls = document.getElementById('manualControls');
const autoControls = document.getElementById('autoControls');
const toggleDetectionBtn = document.getElementById('toggleDetectionBtn');
const resetServosBtn = document.getElementById('resetServosBtn');
const cameraSelect = document.getElementById('cameraSelect');
const modelSelect = document.getElementById('modelSelect');
const scanCameraBtn = document.getElementById('scanCameraBtn'); // New element for camera refresh

// Status elements
const connectionIndicator = document.getElementById('connectionIndicator');
const connectionStatus = document.getElementById('connectionStatus');
const currentMode = document.getElementById('currentMode');
const detectionStatus = document.getElementById('detectionStatus');
const currentModelStatus = document.getElementById('currentModelStatus');
const servo1Pos = document.getElementById('servo1Pos');
const servo2Pos = document.getElementById('servo2Pos');
const servo3Pos = document.getElementById('servo3Pos');
const s1Pos = document.getElementById('s1Pos');
const s2Pos = document.getElementById('s2Pos');
const s3Pos = document.getElementById('s3Pos');
const joystickServo1 = document.getElementById('joystickServo1');
const joystickServo2 = document.getElementById('joystickServo2');
const triggerStatus = document.getElementById('triggerStatus');

// Serial port selection
const serialPortSelect = document.getElementById('serialPortSelect');
const scanSerialBtn = document.getElementById('scanSerialBtn');

// Serial port selection
serialPortSelect.addEventListener('change', function() {
    const selectedPort = this.value;
    console.log('Changing serial port to:', selectedPort);
    
    fetch('/change_serial_port', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ serial_port: selectedPort })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Serial port changed to:', data.serial_port);
        } else {
            console.error('Failed to change serial port:', data.error);
            alert('Failed to change serial port: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error changing serial port:', error);
        alert('Error changing serial port: ' + error.message);
    });
});

// Scan serial ports
scanSerialBtn.addEventListener('click', function() {
    console.log('Scanning for serial ports...');
    
    fetch('/scan_serial_ports', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Available serial ports:', data.serial_ports);
            
            // Clear current options
            serialPortSelect.innerHTML = '';
            
            // Add new options
            data.serial_ports.forEach(port => {
                const option = document.createElement('option');
                option.value = port;
                option.textContent = port;
                if (port === data.current_port) {
                    option.selected = true;
                }
                serialPortSelect.appendChild(option);
            });
            
            console.log('Serial port dropdown updated');
        } else {
            console.error('Failed to scan serial ports:', data.error);
            alert('Failed to scan serial ports: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error scanning serial ports:', error);
        alert('Error scanning serial ports: ' + error.message);
    });
});

// Mode switching
manualModeBtn.addEventListener('click', () => setMode('manual'));
autoModeBtn.addEventListener('click', () => setMode('auto'));

function setMode(mode) {
    fetch('/set_mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: mode })
    })
    .then(response => response.json())
    .then(data => {
        manualMode = data.manual_mode;
        autoMode = data.auto_mode;
        detectionEnabled = data.detection_enabled;
        
        updateModeUI();
    })
    .catch(console.error);
}

function updateModeUI() {
    // Update mode buttons
    manualModeBtn.classList.toggle('active', manualMode);
    autoModeBtn.classList.toggle('active', autoMode);
    
    // Update control panels
    manualControls.classList.toggle('disabled', !manualMode);
    
    // Update status
    currentMode.textContent = manualMode ? 'Manual' : 'Auto';
    detectionStatus.textContent = detectionEnabled ? 'ON' : 'OFF';
    
    // Update connection indicator
    if (detectionEnabled) {
        connectionIndicator.className = 'connection-indicator detecting';
    } else {
        connectionIndicator.className = 'connection-indicator connected';
    }
    
    // Update detection button text
    toggleDetectionBtn.textContent = detectionEnabled ? 'STOP DETECTION' : 'START DETECTION';
}

// Camera selection
cameraSelect.addEventListener('change', function() {
    fetch('/change_camera', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ camera: parseInt(this.value) })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Camera changed to:', data.camera);
        } else {
            console.error('Failed to change camera:', data.error);
        }
    })
    .catch(console.error);
});

// NEW: Camera refresh functionality
scanCameraBtn.addEventListener('click', function() {
    console.log('Scanning for cameras...');
    
    // Add rotating animation to the button
    this.classList.add('rotating');
    
    fetch('/scan_cameras', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Available cameras:', data.cameras);
            
            // Clear current options
            cameraSelect.innerHTML = '';
            
            // Add new options
            data.cameras.forEach(camera => {
                const option = document.createElement('option');
                option.value = camera;
                option.textContent = `Camera ${camera}`;
                if (camera === data.current_camera) {
                    option.selected = true;
                }
                cameraSelect.appendChild(option);
            });
            
            // Show notification
            showCameraNotification('Camera scan completed successfully', 'success');
        } else {
            console.error('Failed to scan cameras:', data.error);
            showCameraNotification('Failed to scan cameras: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error scanning cameras:', error);
        showCameraNotification('Error scanning cameras: ' + error.message, 'error');
    })
    .finally(() => {
        // Remove rotating animation
        this.classList.remove('rotating');
    });
});

// NEW: Function to show camera notification
function showCameraNotification(message, type) {
    // Create notification element if it doesn't exist
    let notification = document.querySelector('.camera-notification');
    if (!notification) {
        notification = document.createElement('div');
        notification.className = 'camera-notification';
        document.body.appendChild(notification);
    }
    
    // Set message and type
    notification.textContent = message;
    notification.className = `camera-notification ${type} show`;
    
    // Hide after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// Model selection
modelSelect.addEventListener('change', function() {
    const selectedModel = this.value;
    console.log('Changing model to:', selectedModel);
    
    fetch('/change_model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: selectedModel })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Model changed to:', data.model);
            currentModelStatus.textContent = data.model;
        } else {
            console.error('Failed to change model:', data.error);
            alert('Failed to change model: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error changing model:', error);
        alert('Error changing model: ' + error.message);
    });
});

// Detection toggle
toggleDetectionBtn.addEventListener('click', function() {
    if (!autoMode) return;
    
    fetch('/toggle_detection', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        detectionEnabled = data.detection_enabled;
        updateModeUI();
    })
    .catch(console.error);
});

// Reset servos
resetServosBtn.addEventListener('click', function() {
    fetch('/reset_servos', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateServoPositions(data.positions);
        }
    })
    .catch(console.error);
});

// Manual joystick control - FIXED VERSION
joystick.addEventListener('mousedown', startDrag);
joystick.addEventListener('touchstart', startDrag, { passive: false });

function startDrag(e) {
    if (!manualMode) return;
    
    isDragging = true;
    joystick.classList.add('active');
    e.preventDefault();
    
    document.addEventListener('mousemove', drag, { passive: false });
    document.addEventListener('mouseup', stopDrag);
    document.addEventListener('touchmove', drag, { passive: false });
    document.addEventListener('touchend', stopDrag);
}

function drag(e) {
    if (!isDragging || !manualMode) return;
    e.preventDefault();
    
    const rect = joystickContainer.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    
    let clientX = e.clientX || (e.touches && e.touches[0].clientX);
    let clientY = e.clientY || (e.touches && e.touches[0].clientY);
    
    const deltaX = clientX - centerX;
    const deltaY = clientY - centerY;
    
    // Square boundary constraint - increased for maximum precision
    const maxDistance = 125;
    
    let x = Math.max(-maxDistance, Math.min(maxDistance, deltaX));
    let y = Math.max(-maxDistance, Math.min(maxDistance, deltaY));
    
    joystick.style.transform = `translate(${x - 50}px, ${y - 50}px)`;
    
    // Convert X movement to Servo2 angle with higher precision (reversed for natural control)
    const servo2Angle = Math.round(90 - (x / maxDistance) * 90);
    
    // Convert Y movement to Servo1 angle with higher precision (NOT reversed - down=bigger angle, up=smaller angle) 
    const servo1Angle = Math.round(90 + (y / maxDistance) * 90);
    
    currentServo1 = Math.max(0, Math.min(180, servo1Angle)); // Y-axis control
    currentServo2 = Math.max(0, Math.min(180, servo2Angle)); // X-axis control
    
    joystickServo1.textContent = currentServo1; // Servo 1 (Y-axis)
    joystickServo2.textContent = currentServo2; // Servo 2 (X-axis)
    
    // Send to server with correct mapping - MODIFIED to include current trigger state
    sendManualControl(currentServo1, currentServo2, triggerPressed ? 90 : null);
}

function stopDrag() {
    if (!isDragging) return;
    
    isDragging = false;
    joystick.classList.remove('active');
    joystick.style.transform = 'translate(-50px, -50px)';
    
    // Return to center position
    currentServo1 = 90; // Servo1 Y-axis center
    currentServo2 = 90; // Servo2 X-axis center
    joystickServo1.textContent = currentServo1;
    joystickServo2.textContent = currentServo2;
    
    document.removeEventListener('mousemove', drag);
    document.removeEventListener('mouseup', stopDrag);
    document.removeEventListener('touchmove', drag);
    document.removeEventListener('touchend', stopDrag);
    
    // Send to server with current trigger state
    sendManualControl(currentServo1, currentServo2, triggerPressed ? 43 : null);
}

// MODIFIED: Trigger control - Now works in both manual and auto mode
triggerButton.addEventListener('mousedown', triggerPress);
triggerButton.addEventListener('mouseup', triggerRelease);
triggerButton.addEventListener('mouseleave', triggerRelease);
triggerButton.addEventListener('touchstart', triggerPress, { passive: false });
triggerButton.addEventListener('touchend', triggerRelease);
triggerButton.addEventListener('touchcancel', triggerRelease);

function triggerPress(e) {
    e.preventDefault();
    if (!triggerPressed) {
        triggerPressed = true;
        triggerButton.classList.add('active');
        triggerStatus.textContent = 'FIRING';
        triggerStatus.className = 'status-error';
        
        // MODIFIED: Works in both manual and auto mode
        if (manualMode) {
            // Use current joystick positions when in manual mode
            sendManualControl(currentServo1, currentServo2, 43);
        } else if (autoMode) {
            // Send trigger command for auto mode
            sendTriggerCommand('press');
        }
    }
}

function triggerRelease(e) {
    if (e) e.preventDefault();
    if (triggerPressed) {
        triggerPressed = false;
        triggerButton.classList.remove('active');
        triggerStatus.textContent = 'SAFE';
        triggerStatus.className = 'status-item';
        
        // MODIFIED: Works in both manual and auto mode
        if (manualMode) {
            // Use current joystick positions when in manual mode
            sendManualControl(currentServo1, currentServo2, 0);
        } else if (autoMode) {
            // Send trigger release command for auto mode
            sendTriggerCommand('release');
        }
    }
}

// NEW: Separate trigger command function for auto mode
function sendTriggerCommand(action) {
    fetch('/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: action })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateServoPositions(data.positions);
            console.log(`Trigger ${action} command sent in auto mode`);
        }
    })
    .catch(console.error);
}

// Manual control communication - MODIFIED to handle concurrent operations
function sendManualControl(servo1, servo2, servo3) {
    if (!manualMode) return;
    
    fetch('/manual_control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            servo1: servo1,  // Y-axis (pin 21)
            servo2: servo2,  // X-axis (pin 19) 
            servo3: servo3   // Trigger (pin 18)
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateServoPositions(data.positions);
        }
    })
    .catch(console.error);
}

// Update servo position displays
function updateServoPositions(positions) {
    servo1Pos.textContent = positions.servo1;
    servo2Pos.textContent = positions.servo2;
    servo3Pos.textContent = positions.servo3;
    s1Pos.textContent = positions.servo1 + '°';
    s2Pos.textContent = positions.servo2 + '°';
    s3Pos.textContent = positions.servo3 + '°';
}

// Status update
function updateStatus() {
    fetch('/status')
    .then(response => response.json())
    .then(data => {
        updateServoPositions(data.servo_positions);
        
        // Update model status
        if (data.current_model) {
            currentModelStatus.textContent = data.current_model;
            // Update model select dropdown
            modelSelect.value = data.current_model;
        } else {
            currentModelStatus.textContent = 'None';
        }
        
        // Update connection status
        if (data.serial_connected) {
            connectionStatus.textContent = 'Connected';
            connectionStatus.className = 'status-item';
            connectionIndicator.className = data.detection_enabled ? 
                'connection-indicator detecting' : 'connection-indicator connected';
        } else {
            connectionStatus.textContent = 'Disconnected';
            connectionStatus.className = 'status-error';
            connectionIndicator.className = 'connection-indicator disconnected';
        }
        
        // Sync modes
        manualMode = data.manual_mode;
        autoMode = data.auto_mode;
        detectionEnabled = data.detection_enabled;
        updateModeUI();
    })
    .catch(() => {
        connectionStatus.textContent = 'Error';
        connectionStatus.className = 'status-error';
        connectionIndicator.className = 'connection-indicator disconnected';
    });
}

// Keyboard support - MODIFIED: Works in both manual and auto mode + Arrow key joystick control
let keyboardControlActive = false;

document.addEventListener('keydown', (e) => {
    // Space bar for trigger - works in both modes
    if (e.code === 'Space' && !triggerPressed) {
        e.preventDefault();
        triggerPress(e);
        return;
    }
    
    // Arrow keys for joystick control - only works in manual mode
    if (manualMode && !isDragging) {
        let stepSize = 2; // Degrees per step
        let servo1Change = 0;
        let servo2Change = 0;
        let keyHandled = false;
        
        switch(e.code) {
            case 'ArrowUp':
                servo1Change = -stepSize; // Up = smaller angle
                keyHandled = true;
                break;
            case 'ArrowDown':
                servo1Change = stepSize; // Down = bigger angle
                keyHandled = true;
                break;
            case 'ArrowLeft':
                servo2Change = stepSize; // Left = bigger angle (natural control)
                keyHandled = true;
                break;
            case 'ArrowRight':
                servo2Change = -stepSize; // Right = smaller angle (natural control)
                keyHandled = true;
                break;
        }
        
        if (keyHandled) {
            e.preventDefault();
            keyboardControlActive = true;
            
            // Calculate new positions with bounds checking
            let newServo1 = Math.max(0, Math.min(180, currentServo1 + servo1Change));
            let newServo2 = Math.max(0, Math.min(180, currentServo2 + servo2Change));
            
            // Update current positions
            currentServo1 = newServo1;
            currentServo2 = newServo2;
            
            // Update display
            joystickServo1.textContent = currentServo1;
            joystickServo2.textContent = currentServo2;
            
            // Update joystick visual position
            updateJoystickVisualPosition();
            
            // Send to server
            sendManualControl(currentServo1, currentServo2, triggerPressed ? 43 : 0);
            
            console.log(`Keyboard control: Servo1=${currentServo1}°, Servo2=${currentServo2}°`);
        }
    }
});

document.addEventListener('keyup', (e) => {
    if (e.code === 'Space' && triggerPressed) {
        e.preventDefault();
        triggerRelease();
    }
});

// NEW: Update joystick visual position based on servo angles
function updateJoystickVisualPosition() {
    const maxDistance = 125;
    
    // Convert servo angles back to joystick position
    // Servo1 (Y-axis): 90 + (y / maxDistance) * 90 -> y = (servo1 - 90) * maxDistance / 90
    // Servo2 (X-axis): 90 - (x / maxDistance) * 90 -> x = (90 - servo2) * maxDistance / 90
    
    const y = ((currentServo1 - 90) * maxDistance) / 90;
    const x = ((90 - currentServo2) * maxDistance) / 90;
    
    // Constrain to boundaries
    const constrainedX = Math.max(-maxDistance, Math.min(maxDistance, x));
    const constrainedY = Math.max(-maxDistance, Math.min(maxDistance, y));
    
    // Update joystick visual position
    joystick.style.transform = `translate(${constrainedX - 50}px, ${constrainedY - 50}px)`;
    
    console.log(`Joystick visual updated: x=${constrainedX}, y=${constrainedY}`);
}

// Prevent context menu and zoom
document.addEventListener('contextmenu', e => e.preventDefault());
document.addEventListener('touchstart', e => {
    if (e.touches.length > 1) {
        e.preventDefault();
    }
}, { passive: false });

// Set current year in footer
document.getElementById('currentYear').textContent = new Date().getFullYear();

// Initialize
updateStatus();
setInterval(updateStatus, 2000);

console.log('Flask Servo Controller initialized - Maximum Precision UI Design');
console.log('Ultra-Precision Joystick: Extra large size (350x350px) with 100px joystick knob');
console.log('Enhanced Range: 125px movement radius for ultra-smooth servo control');
console.log('Servo1 (Pin 21): Y-axis control - DOWN=bigger angle, UP=smaller angle');
console.log('Servo2 (Pin 19): X-axis control (left/right joystick movement)');
console.log('Model Selection: Dynamic YOLO model switching capability added');
console.log('MODIFICATION: Trigger button now works in both manual and auto mode');
console.log('MODIFICATION: Wake word activation no longer resets servo positions');

// Voice Control JavaScript

class AudioManager {
    constructor() {
        this.audioPath = '/static/sound/';
        this.audioIndicator = document.getElementById('audioIndicator');
        this.currentAudio = null;
        
        // Preload audio files for better performance
        this.preloadAudioFiles();
        console.log('AudioManager initialized with path:', this.audioPath);
    }

    preloadAudioFiles() {
        const audioFiles = [
            'opening.mp3',
            'mode auto.mp3',
            'mode manual.mp3',
            'target diubah.mp3',
            'tembakan.mp3'
        ];

        this.audioCache = {};
        
        audioFiles.forEach(file => {
            const audio = new Audio();
            const fullPath = this.audioPath + file;
            audio.src = fullPath;
            audio.preload = 'auto';
            audio.volume = 0.8; // Set volume level
            
            console.log(`Preloading audio: ${fullPath}`);
            
            // Handle loading events
            audio.addEventListener('loadeddata', () => {
                console.log(`Audio file loaded successfully: ${file}`);
            });
            
            audio.addEventListener('error', (e) => {
                console.error(`Failed to load audio file: ${file}`, e);
                console.error(`Full path attempted: ${fullPath}`);
            });
            
            audio.addEventListener('canplaythrough', () => {
                console.log(`Audio file ready to play: ${file}`);
            });
            
            this.audioCache[file] = audio;
        });
        
        // Test if audio files are accessible after a delay
        setTimeout(() => this.testAudioFiles(), 2000);
    }

    testAudioFiles() {
        console.log('Testing audio file accessibility...');
        Object.keys(this.audioCache).forEach(filename => {
            const audio = this.audioCache[filename];
            console.log(`${filename}: readyState=${audio.readyState}, duration=${audio.duration}`);
        });
    }

    playAudio(filename) {
        return new Promise((resolve, reject) => {
            try {
                console.log(`Attempting to play audio: ${filename}`);
                
                // Stop any currently playing audio
                if (this.currentAudio) {
                    this.currentAudio.pause();
                    this.currentAudio.currentTime = 0;
                }

                // Get audio from cache or create new
                let audio = this.audioCache[filename];
                if (!audio) {
                    console.log(`Creating new audio instance for: ${filename}`);
                    const fullPath = this.audioPath + filename;
                    audio = new Audio(fullPath);
                    audio.volume = 0.8;
                    this.audioCache[filename] = audio;
                }

                this.currentAudio = audio;
                
                // Show audio indicator
                this.showAudioIndicator(`Playing: ${filename}`);

                // Set up event handlers
                const onEnded = () => {
                    console.log(`Audio finished: ${filename}`);
                    this.hideAudioIndicator();
                    this.currentAudio = null;
                    audio.removeEventListener('ended', onEnded);
                    audio.removeEventListener('error', onError);
                    audio.removeEventListener('canplay', onCanPlay);
                    resolve();
                };

                const onError = (e) => {
                    console.error(`Error playing audio ${filename}:`, e);
                    console.error('Audio error details:', {
                        code: e.target?.error?.code,
                        message: e.target?.error?.message,
                        src: audio.src,
                        readyState: audio.readyState
                    });
                    this.hideAudioIndicator();
                    this.currentAudio = null;
                    audio.removeEventListener('ended', onEnded);
                    audio.removeEventListener('error', onError);
                    audio.removeEventListener('canplay', onCanPlay);
                    reject(e);
                };

                const onCanPlay = () => {
                    console.log(`Audio can play: ${filename}`);
                };

                audio.addEventListener('ended', onEnded);
                audio.addEventListener('error', onError);
                audio.addEventListener('canplay', onCanPlay);

                // Reset and play
                audio.currentTime = 0;
                
                // Try to play with better error handling
                const playPromise = audio.play();
                
                if (playPromise !== undefined) {
                    playPromise
                        .then(() => {
                            console.log(`Successfully started playing: ${filename}`);
                        })
                        .catch((error) => {
                            console.error(`Play promise rejected for ${filename}:`, error);
                            
                            // Try to handle autoplay policy issues
                            if (error.name === 'NotAllowedError') {
                                console.log('Autoplay blocked - user interaction may be required');
                                this.showAudioIndicator('Audio blocked - click anywhere to enable');
                                
                                // Add one-time click handler to enable audio
                                const enableAudio = () => {
                                    audio.play()
                                        .then(() => {
                                            console.log(`Audio enabled and playing: ${filename}`);
                                            this.showAudioIndicator(`Playing: ${filename}`);
                                        })
                                        .catch(console.error);
                                    document.removeEventListener('click', enableAudio);
                                };
                                document.addEventListener('click', enableAudio);
                            }
                            
                            onError({ target: { error: error } });
                        });
                }

                console.log(`Audio play initiated for: ${filename}`);
                
            } catch (error) {
                console.error(`Error setting up audio ${filename}:`, error);
                this.hideAudioIndicator();
                reject(error);
            }
        });
    }

    showAudioIndicator(message) {
        this.audioIndicator.textContent = `Audio: ${message}`;
        this.audioIndicator.classList.add('show');
    }

    hideAudioIndicator() {
        this.audioIndicator.classList.remove('show');
    }

    stopCurrentAudio() {
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio.currentTime = 0;
            this.currentAudio = null;
            this.hideAudioIndicator();
        }
    }
}

class VoiceController {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.isAwaitingCommand = false;
        this.commandTimeout = null;
        this.lastValidCommandTime = null;
        this.voiceBtn = document.getElementById('voiceBtn');
        this.voiceStatus = document.getElementById('voiceStatus');
        
        // Initialize audio manager
        this.audioManager = new AudioManager();
        
        this.init();
        this.setupEventListeners();
    }

    init() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            
            this.recognition.continuous = true;
            this.recognition.interimResults = false;
            this.recognition.lang = 'id-ID';
            this.recognition.maxAlternatives = 1;
            
            this.setupRecognitionEvents();
            this.updateStatus('Voice ready - Click to start continuous listening', '');
        } else {
            this.updateStatus('Browser tidak mendukung voice recognition', 'error');
            this.voiceBtn.disabled = true;
        }
    }

    setupEventListeners() {
        this.voiceBtn.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('Voice button clicked, isListening:', this.isListening);
            
            if (this.isListening) {
                this.stopContinuousListening();
            } else {
                this.requestMicrophonePermission().then(() => {
                    this.startContinuousListening();
                }).catch((error) => {
                    console.error('Microphone permission denied:', error);
                    this.updateStatus('Izin mikrofon diperlukan', 'error');
                });
            }
        });
    }

    async requestMicrophonePermission() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop());
            return true;
        } catch (error) {
            throw error;
        }
    }

    setupRecognitionEvents() {
        this.recognition.onstart = () => {
            console.log('Continuous speech recognition started');
            this.isListening = true;
            this.voiceBtn.classList.add('listening');
            this.voiceBtn.textContent = 'STOP';
            this.updateStatus('Listening continuously... Say "Hei" to activate', 'listening');
        };

        this.recognition.onresult = (event) => {
            // Skip processing if in cooldown period
            if (isVoiceCooldown) {
                console.log('Voice cooldown active, ignoring input');
                return;
            }
            
            const lastResultIndex = event.results.length - 1;
            const transcript = event.results[lastResultIndex][0].transcript.toLowerCase().trim();
            const confidence = event.results[lastResultIndex][0].confidence;
            
            console.log('Voice input:', transcript, 'Confidence:', confidence);
            
            this.updateStatus(`Heard: "${transcript}"`, 'processing');
            
            setTimeout(() => {
                this.processVoiceCommand(transcript);
            }, 500);
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            let errorMsg = 'Error tidak dikenal';
            
            switch(event.error) {
                case 'no-speech':
                    console.log('No speech detected, continuing to listen...');
                    return;
                case 'audio-capture':
                    errorMsg = 'Mikrofon tidak dapat diakses';
                    break;
                case 'not-allowed':
                    errorMsg = 'Izin mikrofon ditolak';
                    break;
                case 'network':
                    errorMsg = 'Koneksi internet bermasalah';
                    break;
                default:
                    errorMsg = `Error: ${event.error}`;
            }
            
            this.updateStatus(errorMsg, 'error');
            
            if (event.error !== 'not-allowed' && event.error !== 'audio-capture') {
                setTimeout(() => {
                    if (this.isListening) {
                        console.log('Attempting to restart recognition after error...');
                        this.restartRecognition();
                    }
                }, 2000);
            } else {
                this.resetVoiceButton();
            }
        };

        this.recognition.onend = () => {
            console.log('Speech recognition ended');
            
            if (this.isListening) {
                console.log('Auto-restarting continuous recognition...');
                setTimeout(() => {
                    this.restartRecognition();
                }, 100);
            }
        };
    }

    startContinuousListening() {
        if (this.recognition && !this.isListening) {
            try {
                console.log('Starting continuous speech recognition...');
                this.recognition.start();
            } catch (error) {
                console.error('Error starting recognition:', error);
                this.updateStatus('Gagal memulai voice recognition', 'error');
            }
        }
    }

    stopContinuousListening() {
        if (this.recognition && this.isListening) {
            console.log('Stopping continuous speech recognition...');
            this.isListening = false;
            this.recognition.stop();
            
            if (this.commandTimeout) {
                clearTimeout(this.commandTimeout);
                this.commandTimeout = null;
            }
            
            this.isAwaitingCommand = false;
            this.resetVoiceButton();
        }
    }

    restartRecognition() {
        if (this.isListening && this.recognition) {
            try {
                this.recognition.start();
            } catch (error) {
                console.error('Error restarting recognition:', error);
                this.updateStatus('Gagal restart voice recognition', 'error');
                this.resetVoiceButton();
            }
        }
    }

    resetVoiceButton() {
        this.isListening = false;
        this.voiceBtn.classList.remove('listening', 'processing');
        this.voiceBtn.textContent = 'VOICE';
        
        if (!this.isAwaitingCommand) {
            this.updateStatus('Ready for Hei command', '');
        }
    }

    async processVoiceCommand(transcript) {
        this.voiceBtn.classList.add('processing');
        
        console.log('Processing command:', transcript);
        console.log('Current awaiting command state:', this.isAwaitingCommand);
        
        // Check for wake word first
        if (!this.isAwaitingCommand) {
            if (this.containsWakeWord(transcript)) {
                await this.activateCommandMode();
                return;
            } else {
                this.updateStatus(`Wake word not detected. Say "Hei"`, 'error');
                console.log('Wake word not detected in:', transcript);
                setTimeout(() => {
                    this.updateStatus('Voice ready - Click button to start', '');
                }, 3000);
                return;
            }
        }

        // Process commands when in command mode
        await this.executeCommand(transcript);
    }

    containsWakeWord(transcript) {
        const normalizedTranscript = transcript
            .toLowerCase()
            .replace(/\s+/g, ' ')
            .trim();
        
        const wakeWords = [
            'hei',
            'hey'
        ];

        
        console.log('Checking wake words against:', normalizedTranscript);
        
        // Check exact matches first
        for (let wake of wakeWords) {
            if (normalizedTranscript === wake || normalizedTranscript.includes(wake)) {
                console.log('Wake word found (exact):', wake);
                return true;
            }
        }
        
        // Check pattern matches for numbers with spaces
        const patterns = [
            /.*m\s*1\s*7\s*7.*/,
            /.*m\s*satu\s*tujuh\s*tujuh.*/,
            /.*halo.*m\s*1\s*7\s*7.*/,
            /.*halo.*m\s*satu\s*tujuh\s*tujuh.*/,
            /.*oke.*1\s*7\s*7.*/,
        ];
        
        for (let pattern of patterns) {
            if (pattern.test(normalizedTranscript)) {
                console.log('Wake word found (pattern):', pattern, 'in:', normalizedTranscript);
                return true;
            }
        }
        
        console.log('No wake word found in:', normalizedTranscript);
        return false;
    }

    async activateCommandMode() {
        this.isAwaitingCommand = true;
        this.lastValidCommandTime = Date.now();
        this.updateStatus('Command mode active - Say your commands', 'success');
        console.log('Command mode activated - servo positions maintained');
        
        // Play opening sound
        try {
            await this.audioManager.playAudio('opening.mp3');
            console.log('Opening sound played successfully');
        } catch (error) {
            console.error('Error playing opening sound:', error);
        }
        
        this.startCommandTimeout();
    }

    startCommandTimeout() {
        if (this.commandTimeout) {
            clearTimeout(this.commandTimeout);
        }
        
        this.commandTimeout = setTimeout(() => {
            const timeSinceLastCommand = Date.now() - this.lastValidCommandTime;
            console.log('Checking command timeout. Time since last command:', timeSinceLastCommand, 'ms');
            
            if (this.isAwaitingCommand && timeSinceLastCommand >= 10000) {
                this.deactivateCommandMode();
            }
        }, 10000);
    }

    extendCommandTimeout() {
        this.lastValidCommandTime = Date.now();
        console.log('Command timeout extended. Last valid command time updated.');
        this.startCommandTimeout();
        
        if (this.isAwaitingCommand && this.isListening) {
            this.updateStatus('Ready for next command', 'success');
        }
    }

    deactivateCommandMode() {
        this.isAwaitingCommand = false;
        if (this.commandTimeout) {
            clearTimeout(this.commandTimeout);
            this.commandTimeout = null;
        }
        
        if (this.isListening) {
            this.updateStatus('Command timeout - Listening for "Hei"', 'listening');
        } else {
            this.updateStatus('Command timeout - Click voice to start', '');
        }
        console.log('Command mode deactivated due to timeout');
    }

    async executeCommand(transcript) {
        let commandExecuted = false;
        let audioFile = null;
        
        console.log('Executing command:', transcript);

        // Mode selection commands
        if (transcript.includes('aktifkan mode auto') || 
            transcript.includes('mode auto') || 
            transcript.includes('auto mode')) {
            this.switchToAutoMode();
            commandExecuted = true;
            audioFile = 'mode auto.mp3';
            console.log('Switching to auto mode');
        } 
        else if (transcript.includes('aktifkan mode manual') || 
                 transcript.includes('mode manual') || 
                 transcript.includes('manual mode')) {
            this.switchToManualMode();
            commandExecuted = true;
            audioFile = 'mode manual.mp3';
            console.log('Switching to manual mode');
        }
        
        // MODIFIED: Fire control commands - Auto-release after 2 seconds
        else if (
            transcript.includes('tembak') || 
            transcript.includes('nembak') || 
            transcript.includes('fire')
        ) {
            await this.voiceFireCommand();
            commandExecuted = true;
            // Note: Audio will be played after auto-release
            console.log('Voice fire command executed');
        }

        
        // Model selection commands
        else if (transcript.includes('pilih model satu') || 
                 transcript.includes('model satu') || 
                 transcript.includes('satu') ||
                 transcript.includes('1') ||
                 transcript.includes('wajah')) {
            this.selectModel(0);
            commandExecuted = true;
            audioFile = 'target diubah.mp3';
            console.log('Model 1 selected');
        } 
        else if (transcript.includes('pilih model dua') || 
                 transcript.includes('model dua') || 
                 transcript.includes('dua') ||
                 transcript.includes('2') ||
                 transcript.includes('tangan')) {
            this.selectModel(1);
            commandExecuted = true;
            audioFile = 'target diubah.mp3';
            console.log('Model 2 selected');
        } 
        else if (transcript.includes('pilih model tiga') || 
                 transcript.includes('model tiga') || 
                 transcript.includes('tiga') ||
                 transcript.includes('3') ||
                 transcript.includes('bola merah')) {
            this.selectModel(2);
            commandExecuted = true;
            audioFile = 'target diubah.mp3';
            console.log('Model 3 selected');
        }
        else if (transcript.includes('pilih model empat') || 
                 transcript.includes('model empat') || 
                 transcript.includes('empat') ||
                 transcript.includes('4')) {
            this.selectModel(3);
            commandExecuted = true;
            audioFile = 'target diubah.mp3';
            console.log('Model 4 selected');
        }

        // Play audio feedback and update status (except for fire command)
        if (commandExecuted) {
            if (!transcript.includes('tembak') && !transcript.includes('fire')) {
                this.updateStatus('Perintah berhasil dijalankan', 'success');
                console.log('Valid command executed, timeout will be extended');
                
                // Play corresponding audio
                if (audioFile) {
                    try {
                        await this.audioManager.playAudio(audioFile);
                        console.log(`Audio feedback played: ${audioFile}`);
                    } catch (error) {
                        console.error(`Error playing audio feedback: ${audioFile}`, error);
                    }
                }
                
                // Start voice cooldown period
                this.startVoiceCooldown();
                
                // Extend command timeout for valid commands
                this.extendCommandTimeout();
            }
        } else {
            this.updateStatus(`Perintah "${transcript}" tidak dikenali`, 'error');
            console.log('Invalid command, timeout will NOT be extended');
            setTimeout(() => {
                if (this.isAwaitingCommand && this.isListening) {
                    this.updateStatus('Try: "mode auto", "tembak", "satu", etc.', 'success');
                }
            }, 2000);
        }

        return commandExecuted;
    }

    // NEW: Start voice cooldown period to prevent audio feedback detection
    startVoiceCooldown() {
        // Set cooldown flag
        isVoiceCooldown = true;
        this.updateStatus('Voice cooldown active (3s)', 'processing');
        console.log('Voice cooldown started for 3 seconds');
        
        // Clear any existing cooldown timeout
        if (voiceCooldownTimeout) {
            clearTimeout(voiceCooldownTimeout);
        }
        
        // Set timeout to end cooldown
        voiceCooldownTimeout = setTimeout(() => {
            isVoiceCooldown = false;
            console.log('Voice cooldown ended');
            
            if (this.isAwaitingCommand && this.isListening) {
                this.updateStatus('Ready for next command', 'success');
            }
        }, 2000); // 2 second cooldown
    }

    // MODIFIED: Voice fire command with auto-release and UI feedback - works in both modes
    async voiceFireCommand() {
        this.updateStatus('Voice fire activated - 2 second hold', 'success');
        
        // Clear any existing voice fire timeout
        if (voiceFireTimeout) {
            clearTimeout(voiceFireTimeout);
            voiceFireTimeout = null;
        }
        
        // Update button UI to show firing state
        const triggerButton = document.getElementById('triggerButton');
        const triggerStatus = document.getElementById('triggerStatus');
        
        if (triggerButton && triggerStatus) {
            triggerButton.classList.add('active');
            triggerStatus.textContent = 'VOICE FIRING';
            triggerStatus.className = 'status-error';
            console.log('Voice fire: Button UI updated to active state');
        }
        
        // Send fire command to server - works in both manual and auto mode
        try {
            if (manualMode) {
                // In manual mode, use manual control with current positions
                const response = await fetch('/manual_control', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        servo1: currentServo1,
                        servo2: currentServo2,
                        servo3: 43
                    })
                });
                
                const data = await response.json();
                if (data.success) {
                    updateServoPositions(data.positions);
                    console.log('Voice fire: Manual mode - Servo 3 moved to 43 degrees');
                }
            } else if (autoMode) {
                // In auto mode, use trigger endpoint
                const response = await fetch('/trigger', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'press' })
                });
                
                const data = await response.json();
                if (data.success) {
                    updateServoPositions(data.positions);
                    console.log('Voice fire: Auto mode - Servo 3 moved to 43 degrees');
                }
            }
        } catch (error) {
            console.error('Error sending voice fire command:', error);
        }
        
        // Set timeout to auto-release after 2 seconds
        voiceFireTimeout = setTimeout(async () => {
            console.log('Voice fire: Auto-releasing after 2 seconds');
            
            // Send release command to server - works in both modes
            try {
                if (manualMode) {
                    // In manual mode, use manual control
                    const response = await fetch('/manual_control', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            servo1: currentServo1,
                            servo2: currentServo2,
                            servo3: 0
                        })
                    });
                    
                    const data = await response.json();
                    if (data.success) {
                        updateServoPositions(data.positions);
                        console.log('Voice fire: Manual mode - Servo 3 returned to 0 degrees');
                    }
                } else if (autoMode) {
                    // In auto mode, use trigger endpoint
                    const response = await fetch('/trigger', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ action: 'release' })
                    });
                    
                    const data = await response.json();
                    if (data.success) {
                        updateServoPositions(data.positions);
                        console.log('Voice fire: Auto mode - Servo 3 returned to 0 degrees');
                    }
                }
                
                // Update button UI back to normal state
                if (triggerButton && triggerStatus) {
                    triggerButton.classList.remove('active');
                    triggerStatus.textContent = 'SAFE';
                    triggerStatus.className = 'status-item';
                    console.log('Voice fire: Button UI restored to normal state');
                }
                
                // Play audio AFTER servo returns to 0 position and UI is updated
                setTimeout(async () => {
                    try {
                        await this.audioManager.playAudio('tembakan.mp3');
                        console.log('Voice fire: Audio feedback played after release');
                    } catch (error) {
                        console.error('Error playing fire audio:', error);
                    }
                    
                    // Start voice cooldown period after fire command
                    this.startVoiceCooldown();
                    
                    // Update status and extend timeout
                    this.updateStatus('Voice fire completed', 'success');
                    this.extendCommandTimeout();
                }, 150); // Small delay to ensure servo has moved and UI updated
                
            } catch (error) {
                console.error('Error sending voice release command:', error);
                
                // Restore button UI even if there's an error
                if (triggerButton && triggerStatus) {
                    triggerButton.classList.remove('active');
                    triggerStatus.textContent = 'SAFE';
                    triggerStatus.className = 'status-item';
                    console.log('Voice fire: Button UI restored after error');
                }
            }
            
            voiceFireTimeout = null;
        }, 2000); // 2 second timeout
    }

    switchToAutoMode() {
        const autoBtn = document.getElementById('autoModeBtn');
        const manualBtn = document.getElementById('manualModeBtn');
        
        autoBtn.classList.add('active');
        manualBtn.classList.remove('active');
        
        if (typeof window.switchToAutoMode === 'function') {
            window.switchToAutoMode();
        } else {
            autoBtn.click();
        }
    }

    switchToManualMode() {
        const autoBtn = document.getElementById('autoModeBtn');
        const manualBtn = document.getElementById('manualModeBtn');
        
        manualBtn.classList.add('active');
        autoBtn.classList.remove('active');
        
        if (typeof window.switchToManualMode === 'function') {
            window.switchToManualMode();
        } else {
            manualBtn.click();
        }
    }

    selectModel(modelIndex) {
        const modelSelect = document.getElementById('modelSelect');
        console.log('Selecting model index:', modelIndex);
        console.log('Model select element:', modelSelect);
        
        if (modelSelect) {
            console.log('Available model options:', modelSelect.options.length);
            for (let i = 0; i < modelSelect.options.length; i++) {
                console.log(`Option ${i}:`, modelSelect.options[i].value, modelSelect.options[i].text);
            }
            
            // Check if model index exists
            if (modelIndex >= 0 && modelIndex < modelSelect.options.length) {
                const previousValue = modelSelect.value;
                modelSelect.selectedIndex = modelIndex;
                const newValue = modelSelect.value;
                
                console.log('Model changed from:', previousValue, 'to:', newValue);
                
                // Create and dispatch change event
                const changeEvent = new Event('change', {
                    bubbles: true,
                    cancelable: true,
                });
                
                // Also dispatch input event for better compatibility
                const inputEvent = new Event('input', {
                    bubbles: true,
                    cancelable: true,
                });
                
                // Dispatch both events
                modelSelect.dispatchEvent(changeEvent);
                modelSelect.dispatchEvent(inputEvent);
                
                console.log('Model selection events dispatched for index:', modelIndex);
                
                // Verify selection
                setTimeout(() => {
                    console.log('Final selected index:', modelSelect.selectedIndex);
                    console.log('Final selected value:', modelSelect.value);
                }, 100);
                
                return true;
            } else {
                console.error('Model index out of range:', modelIndex, 'Available:', modelSelect.options.length);
                return false;
            }
        } else {
            console.error('Model select element not found');
            return false;
        }
    }

    updateStatus(message, type = '') {
        this.voiceStatus.textContent = message;
        this.voiceStatus.className = `voice-status ${type}`;
    }
}

// Initialize voice controller when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing Voice Controller...');
    
    // Wait a bit for other scripts to load
    setTimeout(() => {
        window.voiceController = new VoiceController();
        console.log('Voice Controller initialized');
    }, 1000);
});

// Tambahkan kode berikut untuk menangani upload model, refresh, dan quit
document.addEventListener('DOMContentLoaded', function() {
    // Modal elements
    const modal = document.getElementById('uploadModal');
    const uploadBtn = document.getElementById('uploadModelBtn');
    const closeBtn = document.querySelector('.close');
    const cancelBtn = document.querySelector('.cancel-btn');
    const uploadForm = document.getElementById('uploadForm');
    const modelFileInput = document.getElementById('modelFile');
    const uploadProgress = document.getElementById('uploadProgress');
    const progressFill = document.querySelector('.progress-fill');
    const progressText = document.querySelector('.progress-text');
    const uploadMessage = document.getElementById('uploadMessage');
    const modelSelect = document.getElementById('modelSelect');

    // Refresh button
    document.getElementById('refreshBtn').addEventListener('click', function() {
        location.reload();
    });
    
    // Quit button
    document.getElementById('quitBtn').addEventListener('click', function() {
        if (confirm('Are you sure you want to quit the application?')) {
            fetch('/quit', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show message before closing
                    const message = document.createElement('div');
                    message.className = 'quit-message';
                    message.textContent = 'Application shutting down...';
                    document.body.appendChild(message);
                    
                    // Close after a short delay
                    setTimeout(() => {
                        window.close();
                        // Fallback if window.close() doesn't work
                        window.location.href = 'about:blank';
                    }, 2000);
                } else {
                    alert('Failed to quit: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error quitting:', error);
                alert('Error quitting: ' + error.message);
            });
        }
    });

    // Open modal
    uploadBtn.addEventListener('click', function() {
        modal.style.display = 'block';
        resetUploadForm();
    });

    // Close modal
    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);

    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            closeModal();
        }
    });

    function closeModal() {
        modal.style.display = 'none';
        resetUploadForm();
    }

    function resetUploadForm() {
        uploadForm.reset();
        uploadProgress.style.display = 'none';
        uploadMessage.style.display = 'none';
        progressFill.style.width = '0%';
        progressText.textContent = 'Uploading... 0%';
    }

    // Handle form submission
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const file = modelFileInput.files[0];
        if (!file) {
            showUploadMessage('Please select a model file', 'error');
            return;
        }

        // Validate file extension
        if (!file.name.endsWith('.pt')) {
            showUploadMessage('Only PyTorch (.pt) files are allowed', 'error');
            return;
        }

        // Create FormData for file upload
        const formData = new FormData();
        formData.append('modelFile', file);

        // Show progress
        uploadProgress.style.display = 'block';
        uploadMessage.style.display = 'none';

        // Create XMLHttpRequest for progress tracking
        const xhr = new XMLHttpRequest();

        // Track upload progress
        xhr.upload.addEventListener('progress', function(e) {
            if (e.lengthComputable) {
                const percentComplete = Math.round((e.loaded / e.total) * 100);
                progressFill.style.width = percentComplete + '%';
                progressText.textContent = `Uploading... ${percentComplete}%`;
            }
        });

        // Handle response
        xhr.addEventListener('load', function() {
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                if (response.success) {
                    showUploadMessage('Model uploaded successfully!', 'success');
                    
                    // Refresh model list
                    setTimeout(() => {
                        closeModal();
                        refreshModelList();
                    }, 1500);
                } else {
                    showUploadMessage(response.error || 'Upload failed', 'error');
                }
            } else {
                showUploadMessage('Upload failed with server error', 'error');
            }
        });

        // Handle errors
        xhr.addEventListener('error', function() {
            showUploadMessage('Upload failed due to network error', 'error');
        });

        // Send request
        xhr.open('POST', '/upload_model');
        xhr.send(formData);
    });

    function showUploadMessage(message, type) {
        uploadMessage.textContent = message;
        uploadMessage.className = 'upload-message ' + type;
        uploadMessage.style.display = 'block';
    }

    function refreshModelList() {
        fetch('/status')
        .then(response => response.json())
        .then(data => {
            // Clear current options
            modelSelect.innerHTML = '';
            
            // Add new options
            data.available_models.forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                if (model === data.current_model) {
                    option.selected = true;
                }
                modelSelect.appendChild(option);
            });
            
            // Update current model status
            document.getElementById('currentModelStatus').textContent = data.current_model || 'None';
        })
        .catch(error => {
            console.error('Error refreshing model list:', error);
        });
    }
});

// Test functions for debugging
window.testVoice = function() {
    if (window.voiceController) {
        console.log('Testing voice controller...');
        window.voiceController.updateStatus('Test mode active', 'success');
        window.voiceController.isAwaitingCommand = true;
        window.voiceController.executeCommand('mode auto');
    }
};

window.testWakeWord = function(text) {
    if (window.voiceController) {
        console.log('Testing wake word with:', text);
        const result = window.voiceController.containsWakeWord(text);
        console.log('Wake word result:', result);
        return result;
    }
};

window.testCommand = function(text) {
    if (window.voiceController) {
        console.log('Testing command processing with:', text);
        window.voiceController.isAwaitingCommand = true;
        window.voiceController.processVoiceCommand(text);
    }
};

window.testModelSelection = function(index) {
    if (window.voiceController) {
        console.log('Testing model selection with index:', index);
        const result = window.voiceController.selectModel(index);
        console.log('Model selection result:', result);
        return result;
    }
};

window.checkModelDropdown = function() {
    const modelSelect = document.getElementById('modelSelect');
    if (modelSelect) {
        console.log('Model dropdown found with', modelSelect.options.length, 'options:');
        for (let i = 0; i < modelSelect.options.length; i++) {
            console.log(`  ${i}: ${modelSelect.options[i].text} (value: ${modelSelect.options[i].value})`);
        }
        console.log('Currently selected:', modelSelect.selectedIndex, modelSelect.value);
    } else {
        console.log('Model dropdown not found');
    }
};

window.checkCommandStatus = function() {
    if (window.voiceController) {
        console.log('Command mode active:', window.voiceController.isAwaitingCommand);
        console.log('Last valid command time:', window.voiceController.lastValidCommandTime);
        console.log('Current time:', Date.now());
        if (window.voiceController.lastValidCommandTime) {
            const timeSince = Date.now() - window.voiceController.lastValidCommandTime;
            console.log('Time since last valid command:', timeSince, 'ms (', Math.round(timeSince/1000), 'seconds)');
        }
        console.log('Timeout active:', window.voiceController.commandTimeout !== null);
    }
};

window.forceCommandTimeout = function() {
    if (window.voiceController && window.voiceController.isAwaitingCommand) {
        console.log('Forcing command timeout...');
        window.voiceController.deactivateCommandMode();
    }
};

window.extendCommandTimeout = function() {
    if (window.voiceController && window.voiceController.isAwaitingCommand) {
        console.log('Manually extending command timeout...');
        window.voiceController.extendCommandTimeout();
    }
};

// Audio testing functions
window.testAudio = function(filename) {
    if (window.voiceController && window.voiceController.audioManager) {
        console.log('Testing audio playback:', filename);
        window.voiceController.audioManager.playAudio(filename)
            .then(() => console.log('Audio test completed'))
            .catch(error => console.error('Audio test failed:', error));
    }
};

window.stopAudio = function() {
    if (window.voiceController && window.voiceController.audioManager) {
        console.log('Stopping current audio...');
        window.voiceController.audioManager.stopCurrentAudio();
    }
};

// Test voice fire command
window.testVoiceFire = function() {
    if (window.voiceController && window.voiceController.isAwaitingCommand) {
        console.log('Testing voice fire command...');
        window.voiceController.voiceFireCommand();
    } else {
        console.log('Voice controller not ready or not in command mode');
    }
};