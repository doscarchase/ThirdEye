#  ----------------------------------------------------------------------------
#  ThirdEye AI Vision Suite - Proprietary and Confidential
#  Copyright (c) 2026 Devon Chase. All rights reserved.
#  ----------------------------------------------------------------------------
import cv2
import numpy as np

class SentryEngine:
    def __init__(self):
        """
        Initializes the Sentry Mode engine.
        Uses OpenCV's HOG + SVM People Detector which is BSD Licensed
        (Free for commercial use and resale, unlike YOLOv8/AGPL).
        """
        # 1. Initialize Background Subtractor for Motion Detection
        # history=500: learns background over time
        # varThreshold=16: sensitivity (lower is more sensitive)
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=25, detectShadows=True
        )

        # 2. Initialize HOG Descriptor for Human Detection
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    def process_frame(self, frame):
        """
        Detects moving humans in the frame.
        Returns: list of bounding boxes [(x, y, w, h), ...]
        """
        detections = []
        height, width = frame.shape[:2]

        # Optimization: Resize frame for faster processing
        # We process on a smaller scale (e.g., width 640) to keep FPS high
        process_width = 640
        scale = width / float(process_width)
        process_height = int(height / scale)
        
        small_frame = cv2.resize(frame, (process_width, process_height))

        # --- STEP 1: Motion Check ---
        # Apply background subtraction to find moving areas
        fg_mask = self.bg_subtractor.apply(small_frame)
        
        # Remove shadows (gray pixels) and noise
        _, fg_mask = cv2.threshold(fg_mask, 250, 255, cv2.THRESH_BINARY)
        
        # Calculate amount of motion
        motion_ratio = cv2.countNonZero(fg_mask) / (process_width * process_height)
        
        # Threshold: If < 0.5% of frame is moving, ignore (saves CPU)
        if motion_ratio < 0.005:
            return []

        # --- STEP 2: Human Detection ---
        # Only run HOG if motion is detected
        # winStride: Step size (8,8) is faster, (4,4) is more accurate
        # padding: Pad input for objects near border
        # scale: Image pyramid scale
        boxes, weights = self.hog.detectMultiScale(
            small_frame, 
            winStride=(8, 8), 
            padding=(8, 8), 
            scale=1.05
        )

        # --- STEP 3: Scale Results Back ---
        for (x, y, w, h) in boxes:
            # Scale coordinates back to original frame size
            real_rect = (
                int(x * scale),
                int(y * scale),
                int(w * scale),
                int(h * scale)
            )
            detections.append(real_rect)

        return detections