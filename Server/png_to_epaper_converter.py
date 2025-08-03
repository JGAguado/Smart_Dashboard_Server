#!/usr/bin/env python3
"""
PNG to 7-Color E-Paper Converter for ESP32-S2 Smart Dashboard
"""

import numpy as np
from PIL import Image
import os


class EpaperColorConverter:
    """Converts PNG images to 7-color e-paper C array format"""
    
    # 7-color e-paper palette (RGB values)
    PALETTE = [
        (0, 0, 0),           # 0 - Black
        (255, 255, 255),     # 1 - White  
        (67, 138, 28),       # 2 - Green
        (100, 64, 255),      # 3 - Blue
        (191, 0, 0),         # 4 - Red
        (255, 243, 56),      # 5 - Yellow
        (232, 126, 0),       # 6 - Orange
        (194, 164, 244)      # 7 - Light Purple (afterimage)
    ]
    
    # Supported resolutions
    SUPPORTED_RESOLUTIONS = [(800, 480), (640, 400), (600, 448)]
    
    def __init__(self):
        self.palette_array = np.array(self.PALETTE)
    
    def find_closest_color(self, rgb_color):
        """Find the closest color in the 7-color palette using Euclidean distance."""
        rgb_array = np.array(rgb_color)
        distances = np.sum((self.palette_array - rgb_array) ** 2, axis=1)
        return np.argmin(distances)
    
    def validate_image_size(self, width, height):
        """Validate image dimensions and check if rotation is needed."""
        # Check if image is in portrait and can be rotated to fit landscape
        for supported_width, supported_height in self.SUPPORTED_RESOLUTIONS:
            if width == supported_height and height == supported_width:
                print(f"Image is {width}x{height} (portrait), rotating to {supported_width}x{supported_height} (landscape)")
                return supported_width, supported_height, True  # needs rotation
            elif width == supported_width:
                if height > supported_height:
                    print(f"Warning: Height {height} exceeds maximum {supported_height} for width {width}")
                    return supported_width, supported_height, False
                return width, height, False  # no rotation needed
        
        print(f"Error: Unsupported dimensions {width}x{height}")
        print(f"Supported resolutions: {self.SUPPORTED_RESOLUTIONS}")
        return None, None, False
    
    def convert_png_to_epaper(self, input_path, output_path=None):
        """Convert PNG image to 7-color e-paper C array format."""
        try:
            print(f"Converting: {input_path}")
            
            # Load and validate image
            with Image.open(input_path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    print(f"Converting from {img.mode} to RGB")
                    img = img.convert('RGB')
                
                width, height = img.size
                print(f"Input image: {width}x{height}")
                
                # Validate dimensions and check rotation
                target_width, target_height, should_rotate = self.validate_image_size(width, height)
                if target_width is None:
                    return None
                
                # Apply rotation if needed
                if should_rotate:
                    print("Rotating image 90° clockwise...")
                    img = img.rotate(-90, expand=True)
                    width, height = img.size
                    print(f"After rotation: {width}x{height}")
                
                # Crop if necessary
                if (width, height) != (target_width, target_height):
                    img = img.crop((0, 0, target_width, target_height))
                    print(f"Cropped to: {target_width}x{target_height}")
                
                # Convert image to numpy array
                img_array = np.array(img)
                
                print("Converting colors to e-paper palette...")
                
                # Create output buffer
                buffer_size = (target_width * target_height) // 2
                output_buffer = bytearray(buffer_size)
                
                byte_index = 0
                for y in range(target_height):
                    for x in range(0, target_width, 2):  # Process 2 pixels at a time
                        # Get first pixel color
                        rgb1 = tuple(img_array[y, x])
                        color1 = self.find_closest_color(rgb1)
                        
                        # Get second pixel color (handle odd width)
                        if x + 1 < target_width:
                            rgb2 = tuple(img_array[y, x + 1])
                            color2 = self.find_closest_color(rgb2)
                        else:
                            color2 = color1  # Duplicate last pixel if odd width
                        
                        # Pack 2 pixels into 1 byte (4 bits each)
                        packed_byte = (color1 << 4) | color2
                        output_buffer[byte_index] = packed_byte
                        byte_index += 1
                
                print(f"Conversion complete: {len(output_buffer)} bytes generated")
                
                # Generate C array code
                c_code = f"// 7 Color Image Data {target_width}*{target_height}\n"
                c_code += f"const unsigned char Image7color[{len(output_buffer)}] = {{\n"
                
                for i, byte_val in enumerate(output_buffer):
                    if i % 16 == 0 and i > 0:
                        c_code += "\n"
                    c_code += f"0x{byte_val:02X},"
                
                c_code += "\n};\n"
                
                # Save to file if output path provided
                if output_path:
                    if output_path.endswith('.c'):
                        with open(output_path, 'w') as f:
                            f.write(c_code)
                        print(f"✅ C array saved to: {output_path}")
                    else:
                        with open(output_path, 'wb') as f:
                            f.write(output_buffer)
                        print(f"✅ Binary data saved to: {output_path}")
                
                return c_code, bytes(output_buffer)
                
        except Exception as e:
            print(f"❌ Error converting image: {e}")
            return None, None


def convert_png_to_c_file(png_path, c_path=None):
    """
    Convenience function to convert PNG to C array file.
    
    Args:
        png_path: Path to PNG file
        c_path: Output C file path (if None, uses PNG name with .c extension)
    
    Returns:
        bool: True if successful, False otherwise
    """
    if c_path is None:
        c_path = os.path.splitext(png_path)[0] + '.c'
    
    converter = EpaperColorConverter()
    result_c, result_binary = converter.convert_png_to_epaper(png_path, c_path)
    
    # Also save binary version for ESP32 firmware
    bin_path = os.path.splitext(c_path)[0] + '.bin'
    if result_binary is not None:
        with open(bin_path, 'wb') as f:
            f.write(result_binary)
        print(f"✅ Binary data saved to: {bin_path}")
    
    return result_c is not None
