"""
Saves the current frame to the 'snapshots' directory.
Argument: 'prefix=my_name' (optional)
"""
import cv2
import os
import time

def run(context, args):
    frame = context.get("frame")
    if frame is None:
        print("[SNAPSHOT] Error: No frame data in context.")
        return

    # Parse args for custom prefix
    prefix = "snapshot"
    if "prefix=" in args:
        parts = args.split("prefix=")
        if len(parts) > 1:
            prefix = parts[1].split(" ")[0]

    save_dir = "snapshots"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.jpg"
    filepath = os.path.join(save_dir, filename)

    try:
        cv2.imwrite(filepath, frame)
        print(f"[SNAPSHOT] Saved: {filepath}")
    except Exception as e:
        print(f"[SNAPSHOT] Save failed: {e}")