"""
Signed Distance Functions (SDF) for geometric primitives.
Based on iquilezles.org implementations.
"""

import taichi as ti
import taichi.math as tim
from core import *

# ==================== Basic Primitives ====================

@ti.func
def sd_circle(p: tim.vec2, r: ti.f32) -> ti.f32:
    """
    Signed distance to a 2D circle.
    
    Args:
        p: Point in 2D space
        r: Circle radius
    
    Returns:
        Signed distance (negative inside, positive outside)
    """
    return length(p) - r


@ti.func
def sd_box(p: tim.vec2, b: tim.vec2) -> ti.f32:
    """
    Signed distance to a 2D axis-aligned box.
    
    Args:
        p: Point in 2D space
        b: Box half-extents (size/2)
    
    Returns:
        Signed distance
    """
    q = abs(p) - b
    return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0)


@ti.func
def sd_ring(p: tim.vec2, r: ti.f32, th: ti.f32) -> ti.f32:
    """
    Signed distance to a ring (circle with thickness).
    
    Args:
        p: Point in 2D space
        r: Ring radius (center of the ring)
        th: Ring thickness (total thickness = 2*th if using proper formula)
    
    Returns:
        Signed distance
    """
    # Actually for a ring we want abs(length(p) - r) - th/2
    # But simpler: abs(outer) - inner approach
    d = length(p) - r
    return abs(d) - th * 0.5


# ==================== Operations ====================

@ti.func
def op_union(d1: ti.f32, d2: ti.f32) -> ti.f32:
    """
    Union of two SDF objects.
    
    Args:
        d1: Signed distance to first object
        d2: Signed distance to second object
    
    Returns:
        Minimum distance (union)
    """
    return min(d1, d2)


@ti.func
def op_subtraction(d1: ti.f32, d2: ti.f32) -> ti.f32:
    """
    Subtraction of d2 from d1 (d1 - d2).
    
    Args:
        d1: Signed distance to first object
        d2: Signed distance to second object
    
    Returns:
        Resulting signed distance
    """
    return max(d1, -d2)


@ti.func
def op_intersection(d1: ti.f32, d2: ti.f32) -> ti.f32:
    """
    Intersection of two SDF objects.
    
    Args:
        d1: Signed distance to first object
        d2: Signed distance to second object
    
    Returns:
        Maximum distance (intersection)
    """
    return max(d1, d2)


@ti.func
def op_smooth_union(d1: ti.f32, d2: ti.f32, k: ti.f32) -> ti.f32:
    """
    Smooth union of two SDF objects using smoothmin.
    
    Args:
        d1: Signed distance to first object
        d2: Signed distance to second object
        k: Smoothness factor
    
    Returns:
        Smoothly blended distance
    """
    return smoothmin(d1, d2, k)


@ti.func
def op_smooth_subtraction(d1: ti.f32, d2: ti.f32, k: ti.f32) -> ti.f32:
    """
    Smooth subtraction using smoothmax.
    
    Args:
        d1: Signed distance to first object
        d2: Signed distance to second object
        k: Smoothness factor
    
    Returns:
        Smoothly subtracted distance
    """
    return smoothmax(d1, -d2, k)


@ti.func
def op_smooth_intersection(d1: ti.f32, d2: ti.f32, k: ti.f32) -> ti.f32:
    """
    Smooth intersection using smoothmax.
    
    Args:
        d1: Signed distance to first object
        d2: Signed distance to second object
        k: Smoothness factor
    
    Returns:
        Smoothly intersected distance
    """
    return -smoothmin(-d1, -d2, k)


# ==================== Domain Operations ====================

@ti.func
def op_repeat(p: tim.vec2, c: tim.vec2) -> tim.vec2:
    """
    Domain repetition - infinite tiling.
    
    Args:
        p: Input point
        c: Cell size (spacing between repetitions)
    
    Returns:
        Point in the first cell (modulo space)
    """
    return tim.fract(p / c + 0.5) * c - 0.5 * c


