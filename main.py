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
        
        # 2. Setup Basic Window Properties (so it's ready when shown)
        self.title("ThirdEye AI Suite")
        self.geometry("1200x800")
        self.base_path = Path(__file__).parent / "assets"
        
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
        
        # 4. Start Loading Thread (Heavy lifting happens here)
        threading.Thread(target=self._load_resources, daemon=True).start()

    def _load_resources(self):
        """Loads heavy libraries and assets while updating splash screen."""
        try:
            # -- STAGE 1: Security Core --
            self.splash.update_progress(0.1, "Verifying Hardware ID...")
            global HardwareGuard
            from security_core import HardwareGuard
            self.guard = HardwareGuard()
            time.sleep(0.3) # Artificial delay for UX smoothness

            # -- STAGE 2: AI Libraries --
            self.splash.update_progress(0.3, "Loading Neural Engine (OpenCV)...")
            global cv2
            import cv2
            
            self.splash.update_progress(0.4, "Shaking The Robots Awake...")
            # Pre-load any images if necessary here
            time.sleep(1.4)

            self.splash.update_progress(0.5, "Initializing Recognition Models...")
            global FaceEngine
            from recognition_engine import FaceEngine
            
            # -- STAGE 3: UI Assets --
            self.splash.update_progress(0.8, "Loading Interface Assets...")
            # Pre-load any images if necessary here
            time.sleep(0.2)

            self.splash.update_progress(0.9, "Petting Soft Kitties...")
            # Pre-load any images if necessary here
            time.sleep(1.2)

            # -- FINISH --
            self.splash.update_progress(1.0, "Ready!")
            time.sleep(0.5)
            
            # Switch to Main Thread to update UI
            self.after(0, self._finalize_startup)
            
        except Exception as e:
            print(f"Critical Startup Error: {e}")
            self.destroy()

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

    # --- UI SETUP METHODS (Same as before) ---
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
        self._stop_camera()
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

    def show_live_vision(self):
        self._stop_camera()
        self._clear_main()
        
        self.video_label = ctk.CTkLabel(self.main_frame, text="")
        self.video_label.pack(pady=10)
        
        self.status_label = ctk.CTkLabel(self.main_frame, text="System Active", font=ctk.CTkFont(size=16))
        self.status_label.pack(pady=5)

        # Start Camera Thread
        self.stop_event = threading.Event()
        self.face_engine = FaceEngine(db_path="assets/known_faces") # Already imported in splash
        threading.Thread(target=self._camera_loop, daemon=True).start()

    def _camera_loop(self):
        cap = cv2.VideoCapture(0)
        while not self.stop_event.is_set():
            ret, frame = cap.read()
            if not ret: break

            # 1. Run Recognition
            identity = self.face_engine.process_frame(frame)
            
            # 2. Trigger Plugins
            self._trigger_user_scripts(identity)

            # 3. Update UI
            # Draw on frame
            color = (0, 255, 0) if identity != "Unknown" else (0, 0, 255)
            cv2.rectangle(frame, (0,0), (640, 50), (0,0,0), -1)
            cv2.putText(frame, f"TARGET: {identity}", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            
            # Convert for Tkinter
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            im_pil = Image.fromarray(frame_rgb)
            ctk_img = ctk.CTkImage(light_image=im_pil, dark_image=im_pil, size=(800, 600))
            
            try:
                self.video_label.configure(image=ctk_img, text="") 
            except:
                break
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
