# ----------------------------------------------------------------------------
#  ThirdEye AI Vision Suite - Proprietary and Confidential
#  Copyright (c) 2026 Devon Chase. All rights reserved.
# ----------------------------------------------------------------------------
"""
Plays a system beep and prints a message.
"""
import os

def run(context, args):
    print(f"[SCRIPT] System Alert Triggered by {context.get('identity')}!")
    # Simple beep
    if os.name == 'nt':
        import winsound
        winsound.Beep(1000, 500) # Frequency, Duration
    else:
        print("\a") # Unix bell