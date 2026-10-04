# Panduan Penggunaan Sistem Futuristic Rifle Controller

Dokumen ini berisi panduan lengkap mengenai persiapan perangkat keras, konfigurasi perangkat lunak, serta pengoperasian antarmuka web untuk sistem prototipe senapan otomatis berbasis ESP32 dan Computer Vision.

---

## 1. Persiapan dan Koneksi Perangkat Keras (Hardware Setup)

1. **Penyambungan Daya Prototipe**:
   - Sambungkan kabel Jack DC male 5.5 mm to USB ke soket daya pada prototipe senapan.
   - Hubungkan ujung kabel USB ke adaptor charger 5V (minimal 2A disarankan) untuk menyuplai daya ke sistem servo.
2. **Koneksi ESP32 ke Komputer**:
   - Hubungkan mikrokontroler ESP32 ke port USB komputer menggunakan kabel data micro-USB / Type-C.
   - Pastikan repositori aplikasi telah diunduh/di-clone dari [https://github.com/Tedshub/shooter-ai](https://github.com/Tedshub/shooter-ai).
3. **Pemeriksaan Port Serial (COM Port)**:
   - Buka **Device Manager** pada sistem operasi Windows (tekan `Win + X` lalu pilih *Device Manager*).
   - Buka menu drop-down **Ports (COM & LPT)** dan catat nomor port ESP32 yang terhubung (contoh: `COM3`, `COM5`, dsb.).
   - Buka file [app.py](f/app.py) dan sesuaikan nomor port default pada baris ke-32:
     ```python
     current_serial_port = "COM5"  # Sesuaikan dengan port COM ESP32 Anda
     ```
   - Port COM juga dapat dideteksi dan dipilih langsung melalui antarmuka web menggunakan tombol **SCAN PORTS**.
4. **Flash Ulang ESP32 (Opsional / Jika Diperlukan)**:
   - Jika ESP32 belum terisi firmware atau membutuhkan pembaruan, buka project sketch Arduino di [shot-automation/shot-automation.ino](/shot-automation/shot-automation.ino).
   - Gunakan **Arduino IDE** dengan board definition ESP32 dan library `ESP32Servo` terpasang.
   - Pilih tipe board ESP32 dan Port COM yang sesuai, kemudian lakukan **Upload / Flash**.
5. **Menyalakan Prototipe**:
   - Setelah semua kabel terhubung dengan benar, hidupkan saklar power utama pada prototipe senapan.

---

## 2. Menjalankan Aplikasi Web (Software Execution)

1. **Persiapan Lingkungan**:
   - Buka terminal atau command prompt pada direktori root proyek.
   - Pastikan dependensi Python seperti Flask, OpenCV, PySerial, dan Ultralytics telah terpasang di environment Anda:
     ```bash
     pip install flask opencv-python pyserial ultralytics
     ```
2. **Menjalankan Server**:
   - Jalankan perintah berikut:
     ```bash
     python app.py
     ```
3. **Membuka Antarmuka**:
   - Setelah server Flask aktif, buka browser web (disarankan Google Chrome atau Microsoft Edge) dan akses alamat:
     ```
     http://127.0.0.1:5000
     ```

---

## 3. Panduan Pengoperasian Antarmuka (Interface Operation)

### A. Kontrol Manual (Manual Control)
- **Virtual Joystick**: Terletak di panel kiri atas. Geser bulatan joystick untuk menggerakkan servo penembak:
  - Sumbu Vertikal (Y): Mengontrol Servo 1 (elevasi / naik-turun, rentang 0-180 derajat).
  - Sumbu Horizontal (X): Mengontrol Servo 2 (azimuth / kiri-kanan, rentang 0-180 derajat).
- **Fire Control (Button FIRE)**: Terletak di panel kanan atas. Klik tombol merah **FIRE** untuk menarik pelatuk (menggerakkan Servo 3 / Trigger).

### B. Mode Kontrol (Control Mode)
- **MANUAL**: Mode kendali penuh oleh pengguna melalui joystick atau perintah manual.
- **AUTO**: Mode pelacakan dan penargetan otomatis berdasarkan bounding box deteksi objek dari model YOLO.

### C. Kontrol Suara (Voice Command)
- Klik tombol **VOICE** pada bagian bawah tengah untuk mengaktifkan fitur pengenalan suara (*continuous listening*).
- Berikan perintah suara yang didukung (misalnya perintah untuk menembak, reposisi, atau perubahan status).

### D. Manajemen Model YOLO (Target Model & Upload)
- **Pilihan Model (Target Model)**: Pilih model deteksi yang aktif melalui menu drop-down *TARGET MODEL* (misalnya `face.pt`, `yolov8n.pt`).
- **Upload Model**: Klik tombol **UPLOAD MODEL** untuk mengunggah file model baru berformat `.pt` (YOLOv8) ke dalam folder `model/`.

### E. Menu Kontrol Otomatis dan Utilitas (Auto Control)
- **TEST ACTUATOR**: Menguji pergerakan semua servo (Servo 1, Servo 2, dan Servo 3) secara berurutan untuk memastikan fungsi mekanik normal.
- **START / STOP DETECTION**: Mengaktifkan atau menonaktifkan feed inferensi computer vision pada layar kamera.
- **RESET POSITION**: Mengembalikan seluruh servo ke posisi default (Servo 1: 90 derajat, Servo 2: 90 derajat, Servo 3: 0 derajat).
- **Scan Camera / Camera Selection**: Mengganti sumber kamera input yang terpasang pada komputer.
- **System Status**: Menampilkan pembacaan sudut posisi saat ini untuk Servo 1 (Y), Servo 2 (X), dan Servo 3 (Trigger) serta status koneksi serial.
