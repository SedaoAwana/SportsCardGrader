"""
Card Analyzer - Core image processing and analysis functionality
"""

import cv2
import numpy as np
from typing import Dict, Tuple, Any
import math


class CardAnalyzer:
    """Analyzes sports cards for quality assessment across multiple criteria."""
    
    def __init__(self):
        self.image = None
        self.gray = None
        self.edges = None
        
    def load_image(self, image_path: str) -> bool:
        """Load an image for analysis."""
        try:
            self.image = cv2.imread(image_path)
            if self.image is None:
                return False
            self.gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            return True
        except Exception as e:
            print(f"Error loading image: {e}")
            return False
    
    def analyze_edges(self) -> Dict[str, Any]:
        """Analyze the quality of card edges."""
        if self.gray is None:
            return {"score": 0, "details": "No image loaded"}
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(self.gray, (5, 5), 0)
        
        # Use Canny edge detection
        edges = cv2.Canny(blurred, 50, 150)
        self.edges = edges
        
        # Find contours to analyze edge quality
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return {"score": 0, "details": "No edges detected"}
        
        # Find the largest contour (should be the card boundary)
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Calculate edge smoothness based on contour properties
        perimeter = cv2.arcLength(largest_contour, True)
        area = cv2.contourArea(largest_contour)
        
        # Approximate the contour to a polygon
        epsilon = 0.02 * perimeter
        approx = cv2.approxPolyDP(largest_contour, epsilon, True)
        
        # Score based on how rectangular the card appears (should be 4 corners)
        corner_score = 100 if len(approx) == 4 else max(0, 100 - abs(len(approx) - 4) * 10)
        
        # Edge smoothness score based on perimeter to area ratio
        if area > 0:
            compactness = (perimeter * perimeter) / (4 * math.pi * area)
            smoothness_score = max(0, 100 - (compactness - 1) * 50)
        else:
            smoothness_score = 0
        
        edge_score = (corner_score + smoothness_score) / 2
        
        return {
            "score": min(100, max(0, edge_score)),
            "details": {
                "corners_detected": len(approx),
                "corner_score": corner_score,
                "smoothness_score": smoothness_score,
                "perimeter": perimeter,
                "area": area
            }
        }
    
    def analyze_corners(self) -> Dict[str, Any]:
        """Analyze the quality of card corners."""
        if self.gray is None:
            return {"score": 0, "details": "No image loaded"}
        
        # Use Harris corner detection
        corners = cv2.cornerHarris(self.gray, 2, 3, 0.04)
        
        # Dilate corner image to enhance corner points
        corners = cv2.dilate(corners, None)
        
        # Threshold for an optimal value, it may vary depending on the image
        corner_threshold = 0.01 * corners.max()
        corner_points = np.where(corners > corner_threshold)
        
        # Count detected corners
        num_corners = len(corner_points[0])
        
        # Analyze corner sharpness
        # Apply additional processing to assess corner quality
        kernel = np.ones((3, 3), np.uint8)
        eroded = cv2.erode(self.gray, kernel, iterations=1)
        dilated = cv2.dilate(self.gray, kernel, iterations=1)
        
        # Calculate gradient to assess corner sharpness
        grad_x = cv2.Sobel(self.gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(self.gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # Calculate corner sharpness score
        avg_gradient = np.mean(gradient_magnitude)
        sharpness_score = min(100, avg_gradient * 2)
        
        # Corner count score (ideal cards should have 4 clear corners)
        if 3 <= num_corners <= 6:
            count_score = 100
        else:
            count_score = max(0, 100 - abs(num_corners - 4) * 15)
        
        corner_score = (sharpness_score + count_score) / 2
        
        return {
            "score": min(100, max(0, corner_score)),
            "details": {
                "corners_detected": num_corners,
                "sharpness_score": sharpness_score,
                "count_score": count_score,
                "avg_gradient": avg_gradient
            }
        }
    
    def analyze_surface(self) -> Dict[str, Any]:
        """Analyze the surface quality of the card."""
        if self.gray is None:
            return {"score": 0, "details": "No image loaded"}
        
        # Calculate image statistics for surface quality assessment
        mean_intensity = np.mean(self.gray)
        std_intensity = np.std(self.gray)
        
        # Detect potential scratches or defects using morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        opened = cv2.morphologyEx(self.gray, cv2.MORPH_OPEN, kernel)
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
        
        # Calculate difference to highlight surface defects
        surface_defects = cv2.absdiff(self.gray, closed)
        defect_score = np.mean(surface_defects)
        
        # Analyze texture uniformity
        # Use Local Binary Pattern-like analysis
        rows, cols = self.gray.shape
        texture_variance = 0
        sample_size = min(rows, cols) // 10
        
        for i in range(0, rows - sample_size, sample_size):
            for j in range(0, cols - sample_size, sample_size):
                patch = self.gray[i:i+sample_size, j:j+sample_size]
                texture_variance += np.var(patch)
        
        # Normalize texture variance
        num_patches = ((rows // sample_size) * (cols // sample_size))
        if num_patches > 0:
            avg_texture_variance = texture_variance / num_patches
        else:
            avg_texture_variance = 0
        
        # Calculate surface quality score
        # Lower defect score and moderate texture variance indicate better surface
        defect_quality = max(0, 100 - defect_score * 2)
        texture_quality = max(0, 100 - (avg_texture_variance / 100))
        
        surface_score = (defect_quality + texture_quality) / 2
        
        return {
            "score": min(100, max(0, surface_score)),
            "details": {
                "mean_intensity": mean_intensity,
                "std_intensity": std_intensity,
                "defect_score": defect_score,
                "texture_variance": avg_texture_variance,
                "defect_quality": defect_quality,
                "texture_quality": texture_quality
            }
        }
    
    def analyze_centering(self) -> Dict[str, Any]:
        """Analyze the centering of the card content."""
        if self.gray is None:
            return {"score": 0, "details": "No image loaded"}
        
        # Find the card boundary using edge detection
        blurred = cv2.GaussianBlur(self.gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return {"score": 0, "details": "No card boundary detected"}
        
        # Find the largest contour (card boundary)
        card_contour = max(contours, key=cv2.contourArea)
        
        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(card_contour)
        
        # Calculate card center
        card_center_x = x + w // 2
        card_center_y = y + h // 2
        
        # Calculate image center
        img_height, img_width = self.gray.shape
        img_center_x = img_width // 2
        img_center_y = img_height // 2
        
        # Calculate centering offset
        offset_x = abs(card_center_x - img_center_x)
        offset_y = abs(card_center_y - img_center_y)
        
        # Calculate centering score based on offset relative to image size
        max_offset_x = img_width * 0.1  # Allow 10% deviation
        max_offset_y = img_height * 0.1
        
        centering_x_score = max(0, 100 - (offset_x / max_offset_x) * 100)
        centering_y_score = max(0, 100 - (offset_y / max_offset_y) * 100)
        
        # Also analyze border uniformity
        border_top = np.mean(self.gray[:10, :])
        border_bottom = np.mean(self.gray[-10:, :])
        border_left = np.mean(self.gray[:, :10])
        border_right = np.mean(self.gray[:, -10:])
        
        # Calculate border uniformity
        borders = [border_top, border_bottom, border_left, border_right]
        border_std = np.std(borders)
        border_uniformity_score = max(0, 100 - border_std)
        
        centering_score = (centering_x_score + centering_y_score + border_uniformity_score) / 3
        
        return {
            "score": min(100, max(0, centering_score)),
            "details": {
                "offset_x": offset_x,
                "offset_y": offset_y,
                "centering_x_score": centering_x_score,
                "centering_y_score": centering_y_score,
                "border_uniformity_score": border_uniformity_score,
                "card_center": (card_center_x, card_center_y),
                "image_center": (img_center_x, img_center_y)
            }
        }
    
    def analyze_all(self) -> Dict[str, Any]:
        """Perform complete analysis of the card."""
        edge_analysis = self.analyze_edges()
        corner_analysis = self.analyze_corners()
        surface_analysis = self.analyze_surface()
        centering_analysis = self.analyze_centering()
        
        return {
            "edges": edge_analysis,
            "corners": corner_analysis,
            "surface": surface_analysis,
            "centering": centering_analysis
        }