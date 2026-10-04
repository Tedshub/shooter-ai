import matplotlib.pyplot as plt
import numpy as np

# =========================
# DATA SETTLING TIME
# =========================
object_positions = [
    "Upper Left",
    "Upper Right",
    "Lower Left",
    "Lower Right",
    "Center Left",
    "Center Right",
    "Center Top",
    "Center Bottom"
]

distance_from_center = [200, 200, 200, 200, 160, 160, 120, 120]

settling_time = [2.45, 2.52, 2.38, 2.48, 1.85, 1.92, 1.65, 1.72]

# =========================
# SCATTER PLOT
# Settling Time vs Distance
# =========================
plt.figure(figsize=(8, 6))

plt.scatter(
    distance_from_center,
    settling_time,
    s=120
)

# Tambahkan label tiap titik
for i in range(len(object_positions)):
    plt.annotate(
        object_positions[i],
        (distance_from_center[i], settling_time[i]),
        textcoords="offset points",
        xytext=(5, 5),
        fontsize=9
    )

# Trend line
z = np.polyfit(distance_from_center, settling_time, 1)
p = np.poly1d(z)

x_line = np.linspace(min(distance_from_center), max(distance_from_center), 100)

plt.plot(x_line, p(x_line), linestyle='--')

plt.title("Settling Time vs Distance from Center")
plt.xlabel("Distance from Center (Pixels)")
plt.ylabel("Settling Time (Seconds)")
plt.grid(True)

plt.tight_layout()
plt.show()

# =========================
# DATA OVERSHOOT
# =========================
average_overshoot = [13.7, 14.4, 13.0, 13.9, 9.4, 10.0, 7.4, 7.7]

# =========================
# BAR CHART OVERSHOOT
# =========================
plt.figure(figsize=(10, 6))

bars = plt.bar(
    object_positions,
    average_overshoot
)

# Tambahkan nilai di atas bar
for bar in bars:
    height = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width()/2,
        height + 0.3,
        f'{height:.1f}%',
        ha='center',
        fontsize=9
    )

# Garis batas overshoot maksimum
plt.axhline(
    y=20,
    linestyle='--',
    label='Success Criteria (<20%)'
)

plt.title("Average Overshoot for Each Object Position")
plt.xlabel("Object Position")
plt.ylabel("Overshoot (%)")

plt.xticks(rotation=15)
plt.legend()
plt.grid(axis='y')

plt.tight_layout()
plt.show()