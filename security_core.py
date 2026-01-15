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
import platform
import subprocess
import os
import sys
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

class HardwareGuard:
    def __init__(self):
        # This generates the ID strictly from the local machine's components.
        # No internet connection or admin dashboard is required.
        self.machine_id = self._get_hardware_fingerprint()
        
        # Salt should be unique to your company/product version
        self.key = self._derive_key(self.machine_id, salt=b"THIRDEYE_V1_PROD_SALT")

    def _get_cmd_output(self, cmd):
        try:
            return subprocess.check_output(cmd, shell=True).decode().strip()
        except:
            return "UNKNOWN"

    def _get_hardware_fingerprint(self):
        """
        Generates a unique hash binding this software to the physical CPU/Motherboard.
        """
        system = platform.system()
        uuid = ""
        
        if system == "Windows":
            # Get Motherboard UUID
            uuid = self._get_cmd_output('wmic csproduct get uuid').split('\n')[1].strip()
        elif system == "Darwin": # MacOS
            # Get IOPlatformUUID
            uuid = self._get_cmd_output("ioreg -d2 -c IOPlatformExpertDevice | awk -F\\\" '/IOPlatformUUID/{print $(NF-1)}'")
        elif system == "Linux":
            # Get machine-id
            uuid = self._get_cmd_output("cat /etc/machine-id")

        # Combine with MAC Address to prevent simple UUID spoofing
        from uuid import getnode
        mac = str(getnode())
        
        raw_id = f"{uuid}-{mac}-{platform.processor()}"
        return raw_id

    def _derive_key(self, input_string, salt):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32, # 32 bytes = 256 bits
            salt=salt,
            iterations=400000, 
        )
        return kdf.derive(input_string.encode())

    def decrypt_to_memory(self, encrypted_path):
        """
        RUNTIME: Decrypts file directly into a RAM byte buffer.
        """
        if not os.path.exists(encrypted_path):
            raise FileNotFoundError("License/Model file missing.")
            
        with open(encrypted_path, 'rb') as f:
            file_data = f.read()
            
        nonce = file_data[:12]
        ciphertext = file_data[12:]
        aesgcm = AESGCM(self.key)
        
        try:
            return aesgcm.decrypt(nonce, ciphertext, None)
        except Exception as e:
            raise PermissionError("HARDWARE ID MISMATCH: Model cannot be loaded on this device.")