"""
Color palettes and color manipulation functions for shaders.
Includes various predefined palettes and color space conversions.
"""

import taichi as ti
import taichi.math as tim

# ==================== Predefined Color Palettes ====================

# Neon/Cyberpunk palette
PALETTE_NEON = ti.Matrix([
    [0.0, 1.0, 1.0],    # Cyan
    [1.0, 0.0, 1.0],    # Magenta
    [1.0, 1.0, 0.0],    # Yellow
    [0.0, 1.0, 0.5],    # Green
    [1.0, 0.5, 0.0],    # Orange
    [0.5, 0.0, 1.0],    # Purple
])

# Pastel palette
PALETTE_PASTEL = ti.Matrix([
    [1.0, 0.8, 0.8],    # Pink
    [0.8, 1.0, 0.8],    # Mint
    [0.8, 0.8, 1.0],    # Lavender
    [1.0, 1.0, 0.8],    # Light yellow
    [0.8, 1.0, 1.0],    # Light cyan
    [1.0, 0.8, 1.0],    # Light magenta
])

# Warm palette
PALETTE_WARM = ti.Matrix([
    [1.0, 0.2, 0.0],    # Red-orange
    [1.0, 0.5, 0.0],    # Orange
    [1.0, 0.8, 0.0],    # Yellow
    [0.8, 0.4, 0.0],    # Brown-orange
    [1.0, 0.0, 0.2],    # Red
    [0.9, 0.3, 0.3],    # Light red
])

# Cool palette
PALETTE_COOL = ti.Matrix([
    [0.0, 0.2, 1.0],    # Blue
    [0.0, 0.8, 1.0],    # Cyan
    [0.0, 1.0, 0.5],    # Mint
    [0.5, 0.0, 1.0],    # Purple
    [0.0, 0.5, 0.8],    # Steel blue
    [0.3, 0.7, 1.0],    # Light blue
])

# Earth tones
PALETTE_EARTH = ti.Matrix([
    [0.4, 0.3, 0.2],    # Brown
    [0.6, 0.5, 0.3],    # Tan
    [0.3, 0.5, 0.2],    # Olive
    [0.5, 0.4, 0.3],    # Sienna
    [0.2, 0.4, 0.3],    # Forest green
    [0.6, 0.4, 0.2],    # Rust
])

# Rainbow spectrum (7 colors)
PALETTE_RAINBOW = ti.Matrix([
    [1.0, 0.0, 0.0],    # Red
    [1.0, 0.5, 0.0],    # Orange
    [1.0, 1.0, 0.0],    # Yellow
    [0.0, 1.0, 0.0],    # Green
    [0.0, 0.0, 1.0],    # Blue
    [0.3, 0.0, 0.5],    # Indigo
    [0.5, 0.0, 1.0],    # Violet
])

# ==================== Color Space Conversions ====================

@ti.func
def rgb_to_hsv(rgb: tim.vec3) -> tim.vec3:
    """
    Convert RGB color to HSV color space.
    
    Args:
        rgb: RGB color with components in [0, 1]
    
    Returns:
        HSV color (h in [0, 360], s,v in [0, 1])
    """
    cmax = max(rgb.r, max(rgb.g, rgb.b))
    cmin = min(rgb.r, min(rgb.g, rgb.b))
    delta = cmax - cmin
    
    # Hue calculation
    h = 0.0
    if delta > 1e-6:
        if cmax == rgb.r:
            h = 60.0 * (tim.fract((rgb.g - rgb.b) / delta + 6.0))
        elif cmax == rgb.g:
            h = 60.0 * ((rgb.b - rgb.r) / delta + 2.0)
        else:
            h = 60.0 * ((rgb.r - rgb.g) / delta + 4.0)
    
    # Saturation
    s = 0.0 if cmax < 1e-6 else delta / cmax
    
    # Value
    v = cmax
    
    return tim.vec3(h, s, v)


