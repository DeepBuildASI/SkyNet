# A818SN // SKY NET
### Real-Time Aerial Threat Detection & High-Altitude EMP Weapon Effects Analysis

**Author:** Asma Rizwan Rao (A818)  
**Classification:** Private Research / Dual-Use Simulation & Control  
**Status:** Active Development (Drone Model Training Phase)  

---

## ⚠️ EXECUTIVE SUMMARY

**A818SN** is a localized, multi-threaded defense analysis and control pipeline. Unlike standard counter-UAS (Unmanned Aerial System) software that stops at bounding boxes, A818SN bridges the gap between **Computer Vision (CV)**, **High-Altitude Electromagnetic Pulse (HEMP) physics**, and **Weapon Control Interfaces**.

The system autonomously detects aerial targets, tracks their telemetry in real-time, maps their global position, dynamically calculates the **Coupling Energy (Joules)** required to induce catastrophic failure in the target's semiconductor architecture via a simulated 500 km exo-atmospheric EMP weapon burst, and provides a serial control interface to execute a fire sequence.

This is not a toy tracker. It is an integrated physics engine and weapon controller disguised as a GUI.

---

## 🛠️ SYSTEM ARCHITECTURE

The software operates on a strict 5-stage pipeline.

### 1. Target Acquisition (YOLO / OpenCV)
*   **Engine:** Ultralytics YOLOv8
*   **Function:** Live-webcam inference. Extracts bounding boxes, confidence scores, and center-mass coordinates.
*   **Current State:** Operating on the COCO dataset (baseline). Currently training a custom YOLOv8s model on **75,000+ high-resolution drone frames** for specialized UAV detection.

### 2. Kinematic Tracking & Telemetry (Matplotlib / Deques)
*   **Function:** Maintains a rolling history of the target's spatial coordinates (X, Y, and Time). 
*   **Output:** Renders live trajectory vectors and velocity graphs to predict the drone's immediate flight path.

### 3. HEMP Physics & Coupling Engine (`a818em`)
This is the core of the system. It calculates the physical impact of a simulated nuclear electromagnetic weapon event.
*   **Waveform Modeling:** Uses the Karzas-Latter simplified model to simulate the E1 pulse (rise time ~5ns, peak field 50 kV/m).
*   **Geometric Attenuation:** Calculates the E-field strength `(kV/m)` at the target's exact distance from Ground Zero using the inverse-square law and atmospheric attenuation.
*   **Circuit Coupling:** Translates free-space E-field strength into actual energy (Joules) coupled into unshielded PCB traces.
*   **Damage Assessment:** Compares coupled energy against a hardcoded semiconductor burnout threshold (1×10⁻⁷ J) to output a binary **"FRIED"** or **"SURVIVED"** verdict.

### 4. Tactical Mapping & Geospatial Targeting (`tkintermapview`)
*   **Function:** Interfaces with live OpenStreetMap/Nominatim APIs.
*   **Capability:** Allows the operator to designate "Ground Zero" anywhere on Earth. Dynamically renders the EMP weapon coverage radius (approx. 2,524 km) as a lethal footprint overlay on the map.

### 5. Weapon Control Interface (`hardware.py`)
A fully functional, thread-safe serial interface designed to command external directed-energy weapon hardware.
*   **State Machine:** `IDLE -> CONNECTED -> CHARGING -> READY -> ARMED -> FIRING -> COOLDOWN`
*   **Safety Interlocks:** Verifies weapon ID handshakes, checks physical interlock continuity, and enforces a strict 30-second cooldown between pulses. 
*   **Failsafes:** Hardware-level Emergency Stop (ESTOP) latching and automatic disarm protocols if the serial connection is severed mid-fire sequence.
*   **Protocol:** Line-based ASCII over COM port. 

---

## ⚡ TECHNICAL STACK

*   **Language:** Python 3.13
*   **Vision:** OpenCV, Ultralytics (PyTorch backend)
*   **UI/UX:** Tkinter
*   **Data Vis:** Matplotlib
*   **Geospatial:** TkinterMapView, Geopy
*   **Serial Comm:** PySerial
*   **Physics Engine:** Custom numerical integration models

---

## 🚀 DEPLOYMENT

```bash
# Clone the repository
git clone https://github.com/DeepBuildASI/skynet.git

# Install dependencies
pip install -r requirements.txt

# Initialize the system
python gui_real.py

(Note: The system requires a connected webcam for active target acquisition. Without weapon hardware connected, the STRIKE function will safely default to physics-only analysis mode.)

🛑 LEGAL & ETHICAL DISCLAIMER
A818SN is a physics calculator and weapon control interface.

The physics engine calculates theoretical coupling based on published IEEE and IEC standards for High-Altitude EMP weapon effects. The hardware interface is a reference architecture for licensed defense contractors. The inclusion of the control software does not constitute a physical weapon.

The author is not responsible for the misuse of this software in violation of local telecommunications laws or international arms control treaties. This project is intended for academic research, threat modeling, and defensive system hardening.