import cv2
import numpy as np
from skimage.measure import shannon_entropy
import os


def detect_faces(image, face_cascade_path=None):
    if face_cascade_path is None:
        face_cascade_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")

    if not os.path.exists(face_cascade_path):
        print(f"[AutoOrient] Haar cascade file not found: {face_cascade_path}")
        return []

    face_cascade = cv2.CascadeClassifier(face_cascade_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    return faces


def rotate_image(image, angle):
    if angle == 0:
        return image
    elif angle == 90:
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    elif angle == 180:
        return cv2.rotate(image, cv2.ROTATE_180)
    elif angle == 270:
        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    else:
        raise ValueError("Invalid rotation angle. Use 0, 90, 180, or 270.")


def auto_orient_image(image, save_debug=True, debug_dir="scans/crops", prefix="oriented"):
    if image is None:
        print(f"[AutoOrient] Received None image for orientation.")
        return None

    os.makedirs(debug_dir, exist_ok=True)

    # Step 1: Try face detection
    for angle in [0, 90, 180, 270]:
        rotated = rotate_image(image, angle)
        faces = detect_faces(rotated)
        for (x, y, w, h) in faces:
            aspect_ratio = w / float(h)
            if 0.75 < aspect_ratio < 1.33:  # heuristically prefer upright faces
                if save_debug:
                    debug_path = os.path.join(debug_dir, f"{prefix}_face_{angle}.jpg")
                    cv2.imwrite(debug_path, rotated)
                    print(f"[AutoOrient] Upright face detected at {angle}°, saved: {debug_path}")
                return rotated

    # Step 2: Fallback to entropy-based orientation
    max_entropy = -1
    best_rotation = image
    best_angle = 0

    for angle in [0, 90, 180, 270]:
        rotated = rotate_image(image, angle)
        entropy = shannon_entropy(cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY))
        if entropy > max_entropy:
            max_entropy = entropy
            best_rotation = rotated
            best_angle = angle

    if save_debug:
        debug_path = os.path.join(debug_dir, f"{prefix}_entropy_{best_angle}.jpg")
        cv2.imwrite(debug_path, best_rotation)
        print(f"[AutoOrient] Using entropy fallback at {best_angle}°, saved: {debug_path}")

    return best_rotation
