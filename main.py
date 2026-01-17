#  ----------------------------------------------------------------------------
#  ThirdEye AI Vision Suite - Proprietary and Confidential
#  Copyright (c) 2026 Devon Chase. All rights reserved.
#
#  NOTICE: All information contained herein is, and remains the property of 
#  Devon Chase. The intellectual and technical concepts contained
#  herein are proprietary and may be covered by U.S. and Foreign Patents.
#  Dissemination of this information or reproduction of this material is 
#  strictly forbidden unless prior written permission is obtained.
#  ----------------------------------------------------------------------------
import customtkinter as ctk
import threading
import time
import os
import sys
from pathlib import Path
from PIL import Image, ImageTk
import importlib

# --- CONFIGURATION ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("dark-blue")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(SCRIPT_DIR, "assets")

def get_asset(filename):
    return os.path.join(ASSETS_DIR, filename)

class SplashScreen(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("ThirdEye Loading")
        self.geometry("400x250")
        self.overrideredirect(True)  # Remove title bar
        self.attributes("-topmost", True) # Keep on top

        # Center the splash screen
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - 400) // 2
        y = (sh - 250) // 2
        self.geometry(f"400x250+{x}+{y}")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Container
        self.frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Logo/Title
        self.lbl_title = ctk.CTkLabel(self.frame, text="ThirdEye AI", font=("Roboto", 30, "bold"))
        self.lbl_title.pack(pady=(40, 10))
        
        self.lbl_status = ctk.CTkLabel(self.frame, text="Initializing...", text_color="gray")
        self.lbl_status.pack(pady=5)
        
        # Progress Bar
        self.progress = ctk.CTkProgressBar(self.frame, width=300, height=15)
        self.progress.set(0.0)
        self.progress.pack(pady=20)

    def update_progress(self, val, status_text):
        self.progress.set(val)
        self.lbl_status.configure(text=status_text)
        self.update()

class ThirdEyeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 1. Hide Main Window Initially
        self.withdraw()
        
        # 2. Setup Basic Window Properties
        self.title("ThirdEye AI Suite")
        self.geometry("1200x800")
        self.base_path = Path(__file__).parent / "assets"
        
        # State Management
        self.active_model_name = None  # None means raw feed
        self.available_cameras = {}    # { "Camera 0": 0, ... }
        self.selected_camera_idx = 0
        self.latest_frame_image = None # Thread-safe frame transfer
        
        # Icon Setup
        try:
            if os.name == 'nt':
                icon_path = self.base_path / "app_icon.ico"
                self.iconbitmap(str(icon_path))
            else:
                icon_path = self.base_path / "thirdeye_logo.png"
                img = Image.open(icon_path)
                self.tk.call('wm', 'iconphoto', self._w, ImageTk.PhotoImage(img))
        except:
            pass

        # 3. Launch Splash Screen
        self.splash = SplashScreen(self)
        
        # 4. Start Loading Thread
        threading.Thread(target=self._load_resources, daemon=True).start()

    def _load_resources(self):
        """Loads heavy libraries and assets while updating splash screen."""
        try:
            # -- STAGE 1: Security Core --
            self.splash.update_progress(0.1, "Verifying Hardware ID...")
            global HardwareGuard
            from security_core import HardwareGuard
            self.guard = HardwareGuard()
            time.sleep(0.3) 

            # -- STAGE 2: AI Libraries --
            self.splash.update_progress(0.3, "Loading Neural Engine (OpenCV)...")
            global cv2
            import cv2
            
            self.splash.update_progress(0.4, "Scanning Optical Sensors...")
            self._scan_cameras()
            time.sleep(0.5)

            self.splash.update_progress(0.5, "Initializing Recognition Models...")
            global FaceEngine
            from recognition_engine import FaceEngine
            # Initialize engine once here to avoid lag later
            self.face_engine = FaceEngine(db_path="assets/known_faces")
            
            self.splash.update_progress(0.6, "Arming Sentry Mode...")
            global SentryEngine
            from sentry_engine import SentryEngine
            self.sentry_engine = SentryEngine()

            # -- STAGE 3: UI Assets --
            self.splash.update_progress(0.8, "Loading Interface Assets...")
            time.sleep(0.2)

            self.splash.update_progress(0.9, "Petting Soft Kitties...")
            time.sleep(0.8)

            # -- FINISH --
            self.splash.update_progress(1.0, "Ready!")
            time.sleep(0.5)
            
            # Switch to Main Thread to update UI
            self.after(0, self._finalize_startup)
            
        except Exception as e:
            print(f"Critical Startup Error: {e}")
            self.destroy()

    def _scan_cameras(self):
        """Map available cameras to indices."""
        self.available_cameras = {}
        real_names = self._get_platform_camera_names()
        
        # Check first 10 indices
        for i in range(10):
            # Enforce DirectShow on Windows to match pygrabber's list order
            backend = cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY
            cap = cv2.VideoCapture(i, backend)
            
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    # If we have a name at this index, use it
                    if i < len(real_names):
                        display_name = f"{real_names[i]} ({i})"
                    else:
                        display_name = f"Camera Source {i}"
                        
                    self.available_cameras[display_name] = i
                cap.release()
            
        if not self.available_cameras:
            self.available_cameras["No Camera Found"] = -1

    def _finalize_startup(self):
        """Called when loading is done. Builds UI and shows window."""
        self.splash.destroy()
        
        # Setup the actual UI Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._setup_sidebar()
        self._setup_main_area()
        self.show_library()
        
        # Show Main Window
        self.deiconify()
        
        # Lift to top
        self.lift()
        self.attributes('-topmost',True)
        self.after_idle(self.attributes,'-topmost',False)

    # --- UI SETUP METHODS ---
    def _setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)
        
        try:
            logo_img = ctk.CTkImage(light_image=Image.open(get_asset("logo_small.png")),
                                    dark_image=Image.open(get_asset("logo_small.png")),
                                    size=(30, 30))
        except:
            logo_img = None

        self.logo_label = ctk.CTkLabel(self.sidebar, text="  ThirdEye", image=logo_img,
                                       compound="left", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 20))
        
        self.btn_live = ctk.CTkButton(self.sidebar, text="Live Vision", height=40, command=self.show_live_vision)
        self.btn_live.grid(row=1, column=0, padx=20, pady=10)
        
        self.btn_lib = ctk.CTkButton(self.sidebar, text="Model Library", height=40, command=self.show_library)
        self.btn_lib.grid(row=2, column=0, padx=20, pady=10)
        
        self.btn_set = ctk.CTkButton(self.sidebar, text="Settings", height=40, command=self.show_settings)
        self.btn_set.grid(row=3, column=0, padx=20, pady=10)
        
        self.theme_switch = ctk.CTkSwitch(self.sidebar, text="Dark Mode", command=self._toggle_theme)
        self.theme_switch.select()
        self.theme_switch.grid(row=5, column=0, padx=20, pady=20)

    def _setup_main_area(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")

    # --- LIBRARY TAB ---
    def show_library(self):
        self._stop_camera()
        self._clear_main()
        
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=20)
        
        header = ctk.CTkLabel(header_frame, text="Intelligence Library", font=ctk.CTkFont(size=22, weight="bold"))
        header.pack(side="left")

        # Scrollable Frame
        self.scroll = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)
        self.scroll.grid_columnconfigure(0, weight=1)
        self.scroll.grid_columnconfigure(1, weight=1)
        
        # --- SCROLL FIX: Bind Global MouseWheel ONLY when hovering the frame ---
        self.scroll.bind("<Enter>", lambda e: self._bind_mouse_wheel())
        self.scroll.bind("<Leave>", lambda e: self._unbind_mouse_wheel())

        models = [
            ("Sentry Mode", "Perimeter human detection.", "assets/img_sentry.png"),
            ("Retail Analytics", "Heatmaps & customer counting.", "assets/img_retail.png"),
            ("License Plate ID", "Automatic LPR for gates.", "assets/img_lpr.png"),
            ("PPE Compliance", "Detects helmets and vests.", "assets/img_ppe.png"),
            ("Fire Watch", "Early smoke and fire detection.", "assets/img_fire.png"),
            ("Weapon Detect", "Identifies firearms in view.", "assets/img_weapon.png"),
            ("Face Verify", "Whitelist/Blacklist recognition.", "assets/img_face.png"),
            ("Loitering Alert", "Flags static subjects > 30s.", "assets/img_loiter.png"),
            ("Crowd Density", "Real-time occupancy tracking.", "assets/img_crowd.png"),
            ("Abandoned Obj", "Detects left bags/packages.", "assets/img_bag.png"),
        ]
        
        for i, (name, desc, img_path) in enumerate(models):
            self._create_grid_card(self.scroll, name, desc, img_path, i // 2, i % 2)

    # Helper methods for the scroll fix
    def _bind_mouse_wheel(self):
        self.bind_all("<MouseWheel>", self._on_mouse_wheel)  # Windows
        self.bind_all("<Button-4>", self._on_mouse_wheel)    # Linux Up
        self.bind_all("<Button-5>", self._on_mouse_wheel)    # Linux Down

    def _unbind_mouse_wheel(self):
        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")

    def _on_mouse_wheel(self, event):
        try:
            # Check OS for scroll direction and scaling
            if sys.platform == "linux":
                scroll_dir = -1 if event.num == 5 else 1
                self.scroll._parent_canvas.yview_scroll(int(scroll_dir), "units")
            else:
                # Windows/Mac: Divide by 120 for standard scaling
                self.scroll._parent_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    def _get_platform_camera_names(self):
        """Fetches real camera names using pygrabber (Win) or v4l2 (Linux)."""
        names = []
        
        # Windows: Use pygrabber (DirectShow)
        if os.name == 'nt':
            try:
                from pygrabber.dshow_graph import FilterGraph
                graph = FilterGraph()
                names = graph.get_input_devices()
            except ImportError:
                print("Tip: Install 'pygrabber' for real camera names on Windows.")
                # Fallback to PowerShell if pygrabber is missing
                import subprocess
                cmd = "Get-CimInstance Win32_PnPEntity | Where-Object { $_.PNPClass -eq 'Image' -or $_.PNPClass -eq 'Camera' } | Select-Object -ExpandProperty Caption"
                try:
                    result = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True)
                    if result.returncode == 0:
                        names = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                except: pass

        # Linux: Use /sys/class/video4linux
        elif sys.platform.startswith("linux"):
            try:
                v4l_path = Path("/sys/class/video4linux")
                if v4l_path.exists():
                    # Sort by logical index (video0, video1...)
                    video_devs = sorted([p for p in v4l_path.iterdir() if p.name.startswith("video")], 
                                      key=lambda x: int(x.name.replace("video", "")))
                    for dev in video_devs:
                        name_file = dev / "name"
                        if name_file.exists():
                            names.append(name_file.read_text().strip())
            except Exception as e:
                print(f"Linux Camera Scan Error: {e}")
            
        return names

    def _create_grid_card(self, parent, name, desc, img_path, r, c):
        card = ctk.CTkFrame(parent, corner_radius=15, border_width=1, border_color="#333333")
        card.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
        
        try:
            pil_img = Image.open(img_path)
            model_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(250, 140))
        except:
            model_img = None

        img_label = ctk.CTkLabel(card, text="", image=model_img)
        img_label.pack(pady=(15, 10))
        
        title = ctk.CTkLabel(card, text=name, font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(anchor="center")
        
        description = ctk.CTkLabel(card, text=desc, text_color="gray")
        description.pack(anchor="center", pady=(0, 10))

        # Activate Button
        is_active = (self.active_model_name == name)
        btn_text = "Active" if is_active else "Activate Model"
        btn_color = "green" if is_active else ["#3B8ED0", "#1F6AA5"]
        
        btn = ctk.CTkButton(card, text=btn_text, fg_color=btn_color,
                            command=lambda n=name: self._activate_and_switch(n))
        btn.pack(pady=(0, 20))

        # --- FIX: Recursively bind mouse wheel to all card elements ---
        def bind_scroll(widget):
            widget.bind("<MouseWheel>", self._on_mouse_wheel)  # Windows
            widget.bind("<Button-4>", self._on_mouse_wheel)    # Linux Up
            widget.bind("<Button-5>", self._on_mouse_wheel)    # Linux Down
            
        for widget in [card, img_label, title, description]:
            bind_scroll(widget)

    def _activate_and_switch(self, model_name):
        self.active_model_name = model_name
        self.show_live_vision()

    # --- LIVE VISION TAB ---
    def show_live_vision(self):
        self._stop_camera()
        self._clear_main()
        # Unbind scroll when leaving library
        self.unbind_all("<MouseWheel>") 
        
        # Control Bar
        controls = ctk.CTkFrame(self.main_frame, height=50, fg_color="transparent")
        controls.pack(fill="x", padx=20, pady=10)
        
        # Camera Selector
        lbl_cam = ctk.CTkLabel(controls, text="Source:", font=("Roboto", 14))
        lbl_cam.pack(side="left", padx=(0, 10))
        
        cam_options = list(self.available_cameras.keys())
        self.cam_dropdown = ctk.CTkOptionMenu(controls, values=cam_options, command=self._on_cam_change, width=200)
        self.cam_dropdown.set(cam_options[0] if cam_options else "No Camera")
        self.cam_dropdown.pack(side="left")

        # Active Model Indicator
        model_text = f"ACTIVE MODEL: {self.active_model_name}" if self.active_model_name else "RAW FEED"
        color = "#e63946" if self.active_model_name else "#2a9d8f"
        
        self.status_pill = ctk.CTkLabel(controls, text=f"  {model_text}  ", 
                                      fg_color=color, corner_radius=15, 
                                      text_color="white", font=("Roboto", 12, "bold"))
        self.status_pill.pack(side="right")

        # Video Area
        self.video_container = ctk.CTkFrame(self.main_frame, fg_color="#000000")
        self.video_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.video_label = ctk.CTkLabel(self.video_container, text="Starting Feed...", text_color="gray")
        self.video_label.pack(expand=True, fill="both")

        # Start Camera Thread
        self.stop_event = threading.Event()
        
        # Determine initial camera index
        start_cam = self.available_cameras.get(self.cam_dropdown.get(), 0)
        
        threading.Thread(target=self._camera_processing_loop, args=(start_cam,), daemon=True).start()
        
        # Start UI Update Loop (Main Thread)
        self._update_ui_loop()

    def _on_cam_change(self, selected_text):
        new_idx = self.available_cameras.get(selected_text)
        if new_idx is not None:
            self._stop_camera()
            # Brief pause to let thread die
            self.after(200, lambda: self._restart_camera(new_idx))

    def _restart_camera(self, idx):
        self.stop_event = threading.Event()
        threading.Thread(target=self._camera_processing_loop, args=(idx,), daemon=True).start()

    def _update_ui_loop(self):
        """Updates the image label from the main thread to prevent flickering."""
        if hasattr(self, 'video_label') and self.latest_frame_image:
            self.video_label.configure(image=self.latest_frame_image, text="")
        
        if not self.stop_event.is_set():
            self.after(30, self._update_ui_loop) # ~30 FPS UI refresh

    def _camera_processing_loop(self, cam_index):
        if cam_index == -1: return
        cap = cv2.VideoCapture(cam_index)
        
        while not self.stop_event.is_set():
            ret, frame = cap.read()
            if not ret: break

            # --- PROCESS BASED ON ACTIVE MODEL ---
            identity = "Unknown"
            processed_frame = frame.copy()

            if self.active_model_name == "Face Verify":
                # Only run heavy face detection if selected
                identity = self.face_engine.process_frame(frame)
                
                # Draw Box
                color = (0, 255, 0) if identity != "Unknown" else (0, 0, 255)
                cv2.rectangle(processed_frame, (0,0), (640, 50), (0,0,0), -1)
                cv2.putText(processed_frame, f"ID: {identity}", (20, 35), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            
            elif self.active_model_name == "Sentry Mode":
                # Sentry Implementation - Human Only
                detections = self.sentry_engine.process_frame(frame)
                
                if detections:
                    # Alert Status
                    cv2.putText(processed_frame, "SENTRY ALERT", (20, 50), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    
                    for (box, score, label) in detections:
                        x, y, w, h = box
                        # Draw Red Box
                        cv2.rectangle(processed_frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                        
                        # Display "Person" and Confidence
                        text = f"{label.upper()} {int(score * 100)}%"
                        cv2.putText(processed_frame, text, (x, y-10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                else:
                    # Scanning Status
                    cv2.putText(processed_frame, "SENTRY ACTIVE: SCANNING...", (20, 50), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # --- PREPARE FOR UI ---
            # 1. Trigger Plugins (only if needed)
            if identity != "Unknown":
                self._trigger_user_scripts(identity)

            # 2. Convert to CTkImage (Thread safe-ish, but better to keep lightweight)
            try:
                frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                im_pil = Image.fromarray(frame_rgb)
                
                # Calculate aspect ratio resize if needed, otherwise fit container
                # For now fixed size for stability
                ctk_img = ctk.CTkImage(light_image=im_pil, dark_image=im_pil, size=(800, 600))
                
                # Store for Main Thread
                self.latest_frame_image = ctk_img
            except Exception as e:
                print(f"Frame Error: {e}")
                continue
                
        cap.release()

    def _trigger_user_scripts(self, name):
        plugin_dir = "plugins"
        if not os.path.exists(plugin_dir): return
        for filename in os.listdir(plugin_dir):
            if filename.endswith(".py"):
                module_name = f"plugins.{filename[:-3]}"
                try:
                    user_plugin = importlib.import_module(module_name)
                    importlib.reload(user_plugin)
                    if hasattr(user_plugin, "on_recognition"):
                        user_plugin.on_recognition(name)
                except Exception:
                    pass

    def show_settings(self):
        self._stop_camera()
        self._clear_main()
        lbl = ctk.CTkLabel(self.main_frame, text=f"Hardware ID: {self.guard.machine_id}", font=ctk.CTkFont(family="Courier"))
        lbl.pack(pady=50)

    def _stop_camera(self):
        if hasattr(self, 'stop_event'):
            self.stop_event.set()

    def _clear_main(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def _toggle_theme(self):
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")

if __name__ == "__main__":
    app = ThirdEyeApp()
    app.mainloop()
