# geometry_utils.py - Detailed Breakdown

## Purpose
This file contains **reusable geometry helper functions**. It's separate so you can use these functions in other tools too.

---

## Part 1: Imports and Class Definition

```python
import math

class GeometryUtils:
    """Collection of geometry utility functions"""
```

- `import math` - Python's math library (sqrt, sin, cos, etc.)
- This class only contains **static methods** (no instance variables)

---

## Part 2: euclidean_distance() - Calculate Distance

```python
@staticmethod
def euclidean_distance(x1, y1, x2, y2):
    """Calculate Euclidean distance between two points"""
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
```

### @staticmethod Decorator

```python
@staticmethod
```
This is a **decorator** - it modifies how the method works:
- Static methods don't need `self`
- Can be called without creating an object
- Usage: `GeometryUtils.euclidean_distance(0, 0, 3, 4)`

**With static method:**
```python
distance = GeometryUtils.euclidean_distance(0, 0, 3, 4)
```

**Without static method (would need):**
```python
geo = GeometryUtils()
distance = geo.euclidean_distance(0, 0, 3, 4)
```

### Distance Formula

```python
return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
```

This implements the Pythagorean theorem:
- Distance = √[(x₂ - x₁)² + (y₂ - y₁)²]

**Example:**
```python
# Point A = (0, 0)
# Point B = (3, 4)
distance = math.sqrt((3-0)**2 + (4-0)**2)
distance = math.sqrt(9 + 16)
distance = math.sqrt(25)
distance = 5.0
```

**Exponentiation operator:**
```python
x ** 2  # x squared (x²)
x ** 3  # x cubed (x³)
x ** 0.5  # Square root of x (√x)
```

---

## Part 3: calculate_centroid() - Find Center Point

```python
@staticmethod
def calculate_centroid(points):
    """Calculate centroid (mean center) of a set of points"""
    if not points:
        return None
    
    sum_x = sum(p["xy"][0] for p in points)
    sum_y = sum(p["xy"][1] for p in points)
    
    centroid_x = sum_x / len(points)
    centroid_y = sum_y / len(points)
    
    return (centroid_x, centroid_y)
```

### Check for empty list
```python
if not points:
    return None
```
- `not points` is True if list is empty: `[]`
- Returns `None` (Python's "null" value) if no points

### Calculate average coordinates
```python
sum_x = sum(p["xy"][0] for p in points)
centroid_x = sum_x / len(points)
```
- Adds up all X coordinates
- Divides by number of points
- Result: average X position

**Example:**
```python
points = [
    {"xy": (0, 0)},
    {"xy": (6, 0)},
    {"xy": (3, 3)}
]

sum_x = 0 + 6 + 3 = 9
sum_y = 0 + 0 + 3 = 3
centroid_x = 9 / 3 = 3.0
centroid_y = 3 / 3 = 1.0

# Centroid is at (3.0, 1.0)
```

### Return tuple
```python
return (centroid_x, centroid_y)
```
- Parentheses create a **tuple** (immutable list)
- Can be unpacked: `x, y = calculate_centroid(points)`

---

## Part 4: calculate_distance_matrix() - All Pairwise Distances

```python
@staticmethod
def calculate_distance_matrix(points1, points2):
    """Calculate distance matrix between two sets of points"""
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
```

### What's a distance matrix?

A 2D grid showing distance from each point in set 1 to each point in set 2.

**Example:**
```python
points1 = [A, B, C]  # 3 points
points2 = [X, Y]     # 2 points

# Result: 3×2 matrix
[
    [dist(A,X), dist(A,Y)],  # Row for point A
    [dist(B,X), dist(B,Y)],  # Row for point B
    [dist(C,X), dist(C,Y)]   # Row for point C
]
```

### Nested loops for 2D structure
```python
for p1 in points1:         # Outer loop: rows
    row = []               # Start new row
    for p2 in points2:     # Inner loop: columns
        dist = ...         # Calculate distance
        row.append(dist)   # Add to row
    distances.append(row)  # Add row to matrix
```

### Accessing results
```python
matrix = calculate_distance_matrix(points1, points2)
distance = matrix[0][1]  # Distance from point 0 to point 1
```
- First `[0]` selects the row (first point in points1)
- Second `[1]` selects the column (second point in points2)

---

## How to Use This Class

### Basic usage:
```python
from geometry_utils import GeometryUtils

# Calculate distance
dist = GeometryUtils.euclidean_distance(0, 0, 3, 4)
print(dist)  # 5.0

# Find centroid
points = [{"xy": (0, 0)}, {"xy": (6, 0)}, {"xy": (3, 6)}]
center = GeometryUtils.calculate_centroid(points)
print(center)  # (3.0, 2.0)
```

### In another class:
```python
class MyAlgorithm:
    def __init__(self):
        self.geo_utils = GeometryUtils()
    
    def calculate(self):
        # Either way works:
        dist1 = self.geo_utils.euclidean_distance(0, 0, 1, 1)
        dist2 = GeometryUtils.euclidean_distance(0, 0, 1, 1)
```

---

## Key Python Concepts

1. **@staticmethod** - Methods that don't need `self`
2. **math.sqrt()** - Square root function
3. **Exponentiation** - `x ** 2` for powers
4. **Tuples** - `(x, y)` immutable sequences
5. **None** - Python's null value
6. **2D lists** - Lists containing lists (matrices)
7. **Generator expressions** - `sum(expression for item in list)`
8. **Nested loops** - Loop inside a loop

---

## How to Modify

### Add Manhattan distance (taxi-cab distance):
```python
@staticmethod
def manhattan_distance(x1, y1, x2, y2):
    """Calculate Manhattan distance (|x2-x1| + |y2-y1|)"""
    return abs(x2 - x1) + abs(y2 - y1)
```

### Add haversine distance (for lat/lon):
```python
@staticmethod
def haversine_distance(lon1, lat1, lon2, lat2):
    """Calculate distance between lat/lon points in kilometers"""
    # Convert to radians
    lon1_rad = math.radians(lon1)
    lat1_rad = math.radians(lat1)
    lon2_rad = math.radians(lon2)
    lat2_rad = math.radians(lat2)
    
    # Haversine formula
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth radius in kilometers
    r = 6371
    return c * r
```

### Add weighted centroid:
```python
@staticmethod
def weighted_centroid(points, weights):
    """Calculate weighted centroid"""
    if not points or not weights:
        return None
    
    total_weight = sum(weights)
    sum_x = sum(p["xy"][0] * w for p, w in zip(points, weights))
    sum_y = sum(p["xy"][1] * w for p, w in zip(points, weights))
    
    centroid_x = sum_x / total_weight
    centroid_y = sum_y / total_weight
    
    return (centroid_x, centroid_y)
```

### Add bounding box calculator:
```python
@staticmethod
def calculate_bounding_box(points):
    """Calculate min/max X and Y coordinates"""
    if not points:
        return None
    
    all_x = [p["xy"][0] for p in points]
    all_y = [p["xy"][1] for p in points]
    
    return {
        "min_x": min(all_x),
        "max_x": max(all_x),
        "min_y": min(all_y),
        "max_y": max(all_y)
    }
```
