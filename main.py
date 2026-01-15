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
import onnxruntime as ort
import threading
from PIL import Image, ImageTk # Added ImageTk for video display
import os
import sys
from pathlib import Path
from security_core import HardwareGuard
import importlib

# REMOVED: import cv2 (Move to lazy load)
# REMOVED: from recognition_engine import FaceEngine (Move to lazy load)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(SCRIPT_DIR, "assets")

def get_asset(filename):
    return os.path.join(ASSETS_DIR, filename)

ctk.set_appearance_mode("System") 
ctk.set_default_color_theme("dark-blue")

class ThirdEyeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.base_path = Path(__file__).parent / "assets"
        self.guard = HardwareGuard()
        self.active_session = None 
        
        # Window Setup
        self.title("ThirdEye AI Suite")
        self.geometry("1200x800")
        
        # Icon Setup
        try:
            if os.name == 'nt':
                icon_path = self.base_path / "app_icon.ico"
                self.iconbitmap(str(icon_path))
            else:
                icon_path = self.base_path / "thirdeye_logo.png"
                img = Image.open(icon_path)
                self.tk.call('wm', 'iconphoto', self._w, ImageTk.PhotoImage(img))
        except Exception as e:
            print(f"Warning: Icon setup failed: {e}")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._setup_sidebar()
        self._setup_main_area()
        self.show_library()

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

    def show_library(self):
        self._stop_camera() # Stop camera if leaving the page
        self._clear_main()
        
        header = ctk.CTkLabel(self.main_frame, text="Intelligence Library", font=ctk.CTkFont(size=22, weight="bold"))
        header.pack(pady=20, padx=30, anchor="w")
        
        scroll = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=10)
        scroll.grid_columnconfigure(0, weight=1)
        scroll.grid_columnconfigure(1, weight=1)

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
            self._create_grid_card(scroll, name, desc, img_path, i // 2, i % 2)

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
        description.pack(anchor="center", pady=(0, 15))

    def show_settings(self):
        self._stop_camera()
        self._clear_main()
        lbl = ctk.CTkLabel(self.main_frame, text=f"Hardware ID: {self.guard.machine_id}", font=ctk.CTkFont(family="Courier"))
        lbl.pack(pady=50)

    # --- LAZY LOADING & FIXED LOGIC START HERE ---

    def show_live_vision(self):
        self._clear_main()
        
        # UI for Loading State
        self.status_label = ctk.CTkLabel(self.main_frame, text="Initializing Neural Engine...", font=ctk.CTkFont(size=16))
        self.status_label.pack(pady=20)
        
        self.video_label = ctk.CTkLabel(self.main_frame, text="")
        self.video_label.pack(pady=10)

        # Start the heavy loading in a separate thread to keep UI responsive
        threading.Thread(target=self._init_camera_thread, daemon=True).start()

    def _init_camera_thread(self):
        """Lazy load heavy libraries only when needed."""
        global cv2, FaceEngine
        
        # Import here so app startup isn't blocked!
        if 'cv2' not in globals():
            import cv2
        if 'FaceEngine' not in globals():
            from recognition_engine import FaceEngine
            
        # Initialize Engine
        self.face_engine = FaceEngine(db_path="assets/known_faces")
        
        # Start Loop
        self.stop_event = threading.Event()
        self._camera_loop()

    def _camera_loop(self):
        cap = cv2.VideoCapture(0)
        while not self.stop_event.is_set():
            ret, frame = cap.read()
            if not ret: break

            # 1. Run Recognition
            identity = self.face_engine.process_frame(frame)
            
            # 2. Trigger Plugins
            self._trigger_user_scripts(identity)

            # 3. Update GUI (Must convert CV2 image to CTkImage)
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Draw name on frame
            cv2.putText(frame_rgb, f"ID: {identity}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Convert to PIL Image
            im_pil = Image.fromarray(frame_rgb)
            ctk_img = ctk.CTkImage(light_image=im_pil, dark_image=im_pil, size=(640, 480))
            
            # Update Label (Use 'after' for thread safety is best, but this works for simple apps)
            try:
                self.video_label.configure(image=ctk_img, text="") 
                self.status_label.configure(text=f"System Active: {identity}")
            except:
                break # Window closed
            
        cap.release()

    def _trigger_user_scripts(self, name):
        plugin_dir = "plugins"
        if not os.path.exists(plugin_dir): return

        for filename in os.listdir(plugin_dir):
            if filename.endswith(".py"):
                module_name = f"plugins.{filename[:-3]}"
                try:
                    user_plugin = importlib.import_module(module_name)
                    # Reload allows editing plugins while app runs
                    importlib.reload(user_plugin) 
                    if hasattr(user_plugin, "on_recognition"):
                        user_plugin.on_recognition(name)
                except Exception as e:
                    print(f"Plugin Error: {e}")

    def _stop_camera(self):
        """Helper to safely stop the thread when switching tabs."""
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