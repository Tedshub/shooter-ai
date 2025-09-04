import serial.tools.list_ports
import serial
import time

def scan_available_ports():
    """
    Scan semua port COM yang tersedia
    """
    print("🔍 Scanning available COM ports...")
    ports = serial.tools.list_ports.comports()
    
    available_ports = []
    
    if not ports:
        print("❌ No COM ports found!")
        return available_ports
    
    print("\n📋 Available COM Ports:")
    print("-" * 50)
    
    for port in ports:
        print(f"Port: {port.device}")
        print(f"Description: {port.description}")
        print(f"Hardware ID: {port.hwid}")
        
        # Test if port can be opened
        try:
            test_serial = serial.Serial(port.device, 115200, timeout=1)
            test_serial.close()
            status = "✅ Available"
            available_ports.append(port.device)
        except Exception as e:
            status = f"❌ Busy/Error: {str(e)[:50]}..."
            
        print(f"Status: {status}")
        print("-" * 50)
    
    return available_ports

def test_esp32_connection(port):
    """
    Test koneksi ke ESP32 di port tertentu
    """
    print(f"\n🔌 Testing ESP32 connection on {port}...")
    
    try:
        ser = serial.Serial(port, 115200, timeout=2)
        time.sleep(2)  # Wait for ESP32 to initialize
        
        # Send test command
        test_cmd = "S1,90,S2,90\n"
        ser.write(test_cmd.encode())
        ser.flush()
        
        # Wait for response
        time.sleep(0.5)
        response = ""
        while ser.in_waiting > 0:
            response += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
        
        ser.close()
        
        if response:
            print(f"✅ ESP32 found on {port}!")
            print(f"Response: {response.strip()}")
            return True
        else:
            print(f"⚠️  Port {port} opened but no ESP32 response")
            return False
            
    except Exception as e:
        print(f"❌ Failed to connect to {port}: {e}")
        return False

def close_conflicting_processes():
    """
    Informasi untuk menutup proses yang menggunakan COM port
    """
    print("\n🛠️  If port is busy, try these steps:")
    print("1. Close Arduino IDE")
    print("2. Close Serial Monitor")
    print("3. Close PuTTY or other terminal programs")
    print("4. Unplug and replug ESP32 USB cable")
    print("5. Check Device Manager for driver issues")
    print("6. Restart Python script")

def main():
    print("🚀 ESP32 COM Port Scanner & Tester")
    print("=" * 50)
    
    # Scan available ports
    available_ports = scan_available_ports()
    
    if not available_ports:
        print("\n❌ No available COM ports found!")
        close_conflicting_processes()
        return
    
    print(f"\n✅ Found {len(available_ports)} available port(s)")
    
    # Test each available port for ESP32
    esp32_ports = []
    for port in available_ports:
        if test_esp32_connection(port):
            esp32_ports.append(port)
    
    print(f"\n📊 Summary:")
    print(f"Available ports: {available_ports}")
    print(f"ESP32 detected on: {esp32_ports}")
    
    if esp32_ports:
        recommended_port = esp32_ports[0]
        print(f"\n🎯 Recommended port: {recommended_port}")
        print(f"Update your code: SERIAL_PORT = \"{recommended_port}\"")
    else:
        print(f"\n⚠️  No ESP32 detected. Make sure:")
        print("- ESP32 is connected via USB")
        print("- ESP32 code is uploaded and running")
        print("- Correct drivers are installed")
        close_conflicting_processes()

if __name__ == "__main__":
    main()