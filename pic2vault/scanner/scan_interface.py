import subprocess
import os
import time
from scanner.auto_crop_photos import auto_crop_photos

SCAN_DEVICE_ID = "genesys:libusb:001:020"  # Default, will update if changed


def find_scan_device():
    try:
        output = subprocess.check_output(["scanimage", "-L"]).decode()
        for line in output.splitlines():
            if "Canon" in line and "LiDE" in line and "genesys" in line:
                return line.split(" `")[0].strip()
    except Exception as e:
        print("[Scanner] Error finding scan device:", e)
    return None


def scan_to_file(output_dir="scans", filename_prefix="scan"):
    global SCAN_DEVICE_ID
    os.makedirs(output_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f"{filename_prefix}_{timestamp}.jpg")

    # Check if device is available, otherwise search
    try:
        subprocess.run(["scanimage", "-d", SCAN_DEVICE_ID, "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print(f"[Scanner] Device {SCAN_DEVICE_ID} not found. Attempting to detect...")
        found = find_scan_device()
        if found:
            SCAN_DEVICE_ID = found
            print(f"[Scanner] Updated scan device to: {SCAN_DEVICE_ID}")
        else:
            print("[Scanner] No compatible scanner found.")
            return []

    try:
        result = subprocess.run([
            "scanimage",
            "-d", SCAN_DEVICE_ID,
            "--format=jpeg",
            "--mode", "Color",
            "--resolution", "1200",
            "--brightness", "20",
            "--contrast", "30",
            "--depth", "8",
           # "--custom-gamma", "no",
            f"--output-file={filepath}"
        ], check=True)

        print(f"[Scanner] Scan saved to: {filepath}")

        # Auto-crop photos after scanning with debug enabled
        cropped_paths = auto_crop_photos(filepath, debug=False)
        if cropped_paths:
            print(f"[Scanner] Cropped into {len(cropped_paths)} photo(s)")
            return cropped_paths  # Return all cropped paths
        else:
            print("[Scanner] No crops found, returning original scan")
            return [filepath]  # Return original scan path in list for consistency

    except subprocess.CalledProcessError as e:
        print("[Scanner] Failed to scan:", e)
        return []
