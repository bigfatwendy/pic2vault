import subprocess
import os
import time

def scan_to_file(output_dir="scans", filename_prefix="scan"):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f"{filename_prefix}_{timestamp}.jpg")

    try:
        result = subprocess.run([
            "scanimage",
            "-d", "genesys:libusb:001:007",
            "--format=jpeg",
            "--mode", "Color",
            "--resolution", "1200",
            f"--output-file={filepath}"
        ], check=True)

        print(f"[Scanner] Scan saved to: {filepath}")
        return filepath
    except subprocess.CalledProcessError as e:
        print("[Scanner] Failed to scan:", e)
        return None
