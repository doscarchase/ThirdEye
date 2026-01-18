# ----------------------------------------------------------------------------
#  ThirdEye AI Vision Suite - Proprietary and Confidential
#  Copyright (c) 2026 Devon Chase. All rights reserved.
# ----------------------------------------------------------------------------
"""
Plays a system beep and prints a message.
"""
import os
import platform
import time

def run(context, args):
    identity = context.get('identity', 'Unknown')
    print(f"[SCRIPT] 🚨 System Alert Triggered by {identity}!")
    
    system_name = platform.system()
    
    try:
        if system_name == "Windows":
            import winsound
            # Frequency 1000Hz, Duration 1000ms
            winsound.Beep(1000, 1000) 
            
        elif system_name == "Darwin": # macOS
            # 'afplay' is standard on macOS
            os.system('afplay /System/Library/Sounds/Glass.aiff')
            
        else: # Linux
            # Try to use the system bell or aplay
            print("\a") # Standard bell
            os.system('play -n synth 0.5 sine 880 >/dev/null 2>&1') # Requires Sox, fails silently if missing
            
    except Exception as e:
        print(f"[SCRIPT] Audio failed: {e}")
