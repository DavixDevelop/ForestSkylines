# Guide

As noted, the aim of this mod is to import 1:1 scale IRL forests into the game and to achieve this, a source file is first needed which can either be a raster file, like a simple PNG file or a vector file, like a polygon forest cover Shapefile. The first one can be created manually in an image editor, but can take some time, while the latter can be obtained from a government forest service, but this guide will not cover obtaining one and will only show on an example on how to create a base image, an sample raster source file and how to use a (multi) polygon Shapefile of the forest cover.

Regardless of source file type and with them, the two distinct workloads, the following prerequisites are recommended:
- QGIS 4.2.3
- General knowledge on GIS (CRS, extents, etc)
- A image editor of your liking (if using a raster source file)
- Base image

## Basics
Before we proceed with creating the tree map, we need to know the CRS or Coordinate Reference System of your location and the extent of your map. The extent of the City Map in Cities: Skylines 2 is **14336x14336m**, hence your extent size must be it as well for a 1:1 scale.<br>

> **Note:** This guide assumes your CRS uses meters as units.

## Unified JSON config file
The mod and the toolsets use a unified JSON config file to keep all the input parameters in one place, which for now must be manually edited. To obtain it download the template `config_file_template.json` file in the repository. The common parameters are in the root, while workload specific parameters are under It's own keys.

```json
{
  "id_list" : [1, 2],
  "color_to_id" : ["#f82bde", "#20a8a2"],
  "trees_bin_path" : "C://Users/user/Games/Cities Skylines 2/Map/forest.bin",
  "raster" : {
    "png_path" : "C://Users/user/Games/Cities Skylines 2/Map/forest.png"
  },
  "vector": {
    "attributes": [ "oak1", "spruce2"],
    "polygon_layer" : "ForestComposition",
    "map_extent" : [ 513477, 527813, 129423, 115087],
    "play_area_offset" : 1247,
    "trees_count" : 1400000,
    "non_play_area_tree_count": 167122
  }
}
```
*Config file prepared for both workloads*

## Preparing the base image
This example will focus on generating a base image in *QGIS* from a *Google Satellite* raster layer, but it will work with any layer, ex. with the *OpenStreetMap* layer as long as you know the extent of the IRL terrain you wish to recreate in-game, which must be exactly **14336x14336 meters**. You can either manually enter the extent or use a Shapefile bounds layer. In this case I will be using the latter.

1. Open QGIS and click on the right bottom button to set the Project CRS
2. Search for the projection you wish to use, ex. the native projection of your location, **EPSG:3794** in this example, select it and press `OK`
3. In the left `Browser` panel, under `XYZ Tiles` drag and drop *Google Satellite* or any GIS raster file/layer, you wish to use into the canvas
4. If you have a Shapefile bounds file, drag in into the canvas as well, and make it invisible by unchecking it in the left *Layers* panel
5. Zoom to your location and set the `Scale` (bottom toolbar) to ex **1:17280**
6. In the top toolbar got to `Project -> Import/Export -> Export Map to Image...`
7. Manually enter the `West`, `North`, `East` and `South` extent or calculate it from a layer (*Calculate from `Layer`*)
8. Set the `Resolution` to an appropriate DPI so that the *Output width and height* are detailed enough, ex. an DPI of *161* is **14283x14283px**, an DPI of *92* is **8161x8161px** and an DPI of *46* is **4082x4082**
9. Click on `Save` and save the raster base image, which will take longer the higher the DPI is

You can now use this base map for creating the raster PNG file of the forest cover, or you can use it in-game as an overlay with a mod.

