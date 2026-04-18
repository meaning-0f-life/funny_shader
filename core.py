"""
Core utility functions for shader programming.
Contains hash functions, smoothing functions, and other common utilities.
"""

import taichi as ti
import taichi.math as tim

# ==================== Hash Functions ====================

@ti.func
def hash21(p: tim.vec2) -> ti.f32:
    """
    2D hash function returning a pseudo-random float in [0, 1).
    Uses a simple hashing algorithm based on dot product and fract.
    
    Args:
        p: 2D input vector
    
    Returns:
        Pseudo-random float in [0, 1)
    """
    # Based on iquilezles.org hash functions
    n = tim.dot(p, tim.vec2(127.1, 311.7))
    return fract(tim.sin(n) * 43758.5453123)


@ti.func
def hash22(p: tim.vec2) -> tim.vec2:
    """
    2D hash function returning a pseudo-random 2D vector in [0, 1).
    
    Args:
        p: 2D input vector
    
    Returns:
        Pseudo-random 2D vector with components in [0, 1)
    """
    return tim.vec2(hash21(p), hash21(p + tim.vec2(19.19, 47.39)))


@ti.func
def hash31(p: tim.vec3) -> ti.f32:
    """
    3D hash function returning a pseudo-random float in [0, 1).
    
    Args:
        p: 3D input vector
    
    Returns:
        Pseudo-random float in [0, 1)
    """
    n = tim.dot(p, tim.vec3(127.1, 311.7, 74.7))
    return fract(tim.sin(n) * 43758.5453123)


# ==================== Smoothing Functions ====================

@ti.func
def smoothstep(edge0: ti.f32, edge1: ti.f32, x: ti.f32) -> ti.f32:
    """
    Smooth Hermite interpolation between 0 and 1 when edge0 <= x <= edge1.
    Returns 0.0 if x <= edge0, 1.0 if x >= edge1, and smooth interpolation otherwise.
    
    Args:
        edge0: Lower edge of the interpolation
        edge1: Upper edge of the interpolation
        x: Input value
    
    Returns:
        Smoothed value in [0, 1]
    """
    t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


@ti.func
def smootherstep(edge0: ti.f32, edge1: ti.f32, x: ti.f32) -> ti.f32:
    """
    Smootherstep - a smoother version of smoothstep using 5th order polynomial.
    Perlin recommended this for smoother results.
    
    Args:
        edge0: Lower edge of the interpolation
        edge1: Upper edge of the interpolation
        x: Input value
    
    Returns:
        Smoothed value in [0, 1] with zero first and second derivatives at endpoints
    """
    t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


@ti.func
def smoothmin(a: ti.f32, b: ti.f32, k: ti.f32) -> ti.f32:
    """
    Smooth minimum function - creates a smooth blending between two values.
    Based on iquilezles.org implementation.
    
    Args:
        a: First value
        b: Second value
        k: Smoothness factor (higher = sharper transition)
    
    Returns:
        Smooth minimum of a and b
    """
    h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return mix(b, a, h) - k * h * (1.0 - h)


@ti.func
def smoothmax(a: ti.f32, b: ti.f32, k: ti.f32) -> ti.f32:
    """
    Smooth maximum function - creates a smooth blending between two values.
    
    Args:
        a: First value
        b: Second value
        k: Smoothness factor (higher = sharper transition)
    
    Returns:
        Smooth maximum of a and b
    """
    return -smoothmin(-a, -b, k)


# ==================== Clamp and Mix ====================

@ti.func
def clamp(x: ti.f32, xmin: ti.f32, xmax: ti.f32) -> ti.f32:
    """
    Clamp a value between a minimum and maximum.
    
    Args:
        x: Input value to clamp
        xmin: Minimum allowed value
        xmax: Maximum allowed value
    
    Returns:
        Clamped value
    """
    return max(xmin, min(xmax, x))


@ti.func
def mix(a: ti.f32, b: ti.f32, t: ti.f32) -> ti.f32:
    """
    Linear interpolation between two values.
    
    Args:
        a: First value
        b: Second value
        t: Interpolation factor (0 = a, 1 = b)
    
    Returns:
        Interpolated value
    """
    return a * (1.0 - t) + b * t


@ti.func
def mix2(a: tim.vec2, b: tim.vec2, t: ti.f32) -> tim.vec2:
    """
    Linear interpolation between two 2D vectors.
    
    Args:
        a: First vector
        b: Second vector
        t: Interpolation factor (0 = a, 1 = b)
    
    Returns:
        Interpolated vector
    """
    return a * (1.0 - t) + b * t


@ti.func
def mix3(a: tim.vec3, b: tim.vec3, t: ti.f32) -> tim.vec3:
    """
    Linear interpolation between two 3D vectors (colors).
    
    Args:
        a: First vector/color
        b: Second vector/color
        t: Interpolation factor (0 = a, 1 = b)
    
    Returns:
        Interpolated vector/color
    """
    return a * (1.0 - t) + b * t


# ==================== Trigonometric Utilities ====================

@ti.func
def deg2rad(deg: ti.f32) -> ti.f32:
    """Convert degrees to radians."""
    return deg * 3.14159265359 / 180.0


@ti.func
def rad2deg(rad: ti.f32) -> ti.f32:
    """Convert radians to degrees."""
    return rad * 180.0 / 3.14159265359


# ==================== Other Utilities ====================

@ti.func
def fract(x: ti.f32) -> ti.f32:
    """
    Return the fractional part of x (x - floor(x)).
    
    Args:
        x: Input value
    
    Returns:
        Fractional part in [0, 1)
    """
    return x - ti.floor(x)


@ti.func
def sign(x: ti.f32) -> ti.f32:
    """
    Sign function: returns -1 for negative, 0 for zero, 1 for positive.
    
    Args:
        x: Input value
    
    Returns:
        Sign of x
    """
    return -1.0 if x < 0.0 else (1.0 if x > 0.0 else 0.0)


@ti.func
def abs(x: ti.f32) -> ti.f32:
    """Absolute value."""
    return x if x >= 0.0 else -x


@ti.func
def length(v: tim.vec2) -> ti.f32:
    """Euclidean length of a 2D vector."""
    return tim.sqrt(v.x * v.x + v.y * v.y)


@ti.func
def distance(a: tim.vec2, b: tim.vec2) -> ti.f32:
    """Euclidean distance between two 2D points."""
    return length(b - a)


@ti.func
def dot(a: tim.vec2, b: tim.vec2) -> ti.f32:
    """Dot product of two 2D vectors."""
    return a.x * b.x + a.y * b.y


@ti.func
def normalize(v: tim.vec2) -> tim.vec2:
    """
    Normalize a 2D vector to unit length.
    
    Args:
        v: Input vector
    
    Returns:
        Normalized vector (or zero vector if length is zero)
    """
    len_v = length(v)
    return v / len_v if len_v > 0.0 else tim.vec2(0.0)
