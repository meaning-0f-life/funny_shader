"""
Домашнее задание по курсу Компьютерный практикум 2025, модуль 3, задание 1
Тема: Компьютерная графика (шейдеры) — Taichi

=== ТЕМА ДЛЯ ТАБЛИЦЫ ВЫБОРА ТЕМ ===
Тема: Космос (Space)
Краткое описание: Анимированная сцена космоса: звёздное поле (включая мерцание и "туманности"),
несколько планет с кольцами и бликами, плюс центральная чёрная дыра с аккреционным диском,
гравитационным искажением (линзинг) и падающими "фотонами" (дугами).

---

=== ЧЕКЛИСТ ===

1) SDF (Signed Distance Functions):
   - sd_circle (круг)
   - sd_ring (кольцо)
   - sd_capsule (капсула/отрезок)
   - sd_box (прямоугольник)
   - sd_star5 (звезда 5-конечная, как SDF-фигура)
   - sd_spiral_like (спиральная полоса в аккреционном диске через расстояние)

2) Функции вида f(x) или f(x, t):
   - star_flicker(id, t)
   - fbm(p, t)
   - swirl(p, strength, t) (нелинейное и зависящее от времени)
   - doppler-ish gradient по углу диска (функция угла и времени)

3) Преобразования пространства линейные:
   - rot2(a): поворот
   - масштабирование/сдвиг: p = p * s + offset

4) Преобразования пространства нелинейные:
   - gravitational_lens(p, center, mass): радиальное нелинейное искажение (линзинг)
   - swirl(p, strength, t): закрутка вокруг центра
   - domain repetition (op_repeat) — нелинейное "дробление" пространства (через fract)

5) Сглаживающие функции:
   - smoothstep (через tim.smoothstep)
   - smin (smooth union)
   - soft_mask (антиалиасинг масок)

6) Смешивание цветов:
   - mix (через tim.mix)
   - наложение слоёв: add / screen-like / mask blend

---

=== ЭЛЕМЕНТЫ ===
  1) Фон-градиент космоса + "туманность" (fbm)
  2) Звёздное поле (много звезд) через domain repetition + hash
  3) Большие звёзды-спрайты (SDF star5)
  4) Кометы/метеоры (капсула + motion blur-like)
  5) Планета A (SDF circle) + освещение/терминатор
  6) Кольца планеты A (SDF ring + поворот)
  7) Планета B (SDF circle) + полосы (f(x,t))
  8) Луна (SDF circle) + орбита
  9) Чёрная дыра (SDF circle) + "event horizon" glow
 10) Аккреционный диск (кольцо + спиральные полосы + допплер-градиент)
 11) Гравитационное линзирование (нелинейное преобразование координат)
 12) "Фотонное кольцо"/дуги (капсулы по окружности, анимированные)

"""

import taichi as ti
import taichi.math as tim

from gui import BaseShader
from core import *
from colors import *
from sdf import *


# ==========================
# Noise / fBm (nebula)
# ==========================

@ti.func
def value_noise(p: tim.vec2) -> ti.f32:
    """
    Cheap 2D value noise via hashing the 4 lattice corners.

    Element type:
      - f(x) function.
      - Uses smoothstep internally (smoothing).
    """
    i = tim.floor(p)
    f = tim.fract(p)

    a = hash21(i + tim.vec2(0.0, 0.0))
    b = hash21(i + tim.vec2(1.0, 0.0))
    c = hash21(i + tim.vec2(0.0, 1.0))
    d = hash21(i + tim.vec2(1.0, 1.0))

    u = f * f * (3.0 - 2.0 * f)  # smoothstep polynomial
    return tim.mix(tim.mix(a, b, u.x), tim.mix(c, d, u.x), u.y)


@ti.func
def fbm(p: tim.vec2, t: ti.f32) -> ti.f32:
    """
    2D fBm (fractal Brownian motion) for nebula-like textures.

    Element type:
      - f(x, t) function.
      - Uses linear transforms (rotation/scale) between octaves.
    """
    s = 0.0
    amp = 0.55
    pp = p
    for k in ti.static(range(5)):
        s += amp * value_noise(pp + 0.07 * t)
        pp = (rot2(0.7) @ pp) * 2.02 + tim.vec2(17.0, 9.0)
        amp *= 0.5
    return s