## Preparing the TreesBIN file from a raster PNG file
This example will work with any raster PNG file with any resolution, especially if you wish to use a PNG file with a resolution higher than *Cites: Skylines 2/Unity* max supported **16384x16384** pixels. Before we get started we must first get ourselves familiarized with the concept of `composition ID's`. Imagine taking a satellite image and painting each tree or tree type with a single color. Each color is now a unique identity – **ID**, therefore for placing trees, as in this case in-game, you don't need the pixel color red, green and blue value. You only need the pixel position - x and y, and the **ID**. But to avoid repeating the **ID** for each pixel position, we store the pixel positions as a list *underneath* the **ID**. This enables us to place one or more types of trees depending on the composition ID.  

Now that we are familiar with the concept of `composition ID's`, you can either get an existing tree cover image, where the colors identity the composition of the forest, or you can create a tree cover manually.  

![](/images/TreeCoverExample.png)
*Sample of a manually created composition tree cover (inside dashed rectangle)*

> Ex, create an image of a higher resolution like 2048x2048, 4096x4096, 8192x81292 or even 14336x14336 in your favorite image editor and import a satellite image like described in the above section. Start identifying the tree types or forest composition types and assign a unique color for each. Use the pencil tool, and paint over the tree types/forest compositions with the unique colors you’ve assigned. Once done, export the image as a PNG. 

With the raster now prepared you can continue with the guide.
### A. JSON config file
If not yet, download the `config_file_template.json` in the root of the repository, open it in your text editor and edit it for the raster workload:<br>
```json
{
  "id_list" : [1, 2],
  "color_to_id" : ["#f82bde", "#20a8a2"],
  "trees_bin_path" : "C://Users/user/Games/Cities Skylines 2/Map/forest.bin",
  "raster" : {
    "png_path" : "C://Users/user/Games/Cities Skylines 2/Map/forest.png"
  }
}
```

**Key definitions**<br>
| Key | Type | Description |
| :---| :--- | :--- |
| `id_list` | integer list | The compositions ID's explained above, tied to a pixel color |
| `color_to_id` | string list | An list of hex colors, the pixel colors that tie to the ID's. <br>Ex: In the template, the color `#f82bde` ties to ID `1` |
| `trees_bin_path` | string | The path to the binary `.bin` TreesBIN file |
| `raster.png_path` | string | The path to the `.png` forest cover file | 

### B. Generating the TreesBIN file
If not yet, download the Windows console app `ImageToTreesBIN` from the releases and launch it. Once it opens, paste in the path to your JSON config file and press *Enter*. Depending on the resolution of your PNG file, this will take some time, but once It's done you can press *Enter* once again after being notified how long it took.

## Preparing the TreesBIN file from vector GIS data
Before we get started, we must first get ourselves with the concept of forest compositions. Imagine going into a forest and mapping out and section of the forest. Let’s call this section a **feature** and the feature is bound by the outline we mapped, ergo we created a **polygon**. Then venture into the mapped forest, and in a grid pattern start identify each tree into a specific type, let call this the `composition`. Then at the end, to make the gathered data presentable, we, among other things, sum up the count and use it calculate the percentage of each composition, so that all compositions, even those that we **didn’t** encounter in this forest section, all **sum-up together to 100%**. After we are done, we repeat this process for an entire forest or area, and we end up with a **vector tree cover layer**, costing of features/polygons that each take note of the composition percentages in It’s attribute table. This attribute table is non other than the gathered data from the trees count, percentages, all stored in columns, where each row is a feature, the column names are the composition names, ex. `oak1`, `spruce1`, and the columns store the composition percentages, ex **5%**, **10%**…  

Next up, we must also get ourselves familiarized with the concept of `composition ID’s`, which is instead of the full composition name, ex `oak1`, an **integer unique identifier**, in this case, `1`. It can be any integer, as longs as each composition is a unique integer. With both concepts familiarized we just need to now generate the positions of the trees for each `composition ID` and store the data in a file, in this case a binary `TreesBIN` file, instead of directly using the vector tree layer in-game. Reason why is because generating points in polygon, on mass, that are effectively spaced between, yet random is a time and resource consuming process, something not quite suitable for a game like Cities: Skylines 2 or any other game for the matter.

