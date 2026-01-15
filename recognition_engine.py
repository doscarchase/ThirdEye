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
import cv2
from deepface import DeepFace
import os
import pandas as pd

class FaceEngine:
    def __init__(self, db_path="known_faces"):
        self.db_path = db_path
        if not os.path.exists(db_path):
            os.makedirs(db_path)

    def process_frame(self, frame):
        """
        Scans a frame for faces and compares them to the local database.
        """
        try:
            # find() returns a list of pandas dataframes
            results = DeepFace.find(
                img_path=frame, 
                db_path=self.db_path, 
                detector_backend='mediapipe', 
                enforce_detection=False,
                model_name='VGG-Face', # MIT License
                silent=True
            )
            
            if len(results) > 0 and not results[0].empty:
                # The 'identity' column contains the path to the matching image
                match_path = results[0].iloc[0]['identity']
                name = os.path.basename(match_path).split('.')[0]
                return name
            return "Unknown"
        except Exception as e:
            return f"Error: {str(e)}"