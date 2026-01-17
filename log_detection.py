# ----------------------------------------------------------------------------
#  ThirdEye AI Vision Suite - Proprietary and Confidential
#  Copyright (c) 2026 Devon Chase. All rights reserved.
# ----------------------------------------------------------------------------
"""
Appends the detection event to 'detection_log.txt'.
"""
import datetime

def run(context, args):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] Model: {context.get('model')} | ID: {context.get('identity')} | Score: {context.get('score')}\n"
    
    with open("detection_log.txt", "a") as f:
        f.write(line)
    print("[SCRIPT] Logged to detection_log.txt")