Now that we are familiarized with the concept of forest compositions, you must find a suitable polygon forest cover Shapefile, but as noted, this guide will not cover this topic. 

![](/images/VectorTreesPositionsExample.png)
*Vector tree layer and derived trees positions from vector data*

> This example will show the data downloaded from *Slovenian Forestry Institute*, but in most cases you should be able to request the composition tree vector data from your **national forest institute** website, as long as the tree vector data stores the composition of the forest in percentages from **0 to 100%**, which should be noted in the documentation or on the national forest institute website itself. With the data download, continue with the guide.

With the suitable Shapefile obtained, follow the next instructions and sections:
1. Open QGIS and click on the right bottom button to set the **Project CRS**
2. Search for the projection you wish to use, ex. the native projection of your location, **EPSG:3794** in this example, select it and press `OK`
3. Save the QGIS project with `CTRL+S` and **continue saving it as you progress** through the instructions as you may need to modify the polygon forests cover. 

### A. Bounding box
If you do not yet have a bounding box Shapefile in the extent of **14336x14336 meters** follow this section, else drag-and-drop your *Bounding box Shapefile* into QGIS and continue to the next section. To create the Shapefile, we'll be using the plugin `BBox Visualizer`.
1. Navigate to the `Plugins->Manage and Install Plugins...`, under the tab *All* search for `BBox Visualizer`, install the plugin and `Close` the window
2. In the Menu bar navigate to `Vector->BBox Visualizer->Visualize BBox`
3. In the new window, make sure the *Select CRS* is set to your CRS and enter your extent in the format of **minx,miny,maxx,maxy**, in this example: *513477,115087,527813,129423*
4. Press `Visualize BBox` and a new **temporary** layer will be created, as shown under the *Layers* panel
5. To save it, right-click on the layer in the *Layers* panel and click on `Make Permanent...`
6. In the newly opened window under *File name* click on the `...` dots, save it to a suitable folder and press `OK`
7. Now a popup should show on top of the map, requesting you to rename the layer to match it with the name of the file.

### B. JSON Config file
Same as with the raster workload, the vector load uses the config file as well, so if not yet, download the `config_file_template.json` in the root of the repository, open it with a text editor and edit it for the vector workload with your data based on the explanations in the **key definitions** bellow:<br>
```json
{
    "id_list" : [11, 21, 30, 34, 39, 41, 50, 60, 70, 80],
    "color_to_id" : ["#28392b", "#494e43", "#5c6652", "#72865f", "#86a469", "#93c265", "#aee677", "#a9fb59", "#c9ff37", "#daf42b"],
    "trees_bin_path" : "C://Users/user/Projects/Games/Cities Skylines 2/Map/Forests/trees.bin",
    "vector" : {
        "attributes" :  ["lzskdv11", "lzskdv21", "lzskdv30", "lzskdv34", "lzskdv39", "lzskdv41", "lzskdv50", "lzskdv60", "lzskdv70", "lzskdv80"], 
        "polygon_layer" : "Forest",
        "map_extent" : [513477, 527813, 129423, 115087],
        "play_area_offset" : 1247,
        "trees_count" : 1400000,
        "non_play_area_tree_count": 167122
    }
}
```
*Example of the JSON config file for the vector workload*

