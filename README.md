# ForestSkylines

ForestSkylines is a mod for Cities: Skylines 2 for importing of forests based on GIS vector or raster data, conceptually based on the older [GeoSkylines](https://github.com/DavixDevelop/GeoSkylines) mod for Cities Skylines 1.

## Prerequisites
- QGIS 4.2.3
- Image editor (Optional)
- General knowledge on GIS (CRS, extents, etc) or raster editing
- Source of GIS forestry data or drawing skills

## Features
The toolset enables users to generate a tree map called TreesBIN, which describes what type of trees and where to place them, based on a simple raster PNG file or GIS vector data. The mod then uses the tree map alongside a unified JSON config file to place the trees to generate the trees.

Depending on the source file, the two distinct workloads are described in the [Guide](./docs/GUIDE.md)

## Future plans
I plan to introduce more UI features into the mod and toolsets, to make the whole process less manual. Ex, the user could first in the editor generate the config file, where they would enter the tree types, what trees to place per tree type and further input options based on the type of source file.