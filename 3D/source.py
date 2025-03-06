"""
Blender plugin for grass generation and animation
"""

bl_info = {
    "name": "Grass Animation",
    "author": "byaliyah",
    "version": (1, 0),
    "blender": (3, 4, 1),
    "location": "View3D",
    "description": "Creates grass and its animations depending on the given parameters",
    "warning": "",
    "doc_url": "",
    "category": "Animation",
}

import bpy
from bpy.props import FloatVectorProperty, PointerProperty, IntProperty

# Parameters-update functions:
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def update_grass_color(self, context):
    """
    Updates grass color
    """
    grass_object = context.scene.grass_object
    grass_material_index = grass_object.particle_systems[0].settings.material - 1
    grass_material = grass_object.data.materials[grass_material_index]
    bsdf = grass_material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = self.grass_color

def update_ground_color(self, context):
    """
    Updates ground color
    """
    obj = bpy.context.active_object
    mat = obj.data.materials[0]
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = self.ground_color

def update_density(self, context):
    """
    Updates count of grass particles
    """
    grass_props = context.scene.grass_props
    grass_object = context.scene.grass_object
    particle_settings = grass_object.particle_systems[0].settings
    particle_settings.count = grass_props.density

def update_strength(self, context):
    """
    Updates wind strength
    """
    wind_props = context.scene.wind_props
    context.scene.wind_object.field.strength = wind_props.strength
    context.scene.turbulence_object.field.strength = wind_props.strength * 2

def update_direction(self, context):
    """
    Updates wind direction
    """
    context.scene.wind_object.rotation_euler[2] = context.scene.wind_props.direction

# Grass handling classes:
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class GrassProps(bpy.types.PropertyGroup):
    """
    Class that handles grass properties storage
    """
    grass_color: FloatVectorProperty(
        name = "Grass Color",
        subtype = 'COLOR',
        default = (0.0, 1.0, 0.0, 1.0),
        description = "Changes the color of the grass",
        min = 0.0,
        max = 1.0,
        size = 4,
        update = update_grass_color
    )
    ground_color: FloatVectorProperty(
        name = "Ground Color",
        subtype = 'COLOR',
        default = (0.5, 0.25, 0.0, 1.0),
        description = "Changes the color of ground",
        min = 0.0,
        max = 1.0,
        size = 4,
        update = update_ground_color
    )
    density: IntProperty(
        name = "Density",
        default = 500,
        description = 'Changes number of grass particles',
        min = 100,
        max = 10000,
        update = update_density
    )

class GrassPanel(bpy.types.Panel):
    """
    Class that handles grass generation panel
    """
    bl_label = "Grass Generation"
    bl_idname = "VIEW3D_PT_grass_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Grass"

    def draw(self, context):
        """
        Method that handles panel drawing
        """
        layout = self.layout
        grass_props = context.scene.grass_props

        layout.label(text="Grass Properties", icon="MOD_PARTICLES")
        layout.prop(grass_props, "ground_color")
        layout.prop(grass_props, "grass_color")
        layout.prop(grass_props, "density")
        layout.operator("grass.generate_grass")

class GrassGenerator(bpy.types.Operator):
    """
    Class that handles ground and particle generation
    """
    bl_label = "Create Grass Object"
    bl_idname = "grass.generate_grass"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        """
        Method that executes grass generation process
        """
        grass_props = context.scene.grass_props

        bpy.ops.mesh.primitive_plane_add(
            size=2.0, enter_editmode=False, align='WORLD',
            location=(0, 0, 0), scale=(1, 1, 1)
        )
        ground_object = bpy.context.object
        context.scene.grass_object = ground_object

        # Usage of node system for appending materials
        ground_material = bpy.data.materials.new("Ground Material")
        ground_material.use_nodes = True
        ground_bsdf = ground_material.node_tree.nodes.get("Principled BSDF")
        ground_bsdf.inputs["Base Color"].default_value = grass_props.ground_color
        ground_object.data.materials.append(ground_material)

        bpy.ops.object.particle_system_add()
        particle_system = ground_object.particle_systems[-1]
        particles = particle_system.settings

        # Setting particle parameters as hair type
        particles.type = 'HAIR'
        particles.hair_length = 1.0
        particles.use_advanced_hair = True
        particles.child_type = 'INTERPOLATED'
        particles.count = grass_props.density
        particles.clump_factor = -0.3
        particles.roughness_1 = 0.2
        particles.tip_radius = 0.005
        particles.brownian_factor = 0.1

        grass_material = bpy.data.materials.new("Grass Material")
        grass_material.use_nodes = True
        grass_bsdf = grass_material.node_tree.nodes.get("Principled BSDF")
        grass_bsdf.inputs["Base Color"].default_value = grass_props.grass_color
        particle_system.settings.material = len(ground_object.data.materials) + 1
        ground_object.data.materials.append(grass_material)

        self.report({'INFO'}, "Grass Object Created!")
        return {'FINISHED'}