**Key definitions**<br>
| Key | Type | Description |
| :---| :--- | :--- |
| `id_list` | integer list | The compositions ID's explained above, tied to the vector layer attributes, that will be written to the bin file instead of the full attribute name. <br>These ID's are then used to configure what tree props to place |
| `color_to_id` | string list | An list of hex colors that tie to the ID's. <br>In the example config, the color `#28392b` ties to ID `11` or in other words to the attribute `lzskdv11` |
| `trees_bin_path` | string | The path to the binary `.bin` TreesBIN file |
| `vector.attributes` | string list | Name of attributes that determine the composition of the forest in percentages (all together add up to **100%**) |
| `vector.polygon_layer` | string | Name of the polygon layer that contains the composition of the forests |
| `vector.map_extent` | integer list | Extent of your IRL map in the format *Left, Right, Top, Bottom*. Must be in meters with a size of **14336x14336** meters. <br>Make sure your polygon layer lies within this extent and It's coordinate reference system uses meters as unit as well |
| `vector.play_area_offset` | integer | Determines where to distribute the `non_play_area_tree_count` of trees or in other words the extent of the play area (*Play Area Extent = Extent - Play Area Offset*). <br>The trees in the non play area get distributed based on the distance from the play area, meaning the further feature/polygon is from the play area, the less dense it is. <br>This is done so that there are as many trees as possible in the play area, to make the forests denser. <br>**Default:** 1247 (14336–13089) |
| `vector.trees_count` | integer | How many trees you wish to place on the map |
| `vector.non_play_area_tree_count` | integer | How many trees you wish to place outside the play area. In turn, `trees_count` get subtracted from this. |

### C. VectorToTreesBIN Script
If not yet, download the `VectorToTreesBIN.py` file in the root of the repository and continue with the guide in QGIS.<br>
1. Drag-and-drop you polygon forest cover Shapefile into the QGIS window
2. Once again make sure that the forest vector layer has the appropriate attributes for `composition` percentages, by going to `View->Identify Features` in the Menu bar. Click on a polygon on the map, and the feature attributes will be shown on the right. There should be attributes that together **sum up to 100%** like shown in the image bellow. If they are, continue on, but if not, you can contact me on Discord under **@davixdevelop**, and I’m sure I can help resolve the issue.

![](/images/AttributeTableCompostionPercentages.png)
*Attribute table of a vector tree layer with composition percentages*

3. Crop your forest layer by navigating to `Vector->Geoprocessing Tools->Intersection...` in the Menu bar. In the newly opened window, for *Input layer* choose your forest layer, while for the *Overlay layer* choose your BBox layer. Under the *Intersection* click on the `...` button to save the new layer to a Shapefile and click `Run`
> **Note**: You may receive an *invalid geometry* error. To fix this error, **don't close the Vector Overlay window** and under the *Processing Toolbox* (if you don't see the toolbox, enable it under `View->Panels->Processing Toolbox`) search for *Fix geometries*. Open the tool and under *Input layer* choose your forest layer. Now click on `Run` and a temporary layer named `Fixed geometries` will be created which you can rename with `F2`. Now back in the `Vector Overlay - Intersection` windows choose this new layer for *Overlay layer* and run the tool again.
4.  The now cropped forest layer may have a `?` button in the *Layers* panel. Click on it to set the layer CRS to your CRS like we did it for the **Project CRS**
5. Hide the original non-cropped forest layer by unchecking the checkbox for it in the *Layers* panel
6. Navigate to  `Plugins->Python Console` in the Menu bar and in the newly opened panel on the bottom, click the **third** icon ("Show Editor")
7. This opens a new sub-panel to the right. Here click on the **first** icon  ("Open Script…") and choose the downloaded script `VectorToTreesBIN.py`
8. The script has two parameters:
    - `config_file_path`: Path to the JSON config file that we edited before
    - `preview`: Change this to `True` if you wish to only preview how the trees will be placed in single feature/polygon (the biggest feature by area in the layer)
9. Save the changes made to the script by clicking on the **third** icon ("Save") and update as well the JSON config file with your inputs, ex. name of the now clipped forests polygon layer and other inputs as explained in the above **JSON Config file** section
10. Run the script by pressing on the **fifth** icon ("Run")
11. This creates a *QgsTask* that is run in the background. Once It’s done, after a while, depending on the complexity of vector layer and trees count, QGIS will send a notification. The script also outputs how many trees/points it has generated, which in most cases is less then the trees count, and how long it took to generate them and create the TreesBIN `.bin` file. This info can found in the bottom *Python Console* panel.

## Using the TreesBIN file in the mod
#ToDo