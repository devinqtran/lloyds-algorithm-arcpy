"""
Lloyd's Algorithm Script for ArcGIS Pro Script Tool
Standalone script version with Voronoi polygons and symbology
"""

import arcpy
import sys
import os

# Add current directory to path so we can import our modules
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from lloyds_algorithm import LloydsAlgorithm
from output_manager import OutputManager


def apply_symbology(layer_name, symbology_type):
    """
    Apply symbology to output layers
    
    Args:
        layer_name: Name of the layer to symbolize
        symbology_type: Type of symbology ('facilities', 'iterations', 'assignments', 'voronoi')
    """
    try:
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map_view = aprx.activeMap
        
        if not map_view:
            arcpy.AddMessage(f"  No active map found")
            return
        
        # Find the layer
        layers = map_view.listLayers(layer_name)
        if not layers:
            arcpy.AddMessage(f"  Layer not found: {layer_name}")
            return
        
        layer = layers[0]
        arcpy.AddMessage(f"  Processing symbology for: {layer_name}")
        
        if symbology_type == 'facilities':
            # Red circles for final facilities
            sym = layer.symbology
            if hasattr(sym, 'renderer'):
                sym.renderer.symbol.color = {'RGB': [230, 76, 60, 100]}  # Red
                sym.renderer.symbol.size = 12
                sym.renderer.symbol.outlineColor = {'RGB': [0, 0, 0, 100]}
                sym.renderer.symbol.outlineWidth = 0.5
                layer.symbology = sym
                arcpy.AddMessage(f"  ✓ Applied red circles to {layer_name}")
        
        elif symbology_type == 'iterations':
            # Unique values by Iteration number
            sym = layer.symbology
            if hasattr(sym, 'updateRenderer'):
                sym.updateRenderer('UniqueValueRenderer')
                sym.renderer.fields = ['Iteration']
                layer.symbology = sym
                arcpy.AddMessage(f"  ✓ Applied unique values by Iteration to {layer_name}")
        
        elif symbology_type == 'assignments':
            # Unique values by Assigned_Facility
            sym = layer.symbology
            if hasattr(sym, 'updateRenderer'):
                sym.updateRenderer('UniqueValueRenderer')
                sym.renderer.fields = ['Assigned_Facility']
                layer.symbology = sym
                arcpy.AddMessage(f"  ✓ Applied unique values by Facility to {layer_name}")
        
        elif symbology_type == 'voronoi':
            arcpy.AddMessage(f"  Applying Voronoi symbology...")
            
            # Step 1: Set layer transparency first (most reliable method)
            layer.transparency = 50
            arcpy.AddMessage(f"  ✓ Set layer transparency to 50%")
            
            # Step 2: Apply unique value renderer
            sym = layer.symbology
            if hasattr(sym, 'updateRenderer'):
                sym.updateRenderer('UniqueValueRenderer')
                sym.renderer.fields = ['Facility_ID']
                layer.symbology = sym
                arcpy.AddMessage(f"  ✓ Applied unique values by Facility_ID")
                
                # Step 3: Update colors with color ramp
                sym = layer.symbology
                try:
                    # Try to apply a color ramp
                    color_ramps = aprx.listColorRamps('Pastel 1')
                    if not color_ramps:
                        color_ramps = aprx.listColorRamps('Basic Random')
                    if color_ramps:
                        sym.renderer.colorRamp = color_ramps[0]
                        layer.symbology = sym
                        arcpy.AddMessage(f"  ✓ Applied color ramp")
                except:
                    arcpy.AddMessage(f"  ⚠ Could not apply color ramp, using default colors")
                
                # Step 4: Format outlines
                try:
                    sym = layer.symbology
                    if hasattr(sym.renderer, 'groups'):
                        for group in sym.renderer.groups:
                            for item in group.items:
                                if hasattr(item, 'symbol'):
                                    item.symbol.outlineColor = {'RGB': [78, 78, 78, 100]}
                                    item.symbol.outlineWidth = 2.0
                        layer.symbology = sym
                        arcpy.AddMessage(f"  ✓ Applied dark outlines")
                except Exception as e:
                    arcpy.AddMessage(f"  ⚠ Could not format outlines: {str(e)}")
            
            arcpy.AddMessage(f"  ✓ Voronoi symbology complete")
        
    except Exception as e:
        arcpy.AddMessage(f"  ✗ Error applying symbology to {layer_name}: {str(e)}")
        import traceback
        arcpy.AddMessage(f"  Details: {traceback.format_exc()}")