# Wind handling classes:
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class WindProps(bpy.types.PropertyGroup):
    """
    Class that handles wind properties storage
    """
    strength: bpy.props.FloatProperty(
        name = 'Wind strength',
        default = 0.5,
        description = 'Changes wind force',
        min = 0,
        max = 1,
        update = update_strength
    )

    direction: bpy.props.FloatProperty(
        name = 'Wind direction',
        description = 'Changes wind direction',
        default = 0.0,
        update = update_direction
    )

class WindPanel(bpy.types.Panel):
    """
    Class that handles wind generation panel
    """
    bl_label = "Wind Simulation panel"
    bl_idname = "Wind_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Grass"
    bl_parent_id = "VIEW3D_PT_grass_panel"

    def draw(self, context):
        """
        Class that handles grass generation panel
        """
        layout = self.layout
        wind_props = context.scene.wind_props

        layout.prop(wind_props, "strength")
        layout.prop(wind_props, "direction")
        layout.operator("wind.create_wind")

class WindGenerator(bpy.types.Operator):
    """
    Class that handles ground and particle generation
    """
    bl_label = "Create wind simulation"
    bl_idname = "wind.create_wind"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        """
        Method that executes grass animation process
        """
        wind_props = context.scene.wind_props

        bpy.ops.object.effector_add(
            type='WIND', align='WORLD', enter_editmode=False,
            location=(0, 0, 1.5), scale=(1, 1, 1), rotation = (-90.0, 0.0, wind_props.direction),
            radius = 0.15)
        wind_object = bpy.context.object
        context.scene.wind_object = wind_object

        bpy.ops.object.effector_add(
            type='TURBULENCE', enter_editmode=False,
            align='WORLD', location=(0, 0, 0), scale=(1, 1, 1)
        )
        turbulence_object = bpy.context.object
        context.scene.turbulence_object = turbulence_object

        turbulence_object.animation_data_create()
        turbulence_object.animation_data.action = bpy.data.actions.new(name="TurbulenceRotation")

        # Turbulence object rotation for grass animation
        fcurve = turbulence_object.animation_data.action.fcurves.new(data_path="rotation_euler", index=0)
        fcurve.keyframe_points.add(count=2)
        fcurve.keyframe_points[0].co = (0, 0)
        fcurve.keyframe_points[1].co = (250, 9.28)
        fcurve.update()

        context.scene.frame_start = 1
        context.scene.frame_end = 250
        bpy.ops.screen.animation_play()

        self.report({'INFO'}, "Wind and Turbulence Simulation Created!")
        return {'FINISHED'}

# Module initialization:
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

classes = [GrassProps, GrassPanel, GrassGenerator, WindProps, WindPanel, WindGenerator]

def register():
    """
    Initializes all classes and properties and registers them
    """
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.grass_props = PointerProperty(type=GrassProps)
    bpy.types.Scene.wind_props = PointerProperty(type=WindProps)
    bpy.types.Scene.grass_object = PointerProperty(type=bpy.types.Object)
    bpy.types.Scene.wind_object = PointerProperty(type=bpy.types.Object)
    bpy.types.Scene.turbulence_object = PointerProperty(type=bpy.types.Object)

def unregister():
    """
    Unregisters all classes and deletes all property
    """
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.grass_props
    del bpy.types.Scene.grass_object
    del bpy.types.Scene.wind_props
    del bpy.types.Scene.wind_object
    del bpy.types.Scene.turbulence_object

if __name__ == "__main__":
    register()
