import cv2
import numpy as np
import math
import argparse

# --- MODERNIZED COLOR CONSTANTS ---
COLOR_ROD_SEED = (0, 0, 255)       
COLOR_REF_POINT = (255, 0, 0)      
COLOR_LINE_SHADOW = (0, 0, 0)      # Black for line shadows
COLOR_LINE = (255, 200, 0)         # Neon Blue/Cyan for high contrast
COLOR_ROD_CIRCLE = (0, 255, 100)   # Vivid Green
COLOR_FALLBACK_CIRCLE = (0, 140, 255) # Vivid Orange
COLOR_REF_LINE = (255, 255, 0)     
COLOR_TEXT = (255, 255, 255)       
COLOR_TEXT_BG = (30, 30, 30)       # Darker grey for better text contrast
TEXT_BG_ALPHA = 0.75               # Slightly more opaque for readability

# Analysis parameters
DEFAULT_ROD_RADIUS_PX = 15
ROI_SIZE = 120
NUM_RAYS_FOR_RADIUS = 36

class MarkingData:
    """Manages data during interactive marking process."""
    def __init__(self, image):
        self.image = image
        self.clone = image.copy()
        self.rod_seed_points = []
        self.reference_points = []
        self.mode = 'rods'
        self.finished = False

def print_header(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")

def print_success(message):
    print(f"✓ {message}")

def print_error(message):
    print(f"✗ {message}")

def print_info(message):
    print(f"ℹ {message}")

def print_warning(message):
    print(f"⚠ {message}")

def draw_ui(data):
    """Redraws the image, points, and UI buttons."""
    data.clone = data.image.copy()
    h, w = data.clone.shape[:2]

    # Draw existing rod points with numbers
    for i, pt in enumerate(data.rod_seed_points):
        cv2.circle(data.clone, pt, 10, COLOR_ROD_SEED, 3)
        cv2.putText(data.clone, str(i+1), (pt[0]+15, pt[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

    # Draw reference points
    for pt in data.reference_points:
        cv2.circle(data.clone, pt, 10, COLOR_REF_POINT, 3)
    if len(data.reference_points) == 2:
        cv2.line(data.clone, data.reference_points[0], data.reference_points[1], COLOR_REF_POINT, 2)

    # --- Draw UI Elements ---
    mode_text = f"MODE: {data.mode.upper()} (Press 's' to switch)"
    cv2.putText(data.clone, mode_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 3)

    # Undo Button
    cv2.rectangle(data.clone, (w - 280, 20), (w - 160, 70), (0, 0, 200), -1)
    cv2.putText(data.clone, "UNDO", (w - 260, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    # Confirm Button
    cv2.rectangle(data.clone, (w - 140, 20), (w - 20, 70), (0, 200, 0), -1)
    cv2.putText(data.clone, "CONFIRM", (w - 130, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

def mouse_callback(event, x, y, flags, param):
    """Handle mouse click events and UI button interactions."""
    data = param
    h, w = data.clone.shape[:2]

    def do_undo():
        if data.mode == 'rods' and data.rod_seed_points:
            data.rod_seed_points.pop()
            print_info("Undo: Removed last rod point.")
        elif data.mode == 'reference' and data.reference_points:
            data.reference_points.pop()
            print_info("Undo: Removed last reference point.")
        draw_ui(data)

    if event == cv2.EVENT_RBUTTONDOWN:
        do_undo()
        return

    if event == cv2.EVENT_LBUTTONDOWN:
        # Check UNDO button
        if w - 280 <= x <= w - 160 and 20 <= y <= 70:
            do_undo()
            return
            
        # Check CONFIRM button
        if w - 140 <= x <= w - 20 and 20 <= y <= 70:
            print_success("Selections confirmed by user.")
            data.finished = True
            return

        # Normal canvas click
        if data.mode == 'rods':
            data.rod_seed_points.append((x, y))
            print_success(f"Rod #{len(data.rod_seed_points)} marked at ({x}, {y})")
        elif data.mode == 'reference':
            if len(data.reference_points) < 2:
                data.reference_points.append((x, y))
                if len(data.reference_points) == 2:
                    print_success("Reference object fully marked.")
        
        draw_ui(data)

def display_instructions():
    print_header("REBAR ANALYZER")
    print("INSTRUCTIONS:")
    print("   1. Click on top surface of each rebar rod")
    print("   2. Press 's' to switch to Reference Object mode")
    print("   3. Click two endpoints of known-length reference object")
    print("\nCONTROLS:")
    print("   Right-Click OR Click 'UNDO' to remove a point")
    print("   Click 'CONFIRM' when finished")
    print("\nDEBUG MODE:")
    print("   Run with '--debug' to visualize detection steps")
    print(f"\nFALLBACK RADIUS: {DEFAULT_ROD_RADIUS_PX}px (when edge detection fails)\n")

def get_user_markings(image):
    data = MarkingData(image)
    window_name = "Manual Rebar Analyzer"
    
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1280, 720) 
    
    draw_ui(data)
    cv2.setMouseCallback(window_name, mouse_callback, data)
    
    display_instructions()
    
    while not data.finished:
        cv2.imshow(window_name, data.clone)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('r'):
            print_info("Resetting markings...")
            data = MarkingData(image)
            draw_ui(data)
            cv2.setMouseCallback(window_name, mouse_callback, data)
        elif key == ord('s'):
            data.mode = 'reference' if data.mode == 'rods' else 'rods'
            print_info(f"Switched to {data.mode.capitalize()} Mode")
            draw_ui(data)
        elif key == ord('q'):
            break 
    
    cv2.destroyAllWindows()
    return data.rod_seed_points, data.reference_points

def create_fallback_detection(seed_point, rod_index):
    print_warning(f"Rod #{rod_index+1}: Using fallback radius ({DEFAULT_ROD_RADIUS_PX}px)")
    return seed_point, DEFAULT_ROD_RADIUS_PX, True  

def find_rod_circle(image, seed_point, is_debug=False, rod_index=0):
    half_roi = ROI_SIZE // 2
    x_start, y_start = max(seed_point[0] - half_roi, 0), max(seed_point[1] - half_roi, 0)
    x_end, y_end = x_start + ROI_SIZE, y_start + ROI_SIZE
    
    if x_end > image.shape[1] or y_end > image.shape[0]:
        print_error(f"Rod #{rod_index+1}: ROI out of bounds")
        return create_fallback_detection(seed_point, rod_index)
        
    roi = image[y_start:y_end, x_start:x_end]
    hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    roi_seed_point = (seed_point[0] - x_start, seed_point[1] - y_start)
    
    patch = hsv_roi[max(0, roi_seed_point[1]-2):roi_seed_point[1]+3, 
                    max(0, roi_seed_point[0]-2):roi_seed_point[0]+3]
    h, s, v = np.median(patch[:,:,0]), np.median(patch[:,:,1]), np.median(patch[:,:,2])
    
    h_range, s_range, v_range = 20, 70, 70
    lower_range = np.array([max(0, h-h_range), max(0, s-s_range), max(0, v-v_range)])
    upper_range = np.array([min(180, h+h_range), min(255, s+s_range), min(255, v+v_range)])
    color_mask = cv2.inRange(hsv_roi, lower_range, upper_range)
    
    kernel = np.ones((3, 3), np.uint8)
    mask_cleaned = cv2.morphologyEx(color_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    contours, _ = cv2.findContours(mask_cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        print_error(f"Rod #{rod_index+1}: No contours found")
        return create_fallback_detection(seed_point, rod_index)
    
    best_contour = max(contours, key=cv2.contourArea)
    M = cv2.moments(best_contour)
    if M["m00"] == 0:
        print_error(f"Rod #{rod_index+1}: Zero area contour")
        return create_fallback_detection(seed_point, rod_index)
        
    refined_center_roi = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
    
    radii = []
    for angle in np.linspace(0, 2 * np.pi, NUM_RAYS_FOR_RADIUS, endpoint=False):
        for r in range(1, int(ROI_SIZE/2)):
            x = int(refined_center_roi[0] + r * np.cos(angle))
            y = int(refined_center_roi[1] + r * np.sin(angle))
            
            if not (0 <= y < ROI_SIZE and 0 <= x < ROI_SIZE):
                break
            
            if mask_cleaned[y, x] == 0:
                radii.append(r)
                break
    
    if not radii or len(radii) < NUM_RAYS_FOR_RADIUS * 0.5:
        print_error(f"Rod #{rod_index+1}: Insufficient edge rays")
        return create_fallback_detection(seed_point, rod_index)
    
    final_radius = np.median(radii)
    final_global_center = (refined_center_roi[0] + x_start, refined_center_roi[1] + y_start)
    
    if is_debug:
        debug_img = roi.copy()
        cv2.circle(debug_img, refined_center_roi, int(final_radius), (0, 255, 0), 2)
        cv2.circle(debug_img, refined_center_roi, 3, (0, 255, 0), -1)
        cv2.circle(debug_img, roi_seed_point, 5, (0, 0, 255), 1)
        
        print_header(f"DEBUG ROD #{rod_index+1}")
        cv2.imshow(f"Rod {rod_index+1} - ROI", roi)
        cv2.imshow(f"Rod {rod_index+1} - Mask", mask_cleaned)
        cv2.imshow(f"Rod {rod_index+1} - Result", debug_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    print_success(f"Rod #{rod_index+1}: Radius = {final_radius:.2f}px (detected)")
    return final_global_center, final_radius, False 

def get_reference_length_from_user():
    while True:
        try:
            length_m = float(input("\nEnter reference object length in millimeters: "))
            if length_m > 0:
                return length_m
            else:
                print_error("Length must be positive")
        except ValueError:
            print_error("Invalid input. Enter a number (e.g., 0.5)")

def calculate_pixel_to_millimeter_ratio(reference_points, real_world_length):
    if len(reference_points) != 2 or real_world_length <= 0:
        return None
    pixel_distance = math.dist(reference_points[0], reference_points[1])
    return pixel_distance / real_world_length

def draw_text_with_bg(img, text, pos, font_scale, text_color, bg_color, pad=8, alpha=0.75):
    """Draws text with a cleaner background box and rounded-looking edges."""
    font = cv2.FONT_HERSHEY_DUPLEX
    thickness = max(1, int(font_scale * 1.5))
    (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    x, y = int(pos[0] - text_w / 2), int(pos[1] + text_h / 2)
    
    p1 = (max(x - pad, 0), max(y - text_h - pad, 0))
    p2 = (min(x + text_w + pad, img.shape[1]), min(y + baseline + pad, img.shape[0]))
    
    if p1[0] < p2[0] and p1[1] < p2[1]:
        sub_img = img[p1[1]:p2[1], p1[0]:p2[0]]
        bg_rect = np.full(sub_img.shape, bg_color, dtype=np.uint8)
        res = cv2.addWeighted(sub_img, 1 - alpha, bg_rect, alpha, 1.0)
        img[p1[1]:p2[1], p1[0]:p2[0]] = res
    
    cv2.putText(img, text, (x+1, y+1), font, font_scale, (0,0,0), thickness+1, cv2.LINE_AA)
    cv2.putText(img, text, (x, y), font, font_scale, text_color, thickness, cv2.LINE_AA)

def draw_rod_connections(image, sorted_indices, rod_data, pixels_per_millimeter, scale):
    """Draws glowing/shadowed lines that are always visible."""
    rod_centers = [data[0] for data in rod_data]
    
    thick_shadow = max(6, int(8 * scale))
    thick_main = max(2, int(3 * scale))
    font_s = max(0.6, 0.8 * scale)
    
    for i in range(len(sorted_indices)):
        start_idx, end_idx = sorted_indices[i], sorted_indices[(i + 1) % len(sorted_indices)]
        start_point, end_point = rod_centers[start_idx], rod_centers[end_idx]
        
        cv2.line(image, start_point, end_point, COLOR_LINE_SHADOW, thick_shadow)
        cv2.line(image, start_point, end_point, COLOR_LINE, thick_main)
        
        pixel_dist = math.dist(start_point, end_point)
        mid_point = (int((start_point[0] + end_point[0]) / 2), 
                    int((start_point[1] + end_point[1]) / 2))
        
        label_text = f"{pixel_dist:.1f}px"
        if pixels_per_millimeter:
            label_text += f" / {pixel_dist / pixels_per_millimeter:.2f}mm"
        
        draw_text_with_bg(image, label_text, mid_point, font_s, COLOR_TEXT, COLOR_TEXT_BG, alpha=TEXT_BG_ALPHA)

def draw_rod_labels(image, sorted_indices, rod_data, scale):
    """Draws high-visibility targeting reticles on the rods."""
    font_s = max(0.7, 0.9 * scale)
    thick_outline = max(4, int(6 * scale))
    thick_inner = max(2, int(3 * scale))
    
    for i, original_idx in enumerate(sorted_indices):
        center, radius, is_fallback = rod_data[original_idx]
        circle_color = COLOR_FALLBACK_CIRCLE if is_fallback else COLOR_ROD_CIRCLE
        
        cv2.circle(image, center, int(radius), (0, 0, 0), thick_outline)  
        cv2.circle(image, center, int(radius), circle_color, thick_inner)
        cv2.circle(image, center, max(2, int(3*scale)), circle_color, -1)
        
        label_pos = (center[0] + int(radius) + int(15*scale), center[1] - int(radius) - int(15*scale))
        label_text = f"R{i+1}" + ("*" if is_fallback else "")
        draw_text_with_bg(image, label_text, label_pos, font_s, COLOR_TEXT, COLOR_TEXT_BG, alpha=TEXT_BG_ALPHA)

def analyze_and_draw_results(image, detected_circles, ref_points, pixels_per_millimeter):
    result_image = image.copy()
    
    if not detected_circles:
        print_error("No rod detections found!")
        return None
        
    # --- CALCULATE DYNAMIC SCALE ---
    h, w = result_image.shape[:2]
    img_scale = max(w, h) / 1920.0 
    img_scale = max(0.6, img_scale) 
    
    rod_centers = [c[0] for c in detected_circles]
    fallback_count = sum(1 for c in detected_circles if len(c) > 2 and c[2])
    successful_radii = [c[1] for c in detected_circles if not (len(c) > 2 and c[2])]
    
    center_of_mass = np.mean(rod_centers, axis=0)
    sorted_indices = sorted(range(len(rod_centers)), 
                          key=lambda i: math.atan2(rod_centers[i][1] - center_of_mass[1], 
                                                  rod_centers[i][0] - center_of_mass[0]))
    
    # Pass the scale to our new drawing functions
    draw_rod_connections(result_image, sorted_indices, detected_circles, pixels_per_millimeter, img_scale)
    draw_rod_labels(result_image, sorted_indices, detected_circles, img_scale)
    
    # Draw reference line
    if len(ref_points) == 2 and pixels_per_millimeter:
        cv2.line(result_image, ref_points[0], ref_points[1], COLOR_REF_LINE, int(3*img_scale))
        ref_dist_px = math.dist(ref_points[0], ref_points[1])
        ref_text = f"Reference: {ref_dist_px:.1f}px / {ref_dist_px / pixels_per_millimeter:.3f}mm"
        ref_mid = (int((ref_points[0][0] + ref_points[1][0]) / 2), 
                  int((ref_points[0][1] + ref_points[1][1]) / 2) + int(30*img_scale))
        draw_text_with_bg(result_image, ref_text, ref_mid, 0.8*img_scale, COLOR_TEXT, (100, 0, 0), alpha=TEXT_BG_ALPHA)
    
    # Draw average radius and fallback info
    if successful_radii:
        avg_radius_px = np.mean(successful_radii)
    else:
        avg_radius_px = DEFAULT_ROD_RADIUS_PX
        
    radius_text = f"Avg. Rod Radius: {avg_radius_px:.2f}px"
    if pixels_per_millimeter:
        radius_text += f" / {avg_radius_px / pixels_per_millimeter:.4f}mm"
    
    pos = (int(50*img_scale), int(60*img_scale))
    font = cv2.FONT_HERSHEY_COMPLEX
    font_sz = 1.2 * img_scale
    
    cv2.putText(result_image, radius_text, (pos[0] + 3, pos[1] + 3), font, font_sz, (0, 0, 0), int(6*img_scale), cv2.LINE_AA)
    cv2.putText(result_image, radius_text, pos, font, font_sz, (255, 255, 255), int(3*img_scale), cv2.LINE_AA)
    
    if fallback_count > 0:
        legend_text = f"* = Fallback radius ({fallback_count} rods)"
        legend_pos = (int(50*img_scale), int(120*img_scale))
        cv2.putText(result_image, legend_text, (legend_pos[0] + 2, legend_pos[1] + 2), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8*img_scale, (0, 0, 0), int(4*img_scale), cv2.LINE_AA)
        cv2.putText(result_image, legend_text, legend_pos, 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8*img_scale, COLOR_FALLBACK_CIRCLE, int(2*img_scale), cv2.LINE_AA)
    
    return result_image

def main():
    parser = argparse.ArgumentParser(description="Interactive rebar analysis tool")
    parser.add_argument("--input", default="rebar_image.jpg", help="Input image path")
    parser.add_argument("--output", default="rebar_analysis_result.jpg", help="Output image path")
    parser.add_argument("--debug", action="store_true", help="Enable debug visualization")
    args = parser.parse_args()
    
    original_image = cv2.imread(args.input)
    if original_image is None:
        print_error(f"Could not load image: '{args.input}'")
        return
    
    rod_seed_points, reference_points = get_user_markings(original_image)
    
    if len(rod_seed_points) < 2:
        print_error("Analysis cancelled: Need at least 2 rod points")
        return
    
    print_header("ANALYZING RODS")
    print_info("Processing rod detections...")
    
    detected_circles = []
    successful_detections = 0
    fallback_detections = 0
    
    for i, pt in enumerate(rod_seed_points):
        result = find_rod_circle(original_image, pt, args.debug, i)
        detected_circles.append(result)
        
        if len(result) > 2 and result[2]: 
            fallback_detections += 1
        else:
            successful_detections += 1
    
    print(f"\nDETECTION SUMMARY:")
    print(f"   • Total rods marked: {len(rod_seed_points)}")
    print(f"   • Successful detections: {successful_detections}")
    print(f"   • Fallback detections: {fallback_detections}")
    print(f"   • Total processed: {len(detected_circles)}")
    
    pixels_per_millimeter = None
    if len(reference_points) == 2:
        real_world_length = get_reference_length_from_user()
        pixels_per_millimeter = calculate_pixel_to_millimeter_ratio(reference_points, real_world_length)
        print_success(f"Scale: {pixels_per_millimeter:.2f} pixels/millimeter")
    else:
        print_info("No reference object - measurements in pixels only")
    
    print_header("GENERATING RESULT")
    result_image = analyze_and_draw_results(original_image, detected_circles, reference_points, pixels_per_millimeter)
    
    if result_image is not None:
        cv2.imwrite(args.output, result_image)
        print_success(f"Analysis complete! Result saved: '{args.output}'")
        
        cv2.namedWindow("Final Analysis Result", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Final Analysis Result", 1280, 720)
        
        cv2.imshow("Final Analysis Result", result_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print_error("Failed to generate result image")

if __name__ == "__main__":
    main()