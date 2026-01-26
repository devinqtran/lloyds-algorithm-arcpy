# lloyds_algorithm.py - Detailed Breakdown

## Purpose
This is the **core algorithm logic** - the "brain" of the tool. It's intentionally separated from ArcGIS so you can test and modify it independently.

---

## Part 1: Imports and Class Definition

```python
import arcpy
import random
from geometry_utils import GeometryUtils
```
- `random` - Python's random number generator
- `GeometryUtils` - Your custom geometry helper class

```python
class LloydsAlgorithm:
    """Core Lloyd's algorithm implementation"""
    
    def __init__(self, num_facilities, max_iterations, convergence_threshold):
        self.num_facilities = num_facilities
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        self.geo_utils = GeometryUtils()
```

**Constructor breakdown:**
- Stores settings as instance variables (`self.variable_name`)
- Creates a GeometryUtils object for distance calculations
- Now these values are available to all methods in the class

---

## Part 2: run() - Main Algorithm Loop

```python
def run(self, points):
    """Execute Lloyd's algorithm"""
```

This is the main method that orchestrates everything.

### Step 1: Initialize facilities
```python
facilities = self._initialize_facilities(points)
```
Picks random starting locations for facilities.

### Step 2: Set up iteration loop
```python
iteration_history = []  # Store results from each iteration
converged = False       # Has algorithm converged?

for iteration in range(self.max_iterations):
```

**range() explained:**
```python
range(20)  # Generates: 0, 1, 2, 3, ... 19
```
So `for iteration in range(20):` loops 20 times with iteration = 0, 1, 2, ... 19

### Step 3: Assignment phase
```python
assignments = self._assign_points_to_facilities(points, facilities)
```
For each demand point, find which facility is closest.

Returns a list like: `[0, 0, 1, 2, 1, ...]` meaning:
- Point 0 → Facility 0
- Point 1 → Facility 0  
- Point 2 → Facility 1
- Point 3 → Facility 2
- etc.

### Step 4: Calculate metrics
```python
objective = self._calculate_objective_function(points, facilities, assignments)
cluster_sizes = self._calculate_cluster_sizes(assignments)
```
- `objective` - Total distance (lower is better)
- `cluster_sizes` - How many points per facility: `[15, 8, 12]`

### Step 5: Store iteration data
```python
iteration_history.append({
    "iteration": iteration + 1,
    "facilities": [f.copy() for f in facilities],
    "objective": objective,
    "assignments": assignments.copy(),
    "cluster_sizes": cluster_sizes
})
```

**Dictionary in a list:**
- `{}` creates a dictionary
- `.append()` adds it to the list
- Each iteration adds one dictionary to the history

**List comprehension:**
```python
[f.copy() for f in facilities]
```
This is shorthand for:
```python
new_list = []
for f in facilities:
    new_list.append(f.copy())
```
- Loops through facilities
- Copies each one (`.copy()` makes a duplicate)
- Creates a new list

**Why copy?**
Without `.copy()`, if you modify facilities later, it changes the history too. Copying prevents this.

### Step 6: Update facilities (centroid calculation)
```python
new_facilities = self._calculate_centroids(points, facilities, assignments)
```
Moves each facility to the center of its assigned points.

### Step 7: Check convergence
```python
max_movement = self._calculate_max_movement(facilities, new_facilities)

if max_movement < self.convergence_threshold:
    converged = True
    facilities = new_facilities
    # Store final state...
    break  # Exit the loop early
```

**Break statement:**
Immediately exits the for loop (stops iterating).

### Step 8: Update for next iteration
```python
facilities = new_facilities
```
Replace old facility locations with new ones.

### Step 9: Return results
```python
return iteration_history
```
Returns list of all iteration dictionaries.

---

## Part 3: _initialize_facilities() - Random Start

```python
def _initialize_facilities(self, points):
    random.seed(42)  # For reproducibility
    selected_indices = random.sample(range(len(points)), self.num_facilities)
    
    facilities = []
    for i, idx in enumerate(selected_indices):
        facilities.append({
            "id": i,
            "x": points[idx]["xy"][0],
            "y": points[idx]["xy"][1]
        })
    
    return facilities
```

**Breaking this down:**

1. **Set random seed:**
   ```python
   random.seed(42)
   ```
   Makes "random" numbers predictable (same results each run). Try changing 42 to another number for different starting points.

2. **Pick random points:**
   ```python
   random.sample(range(len(points)), self.num_facilities)
   ```
   - `len(points)` - Number of points (e.g., 100)
   - `range(100)` - Creates [0, 1, 2, ..., 99]
   - `random.sample(..., 3)` - Picks 3 random numbers
   - Result: `[23, 67, 5]` (random indices)

3. **Enumerate explained:**
   ```python
   for i, idx in enumerate(selected_indices):
   ```
   If `selected_indices = [23, 67, 5]`, enumerate gives:
   - Loop 1: `i=0, idx=23`
   - Loop 2: `i=1, idx=67`
   - Loop 3: `i=2, idx=5`

4. **Create facility dictionary:**
   ```python
   facilities.append({
       "id": i,              # 0, 1, 2 (facility number)
       "x": points[idx]["xy"][0],  # X coordinate
       "y": points[idx]["xy"][1]   # Y coordinate
   })
   ```
   - `points[idx]` - Gets point at index idx
   - `["xy"]` - Gets xy key from dictionary
   - `[0]` - Gets X coordinate (first element)
   - `[1]` - Gets Y coordinate (second element)

---

## Part 4: _assign_points_to_facilities() - Nearest Neighbor

```python
def _assign_points_to_facilities(self, points, facilities):
    assignments = []
    
    for point in points:
        min_dist = float('inf')  # Start with infinity
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
```

