#!/usr/bin/python
"""
Convolution plugin for GIMP
Author: Yahor Byaliauski
"""

import math
import array
import sys
import os
import random
import gimp
import gimpplugin
import gtk
import gimpui
import gimpcolor
import pango
from gimpenums import *
from gimpshelf import shelf
from gimpfu import *

pdb = gimp.pdb

class ConvolutionPlugin(gimpplugin.plugin):
    """
    Main class of the plugin, that takes care of edge detection.
    Contains some mandatory methods for GIMP and some helper methods for edge detection.
    """
    SHELF_KEY = 'CONVOLUTION'  # Shelf is used for saving specified values between plugin runs
    DEFAULT_SETTINGS = {
        ('KERNEL', 'Sobel'),
        ('DISPLAY', 0)
    }

    def __init__(self):
        """
        Constructor that declares empty values to use across class methods.
        """
        self.image = None
        self.drawable = None
        self.settings = None
        self.display_type = 0
        self.kernel_type = 'Sobel'
        self.kernels_x = {'Sobel': [[1, 0, -1],
                                    [2, 0, -2],
                                    [1, 0, -1]],
                          'Roberts': [[1, 0],
                                      [0, -1]],
                          'Prewitt': [[-1, 0, 1],
                                      [-1, 0, 1],
                                      [-1, 0, 1]]}
        self.kernels_y = {'Sobel': [[1, 2, 1],
                                    [0, 0, 0],
                                    [-1, -2, -1]],
                          'Roberts': [[0, 1],
                                      [-1, 0]],
                          'Prewitt': [[-1, -1, -1],
                                      [0, 0, 0],
                                      [1, 1, 1]]}
        self.progress = 0.0

        # Dialog options
        self.spacing = 1
        self.dialog = None
        self.table = None

        # Dialog options for kernel selection
        self.kernel_store = None
        self.kernel_treeView = None
        self.kernel_renderer = None
        self.kernel_column = None
        self.kernel_select = None
        self.kernel_buttons = None

        # Dialog options for display type selection
        self.color_store = None
        self.color_treeView = None
        self.color_renderer = None
        self.color_column = None
        self.color_select = None
        self.color_buttons = None


        self.preview = None

        self.label = None

        self.ok_button = None
        self.cancel_button = None

    def start(self):
        """
        Standard method of GIMP plugin that is called at the beginning.
        """
        print("m_start")
        gimp.main(self.init, self.quit, self.query, self._run)

    def init(self):
        """
        Standard method of GIMP plugin that initialize plugin.
        """
        print("m_init")

    def quit(self):
        """
        Standard method of GIMP plugin that is called at the end.
        """
        print("m_quit")

    def query(self):
        """
        Standard method of GIMP plugin that contains information about plugin
        """
        print("m_query")
        gimp.install_procedure(
            "convolution_main",
            "Convolution for edge detection based on given parameters.",
            "byaliyah@fit.cvut.cz",
            "Yahor Byaliauski",
            "Yahor Byaliauski",
            "2024",
            "<Image>/Filters/Convolution",
            "RGB*, GRAY*",
            PLUGIN,
            [   (PDB_INT32, "run_mode", "Run mode"),
                (PDB_IMAGE, "image", "Input image"),
                (PDB_DRAWABLE, "drawable", "Input drawable"),
                (PDB_STRING, "p_kernel_type", "Type of active kernel for edge detection"),
                (PDB_INT32, "p_display_type", "Type of edge representation"),
            ],
            []
        )

    def clamp_color_value(self, value):
        """
        Limits color value from 0 to 255.
        """
        return max(min(255, value), 0)

    def update_preview(self, force):
        """
        Method that handles preview image updating if changes are made or is forced
        """
        if force or self.preview.get_update():
            self.convolute(self.kernel_type, self.display_type, True)

    def label_show_selection(self):
        """
        Method that handles updating selected parameters in the dialogue window
        """
        switcher = {0: "Grayscale",
                    1: "Red and blue"}
        display_type_text = switcher.get(self.display_type, "None")
        self.label.set_text("Selected values\n" +
                            "\nKernel: " + str(self.kernel_type) +
                            "\nRepresentation: " + display_type_text
                            )

    def create_dialog(self):
        """
        Method that creates widgets for dialogue
        """
        # Dialog initialization
        self.dialog = gimpui.Dialog('Detect edges', 'convolution_dialog',
                                    flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        self.dialog.set_transient()
        self.dialog.set_border_width(self.spacing)
        self.dialog.set_default_size(400, 550)

        # Creating table
        self.table = gtk.Table(1, 1, True)
        self.table.set_row_spacings(self.spacing * 2)
        self.table.set_col_spacings(self.spacing * 2)
        self.table.show_all()
        self.dialog.vbox.add(self.table)

        kernel_label = gtk.Label()
        kernel_label.set_markup('<b>Kernel Type</b>')
        kernel_label.set_alignment(0, 0.5)
        kernel_label.show()
        self.table.attach(kernel_label, 0, 3, 0, 1, xpadding=5, ypadding=2) #xpadding and yppading for widget alignment

        # Group of radio buttons for kernels
        self.kernel_buttons = []
        kernel_group = None
        for index, name in enumerate(self.kernels_x.keys()):
            button = gtk.RadioButton(kernel_group, name)
            button.connect("toggled", self.on_kernel_radio_toggled, name)
            button.show()
            self.kernel_buttons.append(button)
            kernel_group = button if index == 0 else kernel_group
            alignment = gtk.Alignment(0, 0.5, 0, 0)
            alignment.add(button)
            alignment.show()

            self.table.attach(alignment, 0, 3, index + 1, index + 2, gtk.FILL,
                              gtk.FILL, xpadding=10, ypadding=1)  # Add buttons to the table

        color_label = gtk.Label()
        color_label.set_markup('<b>Color Type</b>')
        color_label.set_alignment(0, 0.5)
        color_label.show()
        self.table.attach(color_label, 0, 3, len(self.kernels_x.keys()) + 1,
                          len(self.kernels_x.keys()) + 2, xpadding=5, ypadding=2)
        self.color_buttons = []
        color_types = [("Grayscale", 0), ("Red and blue", 1)]
        color_group = None
        for index, (label, value) in enumerate(color_types):
            button = gtk.RadioButton(color_group, label)
            button.connect("toggled", self.on_color_radio_toggled, value)
            button.show()
            self.color_buttons.append(button)
            color_group = button if index == 0 else color_group
            alignment = gtk.Alignment(0, 0.5, 0, 0)
            alignment.add(button)
            alignment.show()

            self.table.attach(alignment, 0, 3, len(self.kernels_x.keys()) + 2 + index,
                              len(self.kernels_x.keys()) + 3 + index,
                              gtk.FILL, gtk.FILL, xpadding=10, ypadding=1)

        # Preview
        self.preview = gimpui.ZoomPreview(self.drawable)
        self.preview.set_update(True)
        self.preview.show()
        self.preview.connect('invalidated', self.update_preview)
        self.table.attach(self.preview, 1, 3, 0, len(self.kernels_x.keys()) + len(color_types))  # Add preview to table.

        # Label for currently selected settings
        self.label = gtk.Label()
        self.label.show()
        self.table.attach(self.label, 1, 3, len(self.kernels_x.keys()) + len(color_types),
                          len(self.kernels_x.keys()) + len(color_types) + 1)
        self.label_show_selection()

        # Add buttons and show dialog
        self.ok_button = self.dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        self.cancel_button = self.dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)

        self.dialog.show()

    # Callback functions for radio button events
    def on_kernel_radio_toggled(self, button, kernel_name):
        """
        Callback method for kernel radio button event
        """
        if button.get_active():
            self.kernel_select = kernel_name  # Update selected kernel
            self.kernel_type = self.kernel_select
            self.label_show_selection()
            self.update_preview(None)

    def on_color_radio_toggled(self, button, color_value):
        """
        Callback method for color type radio button event
        """
        if button.get_active():
            self.color_select = color_value # Update selected color
            self.display_type = self.color_select
            self.label_show_selection()
            self.update_preview(None)
            # Update selected color

    def show_dialog(self):
        """
        Show created dialog.
        If one does not exist, create one.
        """
        if self.dialog is None:
            self.create_dialog()
        return self.dialog.run()

    def convolution_main(self, run_mode, image, drawable,
                         p_kernel_type='Sobel', p_display_type='0'):
        """
        Main method, that cares about run modes and calling computing convolution method.
        """
        print("m_convolution_main")

        self.image = image
        self.drawable = drawable
        self.settings = None

        if shelf.has_key(self.SHELF_KEY):  # Loads saved settings.
            self.settings = shelf[self.SHELF_KEY]

        if self.settings is None:  # If there is no setting saved, use default ones.
            self.settings = dict(self.DEFAULT_SETTINGS)
            shelf[self.SHELF_KEY] = self.settings

        if run_mode == RUN_INTERACTIVE:  # Interactive mod with UI
            result = self.show_dialog()
            print("m_convolution_main - Dialog shown")
            if result != gtk.RESPONSE_OK:
                return
            self.settings['KERNEL'] = self.kernel_type
            self.settings['DISPLAY'] = self.display_type
            shelf[self.SHELF_KEY] = self.settings

        elif run_mode == RUN_NONINTERACTIVE:  # Non-interactive mode. Used by console.
            self.kernel_type = p_kernel_type
            self.display_type = p_display_type
            self.settings['KERNEL'] = self.kernel_type
            self.settings['DISPLAY'] = self.display_type

        elif run_mode == RUN_WITH_LAST_VALS:  # Run with last values.
            self.kernel_type = self.settings['KERNEL']
            self.display_type = self.settings['DISPLAY']

        gimp.pdb.gimp_image_undo_group_start(self.image)  # Handling undo groups in GIMP (for CTRL + Z)
        self.convolute(self.kernel_type, self.display_type, False)  # Start convolution
        gimp.pdb.gimp_image_undo_group_end(self.image)

    def convolute(self, kernel_name, color_mode, preview):
        """
        Main method, that computes edges and draws them in the selected layer.
        """
        print("m_convolute")

        # Declaring basic variables.
        kernel_x = self.kernels_x[kernel_name]
        kernel_y = self.kernels_y[kernel_name]
        x1 = y1 = x2 = y2 = 0
        step = len(kernel_x[0])

        # Starting sequence for preview option
        if preview:
            gimp.progress_init('Detecting edges (preview)...') # Initialize progress bar
            src_pixels, width, height, bpp = self.preview.get_source()
            src_pixels = array.array('B', src_pixels)
            gimp.progress_update(0.0)

            dst_rgn = self.drawable.get_pixel_rgn(0, 0, width, height, False, False)
            dst_pixels = array.array('B', dst_rgn[0:width, 0:height])
        else:
            gimp.progress_init('Detecting edges...')  # Initialize progress bar
            gimp.progress_update(0.0)

            (x1, y1, x2, y2) = self.drawable.mask_bounds
            width = x2 - x1
            height = y2 - y1
            bpp = self.drawable.bpp

            src_rgn = self.drawable.get_pixel_rgn(x1, y1, width, height, False, False)
            src_pixels = array.array('B', src_rgn[x1:x2, y1:y2])  # Convert bytearray to unsigned char array

            dst_rgn = self.drawable.get_pixel_rgn(0, 0, width, height, True, True)
            dst_pixels = array.array('B', dst_rgn[0:width, 0:height])  # Convert bytearray to unsigned char array

        print("m_convolute - Loop started")
        # Traverse every pixel in picture
        for pos_y in range(0, height):
            for pos_x in range(0, width):
                center_pos = (pos_x + width * pos_y) * bpp
                center_pixel = src_pixels[center_pos:(center_pos + bpp)]
                center_sum_x = 0
                center_sum_y = 0
                # Cycle through surrounding pixels
                for y in range(0, step):
                    for x in range(0, step):
                        selected_x = pos_x - (step / 2) + x
                        selected_y = pos_y - (step / 2) + y
                        if selected_x < 0 or selected_x >= width:  # Mirror padding
                            selected_x = width - abs(selected_x)
                        if selected_y < 0 or selected_y >= height: # Mirror padding
                            selected_y = height - abs(selected_y)
                        selected_pos = (selected_x + width * selected_y) * bpp
                        selected_pixel = src_pixels[selected_pos:(selected_pos + bpp)]
                        grayscale_value = 0
                        for i in range(0, 3):
                            grayscale_value += selected_pixel[i]
                        grayscale_value /= 3  # Get average of RGB values
                        center_sum_x += grayscale_value * kernel_x[x][y]  # Multiply by x kernel
                        center_sum_y += grayscale_value * kernel_y[x][y]  # Multiply by y kernel
                    if color_mode == 1:
                        center_pixel[0] = self.clamp_color_value(center_sum_x)
                        center_pixel[1] = self.clamp_color_value(center_sum_y / 2)
                        center_pixel[2] = self.clamp_color_value(center_sum_y)
                    else:
                        center_pixel[0] = center_pixel[1] = center_pixel[2] = (self.clamp_color_value
                                                                               (int(math.sqrt(center_sum_x ** 2 + center_sum_y ** 2))))
                    dst_pixels[center_pos:(center_pos + bpp)] = center_pixel
            # Update progress bar
            self.progress = float(pos_y + 1) / height
            gimp.progress_update(self.progress)
        print("m_convolute - Loop completed")
        self.progress = 1.0
        gimp.progress_update(self.progress)
        if preview:
            dst_pixels = bytearray(dst_pixels)
            self.preview.draw_buffer(str(dst_pixels), width * bpp)
        else:
            dst_rgn[0:width, 0:height] = dst_pixels.tostring()
            self.drawable.flush()
            self.drawable.merge_shadow(True)  # Take effect, if drawing on the shadow tiles
            self.drawable.update(x1, y1, width, height)
            gimp.displays_flush()  # Update GUI to show changes
        print("m_convolute - Operations applied")


if __name__ == '__main__':
    ConvolutionPlugin().start()
