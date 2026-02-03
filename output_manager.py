"""
Output Manager
Handles creation of all output feature classes
"""

import arcpy
from geometry_utils import GeometryUtils
from lloyds_algorithm import LloydsAlgorithm


class OutputManager:
    """Manages creation of output feature classes"""
    
    def __init__(self, workspace, spatial_reference):
        """
        Initialize output manager
        
        Args:
            workspace: Output workspace path
            spatial_reference: Spatial reference for outputs
        """
        self.workspace = workspace
        self.spatial_ref = spatial_reference
        self.geo_utils = GeometryUtils()

    
    def create_all_outputs(self, iteration_history, points, 
                      facilities_name, iterations_name, assignments_name, 
                      voronoi_name=None):
        """
        Create all output feature classes
        
        Args:
            iteration_history: List of iteration dictionaries
            points: List of demand points
            facilities_name: Name for facilities output
            iterations_name: Name for iterations output
            assignments_name: Name for assignments output
            voronoi_name: Optional name for Voronoi polygons output
        """
        arcpy.AddMessage("\nCreating output feature classes...")
        
        # Get final state
        final_facilities = iteration_history[-1]["facilities"]
        final_assignments = iteration_history[-1]["assignments"]
        
        # Create outputs
        self.create_facilities_output(final_facilities, facilities_name)
        self.create_iterations_output(iteration_history, iterations_name)
        self.create_assignments_output(points, final_facilities, 
                                    final_assignments, assignments_name)
        
        # Create Voronoi polygons if requested (pass points for extent)
        if voronoi_name:
            self.create_voronoi_polygons(final_facilities, points, None, voronoi_name)
    
    def create_facilities_output(self, facilities, output_name):
        """
        Create feature class for final facility locations
        
        Args:
            facilities: List of facility dictionaries
            output_name: Name of output feature class
        """
        output_fc = output_name
        
        # Create feature class
        arcpy.CreateFeatureclass_management(
            self.workspace, 
            output_fc, 
            "POINT", 
            spatial_reference=self.spatial_ref
        )
        
        # Add fields
        arcpy.AddField_management(output_fc, "Facility_ID", "LONG")
        arcpy.AddField_management(output_fc, "X_Coord", "DOUBLE")
        arcpy.AddField_management(output_fc, "Y_Coord", "DOUBLE")
        
        # Insert features
        fields = ["SHAPE@XY", "Facility_ID", "X_Coord", "Y_Coord"]
        with arcpy.da.InsertCursor(output_fc, fields) as cursor:
            for facility in facilities:
                cursor.insertRow([
                    (facility["x"], facility["y"]),
                    facility["id"],
                    facility["x"],
                    facility["y"]
                ])
        
        arcpy.AddMessage(f"  Created {output_fc}")
    
    def create_iterations_output(self, iteration_history, output_name):
        """
        Create feature class showing all iterations
        
        Args:
            iteration_history: List of iteration dictionaries
            output_name: Name of output feature class
        """
        output_fc = output_name
        
        # Create feature class
        arcpy.CreateFeatureclass_management(
            self.workspace,
            output_fc,
            "POINT",
            spatial_reference=self.spatial_ref
        )
        
        # Add fields
        arcpy.AddField_management(output_fc, "Iteration", "LONG")
        arcpy.AddField_management(output_fc, "Facility_ID", "LONG")
        arcpy.AddField_management(output_fc, "Objective", "DOUBLE")
        arcpy.AddField_management(output_fc, "X_Coord", "DOUBLE")
        arcpy.AddField_management(output_fc, "Y_Coord", "DOUBLE")
        arcpy.AddField_management(output_fc, "Cluster_Size", "LONG")
        
        # Insert features
        fields = ["SHAPE@XY", "Iteration", "Facility_ID", "Objective", 
                 "X_Coord", "Y_Coord", "Cluster_Size"]
        
        with arcpy.da.InsertCursor(output_fc, fields) as cursor:
            for iter_data in iteration_history:
                for i, facility in enumerate(iter_data["facilities"]):
                    cluster_size = iter_data["cluster_sizes"][i]
                    cursor.insertRow([
                        (facility["x"], facility["y"]),
                        iter_data["iteration"],
                        facility["id"],
                        iter_data["objective"],
                        facility["x"],
                        facility["y"],
                        cluster_size
                    ])
        
        arcpy.AddMessage(f"  Created {output_fc}")
    
    def create_assignments_output(self, points, facilities, assignments, output_name):
        """
        Create feature class showing point assignments
        
        Args:
            points: List of demand points
            facilities: List of facility locations
            assignments: List of facility assignments
            output_name: Name of output feature class
        """
        output_fc = output_name
        
        # Create feature class
        arcpy.CreateFeatureclass_management(
            self.workspace,
            output_fc,
            "POINT",
            spatial_reference=self.spatial_ref
        )
        
        # Add fields
        arcpy.AddField_management(output_fc, "Point_OID", "LONG")
        arcpy.AddField_management(output_fc, "Assigned_Facility", "LONG")
        arcpy.AddField_management(output_fc, "Distance", "DOUBLE")
        arcpy.AddField_management(output_fc, "Facility_X", "DOUBLE")
        arcpy.AddField_management(output_fc, "Facility_Y", "DOUBLE")
        
        # Insert features
        fields = ["SHAPE@XY", "Point_OID", "Assigned_Facility", 
                 "Distance", "Facility_X", "Facility_Y"]
        
        with arcpy.da.InsertCursor(output_fc, fields) as cursor:
            for i, point in enumerate(points):
                facility_id = assignments[i]
                facility = facilities[facility_id]
                
                dist = self.geo_utils.euclidean_distance(
                    point["xy"][0], point["xy"][1],
                    facility["x"], facility["y"]
                )
                
                cursor.insertRow([
                    point["xy"],
                    point["oid"],
                    facility_id,
                    dist,
                    facility["x"],
                    facility["y"]
                ])
        
        arcpy.AddMessage(f"  Created {output_fc}")

    def create_voronoi_polygons(self, facilities, points, iteration_num, output_name):
        """
        Create Voronoi (Thiessen) polygons for facility locations
        
        Args:
            facilities: List of facility dictionaries
            points: List of demand points (to set proper extent)
            iteration_num: Which iteration (for naming/filtering), can be None
            output_name: Name for output feature class
        """
        import os
        
        arcpy.AddMessage(f"  Creating Voronoi polygons...")
        
        # Step 1: Calculate extent from demand points (not just facilities)
        all_x = [p["xy"][0] for p in points]
        all_y = [p["xy"][1] for p in points]
        
        # Add some buffer (10% on each side)
        x_range = max(all_x) - min(all_x)
        y_range = max(all_y) - min(all_y)
        buffer_pct = 0.1
        
        extent_str = f"{min(all_x) - x_range * buffer_pct} {min(all_y) - y_range * buffer_pct} {max(all_x) + x_range * buffer_pct} {max(all_y) + y_range * buffer_pct}"
        
        # Step 2: Create temporary point feature class for facilities
        temp_facilities = "temp_facilities_voronoi"
        temp_fc_path = os.path.join(self.workspace, temp_facilities)
        
        # Delete if exists
        if arcpy.Exists(temp_fc_path):
            arcpy.Delete_management(temp_fc_path)
        
        arcpy.CreateFeatureclass_management(
            self.workspace,
            temp_facilities,
            "POINT",
            spatial_reference=self.spatial_ref
        )
        
        arcpy.AddField_management(temp_fc_path, "Facility_ID", "LONG")
        
        # Insert facility points
        with arcpy.da.InsertCursor(temp_fc_path, ["SHAPE@XY", "Facility_ID"]) as cursor:
            for facility in facilities:
                cursor.insertRow([
                    (facility["x"], facility["y"]),
                    facility["id"]
                ])
        
        # Step 3: Create Thiessen (Voronoi) polygons with proper extent
        output_fc = output_name
        output_path = os.path.join(self.workspace, output_fc)
        
        # Delete if exists
        if arcpy.Exists(output_path):
            arcpy.Delete_management(output_path)
        
        # Set environment extent before creating Thiessen polygons
        original_extent = arcpy.env.extent
        arcpy.env.extent = extent_str
        
        arcpy.analysis.CreateThiessenPolygons(
            in_features=temp_fc_path,
            out_feature_class=output_path,
            fields_to_copy="ALL"
        )
        
        # Restore original extent
        arcpy.env.extent = original_extent
        
        # Step 4: Add iteration field if needed
        if iteration_num is not None:
            arcpy.AddField_management(output_path, "Iteration", "LONG")
            with arcpy.da.UpdateCursor(output_path, ["Iteration"]) as cursor:
                for row in cursor:
                    row[0] = iteration_num
                    cursor.updateRow(row)
        
        # Step 5: Add area field
        arcpy.AddField_management(output_path, "Area_SqUnits", "DOUBLE")
        with arcpy.da.UpdateCursor(output_path, ["SHAPE@AREA", "Area_SqUnits"]) as cursor:
            for row in cursor:
                row[1] = row[0]
                cursor.updateRow(row)
        
        # Step 6: Clean up temporary data
        arcpy.Delete_management(temp_fc_path)
        
        arcpy.AddMessage(f"  Created {output_fc}")
        
        return output_path