import subprocess
import os
import time
from scanner.auto_crop_photos import auto_crop_photos


def scan_to_file(output_dir="scans", filename_prefix="scan"):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f"{filename_prefix}_{timestamp}.jpg")

    try:
        result = subprocess.run([
            "scanimage",
            "-d", "genesys:libusb:001:018",
            "--format=jpeg",
            "--mode", "Color",
            "--resolution", "1200",
            f"--output-file={filepath}"
        ], check=True)

        print(f"[Scanner] Scan saved to: {filepath}")

        # Auto-crop photos after scanning with debug enabled
        cropped_paths = auto_crop_photos(filepath, debug=True, min_area=10000)
        if cropped_paths:
            print(f"[Scanner] Cropped into {len(cropped_paths)} photo(s)")
            return cropped_paths  # Return all cropped paths
        else:
            print("[Scanner] No crops found, returning original scan")
            return [filepath]  # Return original scan path in list for consistency

    except subprocess.CalledProcessError as e:
        print("[Scanner] Failed to scan:", e)
        return []
