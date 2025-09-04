# 🎯 AI Shooter

**Sistem Penargetan Otomatis Berbasis AI Computer Vision**

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Arduino](https://img.shields.io/badge/Arduino-IDE-green.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.5+-red.svg)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6-yellow.svg)

## 📋 Deskripsi Proyek

SHOT-AUTOMATION adalah sistem penargetan otomatis yang menggunakan teknologi AI Computer Vision untuk deteksi objek dan penargetan presisi. Sistem ini dilengkapi dengan mode manual dan kontrol suara untuk fleksibilitas penggunaan maksimal.

### ✨ Fitur Utama

- 🤖 **Penargetan Otomatis** - AI detection menggunakan model computer vision
- 🎮 **Mode Manual** - Kontrol manual untuk presisi maksimal  
- 🎙️ **Voice Control** - Kontrol dengan perintah suara melalui API
- 🎯 **Multi-Target Detection** - Deteksi multiple objek (face, hand, red_ball)
- 📊 **Real-time Processing** - Pemrosesan video secara real-time
- 🌐 **Web Interface** - Interface web yang user-friendly

## 🏗️ Struktur Proyek

```
SHOT-AUTOMATION/
├── model/                 # Model AI untuk deteksi objek
│   ├── face.pt           # Model deteksi wajah
│   ├── hand.pt           # Model deteksi tangan
│   └── red_ball.pt       # Model deteksi bola merah
├── shot-automation/       # Core aplikasi
│   └── shot-automation.ino # Firmware Arduino
├── static/               # File statis web
│   ├── css/             # Stylesheet
│   ├── js/              # JavaScript files
│   └── sound/           # Audio files
├── templates/            # Template HTML
│   └── index.html       # Interface utama
├── app.py               # Aplikasi Flask utama
├── port_scan.py         # Utilitas scan port
├── requirements.txt     # Dependencies Python
└── README.md           # Dokumentasi proyek
```

## 🛠️ Teknologi yang Digunakan

### Development Tools
- **Google Colab** - Training model AI
- **Arduino IDE** - Programming mikrokontroler
- **VS Code** - Development environment

### Tech Stack
- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, JavaScript
- **AI/ML**: OpenCV, PyTorch/TensorFlow
- **Hardware**: Arduino, Servo Motors
- **Audio**: Web Speech API

## 🚀 Instalasi dan Setup

### Prerequisites
```bash
# Pastikan Python 3.8+ terinstall
python --version

# Install Arduino IDE
# Download dari: https://www.arduino.cc/en/software
```

### 1. Clone Repository
```bash
git clone https://github.com/username/shot-automation.git
cd shot-automation
```

### 2. Setup Python Environment
```bash
# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Setup Arduino
1. Buka Arduino IDE
2. Load file `shot-automation/shot-automation.ino`
3. Pilih board dan port yang sesuai
4. Upload ke Arduino

### 4. Jalankan Aplikasi
```bash
python app.py
```

Akses aplikasi di: `http://localhost:5000`

## 🎮 Cara Penggunaan

### Mode Otomatis
1. Pilih target detection (face/hand/red_ball)
2. Klik "Start Auto Mode"
3. Sistem akan otomatis mendeteksi dan mengarahkan

### Mode Manual
1. Gunakan kontrol directional pada web interface
2. Kontrol servo secara manual dengan presisi tinggi

### Voice Control
1. Klik tombol microphone
2. Berikan perintah suara:
   - "Start auto mode"
   - "Switch to manual"
   - "Move left/right/up/down"
   - "Fire"
   - "Stop"

## 🔧 Konfigurasi

### Model Configuration
Edit konfigurasi model di `app.py`:
```python
MODELS = {
    'face': 'model/face.pt',
    'hand': 'model/hand.pt', 
    'red_ball': 'model/red_ball.pt'
}
```

### Arduino Configuration
Sesuaikan pin configuration di `shot-automation.ino`:
```cpp
#define SERVO_X_PIN 9
#define SERVO_Y_PIN 10
#define TRIGGER_PIN 11
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main interface |
| POST | `/start_auto` | Mulai mode otomatis |
| POST | `/manual_control` | Kontrol manual |
| POST | `/voice_command` | Proses perintah suara |
| GET | `/video_feed` | Stream video real-time |

## 🎯 Model Training

Untuk melatih model baru menggunakan Google Colab:

1. Upload dataset ke Google Drive
2. Buka Colab notebook untuk training
3. Jalankan training script
4. Download model `.pt` hasil training
5. Pindahkan ke folder `model/`

## ⚙️ Hardware Requirements

### Minimum Requirements
- Arduino Uno/Nano
- 2x Servo Motors (SG90 atau setara)
- USB Camera/Webcam
- Breadboard dan jumper wires

### Recommended Setup
- Arduino Mega (untuk performa lebih baik)
- High-torque servo motors
- HD Camera dengan auto-focus
- Power supply eksternal untuk servo

## 🔍 Troubleshooting

### Common Issues

**Camera tidak terdeteksi:**
```bash
# Check available cameras
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

**Port Arduino tidak ditemukan:**
```bash
# Jalankan port scanner
python port_scan.py
```

**Model loading error:**
- Pastikan file model `.pt` ada di folder `model/`
- Check compatibility PyTorch version

## 🤝 Kontribusi

1. Fork repository
2. Buat feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 Lisensi

Distributed under the MIT License. See `LICENSE` for more information.

## 📞 Kontak

**Developer**: Tedy Firmansyah
- Email: tedysyhh07@gmail.com
- LinkedIn: [Tedy Firmansyah](https://www.linkedin.com/in/tedy-firmansyah-305ab5340)
- GitHub: [@Tedshub](https://github.com/Tedshub)

## 🙏 Acknowledgments

- [OpenCV](https://opencv.org/) for computer vision library
- [Flask](https://flask.palletsprojects.com/) for web framework
- [ESP32](https://www.espressif.com/) for microcontroller platform
- [Google Colab](https://colab.research.google.com/) for training environment

---

⭐ **Don't forget to give this project a star if it helped you!** ⭐