# ==========================
# Space warps (black hole)
# ==========================

@ti.func
def swirl(p: tim.vec2, strength: ti.f32, t: ti.f32) -> tim.vec2:
    """
    Nonlinear swirl around origin: rotates more when closer to center.

    Element type:
      - Nonlinear space transform.
      - f(x,t): depends on radius and time.
    """
    r = tim.length(p) + 1e-6
    a = strength / r + 0.35 * tim.sin(t * 0.6 + r * 2.5)
    return (rot2(a) @ p)


@ti.func
def gravitational_lens(p: tim.vec2, center: tim.vec2, mass: ti.f32) -> tim.vec2:
    """
    Simple gravitational lensing warp (non-physical but pretty):
    p' = p + (p-center) * mass / (|p-center|^2 + eps)

    Element type:
      - Nonlinear space transform.
    """
    d = p - center
    r2 = d.dot(d) + 1e-4
    return p + d * (mass / r2)


# ==========================
# Shader
# ==========================

@ti.data_oriented
class SpaceShader(BaseShader):
    """
    "Cosmos" shader:
      - Starfield + nebula
      - 2 planets + rings + moon
      - Black hole + accretion disk + lensing

    The shader is structured as layers:
      1) Background gradient + nebula (fbm)
      2) Repeated starfield (domain repetition)
      3) Big star sprites (SDF star)
      4) Meteors (capsules)
      5) Planets + rings + moon (SDF circles/rings, lighting)
      6) Black hole system: event horizon + accretion disk + lensing
    """

    def __init__(self, width: int = 800, height: int = 800):
        """Initialize the shader with default parameters."""
        super().__init__(width, height, title="Space Shader — Planets, Stars & Black Hole")

        # Anti-aliasing width in SDF space (tuned for typical resolutions)
        self.aa = 0.0035

        # Black hole + planets center in screen space (centered coords)
        self.bh_center = tim.vec2(0.3, 0.0)
        self.planetA_c = tim.vec2(-0.85, -0.4)
        self.planetB_c = tim.vec2(1.2, -0.7)

        # Black hole parameters
        self.bh_radius = 0.4
        self.bh_mass = 0.15

        # Disk parameters
        self.disk_r = 0.5
        self.disk_th = 0.1

    @ti.func
    def render_background(self, p: tim.vec2, t: ti.f32) -> tim.vec3:
        """
        Background layer: gradient + nebula fog.

        Elements:
          - fBm (f(x,t))
          - Color mixing (mix)
        """
        # Subtle vertical gradient
        g = 0.5 + 0.5 * p.y
        base = tim.mix(tim.vec3(0.01, 0.01, 0.02), tim.vec3(0.02, 0.01, 0.05), g)

        # Nebula via fbm in a warped space
        q = (p - self.bh_center) * 1.7
        q = swirl(q, 0.3, t)  # nonlinear transform (swirl)
        n = fbm(q * 2.2 + tim.vec2(0.0, 0.25), t)

        neb = palette_space(n * 0.85 + 0.15)
        neb_strength = tim.smoothstep(0.35, 0.95, n) * 0.55
        bh_dist = tim.length(p - self.bh_center)
        bh_mask = tim.smoothstep(self.bh_radius * 0.95, self.bh_radius * 1.05, bh_dist)
        neb_strength *= bh_mask
        col = tim.mix(base, neb, neb_strength)
        return col

    @ti.func
    def render_starfield(self, p: tim.vec2, t: ti.f32) -> tim.vec3:
        """
        Starfield using domain repetition + hash (many stars).
        Produces tiny stars with flicker, plus occasional cross-like glints.

        Elements:
          - Nonlinear transform: op_repeat
          - f(x,t): flicker
          - SDF: circle for star core
          - Smoothing: smoothstep AA
          - Color blending: additive
        """
        col = tim.vec3(0.0)

        # Two layers for parallax feel
        for layer in ti.static(range(2)):
            sp = 0.08 if layer == 0 else 0.14
            drift = tim.vec2(0.015 * (layer + 1) * t, 0.008 * (layer + 1) * t)
            pp = p + drift

            cell = tim.floor((pp + sp * 0.5) / sp)
            local = op_repeat(pp, sp)

            h = hash21(cell + tim.vec2(13.0 * layer, 7.0))
            # star existence probability
            exist = tim.smoothstep(0.80, 0.92, h)

            # star position jitter inside the cell
            jitter = (hash22(cell + 19.0) - 0.5) * sp * 0.75
            sP = local - jitter

            # core size varies
            r = (0.0018 if layer == 0 else 0.0028) * (0.6 + 1.8 * hash11(h * 91.7))
            d = sd_circle(sP, r)
            m = soft_mask(d, self.aa * 0.55) * exist

            # Flicker
            flick = star_flicker(h * 1000.0 + layer * 17.0, t)
            intensity = (0.65 + 0.75 * flick) * (1.0 if layer == 0 else 0.75)

            # Color: mostly white-blue, sometimes warm
            warm = tim.smoothstep(0.82, 0.98, hash11(h * 31.3))
            c1 = tim.vec3(0.75, 0.85, 1.00)
            c2 = tim.vec3(1.00, 0.78, 0.55)
            c = tim.mix(c1, c2, warm)

            col += c * (m * intensity)

            # Occasional glint (cross) using box SDF, adds variety
            gl = tim.smoothstep(0.92, 0.98, hash11(h * 63.1))
            if gl > 0.0:
                # two thin boxes rotated a bit
                R = rot2(0.2) if layer == 0 else rot2(-0.1)
                sp2 = R @ sP
                d1 = sd_box(sp2, tim.vec2(r * 3.2, r * 0.35))
                d2 = sd_box(sp2, tim.vec2(r * 0.35, r * 3.2))
                mm = (soft_mask(d1, self.aa) + soft_mask(d2, self.aa)) * 0.5
                col += c * mm * (0.35 * gl)

        return col

    @ti.func
    def render_big_stars(self, p: tim.vec2, t: ti.f32) -> tim.vec3:
        """
        A few bigger "sprite-stars" using star SDF for visual richness.

        Elements:
          - SDF: sd_star5
          - Linear transforms: rotation
          - f(x,t): subtle pulsing
          - Color mixing
        """
        col = tim.vec3(0.0)

        # Predefined positions (at least several elements)
        centers = ti.static([
            tim.vec2(-0.75, 0.45),
            tim.vec2(-0.20, 0.65),
            tim.vec2(0.70, 0.55),
        ])

        for i in ti.static(range(3)):
            c = centers[i]
            q = p - c
            q = rot2(0.35 * i + 0.15 * tim.sin(t * 0.5 + i)) @ q  # linear rot with time
            pulse = 1.0 + 0.12 * tim.sin(t * 1.1 + 2.2 * i)
            d = sd_star5(q, 0.035 * pulse, 0.45)
            m = soft_mask(d, self.aa * 1.4)

            # Color: blue-white with slight purple
            base = tim.vec3(0.80, 0.90, 1.00)
            tint = tim.vec3(0.85, 0.70, 1.00)
            cc = tim.mix(base, tint, 0.35)
            col += cc * m * (1.0 + 0.4 * pulse)

        return col

    @ti.func
    def render_meteors(self, p: tim.vec2, t: ti.f32) -> tim.vec3:
        """
        Meteors/Comets: animated capsules with glow tail.

        Elements:
          - SDF: capsule
          - Linear transform: rotation
          - f(x,t): motion over time
          - Smooth masks + color blending
        """
        col = tim.vec3(0.0)

        # 2 meteors for extra dynamics
        for i in ti.static(range(2)):
            # start points are off-screen, move diagonally
            speed = 0.25 + 0.12 * i
            tt = t * speed + i * 1.3

            # repeat time (softly) so meteor reappears occasionally
            phase = tim.fract(tt * 0.12)
            # trajectory in centered coords
            head = tim.vec2(-1.1 + 2.4 * phase, 0.95 - 1.6 * phase) + tim.vec2(0.15 * i, -0.05 * i)
            tail = head - tim.vec2(0.20, 0.14) * (1.0 + 0.4 * i)

            q = p
            # Slight curvature using nonlinear swirl in local space
            q = swirl(q - tim.vec2(0.0, 0.0), 0.02 * (i + 1), t) + tim.vec2(0.0, 0.0)

            tail_dir = tim.normalize(head - tail)
            angle = tim.atan2(tail_dir.y, tail_dir.x)
            q_rot = rot2(-angle) @ q

            q_rep = op_repeat(q_rot, tim.vec2(0.03, 999.0))
            q_rep = rot2(angle) @ q_rep
            q = q_rep

            d = sd_capsule(q, tail, head, 0.0045 + 0.0015 * i)
            m = soft_mask(d, self.aa)

            # Tail glow: stronger near head, fading to tail
            # project point to segment parameter for gradient
            ba = head - tail
            pa = q - tail
            h = tim.clamp(pa.dot(ba) / (ba.dot(ba) + 1e-6), 0.0, 1.0)
            glow = (h ** 1.5) * 1.2

            meteor_col = tim.vec3(0.9, 0.95, 1.0) * (0.6 + 1.0 * glow)
            meteor_col = tim.mix(meteor_col, tim.vec3(1.0, 0.75, 0.45), 0.25 * i)

            col += meteor_col * m

        return col

    @ti.func
    def planet_lighting(self, q: tim.vec2, r: ti.f32, light_dir: tim.vec2) -> ti.f32:
        """
        Simple 2D "sphere" lighting approximation:
          - normal ~ q / r
          - lambert = dot(normal, light_dir)

        Element type:
          - f(x): lighting function
        """
        n = q / (r + 1e-6)
        ndl = tim.clamp(n.dot(light_dir), 0.0, 1.0)
        # Add soft terminator
        return ndl ** 0.7

    @ti.func
    def render_planets(self, p: tim.vec2, t: ti.f32) -> tim.vec3:
        """
        Planets + ring + moon.

        Elements:
          - SDF: circles, rings
          - Linear transforms: rotation, scaling, translation
          - Nonlinear: subtle band distortion via sin
          - Smoothing + color mixing
        """
        col = tim.vec3(0.0)
        light_dir = tim.normalize(tim.vec2(-0.6, 0.35))

        # --- Planet A (with rings) ---
        qA = p - self.planetA_c
        rA = 0.18
        dA = sd_circle(qA, rA)
        mA = soft_mask(dA, self.aa)

        # Planet base color + atmospheric rim
        litA = self.planet_lighting(qA, rA, light_dir)
        baseA = tim.vec3(0.10, 0.22, 0.55)
        oceanA = tim.vec3(0.08, 0.55, 0.65)
        planetA_col = tim.mix(baseA, oceanA, 0.45 + 0.35 * tim.sin(qA.y * 8.0 + t * 0.4))
        planetA_col *= (0.18 + 0.95 * litA)

        # Rim glow (atmosphere) using ring SDF
        rim = soft_mask(sd_ring(qA, rA * 1.01, 0.02), self.aa * 1.2) * 0.9
        planetA_col += tim.vec3(0.35, 0.65, 1.00) * rim * 0.35

        col = tim.mix(col, planetA_col, mA)

        # Rings around Planet A (tilted)
        qR = (rot2(0.55) @ qA)  # linear transform (rotation)
        dR = sd_ring(qR, rA * 1.25, 0.05)
        mR = soft_mask(dR, self.aa)

        # ring shading depends on y (fake thickness) + time
        ring_col = tim.vec3(0.85, 0.75, 0.65)
        ring_col *= 0.55 + 0.45 * tim.sin(qR.x * 12.0 + t * 0.9)
        ring_col *= 0.75 + 0.25 * tim.smoothstep(-0.2, 0.2, qR.y)

        # blend ring behind planet a bit: simple depth trick
        behind = tim.smoothstep(0.00, 0.03, qR.y)  # top part considered "in front"
        ring_alpha = mR * (0.35 + 0.45 * behind)
        col += ring_col * ring_alpha

        # --- Planet B (striped gas giant) ---
        qB = p - self.planetB_c
        rB = 0.12 + 0.01 * tim.sin(t * 0.6)  # f(x,t)
        dB = sd_circle(qB, rB)
        mB = soft_mask(dB, self.aa)

        litB = self.planet_lighting(qB, rB, light_dir)
        # stripes via sin: f(y,t)
        bands = 0.5 + 0.5 * tim.sin(qB.y * 22.0 + 0.7 * tim.sin(t * 0.4))
        colB1 = tim.vec3(0.55, 0.32, 0.70)
        colB2 = tim.vec3(0.95, 0.75, 0.30)
        planetB_col = tim.mix(colB1, colB2, bands) * (0.20 + 0.95 * litB)

        # small highlight
        hl = tim.smoothstep(0.03, 0.0, tim.length(qB - light_dir * 0.06) - 0.03)
        planetB_col += tim.vec3(1.0, 0.95, 0.85) * hl * 0.35

        col = tim.mix(col, planetB_col, mB)

        # --- Moon orbiting Planet A ---
        ang = t * 0.35
        moon_c = self.planetA_c + (rot2(ang) @ tim.vec2(0.32, 0.0))
        qM = p - moon_c
        rM = 0.045
        dM = sd_circle(qM, rM)
        mM = soft_mask(dM, self.aa)

        litM = self.planet_lighting(qM, rM, light_dir)
        moon_col = tim.vec3(0.55, 0.55, 0.60) * (0.18 + 0.95 * litM)
        # craters via noise-like hash sampling (cheap)
        crater = value_noise(qM * 55.0 + tim.vec2(12.0, 9.0))
        moon_col *= 0.85 + 0.25 * crater

        col = tim.mix(col, moon_col, mM)

        # thin orbit line (ring around planet A) — extra element
        qO = p - self.planetA_c
        dO = sd_ring(qO, 0.32, 0.0045)
        mO = soft_mask(dO, self.aa)
        col += tim.vec3(0.25, 0.45, 0.85) * mO * 0.25

        return col

    @ti.func
    def render_black_hole(self, p: tim.vec2, t: ti.f32) -> tim.vec3:
        """
        Black hole system:
          - Event horizon (black disk) + glow
          - Accretion disk (ring band) with spiral lanes + doppler-ish gradient
          - Photon arcs

        Elements:
          - SDF: circle, ring, capsule
          - Nonlinear transforms: lensing + swirl
          - Smoothing: AA masks, smin
          - Color blending: mix/add
        """
        col = tim.vec3(0.0)

        c = self.bh_center

        # Apply gravitational lensing to sampling coordinates (distort background/objects)
        # NOTE: This should be used by caller too if you want full-scene lensing.
        # Here we use it for local disk patterns (extra depth).
        q = p - c

        # Event horizon
        dH = sd_circle(q, self.bh_radius)
        mH = soft_mask(dH, self.aa)
        col = tim.mix(col, tim.vec3(0.0), mH)  # black core

        # Glow around horizon: ring mask
        glow_d = sd_ring(q, self.bh_radius * 1.02, 0.05)
        glow = soft_mask(glow_d, self.aa * 1.6)
        glow_col = tim.vec3(0.25, 0.55, 1.0) * 0.25 + tim.vec3(1.0, 0.55, 0.15) * 0.15
        col += glow_col * glow * 0.75

        # Accretion disk (tilted ring)
        disk_q = rot2(-0.55) @ q
        r = tim.length(disk_q) + 1e-6
        ang = tim.atan2(disk_q.y, disk_q.x)

        # Spiral lines
        spiral = ang + 3.5 * tim.log(r + 1e-3) + 0.9 * tim.sin(t * 0.7)
        lanes = 0.5 + 0.5 * tim.sin(12.0 * spiral + 3.0 * fbm(disk_q * 3.0, t))
        lanes = tim.smoothstep(0.15, 0.85, lanes)

        # Doppler color shift
        dop = 0.5 + 0.5 * tim.sin(ang + 0.4 * t)
        col_hot = tim.vec3(1.0, 0.75, 0.25)
        col_cold = tim.vec3(0.20, 0.55, 1.0)
        disk_col = tim.mix(col_cold, col_hot, dop)
        disk_col *= 0.45 + 1.15 * lanes
        disk_col *= tim.smoothstep(self.bh_radius * 1.05, self.disk_r, r)  # dimming to the center

        # BACK OF THE DISC
        # Curve the coordinates more to see the disk "behind" from above and below
        p_lens_strong = gravitational_lens(p, c, self.bh_mass * 3.0)
        q_back = p_lens_strong - c
        disk_q_back = rot2(-0.55) @ q_back

        d_back = sd_ring(disk_q_back, self.disk_r, self.disk_th)
        # Mask only the "top" and "bottom" parts (where Y has a large module)
        # This creates the illusion that we are seeing the back of the disk above and below the hole
        back_mask = tim.smoothstep(0.05, 0.15, abs(disk_q_back.y)) * (1.0 - mH)
        col += disk_col * soft_mask(d_back, self.aa) * back_mask * 0.8

        # FRONT OF THE DISC
        d_front = sd_ring(disk_q, self.disk_r, self.disk_th)
        # Mask only where there is no horizon, and remove the edges a little
        front_mask = (1.0 - mH) * (1.0 - back_mask * 0.5)
        col += disk_col * soft_mask(d_front, self.aa) * front_mask

        # Photon arcs: a few bright curved strokes (capsules on a ring, animated)
        for i in ti.static(range(3)):
            a0 = t * (0.35 + 0.07 * i) + 2.1 * i
            # define short arc segment endpoints on circle
            R = self.bh_radius * (1.55 + 0.10 * i)
            p1 = tim.vec2(tim.cos(a0), tim.sin(a0)) * R
            p2 = tim.vec2(tim.cos(a0 + 0.55), tim.sin(a0 + 0.55)) * R
            # make them in disk space orientation
            pp = rot2(0.25) @ q

            dArc = sd_capsule(pp, p1, p2, 0.01 + 0.005 * i)
            mArc = soft_mask(dArc, self.aa)

            arc_col = tim.vec3(1.0, 0.95, 0.85) * (0.55 + 0.25 * i)
            col += arc_col * mArc * (1.0 - mH)

        return col

    @ti.func
    def main_image(self, uv: tim.vec2, time: ti.f32) -> tim.vec3:
        """
        Main shading function computing RGB color for each pixel.

        Pipeline:
          - Convert uv -> centered space p with aspect correction
          - Render background
          - Apply global lensing around black hole (nonlinear transform)
          - Render stars, meteors, planets in lensed space for dramatic effect
          - Render black hole on top (with its own disk patterns)
          - Tone map + gamma

        Contains required elements:
          - SDFs, f(x,t), linear+nonlinear transforms, smoothing, color mixing.
        """
        # Centered coordinates with aspect ratio correction
        p = (uv - 0.5) * 2.0
        p.x *= self.width / self.height

        # 1) Background (in original space)
        col = self.render_background(p, time)

        # 2) Apply gravitational lensing to "scene sampling coordinates"
        #    This distorts stars/nebula/planets around the black hole.
        bh_center = tim.vec2(self.bh_center.x, self.bh_center.y)
        p_lens = gravitational_lens(p, bh_center, ti.f32(self.bh_mass))

        # 3) Stars + big stars + meteors (additive)
        col += self.render_starfield(p_lens, time) * 1.15
        col += self.render_big_stars(p_lens, time) * 0.9
        col += self.render_meteors(p_lens, time) * 0.7

        # 4) Planets in lensed space (so they get slightly distorted near BH)
        col = tim.mix(col, col + self.render_planets(p_lens, time), 1.0)

        # 5) Black hole system (render in *original* p for stable center)
        col += self.render_black_hole(p, time) * 1.35

        # 6) Gentle vignette (extra smoothing layer)
        v = tim.smoothstep(1.3, 0.2, tim.length(p))
        col *= 0.75 + 0.25 * v

        # 7) Tone mapping + gamma
        col = col / (1.0 + col)  # simple Reinhard
        col = tim.pow(col, tim.vec3(1.0 / 2.2))
        return tim.clamp(col, 0.0, 1.0)


# ==================== Main Entry Point ====================

if __name__ == "__main__":
    """
    Run the shader.

    Requirements:
      - pip install taichi
      - run: python space.py

    Controls:
      - Close window to exit
    """
    print("=" * 70)
    print("Space Shader — Космос: планеты, звёзды, чёрная дыра")
    print("=" * 70)
    shader = SpaceShader(width=1400, height=800)
    shader.run(fps=60)