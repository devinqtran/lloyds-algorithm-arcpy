# output_manager.py - Detailed Breakdown

## Purpose
This file handles **creating all output feature classes**. It separates data output logic from the algorithm and tool interface.

---

## Part 1: Imports and Class Definition

```python
import arcpy
from geometry_utils import GeometryUtils

class OutputManager:
    """Manages creation of output feature classes"""
    
    def __init__(self, workspace, spatial_reference):
        self.workspace = workspace
        self.spatial_ref = spatial_reference
        self.geo_utils = GeometryUtils()
```

**Constructor stores:**
- `workspace` - Where to save outputs (geodatabase or folder)
- `spatial_ref` - Coordinate system for outputs
- `geo_utils` - For distance calculations

---

## Part 2: create_all_outputs() - Main Coordinator

```python
def create_all_outputs(self, iteration_history, points, 
                      facilities_name, iterations_name, assignments_name):
    """Create all output feature classes"""
    arcpy.AddMessage("\nCreating output feature classes...")
    
    # Get final state
    final_facilities = iteration_history[-1]["facilities"]
    final_assignments = iteration_history[-1]["assignments"]
    
    # Create outputs
    self.create_facilities_output(final_facilities, facilities_name)
    self.create_iterations_output(iteration_history, iterations_name)
    self.create_assignments_output(points, final_facilities, 
                                   final_assignments, assignments_name)
```

### Negative indexing
```python
iteration_history[-1]
```
- `[-1]` gets the **last item** in a list
- `[-2]` would get second-to-last
- Very useful for getting final results

**Example:**
```python
my_list = [10, 20, 30, 40, 50]
my_list[0]   # 10 (first)
my_list[-1]  # 50 (last)
my_list[-2]  # 40 (second to last)
```

---

## Part 3: create_facilities_output() - Final Facility Locations

```python
def create_facilities_output(self, facilities, output_name):
    """Create feature class for final facility locations"""
    output_fc = output_name
    
    # Create feature class
    arcpy.CreateFeatureclass_management(
        self.workspace, 
        output_fc, 
        "POINT", 
        spatial_reference=self.spatial_ref
    )
```

### CreateFeatureclass_management breakdown
```python
arcpy.CreateFeatureclass_management(
    out_path,           # Where to save
    out_name,           # Name of feature class
    geometry_type,      # "POINT", "POLYLINE", "POLYGON"
    spatial_reference   # Coordinate system
)
```

This creates an **empty** feature class - just the structure, no data yet.

### Adding fields
```python
arcpy.AddField_management(output_fc, "Facility_ID", "LONG")
arcpy.AddField_management(output_fc, "X_Coord", "DOUBLE")
arcpy.AddField_management(output_fc, "Y_Coord", "DOUBLE")
```

**Field types:**
- `"LONG"` - Integer numbers (-2,147,483,648 to 2,147,483,647)
- `"DOUBLE"` - Decimal numbers (high precision)
- `"FLOAT"` - Decimal numbers (medium precision)
- `"SHORT"` - Small integers (-32,768 to 32,767)
- `"TEXT"` - Text strings (specify length: `field_length=50`)
- `"DATE"` - Date/time values

### Inserting features with InsertCursor
```python
fields = ["SHAPE@XY", "Facility_ID", "X_Coord", "Y_Coord"]
with arcpy.da.InsertCursor(output_fc, fields) as cursor:
    for facility in facilities:
        cursor.insertRow([
            (facility["x"], facility["y"]),  # SHAPE@XY
            facility["id"],                  # Facility_ID
            facility["x"],                   # X_Coord
            facility["y"]                    # Y_Coord
        ])
```

**Special field tokens:**
- `"SHAPE@XY"` - Point coordinates as tuple `(x, y)`
- `"SHAPE@"` - Full geometry object
- `"OID@"` - Object ID (read-only)
- `"SHAPE@LENGTH"` - Length of line
- `"SHAPE@AREA"` - Area of polygon

