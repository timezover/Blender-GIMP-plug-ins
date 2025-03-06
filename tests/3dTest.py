"""
Testing for GIMP plug-in
"""

import bpy

def test_grass_plugin():
    """
    CLI test for the Grass Animation Blender plugin.
    """
    addon_name = "grass"
    if addon_name not in bpy.context.preferences.addons:
        print(f"ERROR: {addon_name} is not enabled.")
        return
    
    print("INFO: Starting tests for Grass Animation plugin.")
    
    bpy.ops.wm.read_factory_settings(use_empty=True)
    print("INFO: Scene reset to default.")
    
    try:
        bpy.ops.preferences.addon_enable(module=addon_name)
        print(f"INFO: Addon '{addon_name}' enabled successfully.")
    except Exception as e:
        print(f"ERROR: Failed to enable the add-on: {e}")
    try:
        bpy.ops.grass.generate_grass()
        print("INFO: Grass generated successfully.")
    except Exception as e:
        print(f"ERROR: Failed to generate grass. {e}")
        return

    grass_props = bpy.context.scene.grass_props
    grass_props.density = 1000  # Test density update
    grass_props.grass_color = (0.2, 0.8, 0.2, 1.0)  # Test color update
    print(f"INFO: Grass density set to {grass_props.density}.")
    print(f"INFO: Grass color set to {grass_props.grass_color}.")

    try:
        bpy.ops.wind.create_wind()
        print("INFO: Wind simulation created successfully.")
    except Exception as e:
        print(f"ERROR: Failed to create wind simulation. {e}")
        return

    wind_props = bpy.context.scene.wind_props
    wind_props.strength = 0.8
    wind_props.direction = 1.57  # Approximately 90 degrees
    print(f"INFO: Wind strength set to {wind_props.strength}.")
    print(f"INFO: Wind direction set to {wind_props.direction}.")

    print("INFO: All tests passed.")

# Run the test
if __name__ == "__main__":
    try:
    	bpy.ops.preferences.addon_enable(module="grass")
    	print("INFO: Add-on enabled successfully.")
    except Exception as e:
    	print(f"ERROR: Failed to enable the add-on: {e}")
    test_grass_plugin()
