"""
Geometry Utilities
Helper functions for geometric calculations
"""

import math


class GeometryUtils:
    """Collection of geometry utility functions"""
    
    @staticmethod
    def euclidean_distance(x1, y1, x2, y2):
        """
        Calculate Euclidean distance between two points
        
        Args:
            x1, y1: Coordinates of first point
            x2, y2: Coordinates of second point
            
        Returns:
            Distance as float
        """
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    @staticmethod
    def calculate_centroid(points):
        """
        Calculate centroid (mean center) of a set of points
        
        Args:
            points: List of point dictionaries with 'xy' key
            
        Returns:
            Tuple of (x, y) coordinates
        """
        if not points:
            return None
        
        sum_x = sum(p["xy"][0] for p in points)
        sum_y = sum(p["xy"][1] for p in points)
        
        centroid_x = sum_x / len(points)
        centroid_y = sum_y / len(points)
        
        return (centroid_x, centroid_y)
    
    @staticmethod
    def calculate_distance_matrix(points1, points2):
        """
        Calculate distance matrix between two sets of points
        
        Args:
            points1: First set of points
            points2: Second set of points
            
        Returns:
            2D list of distances
        """
        distances = []
        
        for p1 in points1:
            row = []
            for p2 in points2:
                dist = GeometryUtils.euclidean_distance(
                    p1["x"], p1["y"],
                    p2["x"], p2["y"]
                )
                row.append(dist)
            distances.append(row)
        
        return distances