@ti.func
def op_repeat(p: tim.vec2, c: ti.f32) -> tim.vec2:
    """
    Domain repetition: repeats space in cells of size c.

    Element type:
      - Nonlinear space transform (fract-based repetition).
    """
    return tim.fract(p / c + 0.5) * c - 0.5 * c


@ti.func
def op_repeat_limited(p: tim.vec2, c: tim.vec2, limit: ti.i32) -> tim.vec2:
    """
    Domain repetition with limited number of repetitions.
    
    Args:
        p: Input point
        c: Cell size
        limit: Maximum repetitions in each direction (total cells = (2*limit+1)^2)
    
    Returns:
        Point in the first cell
    """
    return p - c * clamp(ti.round(p / c), -limit, limit)


@ti.func
def op_translate(p: tim.vec2, offset: tim.vec2) -> tim.vec2:
    """
    Translate (shift) the domain.
    
    Args:
        p: Input point
        offset: Translation offset
    
    Returns:
        Translated point
    """
    return p - offset


@ti.func
def op_rotate(p: tim.vec2, angle: ti.f32) -> tim.vec2:
    """
    Rotate the domain around origin.
    
    Args:
        p: Input point
        angle: Rotation angle in radians
    
    Returns:
        Rotated point
    """
    c = tim.cos(angle)
    s = tim.sin(angle)
    return tim.vec2(c * p.x - s * p.y, s * p.x + c * p.y)


@ti.func
def op_scale(p: tim.vec2, s: ti.f32) -> tim.vec2:
    """
    Scale the domain.
    
    Args:
        p: Input point
        s: Scale factor
    
    Returns:
        Scaled point
    """
    return p / s


@ti.func
def op_reflect(p: tim.vec2, n: tim.vec2) -> tim.vec2:
    """
    Reflect the domain across a line.
    
    Args:
        p: Input point
        n: Normal vector of the reflection line (will be normalized)
    
    Returns:
        Reflected point
    """
    n_norm = normalize(n)
    return p - 2.0 * dot(p, n_norm) * n_norm


# ==================== 2D to 1D Conversion ====================

@ti.func
def sd_line(p: tim.vec2, a: tim.vec2, b: tim.vec2) -> ti.f32:
    """
    Signed distance to a line segment.
    
    Args:
        p: Point in 2D space
        a: Start point of line segment
        b: End point of line segment
    
    Returns:
        Distance to line segment
    """
    pa = p - a
    ba = b - a
    h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0)
    return length(pa - ba * h)


@ti.func
def sd_vesica(p: tim.vec2, r: ti.f32, d: ti.f32) -> ti.f32:
    """
    Signed distance to a vesica (lens shape formed by two circles).
    
    Args:
        p: Point in 2D space
        r: Radius of both circles
        d: Distance between circle centers (must be < 2r)
    
    Returns:
        Signed distance
    """
    if abs(d) < 1e-6:
        d = 1e-6
    r1 = r * (1.0 + d / (2.0 * r))
    return length(p - tim.vec2(clamp(p.x, -d/2, d/2), 0.0)) - r1


# ==================== Space SDFs ====================

@ti.func
def sd_capsule(p: tim.vec2, a: tim.vec2, b: tim.vec2, r: ti.f32) -> ti.f32:
    """
    Capsule SDF: distance to segment [a,b] with radius r.

    Element type:
      - SDF.
    """
    pa = p - a
    ba = b - a
    h = tim.clamp(pa.dot(ba) / (ba.dot(ba) + 1e-6), 0.0, 1.0)
    return tim.length(pa - ba * h) - r


@ti.func
def sd_star5(p: tim.vec2, r: ti.f32, inner: ti.f32) -> ti.f32:
    """
    A simple 5-point star-like SDF approximation using angular modulation.
    Not physically perfect, but gives a pretty "big star sprite".

    Element type:
      - SDF.
    """
    ang = tim.atan2(p.y, p.x)
    rad = tim.length(p)
    # 5-point modulation: radius changes with angle
    m = 0.5 + 0.5 * tim.cos(5.0 * ang)
    target = tim.mix(inner, 1.0, m) * r
    return rad - target