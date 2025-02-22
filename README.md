# pxrMegascanImporter
Blender addon to get megascan asset with renderman

Requirements
- Renderman Pro Server 26.x
- Renderman for Blender 26.x ( https://github.com/prman-pixar/RenderManForBlender )
- Miniumum Blender 4.3
  
Installation
- create environment "QUIXEL_JSON" variable that points to the "assetData.json".
- create environment "RMANTREE" variable that points to the install directory of RendermanProServer.
- create environment "OCIO" that points to the ACES-1.3 config.

Recommended is that you do this in a .bashrc file and launch blender from a terminal.
Example of contents in a .bashrc

#---
export QUIXEL_JSON=/mnt/projects/Megascans/Downloaded/assetsData.json
export RMANTREE=/opt/pixar/RenderManProServer-26.3
export OCIO=$RMANTREE/lib/ocio/ACES-1.3/config.ocio
#---

Download the zip file and install the addon via preferences.
