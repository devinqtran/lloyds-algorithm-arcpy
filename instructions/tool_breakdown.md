# lloyds_tool.py - Detailed Breakdown

## Purpose
This file handles **all ArcGIS Pro tool interface logic**:
- Defines what parameters users see
- Validates user input
- Loads data from feature classes
- Calls the algorithm
- Creates outputs
- Shows messages to users

---

## Part 1: Imports and Class Definition

```python
import arcpy
import os
from lloyds_algorithm import LloydsAlgorithm
from output_manager import OutputManager
```
**Imports:**
- `arcpy` - ArcGIS functions
- `os` - Operating system functions (for file paths)
- `LloydsAlgorithm` - Your algorithm class (we'll cover this next)
- `OutputManager` - Handles creating feature classes

---

```python
class LloydsAlgorithmTool(object):
    """ArcGIS Pro tool interface for Lloyd's Algorithm"""
    
    def __init__(self):
        self.label = "Lloyd's Algorithm Facility Location"
        self.description = """..."""
        self.canRunInBackground = False
```
**Tool setup:**
- `self.label` - Tool name in ArcGIS Pro
- `self.description` - Help text shown to users
- `self.canRunInBackground = False` - Tool runs in foreground (shows progress)

---

## Part 2: getParameterInfo() - Define Tool Parameters

```python
def getParameterInfo(self):
    """Define parameter definitions"""
```
This method tells ArcGIS Pro what inputs/outputs your tool needs.

### Creating a Parameter:
```python
param0 = arcpy.Parameter(
    displayName="Input Demand Points",      # Label shown to user
    name="input_points",                     # Internal variable name
    datatype="GPFeatureLayer",              # Type of data
    parameterType="Required",               # Required or Optional
    direction="Input")                      # Input or Output
param0.filter.list = ["Point"]              # Only allow point features
```

**Parameter anatomy:**
- `displayName` - What users see
- `name` - How you reference it in code
- `datatype` - What kind of data (feature layer, number, text, etc.)
- `parameterType` - "Required" or "Optional"
- `direction` - "Input" or "Output"
- `filter` - Restricts valid inputs

### Common datatypes:
- `"GPFeatureLayer"` - Feature class/layer
- `"GPLong"` - Integer number
- `"GPDouble"` - Decimal number
- `"GPString"` - Text
- `"DEWorkspace"` - Folder or geodatabase

### Setting default values:
```python
param1.value = 3  # Default to 3 facilities
```

### Return all parameters as a list:
```python
return [param0, param1, param2, param3, param4, param5, param6, param7]
```
Order matters! `parameters[0]` will be param0, `parameters[1]` will be param1, etc.

---

## Part 3: updateMessages() - Validate User Input

```python
def updateMessages(self, parameters):
    """Modify messages created by internal validation"""
    
    if parameters[1].value and parameters[1].value < 1:
        parameters[1].setErrorMessage("Number of facilities must be at least 1")
```

**How it works:**
- Runs whenever user changes a parameter
- `parameters[1]` - References the 2nd parameter (Number of Facilities)
- `parameters[1].value` - Gets the value user entered
- `parameters[1].setErrorMessage(...)` - Shows red error message
- Tool won't run if there are error messages

**The `and` operator:**
```python
if parameters[1].value and parameters[1].value < 1:
```
This checks:
1. Does the parameter have a value? (`parameters[1].value`)
2. Is it less than 1? (`parameters[1].value < 1`)

Both must be true for the error to show.

---

## Part 4: execute() - Main Tool Logic

```python
def execute(self, parameters, messages):
    """Main execution method"""
```
This runs when user clicks "Run" in ArcGIS Pro.

### Step 1: Extract parameter values
```python
input_points = parameters[0].valueAsText
num_facilities = parameters[1].value
max_iterations = parameters[2].value
# ... etc
```
- `parameters[0]` - First parameter (matches order from getParameterInfo)
- `.valueAsText` - Gets value as text string (for file paths)
- `.value` - Gets actual value (numbers, etc.)

### Step 2: Configure environment
```python
arcpy.env.workspace = output_workspace
arcpy.env.overwriteOutput = True
```
- `arcpy.env` - Global settings for ArcGIS operations
- `workspace` - Where outputs are saved
- `overwriteOutput = True` - Replace existing files without asking

### Step 3: Load input data
```python
points, spatial_ref = self._load_demand_points(input_points)
```
- `self._load_demand_points()` - Calls a helper method (defined below)
- Returns TWO values: points (data) and spatial_ref (coordinate system)
- The underscore `_` prefix means "private method" (internal use only)

### Step 4: Run the algorithm
```python
algorithm = LloydsAlgorithm(num_facilities, max_iterations, convergence_threshold)
iteration_history = algorithm.run(points)
```
- Creates an algorithm object with your settings
- Calls `run()` method to execute
- Returns iteration_history (list of all iterations)

### Step 5: Create outputs
```python
output_mgr = OutputManager(output_workspace, spatial_ref)
output_mgr.create_all_outputs(...)
```
- Creates OutputManager object
- Calls method to create all feature classes

### Step 6: Print summary and add to map
```python
self._print_summary(...)
self._add_to_map(...)
```

---

## Part 5: Helper Methods

### _print_header()
```python
def _print_header(self, input_points, num_facilities, max_iterations, convergence_threshold):
    arcpy.AddMessage("=" * 60)  # Prints 60 equal signs
    arcpy.AddMessage("LLOYD'S ALGORITHM FOR OPTIMAL FACILITY LOCATION")
```
- `arcpy.AddMessage()` - Prints to tool's message window
- `"=" * 60` - String multiplication creates "======..." (60 times)

### _load_demand_points()
```python
def _load_demand_points(self, input_points):
    points = []  # Empty list
    spatial_ref = arcpy.Describe(input_points).spatialReference
    
    with arcpy.da.SearchCursor(input_points, ["SHAPE@XY", "OID@"]) as cursor:
        for row in cursor:
            points.append({"xy": row[0], "oid": row[1]})
    
    return points, spatial_ref
```

**Breaking this down:**

1. **Create empty list:**
   ```python
   points = []
   ```

2. **Get spatial reference:**
   ```python
   spatial_ref = arcpy.Describe(input_points).spatialReference
   ```
   - `arcpy.Describe()` - Gets properties of a dataset
   - `.spatialReference` - The coordinate system

3. **Read features with SearchCursor:**
   ```python
   with arcpy.da.SearchCursor(input_points, ["SHAPE@XY", "OID@"]) as cursor:
   ```
   - `SearchCursor` - Reads rows from feature class
   - `["SHAPE@XY", "OID@"]` - Fields to read (coordinates and object ID)
   - `with ... as cursor:` - Context manager (automatically closes cursor when done)

4. **Loop through rows:**
   ```python
   for row in cursor:
       points.append({"xy": row[0], "oid": row[1]})
   ```
   - `for row in cursor:` - Iterate through each feature
   - `row[0]` - First field (SHAPE@XY - coordinates)
   - `row[1]` - Second field (OID@ - object ID)
   - `{"xy": ..., "oid": ...}` - Dictionary (key-value pairs)
   - `.append()` - Adds item to list

5. **Return multiple values:**
   ```python
   return points, spatial_ref
   ```
   Returns a tuple of two values

### _add_to_map()
```python
def _add_to_map(self, workspace, facilities_name, iterations_name, assignments_name):
    try:
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map_view = aprx.activeMap
        if map_view:
            facilities_path = os.path.join(workspace, facilities_name)
            map_view.addDataFromPath(facilities_path)
    except Exception as e:
        arcpy.AddMessage(f"Could not auto-add to map: {str(e)}")
```

**Try-except blocks:**
```python
try:
    # Code that might fail
except Exception as e:
    # What to do if it fails
```
Prevents tool from crashing if map isn't available.

**F-strings:**
```python
f"Could not auto-add to map: {str(e)}"
```
- `f"..."` - Formatted string
- `{str(e)}` - Inserts variable value into string

---

## Key Python Concepts

1. **Methods** - Functions inside classes (`def method_name(self):`)
2. **self** - Reference to current object
3. **Lists** - `[]` ordered collections, can append items
4. **Dictionaries** - `{}` key-value pairs
5. **Tuples** - `()` immutable ordered collections
6. **For loops** - `for item in collection:`
7. **If statements** - `if condition:`
8. **Try-except** - Error handling
9. **Context managers** - `with ... as ...:`
10. **F-strings** - `f"text {variable}"`

---

## How to Modify

### Add a new parameter:
```python
def getParameterInfo(self):
    # ... existing parameters ...
    
    param8 = arcpy.Parameter(
        displayName="Weight Field",
        name="weight_field",
        datatype="Field",
        parameterType="Optional",
        direction="Input")
    
    return [param0, param1, ..., param8]  # Add to list
```

### Add validation:
```python
def updateMessages(self, parameters):
    # ... existing validation ...
    
    if parameters[8].value:
        # Check if weight field is numeric
        pass
```

### Modify what gets printed:
```python
def _print_header(self, ...):
    arcpy.AddMessage("*" * 60)  # Use asterisks instead
    arcpy.AddMessage("MY CUSTOM TOOL")
```