**Algorithm logic:**

1. **For each point:**
   - Start with `min_dist = infinity` (any real distance will be smaller)
   - Check distance to every facility
   - Track which facility is closest

2. **float('inf'):**
   Represents mathematical infinity. Useful as a starting value when finding minimums.

3. **Nested loops:**
   ```python
   for point in points:          # Outer loop: each point
       for facility in facilities:  # Inner loop: each facility
   ```
   If you have 100 points and 3 facilities, this runs 100 × 3 = 300 times.

---

## Part 5: _calculate_objective_function() - Total Distance

```python
def _calculate_objective_function(self, points, facilities, assignments):
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
```

**How it works:**
- Loop through all points
- For each point, find its assigned facility
- Calculate distance
- Add to running total (`+=` means "add to")

**Why enumerate?**
```python
for i, point in enumerate(points):
```
Gives us both:
- `i` - Index (0, 1, 2, ...)
- `point` - The actual point dictionary

We need `i` to look up the assignment: `assignments[i]`

---

## Part 6: _calculate_cluster_sizes() - Count Points per Facility

```python
def _calculate_cluster_sizes(self, assignments):
    sizes = [0] * self.num_facilities
    for assignment in assignments:
        sizes[assignment] += 1
    return sizes
```

**List multiplication:**
```python
[0] * 3  # Creates [0, 0, 0]
```

**Counting logic:**
If `assignments = [0, 0, 1, 2, 1]`:
- Start: `sizes = [0, 0, 0]`
- Point 0 → Facility 0: `sizes[0] += 1` → `[1, 0, 0]`
- Point 1 → Facility 0: `sizes[0] += 1` → `[2, 0, 0]`
- Point 2 → Facility 1: `sizes[1] += 1` → `[2, 1, 0]`
- Point 3 → Facility 2: `sizes[2] += 1` → `[2, 1, 1]`
- Point 4 → Facility 1: `sizes[1] += 1` → `[2, 2, 1]`

Result: `[2, 2, 1]` means Facility 0 has 2 points, Facility 1 has 2 points, Facility 2 has 1 point.

---

## Part 7: _calculate_centroids() - Find Centers

```python
def _calculate_centroids(self, points, facilities, assignments):
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
```

**List comprehension with condition:**
```python
assigned_points = [
    points[i] for i, assign in enumerate(assignments) 
    if assign == facility_id
]
```
This filters points:
- Loop through assignments with index
- Only include point if it's assigned to this facility

Example:
```python
points = [p0, p1, p2, p3, p4]
assignments = [0, 0, 1, 2, 1]
facility_id = 1

# Result: [p2, p4] (points assigned to facility 1)
```

**Generator expression for sum:**
```python
sum(p["xy"][0] for p in assigned_points)
```
Shorthand for:
```python
total = 0
for p in assigned_points:
    total += p["xy"][0]
```

**Centroid calculation:**
```python
centroid_x = sum_x / len(assigned_points)  # Average X
centroid_y = sum_y / len(assigned_points)  # Average Y
```

---

## Part 8: _calculate_max_movement() - Check Convergence

```python
def _calculate_max_movement(self, old_facilities, new_facilities):
    max_dist = 0.0
    
    for old_fac, new_fac in zip(old_facilities, new_facilities):
        dist = self.geo_utils.euclidean_distance(
            old_fac["x"], old_fac["y"],
            new_fac["x"], new_fac["y"]
        )
        if dist > max_dist:
            max_dist = dist
    
    return max_dist
```

**zip() function:**
```python
for old_fac, new_fac in zip(old_facilities, new_facilities):
```
Pairs up elements from two lists:
```python
old = [fac0_old, fac1_old, fac2_old]
new = [fac0_new, fac1_new, fac2_new]

# zip creates:
# Loop 1: old_fac=fac0_old, new_fac=fac0_new
# Loop 2: old_fac=fac1_old, new_fac=fac1_new
# Loop 3: old_fac=fac2_old, new_fac=fac2_new
```

**Finding maximum:**
Tracks the largest movement of any facility.

---

## Key Python Concepts

1. **for loops** - Iterate through collections
2. **range()** - Generate number sequences
3. **enumerate()** - Loop with index and value
4. **zip()** - Pair up multiple lists
5. **List comprehensions** - `[expression for item in list if condition]`
6. **Generator expressions** - `sum(expression for item in list)`
7. **float('inf')** - Infinity value
8. **break** - Exit loop early
9. **.copy()** - Duplicate objects
10. **+=** - Add to variable (`x += 5` same as `x = x + 5`)

---

## How to Modify

### Change initialization to grid instead of random:
```python
def _initialize_facilities(self, points):
    # Find bounding box
    all_x = [p["xy"][0] for p in points]
    all_y = [p["xy"][1] for p in points]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    
    # Create grid
    facilities = []
    grid_size = int(self.num_facilities ** 0.5)  # Square root
    for i in range(self.num_facilities):
        row = i // grid_size
        col = i % grid_size
        x = min_x + (max_x - min_x) * col / grid_size
        y = min_y + (max_y - min_y) * row / grid_size
        facilities.append({"id": i, "x": x, "y": y})
    
    return facilities
```

### Add weighted distances:
```python
def _calculate_objective_function(self, points, facilities, assignments):
    total_distance = 0.0
    
    for i, point in enumerate(points):
        facility_id = assignments[i]
        facility = facilities[facility_id]
        
        dist = self.geo_utils.euclidean_distance(...)
        weight = point.get("weight", 1.0)  # Get weight or default to 1.0
        total_distance += dist * weight
    
    return total_distance
```
