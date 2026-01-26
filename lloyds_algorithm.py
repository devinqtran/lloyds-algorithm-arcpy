"""
Lloyd's Algorithm Core Implementation
Pure algorithm logic independent of ArcGIS
"""

import arcpy
import random
from geometry_utils import GeometryUtils


class LloydsAlgorithm:
    """Core Lloyd's algorithm implementation"""

    # Constructor
    def __init__(self, num_facilities, max_iterations, convergence_threshold):
        """
        Initialize algorithm parameters
        
        Args:
            num_facilities: Number of facilities to locate
            max_iterations: Maximum iterations to run
            convergence_threshold: Stop when facilities move less than this distance
        """
        self.num_facilities = num_facilities
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        self.geo_utils = GeometryUtils()
    
    def run(self, points):
        """
        Execute Lloyd's algorithm
        
        Args:
            points: List of demand point dictionaries with 'xy' and 'oid' keys
            
        Returns:
            List of iteration history dictionaries
        """
        # Initialize facilities
        facilities = self._initialize_facilities(points)
        arcpy.AddMessage(f"Initialized {len(facilities)} facilities randomly")
        arcpy.AddMessage("")
        
        # Run iterations
        iteration_history = []
        converged = False
        
        for iteration in range(self.max_iterations):
            arcpy.AddMessage(f"Iteration {iteration + 1}/{self.max_iterations}")
            
            # Assignment step
            assignments = self._assign_points_to_facilities(points, facilities)
            
            # Calculate metrics
            objective = self._calculate_objective_function(points, facilities, assignments)
            cluster_sizes = self._calculate_cluster_sizes(assignments)
            
            arcpy.AddMessage(f"  Objective function: {objective:.2f}")
            arcpy.AddMessage(f"  Cluster sizes: {cluster_sizes}")
            
            # Store iteration data
            iteration_history.append({
                "iteration": iteration + 1,
                "facilities": [f.copy() for f in facilities],
                "objective": objective,
                "assignments": assignments.copy(),
                "cluster_sizes": cluster_sizes
            })
            
            # Update step - calculate new centroids
            new_facilities = self._calculate_centroids(points, facilities, assignments)
            
            # Convergence check
            max_movement = self._calculate_max_movement(facilities, new_facilities)
            arcpy.AddMessage(f"  Maximum facility movement: {max_movement:.4f}")
            
            if max_movement < self.convergence_threshold:
                arcpy.AddMessage(f"\nConverged at iteration {iteration + 1}!")
                converged = True
                facilities = new_facilities
                
                # Store final state
                final_assignments = self._assign_points_to_facilities(points, facilities)
                final_objective = self._calculate_objective_function(points, facilities, final_assignments)
                final_cluster_sizes = self._calculate_cluster_sizes(final_assignments)
                
                iteration_history.append({
                    "iteration": iteration + 2,
                    "facilities": [f.copy() for f in facilities],
                    "objective": final_objective,
                    "assignments": final_assignments.copy(),
                    "cluster_sizes": final_cluster_sizes
                })
                break
            
            facilities = new_facilities
            arcpy.AddMessage("")
        
        if not converged:
            arcpy.AddMessage(f"\nReached maximum iterations ({self.max_iterations})")
        
        return iteration_history
    
    def _initialize_facilities(self, points):
        """
        Initialize facility locations randomly from demand points
        
        Args:
            points: List of demand points
            
        Returns:
            List of facility dictionaries with 'id', 'x', 'y' keys
        """
        # Randomly creates points for algorithm to start and selects them randomly
        random.seed(42)  # For reproducibility, change number to change starting points
        selected_indices = random.sample(range(len(points)), self.num_facilities)
        
        facilities = []
        for i, idx in enumerate(selected_indices):
            facilities.append({
                "id": i,
                "x": points[idx]["xy"][0],
                "y": points[idx]["xy"][1]
            })
        
        return facilities
    
    # Assign the demand points to facilities using nearest neighbor
    def _assign_points_to_facilities(self, points, facilities):
        """
        Assign each point to its nearest facility
        
        Args:
            points: List of demand points
            facilities: List of facility locations
            
        Returns:
            List of facility IDs (one per point)
        """
        assignments = []
        
        for point in points:
            min_dist = float('inf')
            nearest_facility = 0
            
            for facility in facilities:
                dist = self.geo_utils.euclidean_distance(
                    point["xy"][0], point["xy"][1],
                    facility["x"], facility["y"]
                )
                
                if dist < min_dist:
                    min_dist = dist
                    nearest_facility = facility["id"]
            
            assignments.append(nearest_facility)
        
        return assignments
    
    # Calculates the objective function (total distance)
    def _calculate_objective_function(self, points, facilities, assignments):
        """
        Calculate total distance from points to assigned facilities
        
        Args:
            points: List of demand points
            facilities: List of facility locations
            assignments: List of facility assignments
            
        Returns:
            Total distance (float)
        """
        total_distance = 0.0
        
        for i, point in enumerate(points):
            facility_id = assignments[i]
            facility = facilities[facility_id]
            
            dist = self.geo_utils.euclidean_distance(
                point["xy"][0], point["xy"][1],
                facility["x"], facility["y"]
            )
            total_distance += dist
        
        return total_distance
    
    def _calculate_cluster_sizes(self, assignments):
        """
        Calculate number of points assigned to each facility
        
        Args:
            assignments: List of facility assignments
            
        Returns:
            List of cluster sizes
        """
        sizes = [0] * self.num_facilities
        for assignment in assignments:
            sizes[assignment] += 1
        return sizes
    
    def _calculate_centroids(self, points, facilities, assignments):
        """
        Calculate centroid of points assigned to each facility
        
        Args:
            points: List of demand points
            facilities: List of current facility locations
            assignments: List of facility assignments
            
        Returns:
            List of new facility locations (centroids)
        """
        new_facilities = []
        
        for facility in facilities:
            facility_id = facility["id"]
            
            # Find all points assigned to this facility
            assigned_points = [
                points[i] for i, assign in enumerate(assignments) 
                if assign == facility_id
            ]
            
            if len(assigned_points) == 0:
                # No points assigned - keep facility in same location
                new_facilities.append(facility.copy())
            else:
                # Calculate centroid
                sum_x = sum(p["xy"][0] for p in assigned_points)
                sum_y = sum(p["xy"][1] for p in assigned_points)
                centroid_x = sum_x / len(assigned_points)
                centroid_y = sum_y / len(assigned_points)
                
                new_facilities.append({
                    "id": facility_id,
                    "x": centroid_x,
                    "y": centroid_y
                })
        
        return new_facilities
    
    def _calculate_max_movement(self, old_facilities, new_facilities):
        """
        Calculate maximum distance any facility moved
        
        Args:
            old_facilities: List of previous facility locations
            new_facilities: List of new facility locations
            
        Returns:
            Maximum movement distance (float)
        """
        max_dist = 0.0
        
        for old_fac, new_fac in zip(old_facilities, new_facilities):
            dist = self.geo_utils.euclidean_distance(
                old_fac["x"], old_fac["y"],
                new_fac["x"], new_fac["y"]
            )
            if dist > max_dist:
                max_dist = dist
        
        return max_dist