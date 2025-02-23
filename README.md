**pxrMegascanImporter**

Blender addon to get megascan asset with renderman

**Requirements**
- Renderman Pro Server 26.x
- Renderman for Blender 26.x ( https://github.com/prman-pixar/RenderManForBlender )
- Miniumum Blender 4.3
- Quixel Megascans Bridge Application
- required download settings in Bridge
  
**Geometry**
- FBX, LOD0, LOD1

**Textures ( 4K )**
- Albedo - JPEG
- Specular - JPEG
- Roughness - JPEG
- Translucency - JPEG
- Opacity - JPEG
- Bump - EXR
- Normal - EXR
- NormalBump - EXR
- Displacement - EXR  

**Installation**
- create environment "QUIXEL_JSON" variable that points to the "assetData.json".
- create environment "RMANTREE" variable that points to the install directory of RendermanProServer.
- create environment "OCIO" that points to the ACES-1.3 config.

Recommended is that you do this in a .bashrc file and launch blender from a terminal.
Example of contents in a .bashrc

```
export QUIXEL_JSON=/mnt/projects/Megascans/Downloaded/assetsData.json
export RMANTREE=/opt/pixar/RenderManProServer-26.3
export OCIO=$RMANTREE/lib/ocio/ACES-1.3/config.ocio
```
Download the zip file and install the addon via preferences.

**Limitations**

The UI shows options for 2K,4K,8K, this is a lie. It will only do 4K. 
The option to chose texture format will be removed. I will let renderman do the conversion based on the OCIO config.


