"""
Lloyd's Algorithm Toolbox for ArcGIS Pro
Main toolbox file that registers tools with ArcGIS Pro
"""

import arcpy
from lloyds_tool import LloydsAlgorithmTool


class Toolbox(object):
    """Main toolbox class that ArcGIS Pro recognizes"""
    
    def __init__(self):
        self.label = "Improved Lloyd's Algorithm Toolbox"
        self.alias = "lloyds"
        self.tools = [LloydsAlgorithmTool]