@ti.func
def hsv_to_rgb(hsv: tim.vec3) -> tim.vec3:
    """
    Convert HSV color to RGB color space.
    
    Args:
        hsv: HSV color (h in [0, 360], s,v in [0, 1])
    
    Returns:
        RGB color with components in [0, 1]
    """
    h = hsv.x
    s = hsv.y
    v = hsv.z
    
    c = v * s
    x = c * (1.0 - abs(tim.fract(h / 60.0) - 1.0))
    m = v - c
    
    rgb = tim.vec3(0.0)
    
    if h < 60.0:
        rgb = tim.vec3(c, x, 0.0)
    elif h < 120.0:
        rgb = tim.vec3(x, c, 0.0)
    elif h < 180.0:
        rgb = tim.vec3(0.0, c, x)
    elif h < 240.0:
        rgb = tim.vec3(0.0, x, c)
    elif h < 300.0:
        rgb = tim.vec3(x, 0.0, c)
    else:
        rgb = tim.vec3(c, 0.0, x)
    
    return rgb + m


# ==================== Color Manipulation ====================

@ti.func
def brightness(color: tim.vec3, factor: ti.f32) -> tim.vec3:
    """
    Adjust brightness of a color.
    
    Args:
        color: Input RGB color
        factor: Brightness multiplier (1.0 = unchanged)
    
    Returns:
        Brightness-adjusted color
    """
    return tim.clamp(color * factor, 0.0, 1.0)


@ti.func
def contrast(color: tim.vec3, factor: ti.f32) -> tim.vec3:
    """
    Adjust contrast of a color.
    
    Args:
        color: Input RGB color
        factor: Contrast factor (1.0 = unchanged, 0 = gray)
    
    Returns:
        Contrast-adjusted color
    """
    return tim.clamp((color - 0.5) * factor + 0.5, 0.0, 1.0)


@ti.func
def saturate(color: tim.vec3, factor: ti.f32) -> tim.vec3:
    """
    Adjust saturation of a color.
    
    Args:
        color: Input RGB color
        factor: Saturation multiplier (1.0 = unchanged, 0 = grayscale)
    
    Returns:
        Saturation-adjusted color
    """
    gray = 0.299 * color.r + 0.587 * color.g + 0.114 * color.b
    return tim.mix(tim.vec3(gray), color, factor)


@ti.func
def tint(color: tim.vec3, tint_color: tim.vec3, amount: ti.f32) -> tim.vec3:
    """
    Apply a tint to a color.
    
    Args:
        color: Base color
        tint_color: Tint color to blend
        amount: Tint amount (0 = no tint, 1 = full tint)
    
    Returns:
        Tinted color
    """
    return tim.mix(color, color * tint_color, amount)


# ==================== Palette Selection ==================== #

@ti.func
def get_palette_color(idx: ti.i32, palette: ti.template()) -> tim.vec3:
    """
    Get a color from a palette by index (wraps around).
    
    Args:
        idx: Color index
        palette: Palette array (template parameter)
    
    Returns:
        Color from palette
    """
    n = len(palette)
    return palette[idx % n, :]


@ti.func
def get_palette_color_blend(idx: ti.f32, palette: ti.template()) -> tim.vec3:
    """
    Get a smoothly blended color from a palette using fractional index.
    
    Args:
        idx: Fractional index
        palette: Palette array
    
    Returns:
        Blended color from palette
    """
    i = ti.floor(idx)
    f = tim.fract(idx)
    
    n = len(palette)
    c1 = palette[int(i) % n, :]
    c2 = palette[int(i + 1.0) % n, :]
    
    return tim.mix(c1, c2, f)


# ==================== Gradient Functions ====================

@ti.func
def gradient_linear(p: ti.f32, c1: tim.vec3, c2: tim.vec3) -> tim.vec3:
    """
    Linear gradient between two colors.
    
    Args:
        p: Position in [0, 1]
        c1: Start color
        c2: End color
    
    Returns:
        Interpolated color
    """
    return tim.mix(c1, c2, tim.clamp(p, 0.0, 1.0))


