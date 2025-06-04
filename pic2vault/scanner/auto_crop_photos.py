import cv2
import os
import numpy as np
from sklearn.cluster import KMeans

def auto_crop_photos(scan_path, output_dir="scans/crops", debug=True):
    os.makedirs(output_dir, exist_ok=True)
    img = cv2.imread(scan_path)
    if img is None:
        print(f"[AutoCrop] Failed to load image: {scan_path}")
        return []

    if debug:
        print("[AutoCrop] Image loaded successfully.")

    # Estimate background color using KMeans clustering on a random sample of the image
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
        bg_color_path = os.path.join(output_dir, "debug_bg_color.jpg")
        cv2.imwrite(bg_color_path, bg_color_img)
        print(f"[AutoCrop] Saved background color debug image to: {bg_color_path}")

    # Remove background using distance to background color
    diff = np.linalg.norm(img.astype(np.int16) - bg_color.astype(np.int16), axis=2)
    mask = (diff > 40).astype(np.uint8) * 255

    if debug:
        print("[AutoCrop] Removed background color from scan")

    # Remove 1% border from all sides of the mask
    h, w = img.shape[:2]
    border_h = int(h * 0.01)
    border_w = int(w * 0.01)
    mask[:border_h, :] = 0
    mask[-border_h:, :] = 0
    mask[:, :border_w] = 0
    mask[:, -border_w:] = 0

    # Filter out small white regions (less than 1% of image area)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    image_area = h * w
    min_area = image_area * 0.01

    filtered_mask = np.zeros_like(mask)
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] >= min_area:
            filtered_mask[labels == i] = 255
        elif debug:
            print(f"[AutoCrop] Removed small region {i} (area={stats[i, cv2.CC_STAT_AREA]})")

    if debug:
        mask_debug_path = os.path.join(output_dir, "debug_mask_filtered.jpg")
        cv2.imwrite(mask_debug_path, filtered_mask)
        print(f"[AutoCrop] Saved filtered mask debug image to: {mask_debug_path}")

    # Apply mask to the original image
    foreground = cv2.bitwise_and(img, img, mask=filtered_mask)

    if debug:
        debug_fg_path = os.path.join(output_dir, "debug_foreground_removed.jpg")
        cv2.imwrite(debug_fg_path, foreground)
        print(f"[AutoCrop] Saved foreground debug image to: {debug_fg_path}")

    # Find contours in the mask
    contours, _ = cv2.findContours(filtered_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    overlay = img.copy()

    for i, cnt in enumerate(contours):
        if len(cnt) >= 3:
            epsilon = 0.02 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            if len(approx) >= 3:
                rect = cv2.minAreaRect(cnt)
                box = cv2.boxPoints(rect)
                box = np.intp(box)
                cv2.drawContours(overlay, [box], 0, (0, 255, 0), 2)
                cv2.putText(overlay, str(i), tuple(box[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    if debug:
        overlay_path = os.path.join(output_dir, "debug_overlay_crops.jpg")
        cv2.imwrite(overlay_path, overlay)
        print(f"[AutoCrop] Saved debug overlay with crops to: {overlay_path}")

    return []
