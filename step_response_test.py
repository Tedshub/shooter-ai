import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# Simulasi Step Response Servo Tracking
# P-Control vs PID
# ==========================================

# Waktu simulasi
t = np.linspace(0, 5, 500)

# ==========================================
# P-CONTROL RESPONSE
# Stabil namun lebih lambat
# ==========================================
p_response = 1 - np.exp(-1.2 * t)

# Tambahkan sedikit error steady-state
p_response = p_response * 0.96

# ==========================================
# PID RESPONSE
# Lebih cepat dengan overshoot kecil
# ==========================================
zeta = 0.6      # damping ratio
wn = 3.2        # natural frequency

pid_response = 1 - (
    np.exp(-zeta * wn * t) *
    (
        np.cos(wn * np.sqrt(1 - zeta**2) * t)
        +
        (
            zeta / np.sqrt(1 - zeta**2)
        ) *
        np.sin(wn * np.sqrt(1 - zeta**2) * t)
    )
)

# ==========================================
# Plot
# ==========================================

plt.figure(figsize=(9, 5))

plt.plot(
    t,
    p_response,
    label='P-Control',
    linewidth=2
)

plt.plot(
    t,
    pid_response,
    label='PID Control',
    linewidth=2
)

# Target step line
plt.axhline(
    y=1,
    linestyle='--',
    linewidth=1,
    label='Target Position'
)

# Formatting
plt.title('Step Response Comparison: P-Control vs PID')
plt.xlabel('Time (seconds)')
plt.ylabel('Normalized Position Response')
plt.xlim(0, 5)
plt.ylim(0, 1.25)

plt.grid(True)
plt.legend()

# Tambahkan anotasi overshoot PID
peak_idx = np.argmax(pid_response)
peak_time = t[peak_idx]
peak_value = pid_response[peak_idx]

plt.plot(peak_time, peak_value, 'ro')

plt.annotate(
    f'Overshoot = {(peak_value - 1)*100:.1f}%',
    xy=(peak_time, peak_value),
    xytext=(peak_time + 0.4, peak_value + 0.08),
    arrowprops=dict(arrowstyle='->')
)

# Tambahkan settling indication P-control
plt.annotate(
    'Stable Response',
    xy=(3.5, p_response[np.searchsorted(t, 3.5)]),
    xytext=(2.6, 0.82),
    arrowprops=dict(arrowstyle='->')
)

plt.tight_layout()
plt.show()