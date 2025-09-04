import cv2
import numpy as np
from datetime import datetime
import pytz
from ultralytics import YOLO

# Ukuran frame
frame_width = 1280
frame_height = 720

# Skala koordinat
x_min, x_max = -15, 15
y_min, y_max = -10, 10
x_range = x_max - x_min
y_range = y_max - y_min
pixels_per_unit_x = frame_width / x_range
pixels_per_unit_y = frame_height / y_range
center_x = frame_width // 2
center_y = frame_height // 2

# Load YOLOv8 model
model = YOLO("model/best.pt")

def draw_axis_grid(frame):
    overlay = frame.copy()
    line_color = (0, 255, 0)
    text_color = (0, 255, 255)
    thickness = 1
    text_thickness = 1
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Sumbu X dan Y
    cv2.line(overlay, (0, center_y), (frame_width, center_y), line_color, 2)
    cv2.line(overlay, (center_x, 0), (center_x, frame_height), line_color, 2)

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

def draw_labels(frame, detected=0, disabled=0):
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

    labels = [
        f"{time_str}",
        f"Target terdeteksi = {detected}",
        f"Target dilumpuhkan = {disabled}"
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
    x_unit = (x_pixel - center_x) / pixels_per_unit_x
    y_unit = (center_y - y_pixel) / pixels_per_unit_y
    return round(x_unit, 2), round(y_unit, 2)

import cv2
import numpy as np
from datetime import datetime
import pytz
from ultralytics import YOLO

# Ukuran frame
frame_width = 1280
frame_height = 720

# Skala koordinat
x_min, x_max = -15, 15
y_min, y_max = -10, 10
x_range = x_max - x_min
y_range = y_max - y_min
pixels_per_unit_x = frame_width / x_range
pixels_per_unit_y = frame_height / y_range
center_x = frame_width // 2
center_y = frame_height // 2

# Load YOLOv8 model
model = YOLO("model/best.pt")

def draw_axis_grid(frame):
    overlay = frame.copy()
    line_color = (0, 255, 0)
    text_color = (0, 255, 255)
    thickness = 1
    text_thickness = 1
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Sumbu X dan Y
    cv2.line(overlay, (0, center_y), (frame_width, center_y), line_color, 2)
    cv2.line(overlay, (center_x, 0), (center_x, frame_height), line_color, 2)

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

def draw_labels(frame, detected=0, disabled=0):
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

    labels = [
        f"{time_str}",
        f"Target terdeteksi = {detected}",
        f"Target dilumpuhkan = {disabled}"
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
    x_unit = (x_pixel - center_x) / pixels_per_unit_x
    y_unit = (center_y - y_pixel) / pixels_per_unit_y
    return round(x_unit, 2), round(y_unit, 2)

def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)

    if not cap.isOpened():
        print("❌ Tidak dapat membuka kamera.")
        return

    cv2.namedWindow("Kamera Fullscreen", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Kamera Fullscreen", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    print("✅ Tekan 'q' untuk keluar.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Gagal membaca frame.")
            break

        frame = cv2.resize(frame, (frame_width, frame_height))
        results = model.predict(frame, imgsz=640, conf=0.5, verbose=False)
        detections = results[0].boxes.xyxy.cpu().numpy() if results[0].boxes else []

        frame_with_axis = draw_axis_grid(frame)

        for i, box in enumerate(detections):
            x1, y1, x2, y2 = box[:4].astype(int)
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)

            # Konversi ke koordinat unit
            coord_x, coord_y = pixel_to_coords(cx, cy)

            # Gambar bounding box dan titik tengah
            cv2.rectangle(frame_with_axis, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.circle(frame_with_axis, (cx, cy), 4, (255, 255, 0), -1)

            # Tampilkan teks koordinat
            cv2.putText(
                frame_with_axis,
                f"({coord_x}, {coord_y})",
                (cx + 10, cy - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )

            # Tambahkan label identitas objek (nomor urut) - putih bold
            label_text = f"Target {i+1}"
            cv2.putText(
                frame_with_axis,
                label_text,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2  # bold
            )

        frame_with_labels = draw_labels(frame_with_axis, detected=len(detections), disabled=0)
        cv2.imshow("Kamera Fullscreen", frame_with_labels)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
