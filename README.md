**pxrMegascanImporter**

Blender addon to get megascan asset with renderman.
UI is present in the 3D viewport ( see import_asset.png file )

**A Youtube Video about the installation and usage**

https://www.youtube.com/watch?v=4U22XPkD0Xw

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

Linux Example
```
export QUIXEL_JSON=/mnt/projects/Megascans/Downloaded/assetsData.json
export RMANTREE=/opt/pixar/RenderManProServer-26.3
export OCIO=$RMANTREE/lib/ocio/ACES-1.3/config.ocio
```

Macos Example
```
export QUIXEL_JSON=/Users/stan/Documents/Megascans\ Library/Downloaded/assetsData.json
export RMANTREE=/Applications/Pixar/RenderManProServer-26.3
export OCIO=$RMANTREE/lib/ocio/ACES-1.3/config.ocio
```

Download the zip file and install the addon via preferences.
