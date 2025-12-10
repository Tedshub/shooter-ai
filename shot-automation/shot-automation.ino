#include <ESP32Servo.h>

// Servo objects
Servo servo1; // Servo 1 - sumbu Y
Servo servo2; // Servo 2 - sumbu X  
Servo servo3; // Servo 3 - trigger

// Pin definitions
const int servo1Pin = 21; // Servo Y
const int servo2Pin = 19; // Servo X
const int servo3Pin = 18; // Servo trigger

// Current positions
int currentServo1Pos = 90; // Posisi awal sumbu Y
int currentServo2Pos = 90; // Posisi awal sumbu X
int currentServo3Pos = 0;  // Posisi awal trigger

// Batasan sudut servo
const int minAngle = 0;
const int maxAngle = 180;

// Serial command buffer
String inputString = "";
boolean stringComplete = false;

void setup() {
  Serial.begin(115200);
  Serial.println();
  Serial.println("==============================================");
  Serial.println("  ESP32 Flask Servo Controller (V4.0)       ");
  Serial.println("==============================================");
  
  // Attach servos to pins
  Serial.println("Initializing servos...");
  servo1.attach(servo1Pin);
  servo2.attach(servo2Pin);
  servo3.attach(servo3Pin);
  
  // Set initial positions
  servo1.write(currentServo1Pos);
  servo2.write(currentServo2Pos);
  servo3.write(currentServo3Pos);
  
  Serial.println("✓ Servo 1 (Pin 21) initialized at 90°");
  Serial.println("✓ Servo 2 (Pin 19) initialized at 90°");
  Serial.println("✓ Servo 3 (Pin 18) initialized at 0°");
  Serial.println("✓ Serial communication ready on COM5");
  Serial.println("==============================================");
  Serial.println();
  Serial.println("📡 Ready to receive commands from Python Flask");
  Serial.println("Command format: S1,90,S2,120,S3,45");
  Serial.println("Example: S1,90,S2,60");
  Serial.println();
  
  // Reserve 200 bytes for the inputString
  inputString.reserve(200);
}

void loop() {
  // Check for serial commands
  if (Serial.available()) {
    while (Serial.available()) {
      char inChar = (char)Serial.read();
      inputString += inChar;
      
      // If we get a newline, set a flag to process the command
      if (inChar == '\n') {
        stringComplete = true;
        break;
      }
    }
  }
  
  // Process complete command
  if (stringComplete) {
    processFlaskCommand(inputString);
    inputString = "";
    stringComplete = false;
  }
  
  // Small delay to prevent overwhelming the serial buffer
  delay(5); // Reduced delay for better responsiveness
}

void processFlaskCommand(String command) {
  command.trim(); // Remove whitespace and newlines
  
  Serial.print("Flask command: ");
  Serial.println(command);
  
  if (command.length() == 0) {
    Serial.println("Empty command received");
    return;
  }
  
  // Parse Flask format: S1,90,S2,120,S3,45
  int index = 0;
  bool commandProcessed = false;
  
  while (index < command.length()) {
    // Find servo identifier
    int commaIndex = command.indexOf(',', index);
    if (commaIndex == -1) break;
    
    String servoId = command.substring(index, commaIndex);
    index = commaIndex + 1;
    
    // Find angle value
    commaIndex = command.indexOf(',', index);
    String angleStr;
    if (commaIndex == -1) {
      angleStr = command.substring(index);
      index = command.length();
    } else {
      angleStr = command.substring(index, commaIndex);
      index = commaIndex + 1;
    }
    
    // Process servo command
    int angle = angleStr.toInt();
    
    // Validate angle range
    if (angle < minAngle || angle > maxAngle) {
      Serial.print("Invalid angle for ");
      Serial.print(servoId);
      Serial.print(": ");
      Serial.print(angle);
      Serial.println("°");
      continue;
    }
    
    // Move servo
    if (servoId == "S1") {
      currentServo1Pos = angle;
      servo1.write(currentServo1Pos);
      Serial.print("Servo 1 (Y-Axis) → ");
      Serial.print(currentServo1Pos);
      Serial.println("°");
      commandProcessed = true;
      
    } else if (servoId == "S2") {
      currentServo2Pos = angle;
      servo2.write(currentServo2Pos);
      Serial.print("Servo 2 (X-Axis) → ");
      Serial.print(currentServo2Pos);
      Serial.println("°");
      commandProcessed = true;
      
    } else if (servoId == "S3") {
      currentServo3Pos = angle;
      servo3.write(currentServo3Pos);
      Serial.print("Servo 3 (Trigger) → ");
      Serial.print(currentServo3Pos);
      Serial.println("°");
      commandProcessed = true;
    }
    
    // Small delay between servo movements for stability
    if (commandProcessed) {
      delay(15);
    }
  }
  
  if (commandProcessed) {
    // Send confirmation back to Flask
    Serial.print("Positions: S1:");
    Serial.print(currentServo1Pos);
    Serial.print("° S2:");
    Serial.print(currentServo2Pos);
    Serial.print("° S3:");
    Serial.print(currentServo3Pos);
    Serial.println("°");
  }
  
  Serial.println();
}

// Function to reset all servos to initial position
void resetServos() {
  Serial.println("Resetting all servos to initial positions...");
  
  currentServo1Pos = 90;
  currentServo2Pos = 90;
  currentServo3Pos = 0;
  
  servo1.write(currentServo1Pos);
  delay(15);
  servo2.write(currentServo2Pos);
  delay(15);
  servo3.write(currentServo3Pos);
  
  Serial.println("Reset complete: S1:90° S2:90° S3:0°");
}

// Function to get current positions
void getCurrentPositions() {
  Serial.print("Current positions - S1:");
  Serial.print(currentServo1Pos);
  Serial.print("° S2:");
  Serial.print(currentServo2Pos);
  Serial.print("° S3:");
  Serial.print(currentServo3Pos);
  Serial.println("°");
}