def main():
    """Main function for script tool execution"""
    
    try:
        # Get parameters from ArcGIS tool
        input_points = arcpy.GetParameterAsText(0)
        num_facilities = int(arcpy.GetParameter(1))
        max_iterations = int(arcpy.GetParameter(2))
        convergence_threshold = float(arcpy.GetParameter(3))
        output_workspace = arcpy.GetParameterAsText(4)
        output_facilities_name = arcpy.GetParameterAsText(5)
        output_iterations_name = arcpy.GetParameterAsText(6)
        output_assignments_name = arcpy.GetParameterAsText(7)
        
        # Check if parameter 8 exists (Voronoi - optional)
        create_voronoi = False
        output_voronoi_name = None
        try:
            output_voronoi_name = arcpy.GetParameterAsText(8)
            if output_voronoi_name:
                create_voronoi = True
        except:
            pass
        
        # Check if parameter 9 exists (Random Seed - optional)
        random_seed = 42  # Default value
        try:
            seed_param = arcpy.GetParameterAsText(9)
            if seed_param and seed_param.strip():
                random_seed = int(seed_param)
        except:
            pass  # Use default if parameter doesn't exist or is invalid
        
        # Configure environment
        arcpy.env.workspace = output_workspace
        arcpy.env.overwriteOutput = True
        
        # Print header
        arcpy.AddMessage("=" * 60)
        arcpy.AddMessage("LLOYD'S ALGORITHM FOR OPTIMAL FACILITY LOCATION")
        arcpy.AddMessage("=" * 60)
        arcpy.AddMessage(f"Input points: {input_points}")
        arcpy.AddMessage(f"Number of facilities: {num_facilities}")
        arcpy.AddMessage(f"Maximum iterations: {max_iterations}")
        arcpy.AddMessage(f"Convergence threshold: {convergence_threshold}")
        arcpy.AddMessage(f"Random seed: {random_seed}")
        if create_voronoi:
            arcpy.AddMessage(f"Creating Voronoi polygons: Yes")
        arcpy.AddMessage("")
        
        # Load demand points
        points = []
        spatial_ref = arcpy.Describe(input_points).spatialReference
        
        with arcpy.da.SearchCursor(input_points, ["SHAPE@XY", "OID@"]) as cursor:
            for row in cursor:
                points.append({"xy": row[0], "oid": row[1]})
        
        arcpy.AddMessage(f"Loaded {len(points)} demand points")
        arcpy.AddMessage("")
        
        # Validate
        if len(points) < num_facilities:
            arcpy.AddError(f"Cannot place {num_facilities} facilities with only {len(points)} points")
            return
        
        # Run Lloyd's Algorithm
        arcpy.AddMessage(f"Initialized {num_facilities} facilities randomly")
        arcpy.AddMessage("")
        
        algorithm = LloydsAlgorithm(num_facilities, max_iterations, convergence_threshold, random_seed)
        iteration_history = algorithm.run(points)
        
        # Create outputs - Pass the voronoi name directly into create_all_outputs
        arcpy.AddMessage("\nCreating output feature classes...")
        output_mgr = OutputManager(output_workspace, spatial_ref)

        # Note: We pass the Voronoi name as the 5th optional argument here
        output_mgr.create_all_outputs(
            iteration_history,
            points,
            output_facilities_name,
            output_iterations_name,
            output_assignments_name,
            output_voronoi_name if create_voronoi else None
        )
        
        # Print summary
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
        arcpy.AddMessage(f"  - {output_facilities_name} (final facility locations)")
        arcpy.AddMessage(f"  - {output_iterations_name} (all iterations)")
        arcpy.AddMessage(f"  - {output_assignments_name} (point assignments)")
        if create_voronoi:
            arcpy.AddMessage(f"  - {output_voronoi_name} (service area polygons)")
        arcpy.AddMessage("=" * 60)
        
        # Add outputs to map with symbology
        arcpy.AddMessage("\nAdding layers to map and applying symbology...")
        try:
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            map_view = aprx.activeMap
            
            if map_view:
                facilities_path = os.path.join(output_workspace, output_facilities_name)
                iterations_path = os.path.join(output_workspace, output_iterations_name)
                assignments_path = os.path.join(output_workspace, output_assignments_name)
                
                # Add layers
                map_view.addDataFromPath(facilities_path)
                map_view.addDataFromPath(iterations_path)
                map_view.addDataFromPath(assignments_path)
                
                # Add Voronoi if created
                if create_voronoi:
                    voronoi_path = os.path.join(output_workspace, output_voronoi_name)
                    map_view.addDataFromPath(voronoi_path)
                
                arcpy.AddMessage("Layers added to map!")
                
                # Apply symbology
                arcpy.AddMessage("\nApplying symbology...")
                apply_symbology(output_facilities_name, 'facilities')
                apply_symbology(output_iterations_name, 'iterations')
                apply_symbology(output_assignments_name, 'assignments')
                
                if create_voronoi:
                    apply_symbology(output_voronoi_name, 'voronoi')
                
                arcpy.AddMessage("Symbology applied!")
                
        except Exception as e:
            arcpy.AddMessage(f"\nCould not auto-add to map: {str(e)}")
            arcpy.AddMessage("Please add layers manually from Catalog pane")
        
    except Exception as e:
        arcpy.AddError(f"Error: {str(e)}")
        import traceback
        arcpy.AddError(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()