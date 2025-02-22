# pxrMegascanImporter
Blender addon to get megascan asset with renderman

Requirements
- Renderman Pro Server 26.x
- ACES 1.3 Studio config, https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES/releases

Installation
- create environment "QUIXEL_JSON" variable that points to the "assetData.json".
- create environment "RMANTREE" variable that points to the install directory of RendermanProServer.
- create environment "OCIO" that points to the ACES-1.3 config.
Recommended is that you do this in a .bashrc file and launch blender from a terminal.
   example of contents in a .bashrc
      export QUIXEL_JSON=/home/stan/Projects/Megascans/Downloaded/assetsData.json
      expo1t RMANTREE=/opt/pixar/RenderManProServer-26.3
      export OCIO=$RMANTREE/lib/ocio/ACES-1.3/config.ocio
