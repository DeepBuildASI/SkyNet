# A818SN - REAL GUI with Live Video + Real Tracking + Map + Graphs
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'a818em'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'a818sn'))

import tkinter as tk
import cv2
from PIL import Image, ImageTk
from tkintermapview import TkinterMapView
from geopy.geocoders import Nominatim

from geo import haversine_km
from coverage import full_coverage_report
from attenuation import efield_at_distance
from coupling import coupled_energy, kill_decision
from config import HOB_KM

from real_detect import RealTracker
from real_gps import get_real_location

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def circle_coords(lat, lon, radius_km, points=72):
    coords = []
    for i in range(points):
        angle = 2 * math.pi * i / points
        dlat = (radius_km / 111.0) * math.cos(angle)
        dlon = (radius_km / (111.0 * math.cos(math.radians(lat)))) * math.sin(angle)
        coords.append((lat + dlat, lon + dlon))
    return coords


class A818SN_RealApp:
    def __init__(self, root):
        self.root = root
        self.armed = False
        self.gz = None
        self.tgt = None
        self.geolocator = Nominatim(user_agent="a818sn_sky_net")

        self.tracker = RealTracker(model_path=os.path.join(
            os.path.dirname(__file__), 'yolov8n.pt'))
        self.tracking = False

        self.root.title("A818SN SKY NET - REAL SYSTEM")
        self.root.geometry("1600x950")
        self.root.configure(bg="#0a0a0a")

        # ===== LEFT PANEL =====
        left = tk.Frame(root, bg="#0a0a0a", width=350)
        left.pack(side="left", fill="y", padx=5, pady=5)

        tk.Label(left, text="A818SN SKY NET", font=("Consolas", 16, "bold"),
                 fg="#00ff88", bg="#0a0a0a").pack(pady=5)
        tk.Label(left, text="REAL Detection + EMP Sim", font=("Consolas", 9),
                 fg="#ff8800", bg="#0a0a0a").pack()

        self.gps_label = tk.Label(left, text="GPS: detecting...", fg="#ffff00",
                                   bg="#0a0a0a", font=("Consolas", 9), wraplength=330)
        self.gps_label.pack(pady=5)

        tk.Label(left, text="GROUND ZERO:", fg="#00aaff", bg="#0a0a0a",
                 font=("Consolas", 9, "bold")).pack(anchor="w", pady=(5, 0))
        self.gz_entry = tk.Entry(left, width=40, font=("Consolas", 10),
                                  bg="#111", fg="#00ff88", insertbackground="#00ff88")
        self.gz_entry.pack(pady=2)
        tk.Button(left, text="Set GZ + Zoom", command=self.set_gz_search,
                  bg="#0066cc", fg="#fff", font=("Consolas", 9)).pack()

        tk.Label(left, text="TARGET:", fg="#00aaff", bg="#0a0a0a",
                 font=("Consolas", 9, "bold")).pack(anchor="w", pady=(5, 0))
        self.tgt_entry = tk.Entry(left, width=40, font=("Consolas", 10),
                                   bg="#111", fg="#00ff88", insertbackground="#00ff88")
        self.tgt_entry.pack(pady=2)
        tk.Button(left, text="Set Target + Zoom", command=self.set_tgt_search,
                  bg="#0066cc", fg="#fff", font=("Consolas", 9)).pack()

        tk.Button(left, text="Draw Coverage Zone", command=self.draw_coverage,
                  bg="#0066cc", fg="#fff", font=("Consolas", 9)).pack(pady=3)

        track_frame = tk.LabelFrame(left, text="REAL TRACKING (YOLO)",
                                     bg="#0a0a0a", fg="#ff00ff",
                                     font=("Consolas", 9, "bold"))
        track_frame.pack(pady=5, fill="x")

        tk.Button(track_frame, text="START REAL TRACKING", command=self.start_tracking,
                  bg="#aa00aa", fg="#fff", font=("Consolas", 9)).pack(pady=2, padx=5, fill="x")
        tk.Button(track_frame, text="STOP TRACKING", command=self.stop_tracking,
                  bg="#333", fg="#fff", font=("Consolas", 9)).pack(pady=2, padx=5, fill="x")
        tk.Button(track_frame, text="CLEAR TRACK", command=self.clear_track,
                  bg="#333", fg="#fff", font=("Consolas", 9)).pack(pady=2, padx=5, fill="x")

        self.track_label = tk.Label(track_frame, text="IDLE", fg="#888",
                                     bg="#0a0a0a", font=("Consolas", 9, "bold"))
        self.track_label.pack(pady=2)
        self.fps_label = tk.Label(track_frame, text="FPS: --", fg="#00aaff",
                                   bg="#0a0a0a", font=("Consolas", 9))
        self.fps_label.pack(pady=2)

        self.arm_btn = tk.Button(left, text="ARM", width=20, bg="#333", fg="#fff",
                                  font=("Consolas", 12, "bold"), command=self.toggle_arm)
        self.arm_btn.pack(pady=10)

        self.strike_btn = tk.Button(left, text="STRIKE", width=20, bg="#444", fg="#888",
                                     font=("Consolas", 14, "bold"), state="disabled",
                                     command=self.on_strike)
        self.strike_btn.pack()

        self.result_label = tk.Label(left, text="Awaiting...", font=("Consolas", 10),
                                      fg="#00ff88", bg="#0a0a0a", wraplength=330)
        self.result_label.pack(pady=3)

        tk.Label(left, text="LOG:", fg="#fff", bg="#0a0a0a",
                 font=("Consolas", 9, "bold")).pack(anchor="w")
        self.log = tk.Text(left, height=8, width=45, bg="#111", fg="#00ff88",
                            font=("Consolas", 8), state="disabled")
        self.log.pack(fill="both", expand=True)

        # ===== CENTER - VIDEO =====
        center = tk.Frame(root, bg="#0a0a0a")
        center.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        tk.Label(center, text="LIVE CAMERA FEED (YOLO)", fg="#00ff88",
                 bg="#0a0a0a", font=("Consolas", 11, "bold")).pack()

        self.video_label = tk.Label(center, bg="#000", width=640, height=480)
        self.video_label.pack()

        # ===== RIGHT =====
        right = tk.Frame(root, bg="#0a0a0a", width=500)
        right.pack(side="right", fill="y", padx=5, pady=5)

        tk.Label(right, text="TACTICAL MAP", fg="#00ff88", bg="#0a0a0a",
                 font=("Consolas", 10, "bold")).pack()

        self.map_widget = TkinterMapView(right, width=480, height=280, corner_radius=0)
        self.map_widget.pack()
        self.map_widget.set_position(31.5826, 74.3276)
        self.map_widget.set_zoom(5)

        tk.Label(right, text="LIVE TRACKING GRAPHS", fg="#ff00ff",
                 bg="#0a0a0a", font=("Consolas", 10, "bold")).pack(pady=5)

        self.fig1 = Figure(figsize=(4.5, 2.3), dpi=75, facecolor="#111")
        self.ax1 = self.fig1.add_subplot(111)
        self.ax1.set_facecolor("#000")
        self.ax1.set_title("Trajectory (X vs Y)", color="#00ff88", fontsize=8)
        self.ax1.tick_params(colors="#888", labelsize=6)
        self.ax1.grid(True, color="#222")
        self.line1, = self.ax1.plot([], [], color="#00ff88", linewidth=2)
        canvas1 = FigureCanvasTkAgg(self.fig1, master=right)
        canvas1.draw()
        canvas1.get_tk_widget().pack(pady=2)
        self.canvas1 = canvas1

        self.fig2 = Figure(figsize=(4.5, 1.8), dpi=75, facecolor="#111")
        self.ax2 = self.fig2.add_subplot(111)
        self.ax2.set_facecolor("#000")
        self.ax2.set_title("X vs Time", color="#00aaff", fontsize=8)
        self.ax2.tick_params(colors="#888", labelsize=6)
        self.ax2.grid(True, color="#222")
        self.line2, = self.ax2.plot([], [], color="#00aaff", linewidth=2)
        canvas2 = FigureCanvasTkAgg(self.fig2, master=right)
        canvas2.draw()
        canvas2.get_tk_widget().pack(pady=2)
        self.canvas2 = canvas2

        self.fig3 = Figure(figsize=(4.5, 1.8), dpi=75, facecolor="#111")
        self.ax3 = self.fig3.add_subplot(111)
        self.ax3.set_facecolor("#000")
        self.ax3.set_title("Y vs Time", color="#ff8800", fontsize=8)
        self.ax3.tick_params(colors="#888", labelsize=6)
        self.ax3.grid(True, color="#222")
        self.line3, = self.ax3.plot([], [], color="#ff8800", linewidth=2)
        canvas3 = FigureCanvasTkAgg(self.fig3, master=right)
        canvas3.draw()
        canvas3.get_tk_widget().pack(pady=2)
        self.canvas3 = canvas3

        self.gz_marker = None
        self.tgt_marker = None
        self.coverage_polygon = None

        self.write_log("> A818SN REAL v1 online")
        self.write_log("> YOLO loaded")
        self.root.after(200, self.refresh_gps)

    def write_log(self, msg):
        self.log.config(state="normal")
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)
        self.log.config(state="disabled")

    def refresh_gps(self):
        loc = get_real_location()
        if loc.get("success"):
            self.gps_label.config(
                text=f"GPS: {loc['city']}, {loc['country']}",
                fg="#00ff88")
            self.gz = (f"{loc['city']}, {loc['country']}", loc['lat'], loc['lon'])
            self.map_widget.set_position(loc['lat'], loc['lon'])
            self.gz_marker = self.map_widget.set_marker(loc['lat'], loc['lon'], text="YOU")
            self.write_log(f"> GPS: {loc['city']}, {loc['country']}")
        else:
            self.gps_label.config(text=f"GPS failed", fg="#ff4444")

    def geocode(self, query):
        try:
            loc = self.geolocator.geocode(query, timeout=10)
            if loc:
                return loc.latitude, loc.longitude, loc.address
        except Exception:
            pass
        return None, None, None

    def set_gz_search(self):
        q = self.gz_entry.get().strip()
        if not q: return
        lat, lon, addr = self.geocode(q)
        if lat is None:
            self.write_log(f"> GZ NOT FOUND: {q}")
            return
        self.gz = (addr, lat, lon)
        if self.gz_marker:
            self.gz_marker.delete()
        self.gz_marker = self.map_widget.set_marker(lat, lon, text="GZ")
        self.map_widget.set_position(lat, lon)
        self.map_widget.set_zoom(6)
        self.write_log(f"> GZ: {addr[:45]}")

    def set_tgt_search(self):
        q = self.tgt_entry.get().strip()
        if not q: return
        lat, lon, addr = self.geocode(q)
        if lat is None:
            self.write_log(f"> TARGET NOT FOUND: {q}")
            return
        self.tgt = (addr, lat, lon)
        if self.tgt_marker:
            self.tgt_marker.delete()
        self.tgt_marker = self.map_widget.set_marker(lat, lon, text="TGT")
        self.map_widget.set_position(lat, lon)
        self.map_widget.set_zoom(6)
        self.write_log(f"> TARGET: {addr[:45]}")

    def draw_coverage(self):
        if not self.gz: return
        name, lat, lon = self.gz
        R = full_coverage_report(HOB_KM)["radius_km"]
        if self.coverage_polygon:
            self.coverage_polygon.delete()
        coords = circle_coords(lat, lon, R)
        self.coverage_polygon = self.map_widget.set_polygon(
            coords, fill_color=None, outline_color="#00ff00", border_width=3)
        self.write_log(f"> Coverage: {R:.0f} km")

    def start_tracking(self):
        self.tracking = True
        self.track_label.config(text="TRACKING...", fg="#00ff88")
        self.write_log("> REAL tracking started")
        self.track_loop()

    def stop_tracking(self):
        self.tracking = False
        self.track_label.config(text="STOPPED", fg="#ff8800")
        self.write_log("> Tracking stopped")

    def clear_track(self):
        self.tracker.reset()
        self.line1.set_data([], [])
        self.line2.set_data([], [])
        self.line3.set_data([], [])
        self.canvas1.draw()
        self.canvas2.draw()
        self.canvas3.draw()
        self.write_log("> Track cleared")

    def track_loop(self):
        if not self.tracking:
            return

        frame, detections = self.tracker.get_frame_with_detections()

        if frame is not None:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = img.resize((640, 480))
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.config(image=imgtk)

            self.fps_label.config(text=f"FPS: {self.tracker.fps:.1f}")

            if len(self.tracker.x) > 1:
                self.line1.set_data(list(self.tracker.x), list(self.tracker.y))
                self.ax1.relim(); self.ax1.autoscale_view()
                self.canvas1.draw()

                self.line2.set_data(list(self.tracker.t), list(self.tracker.x))
                self.ax2.relim(); self.ax2.autoscale_view()
                self.canvas2.draw()

                self.line3.set_data(list(self.tracker.t), list(self.tracker.y))
                self.ax3.relim(); self.ax3.autoscale_view()
                self.canvas3.draw()

            if detections:
                self.track_label.config(
                    text=f"DETECTED {len(detections)} obj | conf {detections[0]['conf']:.2f}",
                    fg="#00ff88")
            else:
                self.track_label.config(text="NO DETECTION", fg="#ff8800")

        self.root.after(30, self.track_loop)

    def toggle_arm(self):
        if not self.gz or not self.tgt:
            self.write_log("> Set GZ and Target first")
            return
        self.armed = not self.armed
        if self.armed:
            self.arm_btn.config(text="DISARM", bg="#cc0000")
            self.strike_btn.config(state="normal", bg="#ff2222", fg="#fff")
            self.write_log("> ARMED")
        else:
            self.arm_btn.config(text="ARM", bg="#333")
            self.strike_btn.config(state="disabled", bg="#444", fg="#888")
            self.write_log("> SAFE")

    def on_strike(self):
        if not self.armed or not self.gz or not self.tgt:
            return
        gz_name, gz_lat, gz_lon = self.gz
        tgt_name, tgt_lat, tgt_lon = self.tgt
        d = haversine_km(gz_lat, gz_lon, tgt_lat, tgt_lon)
        cov = full_coverage_report(HOB_KM)
        in_r = d <= cov["radius_km"]
        E = efield_at_distance(d, HOB_KM) if in_r else 0
        Ec = coupled_energy(E) if in_r else 0
        res = kill_decision(Ec) if in_r else "OUT_OF_RANGE"
        self.write_log(f"> STRIKE: {d:.1f} km | E={E:.2f} kV/m | {res}")
        color = "#ff2222" if res == "FRIED" else "#00ff88"
        self.result_label.config(text=f"{res} | {d:.1f} km | {E:.2f} kV/m", fg=color)
        self.armed = False
        self.arm_btn.config(text="ARM", bg="#333")
        self.strike_btn.config(state="disabled", bg="#444", fg="#888")


if __name__ == "__main__":
    root = tk.Tk()
    app = A818SN_RealApp(root)
    root.mainloop()