**InsertCursor:**
- Takes list of field names
- `.insertRow()` takes list of values in same order
- Context manager (`with ... as cursor:`) automatically saves and closes

**Example:**
```python
# Fields: ["SHAPE@XY", "Name", "Value"]
cursor.insertRow([
    (100, 200),      # Coordinates
    "Point A",       # Name
    42               # Value
])
```

---

## Part 4: create_iterations_output() - All Iterations

```python
def create_iterations_output(self, iteration_history, output_name):
    """Create feature class showing all iterations"""
    
    # ... Create feature class and add fields ...
    
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
```

### Nested loops for multiple features
```python
for iter_data in iteration_history:          # Each iteration
    for i, facility in enumerate(iter_data["facilities"]):  # Each facility
        cursor.insertRow([...])
```

**This creates:**
- If 5 iterations and 3 facilities per iteration = 15 total features
- Each facility appears once per iteration
- Can visualize how facilities moved over time

**Getting cluster size:**
```python
cluster_size = iter_data["cluster_sizes"][i]
```
- `iter_data["cluster_sizes"]` is a list like `[10, 8, 12]`
- `i` is the facility index (0, 1, 2)
- So this gets the cluster size for the current facility

---

## Part 5: create_assignments_output() - Point Assignments

```python
def create_assignments_output(self, points, facilities, assignments, output_name):
    """Create feature class showing point assignments"""
    
    # ... Create feature class and add fields ...
    
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
                point["xy"],        # Original point location
                point["oid"],       # Original point ID
                facility_id,        # Which facility serves it
                dist,               # Distance to facility
                facility["x"],      # Facility X
                facility["y"]       # Facility Y
            ])
```

### Lookup pattern
```python
for i, point in enumerate(points):
    facility_id = assignments[i]       # Get facility for this point
    facility = facilities[facility_id]  # Get facility details
```

**Step by step:**
1. Loop through points with index `i`
2. Look up which facility serves this point: `assignments[i]`
3. Get that facility's data from the facilities list

**Example:**
```python
points = [point0, point1, point2]
assignments = [0, 1, 0]  # point0→fac0, point1→fac1, point2→fac0
facilities = [fac0, fac1]

# When i=0:
facility_id = assignments[0]  # = 0
facility = facilities[0]      # = fac0

# When i=1:
facility_id = assignments[1]  # = 1
facility = facilities[1]      # = fac1
```

---

## Common ArcPy Data Access Patterns

### Creating Feature Classes
```python
# 1. Create empty feature class
arcpy.CreateFeatureclass_management(workspace, name, geometry_type, spatial_reference=sr)

# 2. Add fields
arcpy.AddField_management(fc, "FieldName", "LONG")

# 3. Insert data
with arcpy.da.InsertCursor(fc, ["SHAPE@XY", "FieldName"]) as cursor:
    cursor.insertRow([(x, y), value])
```

### Reading Feature Classes
```python
# SearchCursor - read data
with arcpy.da.SearchCursor(fc, ["SHAPE@XY", "FieldName"]) as cursor:
    for row in cursor:
        coords = row[0]
        value = row[1]
```

### Updating Feature Classes
```python
# UpdateCursor - modify existing data
with arcpy.da.UpdateCursor(fc, ["FieldName"]) as cursor:
    for row in cursor:
        row[0] = row[0] * 2  # Double the value
        cursor.updateRow(row)
```

### Deleting Features
```python
# Delete features matching condition
with arcpy.da.UpdateCursor(fc, ["FieldName"]) as cursor:
    for row in cursor:
        if row[0] < 0:
            cursor.deleteRow()
```

---

## Key Python Concepts

1. **Context managers** - `with ... as cursor:` (automatic cleanup)
2. **InsertCursor** - Add new features
3. **SearchCursor** - Read features
4. **UpdateCursor** - Modify features
5. **Negative indexing** - `list[-1]` gets last item
6. **enumerate()** - Loop with index and value
7. **Nested loops** - Loop inside loop for 2D iteration

---

## How to Modify