@ti.func
def gradient_radial(p: tim.vec2, center: tim.vec2, c1: tim.vec3, c2: tim.vec3) -> tim.vec3:
    """
    Radial gradient from a center point.
    
    Args:
        p: Current point
        center: Gradient center
        c1: Color at center
        c2: Color at edge (distance = 1)
    
    Returns:
        Interpolated color based on distance from center
    """
    d = tim.length(p - center)
    return tim.mix(c1, c2, tim.clamp(d, 0.0, 1.0))


# ==================== Special Effects ====================

@ti.func
def glow(color: tim.vec3, intensity: ti.f32) -> tim.vec3:
    """
    Create a glowing effect by boosting brightness.
    
    Args:
        color: Base color
        intensity: Glow intensity (higher = more glow)
    
    Returns:
        Glowing color
    """
    return color * (1.0 + intensity)


@ti.func
def darken(color: tim.vec3, amount: ti.f32) -> tim.vec3:
    """
    Darken a color by a given amount.
    
    Args:
        color: Input color
        amount: Darkening amount [0, 1]
    
    Returns:
        Darkened color
    """
    return color * (1.0 - amount)


@ti.func
def lighten(color: tim.vec3, amount: ti.f32) -> tim.vec3:
    """
    Lighten a color by a given amount.
    
    Args:
        color: Input color
        amount: Lightening amount [0, 1]
    
    Returns:
        Lightened color
    """
    return color + (1.0 - color) * amount


@ti.func
def alpha_blend(fg: tim.vec3, bg: tim.vec3, alpha: ti.f32) -> tim.vec3:
    """
    Alpha blend foreground over background.
    
    Args:
        fg: Foreground color
        bg: Background color
        alpha: Alpha value in [0, 1]
    
    Returns:
        Blended color
    """
    return tim.mix(bg, fg, alpha)


# ==================== Utility ====================

@ti.func
def grayscale(color: tim.vec3) -> ti.f32:
    """
    Convert color to grayscale luminance.
    
    Args:
        color: RGB color
    
    Returns:
        Grayscale value in [0, 1]
    """
    return 0.299 * color.r + 0.587 * color.g + 0.114 * color.b


@ti.func
def invert(color: tim.vec3) -> tim.vec3:
    """
    Invert a color.
    
    Args:
        color: RGB color
    
    Returns:
        Inverted color
    """
    return tim.vec3(1.0) - color


@ti.func
def clamp_color(color: tim.vec3) -> tim.vec3:
    """
    Clamp color components to [0, 1].
    
    Args:
        color: Input color
    
    Returns:
        Clamped color
    """
    return tim.vec3(tim.clamp(color.r, 0.0, 1.0), 
                    tim.clamp(color.g, 0.0, 1.0), 
                    tim.clamp(color.b, 0.0, 1.0))


# ==================== Space helpers ====================

@ti.func
def palette_space(u: ti.f32) -> tim.vec3:
    """
    A smooth cosmic palette (blue/purple/cyan with warm accents).

    Element type:
      - Color mixing.
    """
    # Use cosine palette style
    a = tim.vec3(0.25, 0.22, 0.35)
    b = tim.vec3(0.40, 0.35, 0.55)
    c = tim.vec3(1.00, 1.00, 1.00)
    d = tim.vec3(0.00, 0.15, 0.35)
    return a + b * tim.cos(6.2831853 * (c * u + d))


from core import hash11
@ti.func
def star_flicker(seed: ti.f32, t: ti.f32) -> ti.f32:
    """
    Star flicker function in [0..1], stable per-star and animated in time.

    Element type:
      - f(x,t).
    """
    f = 0.6 + 0.4 * tim.sin(t * (2.0 + 6.0 * hash11(seed)) + 6.28318 * hash11(seed + 3.1))
    return tim.clamp(f, 0.0, 1.0)