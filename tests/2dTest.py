#!/usr/bin/python
"""
CLI test for GIMP plug-in
"""

import os
from gimpfu import pdb

INPUT_IMAGE = "LenaSrc.jpg"  # Path to the input image
OUTPUT_IMAGE = "LenaEdit.jpg"  # Path to the output image

def test_convolution_plugin():
    """
    Main function for testing the convolution plugin
    """
    try:
        image = pdb.gimp_file_load(INPUT_IMAGE, INPUT_IMAGE)
        drawable = pdb.gimp_image_get_active_drawable(image)

        kernel_type = "Sobel"  # Options: "Sobel", "Roberts", "Prewitt"
        display_type = 0  # 0: Grayscale, 1: Red and Blue

        pdb.convolution_main(
            run_mode=1,  # RUN_INTERACTIVE: 0, RUN_NONINTERACTIVE: 1, RUN_WITH_LAST_VALS: 2
            image=image,
            drawable=drawable,
            p_kernel_type=kernel_type,
            p_display_type=display_type,
        )

        # Save the resulting image
        pdb.file_jpeg_save(image, drawable, OUTPUT_IMAGE, OUTPUT_IMAGE, 0.9, 0, 0, 0, "", 0, 0, 0, 0)

        print("Plugin test completed. Output saved.")

    except Exception as e:
        print("Test failed with error.")
    finally:
        # Clean up GIMP resources
        if 'image' in locals():
            pdb.gimp_image_delete(image)

if __name__ == "__main__":
    test_convolution_plugin()
