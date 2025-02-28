import json
import os
import bpy
from RenderManForBlender.rfb_utils import shadergraph_utils
import RenderManForBlender.rman_bl_nodes as rman_bl_nodes
import RenderManForBlender.rfb_api as rfb_api


quixel_jsonfile = os.environ["QUIXEL_JSON"]

def register_properties():
    bpy.types.Scene.ms_id_text = bpy.props.StringProperty(
        name="Megascan ID",              # Label for the text field
        description="Paste in the megascan ID from the bridge application",  # Tooltip description
        default=""                      # Default value
    )
    bpy.types.Scene.ms_texture_size = bpy.props.EnumProperty(
        name="My Combo Box",
        description="Choose an option",
        items= [ ("8K", "8K", "8K"),
                 ("4K", "4K", "4K "),
                 ("2K", "2K", "2K"),
        ],
        default="4K"
    )
    bpy.types.Scene.ms_manifold = bpy.props.EnumProperty(
            name="My Combo Box",
            description="Choose an option",
            items= [ ("uv/tiling", "uv/tiling", ""),
                     ("PxrRoundCube", "triplanar", ""),
                     ("PxrHexTileManifold", "hextile", ""),
            ],
            default="uv/tiling"
    )
            
def unregister_properties():
    del bpy.types.Scene.ms_texture_type
    del bpy.types.Scene.ms_texture_size
    del bpy.types.Scene.ms_manifold
    del bpy.types.Scene.ms_id_text

class MegascanSurfacePanel(bpy.types.Panel):
    bl_label = "Megascan Surface Option"
    bl_idname = "VIEW3D_PT_ms_surface"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Megascan'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene   
        layout.prop(scene, "ms_manifold", text="manifold")
        
class MegascanGeneralPanel(bpy.types.Panel):
    bl_label = "Megascan General"
    bl_idname = "VIEW3D_PT_ms_general"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Megascan'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Add a text field
        layout.prop(scene, "ms_id_text", text="Asset ID")
        layout.prop(scene, "ms_texture_size", text="Resolution")
        layout.prop(scene, "ms_texture_type", text="Format") #this is a lie, we force exr at the moment
        # Add a button to display the text

class MegascanExecutePanel(bpy.types.Panel):
    bl_label = "Megascan  Execute"
    bl_idname = "VIEW3D_PT_ms_execute"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Megascan'    
    
    def draw(self, context):
        layout = self.layout
        layout.operator("wm.ms_get_asset", text="Get Asset")

class MegascanPanelOP(bpy.types.Operator):
    bl_idname = "wm.ms_get_asset"
    bl_label = "Megascan ID"
    
    def execute(self, context):
        ms = MegascanImporter()        
        ms.run( context.scene.ms_id_text, 
                context.scene.ms_texture_size, 
                context.scene.ms_manifold )
        return {'FINISHED'}

# ------------------------------------------------------------------------------------------------------

