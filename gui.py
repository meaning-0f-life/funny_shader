"""
GUI and window management for Taichi shaders.
Provides a BaseShader class that handles window creation, rendering loop, and image output.
"""

import taichi as ti
import taichi.math as tim

# ==================== BaseShader Class ====================

class BaseShader:
    """
    Base class for Taichi-based shaders.
    Handles window creation, rendering loop, and image buffer management.
    
    Subclasses must override the main_image method to implement custom shader logic.
    
    Attributes:
        width (int): Window width in pixels
        height (int): Window height in pixels
        pixel (ti.field): 2D field storing RGB color for each pixel
        gui (ti.GUI): Taichi GUI window
    """
    
    def __init__(self, width: int = 800, height: int = 800, title: str = "Shader"):
        """
        Initialize the BaseShader with specified dimensions.
        
        Args:
            width: Window width (default 800)
            height: Window height (default 800)
            title: Window title (default "Shader")
        """
        self.width = width
        self.height = height
        
        # Initialize Taichi with GPU backend (or CPU if not available)
        ti.init(arch=ti.gpu, default_fp=ti.f32)
        
        # Create pixel buffer as a 2D field of 3D vectors (RGB)
        self.pixel = ti.Vector.field(3, dtype=ti.f32, shape=(width, height))
        
        # Create GUI window
        self.gui = ti.GUI(title, res=(width, height))
    
    
    @ti.func
    def main_image(self, uv: tim.vec2, time: ti.f32) -> tim.vec3:
        """
        Main shader function - computes color for a given UV coordinate and time.
        
        This method should be overridden by subclasses to implement custom shader logic.
        
        Args:
            uv: Normalized screen coordinates in [0, 1] (origin at bottom-left)
            time: Time in seconds since start
        
        Returns:
            RGB color as a 3D vector with components in [0, 1]
        """
        # Default implementation: black screen
        return tim.vec3(0.0)
    
    
    @ti.kernel
    def render_frame(self, time: ti.f32):
        """
        Render a single frame by calling main_image for each pixel.
        
        Args:
            time: Current time in seconds
        """
        for i, j in self.pixel:
            # Convert pixel coordinates to normalized UV [0, 1]
            uv = tim.vec2(i / self.width, j / self.height)
            
            # Call the shader function
            color = self.main_image(uv, time)
            
            # Store result in pixel buffer
            self.pixel[i, j] = clamp_color(color)
    
    
    def run(self, fps: int = 60):
        """
        Start the main rendering loop.
        
        Args:
            fps: Target frames per second (default 60)
        """
        import time as pytime
        
        start_time = pytime.time()
        frame_count = 0
        
        while self.gui.running:
            # Calculate elapsed time
            current_time = pytime.time()
            elapsed = current_time - start_time
            
            # Render frame
            self.render_frame(elapsed)
            
            # Display the pixel buffer in the GUI
            self.gui.set_image(self.pixel)
            
            # Update window title with FPS
            if frame_count % 30 == 0:
                actual_fps = frame_count / elapsed if elapsed > 0 else 0
                self.gui.title = f"Shader | FPS: {actual_fps:.1f}"
            
            # Handle events and maintain frame rate
            self.gui.show()
            frame_count += 1
            
            # Simple frame rate control
            target_frame_time = 1.0 / fps
            sleep_time = target_frame_time - (pytime.time() - current_time)
            if sleep_time > 0:
                pytime.sleep(sleep_time)
        
        print(f"Render loop ended. Total frames: {frame_count}")
    
    
    def save_frame(self, filename: str = "frame.png"):
        """
        Save the current frame to a PNG file.
        
        Args:
            filename: Output filename (default "frame.png")
        """
        import imageio
        import numpy as np
        
        # Convert Taichi field to numpy array
        img = self.pixel.to_numpy()
        
        # Flip vertically (Taichi's origin is bottom-left, imageio expects top-left)
        img = img[::-1, :, :]
        
        # Convert from float [0,1] to uint8 [0,255]
        img_uint8 = (img * 255).astype('uint8')
        
        # Save using imageio
        imageio.imwrite(filename, img_uint8)
        print(f"Frame saved to {filename}")
    
    
    def close(self):
        """Close the GUI window."""
        self.gui.close()


# ==================== Utility Functions ====================

@ti.func
def clamp_color(color: tim.vec3) -> tim.vec3:
    """
    Clamp color components to valid range [0, 1].
    
    Args:
        color: Input RGB color
    
    Returns:
        Clamped color
    """
    return tim.vec3(
        tim.clamp(color.r, 0.0, 1.0),
        tim.clamp(color.g, 0.0, 1.0),
        tim.clamp(color.b, 0.0, 1.0)
    )


@ti.func
def gamma_correct(color: tim.vec3, gamma: ti.f32 = 2.2) -> tim.vec3:
    """
    Apply gamma correction to color.
    
    Args:
        color: Input linear color
        gamma: Gamma value (default 2.2 for sRGB)
    
    Returns:
        Gamma-corrected color
    """
    return tim.pow(color, tim.vec3(1.0 / gamma))