### Add a statistics field to facilities output:
```python
def create_facilities_output(self, facilities, output_name):
    # ... existing code ...
    
    # Add additional field
    arcpy.AddField_management(output_fc, "Avg_Distance", "DOUBLE")
    
    # Calculate average distance per facility (you'd need to compute this)
    fields = ["SHAPE@XY", "Facility_ID", "X_Coord", "Y_Coord", "Avg_Distance"]
    with arcpy.da.InsertCursor(output_fc, fields) as cursor:
        for facility in facilities:
            avg_dist = facility.get("avg_distance", 0.0)  # Get if exists
            cursor.insertRow([
                (facility["x"], facility["y"]),
                facility["id"],
                facility["x"],
                facility["y"],
                avg_dist
            ])
```

### Create polyline connections between points and facilities:
```python
def create_spider_lines(self, points, facilities, assignments, output_name):
    """Create lines from each point to its assigned facility"""
    output_fc = output_name
    
    arcpy.CreateFeatureclass_management(
        self.workspace,
        output_fc,
        "POLYLINE",
        spatial_reference=self.spatial_ref
    )
    
    arcpy.AddField_management(output_fc, "Point_OID", "LONG")
    arcpy.AddField_management(output_fc, "Facility_ID", "LONG")
    arcpy.AddField_management(output_fc, "Distance", "DOUBLE")
    
    fields = ["SHAPE@", "Point_OID", "Facility_ID", "Distance"]
    
    with arcpy.da.InsertCursor(output_fc, fields) as cursor:
        for i, point in enumerate(points):
            facility_id = assignments[i]
            facility = facilities[facility_id]
            
            # Create line geometry
            start_point = arcpy.Point(point["xy"][0], point["xy"][1])
            end_point = arcpy.Point(facility["x"], facility["y"])
            array = arcpy.Array([start_point, end_point])
            polyline = arcpy.Polyline(array, self.spatial_ref)
            
            dist = self.geo_utils.euclidean_distance(
                point["xy"][0], point["xy"][1],
                facility["x"], facility["y"]
            )
            
            cursor.insertRow([polyline, point["oid"], facility_id, dist])
```

### Add summary statistics table:
```python
def create_summary_table(self, iteration_history, output_name):
    """Create table summarizing each iteration"""
    output_table = output_name
    
    arcpy.CreateTable_management(self.workspace, output_table)
    
    arcpy.AddField_management(output_table, "Iteration", "LONG")
    arcpy.AddField_management(output_table, "Objective", "DOUBLE")
    arcpy.AddField_management(output_table, "Min_Cluster", "LONG")
    arcpy.AddField_management(output_table, "Max_Cluster", "LONG")
    arcpy.AddField_management(output_table, "Avg_Cluster", "DOUBLE")
    
    fields = ["Iteration", "Objective", "Min_Cluster", "Max_Cluster", "Avg_Cluster"]
    
    with arcpy.da.InsertCursor(output_table, fields) as cursor:
        for iter_data in iteration_history:
            sizes = iter_data["cluster_sizes"]
            cursor.insertRow([
                iter_data["iteration"],
                iter_data["objective"],
                min(sizes),
                max(sizes),
                sum(sizes) / len(sizes)
            ])
```

---

## Debugging Tips

### Print what you're inserting:
```python
for facility in facilities:
    row_data = [
        (facility["x"], facility["y"]),
        facility["id"],
        facility["x"],
        facility["y"]
    ]
    arcpy.AddMessage(f"Inserting: {row_data}")
    cursor.insertRow(row_data)
```

### Check if feature class was created:
```python
if arcpy.Exists(output_fc):
    arcpy.AddMessage(f"✓ {output_fc} created successfully")
    count = int(arcpy.GetCount_management(output_fc)[0])
    arcpy.AddMessage(f"  Features: {count}")
else:
    arcpy.AddError(f"✗ Failed to create {output_fc}")
```

### Validate field names:
```python
fields = [f.name for f in arcpy.ListFields(output_fc)]
arcpy.AddMessage(f"Fields in {output_fc}: {fields}")
```