class MegascanImporter():
    def __init__(self):
        # ------------------------------------------------
        # We load the json file that Megascan Bridge has 
        # created, this has basic information about the
        # downloaded assets
        # ------------------------------------------------

        with open(quixel_jsonfile, "r") as file:
            self.data = json.load(file) 

        self.channels = ["albedo", "ao", "roughness", "displacement", "specular"]
        self.map_options = {"8K":"8192x8192", "4K":"4096x4096", "2k":"2048x2048"}
        self.mesh_type = "fbx"
     
    def load_asset_data(self):
        # ------------------------------------------------
        # We load the asset JSON file to get all the data 
        # for the asset that we need
        # ------------------------------------------------
        for asset in self.data:
            if asset['id'] == self.ms_id:
                self.name = "{}_{}".format(asset['name'].replace(" ", "_"), asset['id'])
                self.asset_json = f"{asset['parentDir']}/{'/'.join(asset['jsonPath'])}"
                self.asset_root = os.path.dirname(self.asset_json)
                with open(self.asset_json, "r") as file:
                    self.asset_data = json.load(file)

    def get_meshes(self):
        # ------------------------------------------------
        # Currently we only support FBX files for blender 
        # ------------------------------------------------

        file_list = []
        try:
            for meshtype in self.asset_data["meshes"]:
                if meshtype["type"] == "lod":
                    for filetype in meshtype["uris"]:
                        if filetype["mimeType"] == f"application/x-{self.mesh_type}":
                            file_list.append(filetype["uri"])
        except KeyError:
            for meshtype in self.asset_data["models"]:
                if meshtype["type"] == "lod":
                    if meshtype["mimeType"] == f"application/x-{self.mesh_type}":
                        file_list.append(meshtype["uri"])

        filtered_list = [f"{self.asset_root}/{mesh_file}" for mesh_file in file_list if "lod0" in mesh_file.lower()]
        filtered_list.sort()

        return filtered_list

    def get_texturePaths(self):
        # ------------------------------------------------
        # inspect the asset json file and extract all
        # texture paths we can find. 
        # ------------------------------------------------

        texturePaths = []                            
        asset_type = self.asset_data["semanticTags"]["asset_type"]

        if asset_type.lower() == "3d plant":
            self.channels.extend(["translucency", "opacity", "bump"])
        if asset_type.lower() == "3d asset":
            self.channels.extend(["normalbump", "opacity"])
        if asset_type.lower() == "surface":
            self.channels.extend(["normal"]) 

        exrs = [ "bump", "normalbump", "normal", "displacement" ]

        try:
            for texture in self.asset_data["maps"]:
                if texture["name"].lower() in self.channels:
                    if texture["name"].lower() in exrs:
                        if texture["mimeType"] == f"image/x-exr":
                            texturePath = f"{self.asset_root}/{texture['uri']}"
                            if f"_{self.map_size}_" in texturePath:
                                texturePaths.append(texturePath)
                    else:
                        if texture["mimeType"] == f"image/jpeg":
                            texturePath = f"{self.asset_root}/{texture['uri']}"
                            if f"_{self.map_size}_" in texturePath:
                                texturePaths.append(texturePath)
                        
        except KeyError:
            for texture in self.asset_data["components"]:
                if texture["name"].lower() in self.channels:         
                    for uri in texture["uris"]:
                        for size in uri["resolutions"]:
                            for image_type in size["formats"]:
                                if texture["name"].lower() in exrs:
                                    if image_type["mimeType"] == f"image/x-exr":
                                        if not "_lod" in image_type['uri'].lower():
                                            texturePath = f"{self.asset_root}/{image_type['uri']}"
                                            if f"_{self.map_size}_" in texturePath:
                                                texturePaths.append(f"{self.asset_root}/{image_type['uri']}")
                                else:
                                    if image_type["mimeType"] == f"image/jpeg":
                                        if not "_lod" in image_type['uri'].lower():
                                            texturePath = f"{self.asset_root}/{image_type['uri']}"
                                            if f"_{self.map_size}_" in texturePath:
                                                texturePaths.append(f"{self.asset_root}/{image_type['uri']}")
        return texturePaths

    def create_pxr_util_node(self, nodeType=None, nodeName=None):
        node = self.nodeTree.nodes.new(rman_bl_nodes.__BL_NODES_MAP__[nodeType])
        if nodeName:
            node.name = nodeName
        node.hide = True 
        return node

    def create_pxr_node( self, nodeType=None, nodeName=None, texturePath=None):
        #texturePath = os.path.splitext(texturePath)[0] + ".tex"
        if self.asset_data["semanticTags"]["asset_type"].lower() in ["surface", "atlas", "decals"]:
            if not self.manifold == "uv/tiling":
                node = self.nodeTree.nodes.new(rman_bl_nodes.__BL_NODES_MAP__["PxrMultiTexture"])
                node.filename0 = texturePath
                node.name = nodeName
                self.nodeTree.links.new(node.inputs["Multi Manifold"], self.pxrmanifold.outputs["resultMulti"])
            else:
                node = self.nodeTree.nodes.new(rman_bl_nodes.__BL_NODES_MAP__[nodeType])
                node.filename = texturePath
                node.name = nodeName
        else:
            node = self.nodeTree.nodes.new(rman_bl_nodes.__BL_NODES_MAP__[nodeType])
            node.filename = texturePath
            node.name = nodeName

        node.hide = True 
        return node

    def create_bl_node(self, nodeType=None, nodeName=None, texturePath=None):    
        node = self.nodeTree.nodes.new(nodeType)
        node.name = nodeName
        if texturePath:
            node.image = bpy.data.images.load(texturePath)
        node.hide = True 
        return node

    def create_material(self):
        # -----------------------------------------------
        # For now we only support PxrSurface. We also add
        # a blender texture so that we can get viewport
        # textures visible.
        # -----------------------------------------------

        asset_type = self.asset_data["semanticTags"]["asset_type"]

        self.material, pxr_bxdf = rfb_api.create_bxdf('PxrSurface')
        self.material.name = self.name + "_mtl"
        self.material.use_nodes = True
        self.nodeTree = self.material.node_tree

        pxr_bxdf.diffuseDoubleSided = True
        pxr_bxdf.enablePrimarySpecular = True
        pxr_bxdf.diffuseBackUseDiffuseColor = False

        pxr_bxdf.hide = True
        posx, posy = pxr_bxdf.location
        out = self.nodeTree.nodes.get("RenderMan Material")

        # the blender bxdf is used for viewport textures
        bl_bxdf = self.nodeTree.nodes.get("Principled BSDF")
        bl_posx, bl_posy = bl_bxdf.location
        
        texturePaths = self.get_texturePaths()
        
        if asset_type == "surface":
            if not self.manifold == "uv/tiling":
                self.pxrmanifold = self.nodeTree.nodes.new(rman_bl_nodes.__BL_NODES_MAP__[self.manifold])
                self.pxrmanifold.hide = True
                self.pxrmanifold.location = [(posx - 600), posy]

        for texturePath in texturePaths:
            if "_albedo." in texturePath.lower():
                node = self.create_pxr_node("PxrTexture", "albedo", texturePath)
                node.location = [(posx - 300), posy]
                self.nodeTree.links.new(pxr_bxdf.inputs["Diffuse Color"], node.outputs[0])
                node.filename_colorspace = "srgb_texture"
                if not asset_type.lower() in ["decals"]:
                    try:
                        textureFile = [texture for texture in os.listdir(f"{self.asset_root}/Thumbs/1k") if "albedo" in texture.lower()][0]
                        bl_node = self.create_bl_node("ShaderNodeTexImage", "bl_albedo", f"{self.asset_root}/Thumbs/1k/{textureFile}")
                        bl_node.location = [(bl_posx - 300), (bl_posy + 300)]
                        self.nodeTree.links.new(bl_bxdf.inputs["Base Color"], bl_node.outputs[0])                
                    except IndexError:
                        pass
            if "_specular." in texturePath.lower():
                node = self.create_pxr_node("PxrTexture", "specular", texturePath)
                node.location = [(posx - 300), (posy - 200)]                           
                self.nodeTree.links.new(pxr_bxdf.inputs["Primary Specular Face Color"], node.outputs[0])
                node.filename_colorspace = "srgb_texture"
                if not asset_type.lower() in [ "decals"]:
                    try:
                        textureFile = [texture for texture in os.listdir(f"{self.asset_root}/Thumbs/1k") if "specular" in texture.lower()][0]
                        bl_node = self.create_bl_node("ShaderNodeTexImage", "bl_specular", f"{self.asset_root}/Thumbs/1k/{textureFile}")
                        bl_node.location = [(bl_posx - 300), (bl_posy + 200)]
                        self.nodeTree.links.new(bl_bxdf.inputs[14], bl_node.outputs[0])                 
                    except IndexError:
                        pass 
            if "_roughness." in texturePath.lower():
                node = self.create_pxr_node("PxrTexture", "roughness", texturePath)
                node.location = [(posx - 300), (posy - 300)]  
                node.hide = True                 
                self.nodeTree.links.new(pxr_bxdf.inputs["Primary Specular Roughness"], node.outputs[1])
                
                if not asset_type.lower() in ["decals"]:
                    try:
                        textureFile = [texture for texture in os.listdir(f"{self.asset_root}/Thumbs/1k") if "roughness" in texture.lower()][0]
                        bl_node = self.create_bl_node("ShaderNodeTexImage", "bl_roughness", f"{self.asset_root}/Thumbs/1k/{textureFile}")
                        bl_node.image.colorspace_settings.name = "Raw"
                        bl_node.location = [(bl_posx - 300), (bl_posy + 100)]
                        self.nodeTree.links.new(bl_bxdf.inputs["Roughness"], bl_node.outputs[0]) 
                    except IndexError:
                        pass

            if "_translucency." in texturePath.lower():
                node = self.create_pxr_node("PxrTexture", "translucency", texturePath)
                node.location = [(posx - 300), (posy - 400)]
                node.filename_colorspace = "srgb_texture"           
                pxr_bxdf.diffuseTransmitGain = 0.1
                self.nodeTree.links.new(pxr_bxdf.inputs["Diffuse Back Color"], node.outputs[0])
                self.nodeTree.links.new(pxr_bxdf.inputs["Diffuse Transmit Color"], node.outputs[0])

            if "_opacity." in texturePath.lower():
                node = self.create_pxr_node("PxrTexture", "opacity", texturePath)
                node.location = [(posx - 300), (posy - 500)] 
                node.hide = True                 
                self.nodeTree.links.new(pxr_bxdf.inputs["Presence"], node.outputs[1])

                if not asset_type.lower() in ["decals"]:
                    try:
                        textureFile = [texture for texture in os.listdir(f"{self.asset_root}/Thumbs/1k") if "opacity" in texture.lower()][0]
                        bl_node = self.create_bl_node("ShaderNodeTexImage", "bl_opacity", f"{self.asset_root}/Thumbs/1k/{textureFile}")
                        bl_node.image.colorspace_settings.name = "Raw"
                        bl_node.location = [(bl_posx - 300), bl_posy]
                        self.nodeTree.links.new(bl_bxdf.inputs["Alpha"], bl_node.outputs[0])
                    except IndexError:
                        pass

            if "_bump." in texturePath.lower():
                node = self.create_pxr_node("PxrBump", "bump", texturePath)
                node.scale = 0.001
                node.location = [(posx - 300), (posy - 600)]

                self.nodeTree.links.new(pxr_bxdf.inputs["Bump"], node.outputs[0])

            if "_normalbump." in texturePath.lower():
                node = self.create_pxr_node("PxrNormalMap", "normalBump", texturePath)
                node.orientation = "1"
                node.location = [(posx - 300), (posy - 600)]                  
                self.nodeTree.links.new(pxr_bxdf.inputs["Bump"], node.outputs[0])

            if "_displacement." in texturePath.lower():
                node = self.create_pxr_node("PxrTexture", "displacement", texturePath)
                node.location = [(posx - 300), (posy - 700)]
                
                pxrremap = self.create_pxr_util_node("PxrDispTransform")
                pxrremap.dispRemapMode = "2"
               
                pxrremap.location = [(posx - 150), (posy - 700)]                
                pxrremap.hide = True

                pxrdisplace = self.create_pxr_util_node("PxrDisplace")
                pxrdisplace.dispAmount = 0.01
                pxrdisplace.location = [posx, (posy - 700)]               
                pxrdisplace.hide = True

                self.nodeTree.links.new(pxrremap.inputs["Scalar Displacement"], node.outputs[1])
                self.nodeTree.links.new(pxrdisplace.inputs["Scalar Displacement"], pxrremap.outputs[1])
                self.nodeTree.links.new(out.inputs["Displacement"], pxrdisplace.outputs[0])
                
                textureFile = [texture for texture in os.listdir(f"{self.asset_root}/Thumbs/1k") if "displacement" in texture.lower()][0]
                if textureFile:
                    bl_node = self.create_bl_node("ShaderNodeTexImage", "bl_opacity", f"{self.asset_root}/Thumbs/1k/{textureFile}")
                    bl_node.image.colorspace_settings.name = "Raw"
                    bl_node.location = [(bl_posx - 300), bl_posy]
                    bl_disp_node = self.create_bl_node("ShaderNodeDisplacement", "bl_displacement")
                    bl_disp_node.inputs[2].default_value = 0.01
                    
                    self.nodeTree.links.new(bl_disp_node.inputs["Height"], bl_node.outputs[0])
                    bl_mat = self.nodeTree.nodes.get("Material Output")
                    self.nodeTree.links.new(bl_mat.inputs["Displacement"], bl_disp_node.outputs[0])

        if not asset_type in ["surface", "atlas"]:
            self.import_fbx()



    def run(self, ms_id, ms_texture_size, ms_manifold ):
        # -----------------------------------------------
        # fetch what the user has entered
        # -----------------------------------------------
        self.map_size = ms_texture_size
        self.ms_id = ms_id
        self.manifold = ms_manifold

        # -----------------------------------------------
        # lets do it!
        # -----------------------------------------------

        self.load_asset_data()
        self.create_material()
           
        
    def import_fbx(self):
        # -----------------------------------------------
        # we import the FBX meshes and place them under
        # a collection with the same name as the asset
        # -----------------------------------------------
        collection_name = self.name

        # Ensure the collection exists or create it
        if collection_name in bpy.data.collections:
            collection = bpy.data.collections[collection_name]
        else:
            collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(collection)

        for fbx_file_path in self.get_meshes():
            bpy.ops.import_scene.fbx(filepath=fbx_file_path)
            
            for obj in bpy.data.objects:
                if obj.type == 'EMPTY' and obj.name.lower() == "world_root":
                    # Reassign its children to the scene or another parent
                    for child in obj.children:
                        child.parent = None  # Remove parent-child relationship
                    # Remove the empty object
                    bpy.data.objects.remove(obj, do_unlink=True)            

            selectedObjects = []
            obj_objects = [ o for o in bpy.context.scene.objects if o.select_get() ]
            selectedObjects += obj_objects
            
            for obj in selectedObjects:
                # assign material to obj
                obj.active_material = self.material
                lodname = obj.name.split("_")[-2]

                obj.name = f"{self.name}_{lodname}"
                # apply renderman subdiv scheme
                try:
                    obj.data.renderman.rman_smoothnormals = True
                    obj.data.renderman.rman_preventPolyCracks = True
                    obj.data.renderman.rman_subdiv_scheme = "catmull-clark"
                    
                except AttributeError:
                    pass

                # Apply scale and rotation to the object's data          
                try:
                    obj.data.transform(obj.matrix_world)
                    obj.scale = (1, 1, 1)
                    obj.rotation_euler = (0, 0, 0)
                except AttributeError:
                    pass                    

                # Unlink the object from the default collection
                for col in obj.users_collection:
                    col.objects.unlink(obj)
                # Link the object to the target collection
                collection.objects.link(obj)


# Register and Unregister the classes
def register():
    bpy.utils.register_class(MegascanGeneralPanel)
    bpy.utils.register_class(MegascanSurfacePanel)
    bpy.utils.register_class(MegascanExecutePanel)    
    bpy.utils.register_class(MegascanPanelOP)
    register_properties()

def unregister():
    bpy.utils.unregister_class(MegascanGeneralPanel)
    bpy.utils.unregister_class(MegascanSurfacePanel)
    bpy.utils.unregister_class(MegascanExecutePanel)
    bpy.utils.unregister_class(MegascanPanelOP)
    unregister_properties()

if __name__ == "__main__":
    register()
