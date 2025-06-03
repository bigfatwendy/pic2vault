from scanner.auto_crop_photos import auto_crop_photos

def test_from_existing_image():
    input_path = "scans/scan_test.jpg"  # <-- Replace with your actual image path
    print(f"[Test] Running auto-crop on: {input_path}")

    cropped_paths = auto_crop_photos(input_path)
    if cropped_paths:
        print(f"[Test] Cropped {len(cropped_paths)} photo(s):")
        for path in cropped_paths:
            print(f" - {path}")
    else:
        print("[Test] No crops found.")

if __name__ == "__main__":
    test_from_existing_image()
