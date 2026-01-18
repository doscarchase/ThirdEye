# ----------------------------------------------------------------------------
#  ThirdEye AI Vision Suite - Proprietary and Confidential
#  Copyright (c) 2026 Devon Chase. All rights reserved.
# ----------------------------------------------------------------------------
"""
Simulates a visual flash (Argument: 'color=red' or 'color=white')
"""
import customtkinter as ctk
import time

def run(context, args):
    flash = None
    try:
        color = "white"
        if "red" in args: color = "#FF0000"
        
        # Create Toplevel Window
        flash = ctk.CTkToplevel()
        
        # FIX 1: Use manual geometry instead of native fullscreen.
        # This prevents macOS from creating a new "Space" (the sliding animation).
        screen_width = flash.winfo_screenwidth()
        screen_height = flash.winfo_screenheight()
        flash.geometry(f"{screen_width}x{screen_height}+0+0")
        
        # Remove title bar and borders
        flash.overrideredirect(True)
        
        # Visual properties
        flash.configure(fg_color=color)
        flash.attributes("-alpha", 0.4) # Transparency
        flash.attributes("-topmost", True)
        
        # FIX 2: Force the window to render immediately (required if running in a thread)
        flash.update()
        
        # Hold the flash
        time.sleep(0.1)
        
    except Exception as e:
        print(f"[SCRIPT] Flash Error: {e}")
        
    finally:
        # FIX 3: Robust Cleanup
        # Using 'finally' ensures this runs even if an error occurred above.
        if flash:
            try:
                flash.destroy()
                # FIX 4: Force update again to process the destroy event immediately
                # This prevents ghost windows from getting stuck on screen.
                flash.update()
            except Exception as e:
                print(f"[SCRIPT] Cleanup Error: {e}")

    print(f"[SCRIPT] VISUAL FLASH ACTIVATED: {color}")
