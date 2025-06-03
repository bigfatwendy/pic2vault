import cv2
import os
import numpy as np
from sklearn.cluster import KMeans


def auto_crop_photos(scan_path, output_dir="scans/crops", debug=True, min_area=50000, margin=10):
    os.makedirs(output_dir, exist_ok=True)
    img = cv2.imread(scan_path)
    if img is None:
        print(f"[AutoCrop] Failed to load image: {scan_path}")
        return []

    # === Estimate background color using KMeans clustering on entire image pixels ===
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
        print(f"[AutoCrop] Estimated background color via KMeans (BGR): {bg_color.tolist()}")
        bg_img = np.full_like(img, bg_color)
        bg_vis_path = os.path.join(output_dir, "debug_background_color_kmeans.jpg")
        cv2.imwrite(bg_vis_path, bg_img)
        print(f"[AutoCrop] Background color preview saved to: {bg_vis_path}")

    # === Create mask of non-background regions using basic thresholding ===
    diff = cv2.absdiff(img, bg_color)
    mask_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, mask_color = cv2.threshold(mask_gray, 30, 255, cv2.THRESH_BINARY)

    # === Edge-based mask to improve detection ===
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    # === Use Hough Line Transform to help complete edges near photo borders ===
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=50, maxLineGap=500)
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(edges, (x1, y1), (x2, y2), 255, 2)
    if debug:
        hough_path = os.path.join(output_dir, "debug_hough_lines.jpg")
        cv2.imwrite(hough_path, edges)
        print(f"[AutoCrop] Hough lines preview saved to: {hough_path}")

    # Combine both masks
    combined_mask = cv2.bitwise_or(mask_color, edges)

    # === Morphological operations to refine ===
    kernel = np.ones((5, 5), np.uint8)
    combined_mask = cv2.dilate(combined_mask, kernel, iterations=2)
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(combined_mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    preview = img.copy()
    all_contours_preview = img.copy()
    cv2.drawContours(all_contours_preview, contours, -1, (0, 0, 255), 2)
    if debug:
        all_path = os.path.join(output_dir, "debug_all_contours.jpg")
        cv2.imwrite(all_path, all_contours_preview)
        print(f"[AutoCrop] All contours debug preview saved to: {all_path}")

    print(f"[AutoCrop] Found {len(contours)} contours.")

    saved_paths = []
    height_limit, width_limit = img.shape[:2]
    edge_thresh = int(width_limit * 0.01)  # 1% of the width

    for i, cnt in enumerate(sorted(contours, key=cv2.contourArea, reverse=True)):
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)

        if len(approx) < 4:
            if debug:
                print(f"[AutoCrop] Skipped contour {i} due to insufficient corners: {len(approx)}")
            continue

        rect = cv2.minAreaRect(cnt)
        box = cv2.boxPoints(rect)
        box = box.astype(int)

        # Expand box if touching edge (incomplete contour)
        x_coords, y_coords = box[:, 0], box[:, 1]
        if np.any(x_coords <= edge_thresh) or np.any(x_coords >= width_limit - edge_thresh):
            box[:, 0] = np.clip(box[:, 0] - 5, 0, width_limit - 1)
        if np.any(y_coords <= edge_thresh) or np.any(y_coords >= height_limit - edge_thresh):
            box[:, 1] = np.clip(box[:, 1] - 5, 0, height_limit - 1)

        width = int(rect[1][0])
        height = int(rect[1][1])
        area = width * height
        aspect_ratio = max(width, height) / float(min(width, height)) if min(width, height) > 0 else 0

        if debug:
            print(f"[AutoCrop] Contour {i}: area={area}, aspect_ratio={aspect_ratio:.2f}, angle={rect[2]:.2f}")

        if area < min_area:
            if debug:
                print(f"[AutoCrop] Skipped contour {i} due to small area.")
            continue
        if not (0.4 < aspect_ratio < 3.2):
            if debug:
                print(f"[AutoCrop] Skipped contour {i} due to aspect ratio.")
            continue

        box[:, 0] = np.clip(box[:, 0], 5, width_limit - 5)
        box[:, 1] = np.clip(box[:, 1], 5, height_limit - 5)

        src_pts = box.astype("float32")
        dst_pts = np.array([[0, height-1], [0, 0], [width-1, 0], [width-1, height-1]], dtype="float32")
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        warped = cv2.warpPerspective(img, M, (width, height))

        y1 = max(0, margin)
        y2 = min(warped.shape[0], height - margin)
        x1 = max(0, margin)
        x2 = min(warped.shape[1], width - margin)
        cropped = warped[y1:y2, x1:x2]

        out_path = os.path.join(output_dir, f"photo_{i+1}.jpg")
        cv2.imwrite(out_path, cropped)
        saved_paths.append(out_path)

        if debug:
            print(f"[AutoCrop] Saved crop to: {out_path}")
            cv2.drawContours(preview, [box], -1, (0, 255, 0), 2)
            cX, cY = np.mean(box[:, 0]), np.mean(box[:, 1])
            cv2.putText(preview, f"{i+1}", (int(cX), int(cY)), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    if debug:
        labeled_preview_path = os.path.join(output_dir, "debug_labeled_contours.jpg")
        cv2.imwrite(labeled_preview_path, preview)
        print(f"[AutoCrop] Labeled contour preview saved to: {labeled_preview_path}")

    print(f"[AutoCrop] Extracted {len(saved_paths)} photo(s).")
    return saved_paths
