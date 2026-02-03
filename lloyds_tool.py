"""
Lloyd's Algorithm Tool - ArcGIS Pro Interface
Handles all ArcGIS-specific tool interface logic
"""

import arcpy
import os
from lloyds_algorithm import LloydsAlgorithm
from output_manager import OutputManager


class LloydsAlgorithmTool(object):
    """ArcGIS Pro tool interface for Lloyd's Algorithm"""
    
    def __init__(self):
        self.label = "Lloyd's Algorithm Facility Location"
        self.description = """Find optimal facility locations using Lloyd's algorithm (Voronoi iteration).
        
        This tool takes a set of demand points and determines the optimal locations for a specified 
        number of facilities. It works by iteratively:
        1. Assigning each demand point to its nearest facility
        2. Moving each facility to the centroid of its assigned points
        3. Repeating until convergence
        
        The algorithm minimizes the total distance from demand points to their nearest facility.
        """
        self.canRunInBackground = False
        
    def getParameterInfo(self):
        """Define parameter definitions"""
        
        param0 = arcpy.Parameter(
            displayName="Input Demand Points",
            name="input_points",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Point"]
        
        param1 = arcpy.Parameter(
            displayName="Number of Facilities",
            name="num_facilities",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        param1.value = 3
        
        param2 = arcpy.Parameter(
            displayName="Maximum Iterations",
            name="max_iterations",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        param2.value = 20
        
        param3 = arcpy.Parameter(
            displayName="Convergence Threshold (map units)",
            name="convergence_threshold",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param3.value = 0.1
        
        param4 = arcpy.Parameter(
            displayName="Output Workspace",
            name="output_workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")
        param4.defaultEnvironmentName = "workspace"
        
        param5 = arcpy.Parameter(
            displayName="Output Facility Locations",
            name="output_facilities",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param5.value = "Optimal_Facilities"
        
        param6 = arcpy.Parameter(
            displayName="Output All Iterations",
            name="output_iterations",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param6.value = "Facility_Iterations"
        
        param7 = arcpy.Parameter(
            displayName="Output Point Assignments",
            name="output_assignments",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param7.value = "Point_Assignments"

        param8 = arcpy.Parameter(
            displayName="Output Voronoi Polygons (Optional)",
            name="output_voronoi",
            datatype="GPString",
            parameterType="Optional",
            direction="Input")
        param8.value = "Voronoi_ServiceAreas"
        
        return [param0, param1, param2, param3, param4, param5, param6, param7, param8]
    
    def isLicensed(self):
        """Set whether tool is licensed to execute"""
        return True
    
    def updateParameters(self, parameters):
        """Modify parameter values and properties before validation"""
        return
    
    def updateMessages(self, parameters):
        """Modify messages created by internal validation"""
        if parameters[1].value and parameters[1].value < 1:
            parameters[1].setErrorMessage("Number of facilities must be at least 1")
            
        if parameters[2].value and parameters[2].value < 1:
            parameters[2].setErrorMessage("Maximum iterations must be at least 1")
            
        if parameters[3].value and parameters[3].value <= 0:
            parameters[3].setErrorMessage("Convergence threshold must be positive")
        return
    
    def execute(self, parameters, messages):
        """Main execution method"""
        
        # Extract parameters
        input_points = parameters[0].valueAsText
        num_facilities = parameters[1].value
        max_iterations = parameters[2].value
        convergence_threshold = parameters[3].value
        output_workspace = parameters[4].valueAsText
        output_facilities_name = parameters[5].valueAsText
        output_iterations_name = parameters[6].valueAsText
        output_assignments_name = parameters[7].valueAsText
        output_voronoi_name = parameters[8].valueAsText if parameters[8].valueAsText else None
        
        # Configure environment
        arcpy.env.workspace = output_workspace
        arcpy.env.overwriteOutput = True
        
        # Print header
        self._print_header(input_points, num_facilities, max_iterations, 
                          convergence_threshold, output_voronoi_name)
        
        # Load demand points
        points, spatial_ref = self._load_demand_points(input_points)
        
        if len(points) < num_facilities:
            arcpy.AddError(f"Cannot place {num_facilities} facilities with only {len(points)} points")
            return
        
        # Run Lloyd's Algorithm
        algorithm = LloydsAlgorithm(num_facilities, max_iterations, convergence_threshold)
        iteration_history = algorithm.run(points)
        
        # Create outputs
        output_mgr = OutputManager(output_workspace, spatial_ref)
        output_mgr.create_all_outputs(
            iteration_history,
            points,
            output_facilities_name,
            output_iterations_name,
            output_assignments_name,
            output_voronoi_name
        )
        
        # Print summary
        self._print_summary(iteration_history, output_facilities_name, 
                          output_iterations_name, output_assignments_name,
                          output_voronoi_name)
        
        # Add to map
        self._add_to_map(output_workspace, output_facilities_name, 
                        output_iterations_name, output_assignments_name,
                        output_voronoi_name)
        
        return
    
    def _print_header(self, input_points, num_facilities, max_iterations, 
                     convergence_threshold, voronoi_name):
        """Print tool execution header"""
        arcpy.AddMessage("=" * 60)
        arcpy.AddMessage("LLOYD'S ALGORITHM FOR OPTIMAL FACILITY LOCATION")
        arcpy.AddMessage("=" * 60)
        arcpy.AddMessage(f"Input points: {input_points}")
        arcpy.AddMessage(f"Number of facilities: {num_facilities}")
        arcpy.AddMessage(f"Maximum iterations: {max_iterations}")
        arcpy.AddMessage(f"Convergence threshold: {convergence_threshold}")
        if voronoi_name:
            arcpy.AddMessage(f"Creating Voronoi polygons: Yes")
        arcpy.AddMessage("")
    
    def _load_demand_points(self, input_points):
        """Load demand points from feature class"""
        points = []
        spatial_ref = arcpy.Describe(input_points).spatialReference
        
        with arcpy.da.SearchCursor(input_points, ["SHAPE@XY", "OID@"]) as cursor:
            for row in cursor:
                points.append({"xy": row[0], "oid": row[1]})
        
        arcpy.AddMessage(f"Loaded {len(points)} demand points")
        arcpy.AddMessage("")
        return points, spatial_ref
    
    def _print_summary(self, iteration_history, facilities_name, iterations_name, 
                      assignments_name, voronoi_name=None):
        """Print execution summary"""
        arcpy.AddMessage("")
        arcpy.AddMessage("=" * 60)
        arcpy.AddMessage("SUMMARY")
        arcpy.AddMessage("=" * 60)
        arcpy.AddMessage(f"Total iterations: {len(iteration_history)}")
        arcpy.AddMessage(f"Initial objective: {iteration_history[0]['objective']:.2f}")
        arcpy.AddMessage(f"Final objective: {iteration_history[-1]['objective']:.2f}")
        
        improvement = ((iteration_history[0]['objective'] - iteration_history[-1]['objective']) 
                      / iteration_history[0]['objective'] * 100)
        arcpy.AddMessage(f"Improvement: {improvement:.2f}%")
        arcpy.AddMessage("")
        
        arcpy.AddMessage("Final Facility Locations:")
        for facility in iteration_history[-1]['facilities']:
            arcpy.AddMessage(f"  Facility {facility['id']}: ({facility['x']:.2f}, {facility['y']:.2f})")
        arcpy.AddMessage("")
        
        arcpy.AddMessage("Outputs created:")
        arcpy.AddMessage(f"  - {facilities_name} (final facility locations)")
        arcpy.AddMessage(f"  - {iterations_name} (all iterations)")
        arcpy.AddMessage(f"  - {assignments_name} (point assignments)")
        if voronoi_name:
            arcpy.AddMessage(f"  - {voronoi_name} (Voronoi service areas)")
        arcpy.AddMessage("=" * 60)
    
    def _add_to_map(self, workspace, facilities_name, iterations_name, 
                    assignments_name, voronoi_name=None):
        """Add output layers to current map"""
        try:
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            map_view = aprx.activeMap
            if map_view:
                # Add Voronoi first (so it's at the bottom of layer stack)
                if voronoi_name:
                    voronoi_path = os.path.join(workspace, voronoi_name)
                    if arcpy.Exists(voronoi_path):
                        voronoi_layer = map_view.addDataFromPath(voronoi_path)
                        self._apply_voronoi_symbology(voronoi_layer)
                
                # Add other layers
                facilities_path = os.path.join(workspace, facilities_name)
                iterations_path = os.path.join(workspace, iterations_name)
                assignments_path = os.path.join(workspace, assignments_name)
                
                map_view.addDataFromPath(facilities_path)
                map_view.addDataFromPath(iterations_path)
                assignments_layer = map_view.addDataFromPath(assignments_path)
                
                # Apply unique value symbology to assignments
                self._apply_unique_value_symbology(assignments_layer)
                
                arcpy.AddMessage("\nLayers added to current map!")
        except Exception as e:
            arcpy.AddMessage(f"\nCould not auto-add to map: {str(e)}")
            arcpy.AddMessage("Please add layers manually from Catalog pane")

    def _apply_unique_value_symbology(self, layer):
        """Apply unique value symbology to assignments layer based on Assigned_Facility"""
        try:
            sym = layer.symbology
            
            if hasattr(sym, 'renderer'):
                sym.updateRenderer('UniqueValueRenderer')
                sym.renderer.fields = ['Assigned_Facility']
                layer.symbology = sym
                arcpy.AddMessage("  Applied unique value symbology based on Assigned_Facility")
            else:
                arcpy.AddMessage("  Layer does not support renderer-based symbology")
            
        except Exception as e:
            arcpy.AddMessage(f"  Could not apply symbology: {str(e)}")

    def _apply_voronoi_symbology(self, layer):
        """Apply unique value symbology to Voronoi polygons based on Facility_ID"""
        try:
            sym = layer.symbology
            
            if hasattr(sym, 'renderer'):
                # Update to unique values renderer
                sym.updateRenderer('UniqueValueRenderer')
                sym.renderer.fields = ['Facility_ID']
                
                # Set transparency at the layer level
                layer.transparency = 50  # 50% transparent
                
                # Apply the symbology back to the layer
                layer.symbology = sym
                
                arcpy.AddMessage("  Applied unique value symbology to Voronoi polygons")
                
        except Exception as e:
            arcpy.AddMessage(f"  Could not apply Voronoi symbology: {str(e)}")