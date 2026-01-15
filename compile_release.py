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
import os
import sys

# The specific command to harden the binary
command = [
    "python -m nuitka",
    "--standalone",                   # Create a portable folder
    "--onefile",                      # Create a single .exe (optional, standalone is faster)
    "--plugin-enable=tk-inter",       # Needed for CustomTkinter
    "--plugin-enable=numpy",          # Needed for AI
    "--include-data-dir=customtkinter=customtkinter", # Force include UI assets
    "--windows-disable-console",      # No black popup window
    "--company-name=CleanCountyCo",   # Your metadata
    "--product-name=ThirdEye",
    "--product-version=1.0.0",
    "main.py"                         # Your entry point
]

full_command = " ".join(command)
print(f"Building Release with Nuitka...\nCommand: {full_command}")
os.system(full_command)