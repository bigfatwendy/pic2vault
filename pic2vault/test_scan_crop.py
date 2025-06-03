from scanner.scan_interface import scan_to_file

def main():
    print("[Test] Starting scan and auto-crop test...")
    cropped_images = scan_to_file()

    if cropped_images:
        print(f"[Test] {len(cropped_images)} image(s) returned:")
        for path in cropped_images:
            print(f" - {path}")
    else:
        print("[Test] No images returned.")

if __name__ == "__main__":
    main()
