import cv2
import os
import numpy as np
import time
from sklearn.cluster import KMeans

def remove_bg_border(image, bg_color, threshold=40):
    diff = np.linalg.norm(image.astype(np.int16) - bg_color.astype(np.int16), axis=2)
    return (diff > threshold).astype(np.uint8) * 255

def trim_border_from_crop(crop, bg_color, threshold=80):
    gray_diff = np.linalg.norm(crop.astype(np.int16) - bg_color.astype(np.int16), axis=2).astype(np.uint8)
    mask = (gray_diff > threshold).astype(np.uint8) * 255
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return crop
    x, y, w, h = cv2.boundingRect(max(contours, key=cv2.contourArea))
    return crop[y:y+h, x:x+w]

def auto_crop_photos(scan_path, output_dir="scans/crops", debug=False):
    os.makedirs(output_dir, exist_ok=True)
    img = cv2.imread(scan_path)
    if img is None:
        print(f"[AutoCrop] Failed to load image: {scan_path}")
        return []

    if debug:
        print("[AutoCrop] Image loaded successfully.")

    # Estimate background color
    reshaped_img = img.reshape(-1, 3)
    sample_indices = np.random.choice(reshaped_img.shape[0], size=min(10000, reshaped_img.shape[0]), replace=False)
    sampled_pixels = reshaped_img[sample_indices]

    kmeans = KMeans(n_clusters=3, random_state=42, n_init='auto')
    kmeans.fit(sampled_pixels)
    cluster_centers = kmeans.cluster_centers_.astype(np.uint8)
    labels, counts = np.unique(kmeans.labels_, return_counts=True)
    dominant_index = np.argmax(counts)
    bg_color = cluster_centers[dominant_index]

    if debug:
        print(f"[AutoCrop] Estimated background color: {bg_color}")
        bg_color_img = np.full((100, 100, 3), bg_color, dtype=np.uint8)
        cv2.imwrite(os.path.join(output_dir, "debug_bg_color.jpg"), bg_color_img)

    # Create background-removed mask
    mask = remove_bg_border(img, bg_color)

    # Remove 1% border
    h, w = img.shape[:2]
    border_h = int(h * 0.01)
    border_w = int(w * 0.01)
    mask[:border_h, :] = 0
    mask[-border_h:, :] = 0
    mask[:, :border_w] = 0
    mask[:, -border_w:] = 0

    # Filter small regions
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    image_area = h * w
    min_area = image_area * 0.01

    filtered_mask = np.zeros_like(mask)
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] >= min_area:
            filtered_mask[labels == i] = 255

    if debug:
        cv2.imwrite(os.path.join(output_dir, "debug_mask_filtered.jpg"), filtered_mask)

    # Apply filtered mask
    foreground = cv2.bitwise_and(img, img, mask=filtered_mask)
    if debug:
        cv2.imwrite(os.path.join(output_dir, "debug_foreground_removed.jpg"), foreground)

    # Find and crop regions
    contours, _ = cv2.findContours(filtered_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    overlay = img.copy()
    cropped_paths = []

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    for i, cnt in enumerate(contours):
        if len(cnt) >= 3:
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            box = np.intp(box)
            width, height = int(rect[1][0]), int(rect[1][1])

            if width > 0 and height > 0:
                src_pts = box.astype("float32")
                dst_pts = np.array([[0, height - 1], [0, 0], [width - 1, 0], [width - 1, height - 1]], dtype="float32")
                M = cv2.getPerspectiveTransform(src_pts, dst_pts)
                warped = cv2.warpPerspective(img, M, (width, height))
                cleaned = trim_border_from_crop(warped, bg_color)

                crop_path = os.path.join(output_dir, f"photo_{timestamp}_{i+1}.jpg")
                cv2.imwrite(crop_path, cleaned)
                cropped_paths.append(crop_path)

                if debug:
                    cv2.drawContours(overlay, [box], 0, (0, 255, 0), 2)
                    cv2.putText(overlay, str(i), tuple(box[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    print(f"[AutoCrop] Saved cropped photo: {crop_path}")

    if debug:
        cv2.imwrite(os.path.join(output_dir, "debug_overlay_crops.jpg"), overlay)

    return cropped_paths
