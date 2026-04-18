"""
Домашнее задание по курсу Компьютерный практикум 2025, модуль 3, задание 1
Тема: Компьютерная графика (шейдеры)

=== ДЕКОМПОЗИЦИЯ АНИМАЦИИ ===

Задача: Повторить анимацию "плотная сетка из кругов (колец) на чёрном фоне"
Каждый круг имеет:
  - яркую цветную окантовку (кольцо)
  - более тёмную/приглушённую внутреннюю часть
  - случайные размеры и цвета
  - равномерное расположение по сетке

---

### 1. ЭЛЕМЕНТЫ АНИМАЦИИ

#### 1.1. Функция сетки (Grid Pattern)
Элемент: Бесконечная сетка точек, каждая точка - центр круга.
Реализация: domain repetition (повторение области)
Формула: p_grid = fract(p / spacing + 0.5) * spacing - 0.5 * spacing
Graphtoy: https://www.graphtoy.com/?f1(x,t)=fract(x/0.3+0.5)*0.3-0.15&v1=true&f2(x,t)=x&v2=false&f3(x,t)=&v3=false&f4(x,t)=&v4=false&f5(x,t)=&v5=false&f6(x,t)=&v6=false&grid=1&coords=0,0,12.5

#### 1.2. Функция круга (Circle SDF)
Элемент: Расстояние до круга заданного радиуса.
Формула: d_circle = length(p) - radius
Graphtoy: https://graphtoy.com/?f1(x,t)=abs(t-0.1)&v1=true&f2(x,t)=&v2=false&f3(x,t)=&v3=false&f4(x,t)=&v4=false&f5(x,t)=&v5=false&f6(x,t)=&v6=false&grid=1&coords=0,0,12.5

#### 1.3. Функция кольца (Ring)
Элемент: Кольцо - это область между двумя радиусами.
Реализация: abs(length(p) - radius) - thickness/2
Graphtoy: https://graphtoy.com/?f1(x,t)=abs(t-0.1)-0.02&v1=true&f2(x,t)=&v2=false&f3(x,t)=&v3=true&f4(x,t)=&v4=false&f5(x,t)=&v5=true&f6(x,t)=&v6=false&grid=1&coords=0,0,12.5

#### 1.4. Функция псевдослучайного числа (Hash)
Элемент: Генерация случайного числа от 0 до 1 на основе координат.
Формула: hash = fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123)
Graphtoy: https://www.graphtoy.com/?f1(x,t)=fract(sin(x*127.1+311.7)*43758.5453)&v1=true&f2(x,t)=&v2=false&f3(x,t)=&v4=false&f5(x,t)=&v6=false&grid=1&coords=0,0,12.5

#### 1.5. Функция сглаживания (Smoothstep)
Элемент: Плавный переход для антиалиасинга и мягких границ.
Формула: t = clamp((x - edge0) / (edge1 - edge0), 0, 1); return t*t*(3-2*t)
Graphtoy: https://graphtoy.com/?f1(x,t)=max(0,%20min((x-0.1)/(0.2-0.1),1))%5E2%20*%20(3%20-%202%20*%20max(0,%20min((x-0.1)/(0.2-0.1),1)))&v1=true&f2(x,t)=&v2=false&f3(x,t)=&v3=true&f4(x,t)=&v4=false&f5(x,t)=&v5=true&f6(x,t)=&v6=false&grid=1&coords=0,0,12.5

#### 1.6. Функция цвета (Color Palette)
Элемент: Выбор цвета из палитры по индексу с плавным смешиванием.
Реализация: palette[idx % N] или mix(palette[i], palette[i+1], fract(idx))
Graphtoy: https://graphtoy.com/?f1(x,t)=fract(x*3.0)&v1=true&f2(x,t)=&v2=false&f3(x,t)=&v3=true&f4(x,t)=&v4=false&f5(x,t)=&v5=true&f6(x,t)=&v6=false&grid=1&coords=0,0,12.5
Элемент: Зависимость от времени для пульсации/мерцания.
Формулы:
  - Пульсация радиуса: radius = base_radius * (1.0 + 0.1 * sin(time * 2.0 + phase))
  - Мерцание яркости: brightness = 0.8 + 0.2 * sin(time * 3.0 + phase)
Graphtoy: https://graphtoy.com/?f1(x,t)=0.1*(1+0.1*sin(t*2))&v1=true&f2(x,t)=0.8+0.2*sin(t*3)&v2=true&f3(x,t)=&v3=true&f4(x,t)=&v4=false&f5(x,t)=&v5=true&f6(x,t)=&v6=false&grid=1&coords=0,0,12.5

---

### 2. ВЗАИМОСВЯЗИ ЭЛЕМЕНТОВ

1. **Сетка → Круги**:
   - Координаты пикселя (p) преобразуются в координаты сетки через domain repetition
   - Для каждой ячейки сетки вычисляется один круг

2. **Круг → Кольцо**:
   - SDF круга используется для создания кольца через операцию: abs(d_circle) - thickness/2
   - Внутри кольца (d < 0) - тёмная область, снаружи (d > 0) - фон

3. **Координаты → Hash → Цвет и Размер**:
   - Для каждой ячейки сетки вычисляется хэш от её индексов (i, j)
   - Хэш определяет:
     * индекс цвета из палитры
     * базовый радиус круга
     * фазу анимации (чтобы пульсации были разными)

4. **Время → Анимация**:
   - time передаётся в функции пульсации
   - Модифицирует радиус и яркость в зависимости от фазы

5. **SDF → Цвет**:
   - Значение SDF (d) используется для:
     * определения, где находится пиксель (внутри/снаружи кольца)
     * плавного перехода цветов через smoothstep (антиалиасинг)
   - Результат: яркое цветное кольцо на границе, тёмный центр

---

### 3. ПРЕДЛАГАЕМАЯ РЕАЛИЗАЦИЯ

#### Структура кода:

1. **Инициализация**:
   - Создать поле пикселей (pixel field)
   - Определить палитру цветов (PALETTE_NEON)
   - Задать параметры: spacing (шаг сетки), base_radius, ring_thickness

2. **Функция main_image(uv, time)**:
   a. Преобразовать uv в координаты в пространстве [-1, 1] с сохранением пропорций
   b. Применить domain repetition: p_grid = op_repeat(p, spacing)
   c. Вычислить индекс ячейки: cell_id = floor((p + spacing*0.5) / spacing)
   d. Получить хэш от cell_id: h = hash21(cell_id)
   e. Определить параметры круга:
      - radius = mix(min_radius, max_radius, h)
      - color_idx = floor(h * palette_size)
      - phase = h * 6.28 (0..2π)
   f. Вычислить SDF кольца: d = abs(length(p_grid) - radius) - thickness/2
   g. Применить анимацию:
      - radius_anim = radius * (1.0 + 0.05 * sin(time * 2.0 + phase))
      - brightness_factor = 0.8 + 0.2 * sin(time * 3.0 + phase)
   h. Вычислить цвет:
      - base_color = get_palette_color(color_idx, PALETTE_NEON)
      - ring_color = base_color * brightness_factor * 2.0 (яркая окантовка)
      - inner_color = base_color * 0.3 (приглушённый центр)
   i. Смешать цвета по SDF с smoothstep:
      - t = smoothstep(anti_alias_width, -anti_alias_width, d)
      - color = mix(inner_color, ring_color, t)
   j. Если d > 0 (за кольцом) - чёрный фон
   k. Вернуть цвет

3. **Запуск**:
   - Создать экземпляр шейдера
   - Запустить цикл рендеринга

---

### 4. ГРАФИКИ НА GRAPHTOY.COM

Все ключевые функции представлены на graphtoy.com:
- Сетка (fract-based repetition): ссылка выше
- Круг (length-based SDF): ссылка выше
- Кольцо (abs(length - r)): ссылка выше
- Hash-функция: ссылка выше
- Smoothstep: ссылка выше
- Пульсация (sin(time)): ссылка выше
- Смешивание цветов (mix): ссылка выше

---

### 5. ДОПОЛНИТЕЛЬНЫЕ ДЕТАЛИ

- **Антиалиасинг**: используем smoothstep с шириной ~2-3 пикселя
- **Пропорции**: сохраняем aspect ratio, чтобы круги не были эллипсами
- **Оптимизация**: все вычисления в ti.func, рендер в ti.kernel
- **Документация**: все функции/методы/классы имеют docstrings

---

### REFERENCES (Ссылки на ресурсы):
- iquilezles.org - SDF и шейдеры
- graphtoy.com - визуализация функций
- taichi-lang.org - документация Taichi
- Палитры: www.colorhunt.co, www.learnui.design

"""

import taichi as ti
import taichi.math as tim
from gui import BaseShader
from core import *
from colors import *
from sdf import *


# ==================== Circle Grid Shader with Column Motion ====================

@ti.data_oriented
class CircleGridShader(BaseShader):
    """
    Shader rendering a dense grid of colorful rings (circles with outlines).
    Each ring has a bright colored border and a darker interior.
    NEIGHBORING COLUMNS MOVE DOWN AT DIFFERENT RANDOM SPEEDS.
    """

    def __init__(self, width: int = 800, height: int = 800):
        """Initialize the shader with default parameters."""
        super().__init__(width, height, title="Circle Grid Shader - Moving Columns")

        # Shader parameters
        self.spacing = 0.25  # Grid cell size (in normalized coordinates)
        self.base_radius = 0.06  # Base circle radius
        self.radius_variation = 0.05  # How much radius can vary
        self.ring_thickness = 0.015  # Thickness of the bright ring
        self.anti_alias_width = 0.005  # For smooth edges

        # Animation parameters
        self.pulse_speed = 1.5  # Speed of radius pulsing
        self.flicker_speed = 2.0  # Speed of brightness flickering
        self.pulse_amplitude = 0.1  # How much radius changes
        self.flicker_amplitude = 0.2  # How much brightness changes
        self.inner_pulse_speed = 2.8  # Speed of inner disk pulsing
        self.inner_pulse_amplitude = 0.35  # Radius modulation of inner disk

        # COLUMN MOTION parameters
        self.column_speed_range_min = 0.3  # Min speed for columns moving down
        self.column_speed_range_max = 1.0  # Max speed for columns moving down

    @ti.func
    def get_column_speed(self, column_id: ti.f32) -> ti.f32:
        """
        Generate random speed for each column based on column index.
        Uses hash function to ensure consistent speeds per column.

        Args:
            column_id: Column index (x-coordinate of cell)

        Returns:
            Speed value between min and max range
        """
        # Create hash from column_id using fract and sin
        h = tim.fract(tim.sin(column_id * 127.1 + 311.7) * 43758.5453123)
        # Map to speed range
        return self.column_speed_range_min + h * (self.column_speed_range_max - self.column_speed_range_min)

    @ti.func
    def main_image(self, uv: tim.vec2, time: ti.f32) -> tim.vec3:
        """
        Main shader function - computes color for each pixel.

        Columns move downward at different random speeds.

        Args:
            uv: Normalized screen coordinates [0, 1] (origin bottom-left)
            time: Time in seconds since start

        Returns:
            RGB color for this pixel
        """
        # Convert UV to centered coordinates [-1, 1] with aspect ratio correction
        p = (uv - 0.5) * 2.0
        p.x *= self.width / self.height  # Correct aspect ratio

        # Compute cell index BEFORE repetition to know which column we're in
        original_cell_id = tim.floor((p + tim.vec2(self.spacing * 0.5)) / self.spacing)

        # Get random speed for this column (based on column index - X coordinate)
        column_id = original_cell_id.x
        column_speed = self.get_column_speed(column_id)

        # Continuous downward motion without modulo reset.
        # Positive offset in sampling space produces downward visual motion on screen.
        # This also avoids visible "random refresh" jumps caused by discontinuous wrap.
        vertical_offset = time * column_speed

        # Apply offset to the Y coordinate before grid repetition
        p_offset_y = p.y + vertical_offset

        # Create offset position for grid calculation
        p_offset = tim.vec2(p.x, p_offset_y)

        # Apply domain repetition to create grid with offset Y
        p_grid = op_repeat(p_offset, tim.vec2(self.spacing))

        # Compute cell index from offset position
        cell_id = tim.floor((p_offset + tim.vec2(self.spacing * 0.5)) / self.spacing)

        # Generate pseudo-random values from cell index
        h1 = hash21(cell_id)  # Main hash [0, 1)
        h2 = hash21(cell_id + tim.vec2(37.0, 17.0))  # Secondary hash for variation

        # Circle parameters based on hash
        radius = self.base_radius + h1 * self.radius_variation
        color_idx = h1 * 6.0  # Map to palette index (0-6 for 7-color rainbow)
        phase = h2 * 6.28318530718  # Random phase [0, 2π)

        # Animation: pulsing radius and flickering brightness
        radius_anim = radius * (1.0 + self.pulse_amplitude * tim.sin(time * self.pulse_speed + phase))
        brightness_factor = 0.8 + self.flicker_amplitude * tim.sin(time * self.flicker_speed + phase)

        # Compute SDF for ring (circle with thickness)
        d_center = tim.length(p_grid)
        d_ring = abs(d_center - radius_anim) - self.ring_thickness * 0.5

        # Inner pulse disk: separate radius animation inside the ring
        inner_base_radius = radius_anim * 0.58
        inner_radius = inner_base_radius * (
                1.0 + self.inner_pulse_amplitude * tim.sin(time * self.inner_pulse_speed + phase + h1 * 6.28318530718)
        )
        inner_radius = max(inner_radius, self.ring_thickness * 0.25)
        d_inner = d_center - inner_radius

        # Get base color from palette
        base_color = get_palette_color_blend(color_idx, PALETTE_RAINBOW)

        # Define colors for ring and interior
        ring_color = base_color * brightness_factor * 1.5  # Bright, saturated
        inner_color = base_color * 0.25  # Dimmed interior
        pulse_color = base_color * (0.55 + 0.35 * brightness_factor)
        bg_color = tim.vec3(0.0)  # Black background

        # Ring mask (1 on ring band, 0 elsewhere)
        ring_mask = smoothstep(
            self.anti_alias_width,
            -self.anti_alias_width,
            d_ring
        )

        # Base fill for full circle interior (inside animated radius)
        circle_mask = smoothstep(self.anti_alias_width, -self.anti_alias_width, d_center - radius_anim)
        circle_color = mix(bg_color, inner_color, circle_mask)
        circle_color = mix(circle_color, ring_color, ring_mask)

        # Add pulsing inner disk with anti-aliased edge
        pulse_mask = smoothstep(self.anti_alias_width, -self.anti_alias_width, d_inner)
        circle_color = mix(circle_color, pulse_color, pulse_mask)

        return circle_color


# ==================== Main Entry Point ====================

if __name__ == "__main__":
    """
    Main entry point - create and run the shader.

    NEW FEATURE: Neighboring columns move downward at different random speeds!

    Requirements:
    - Taichi installed: pip install taichi
    - GPU recommended for real-time performance

    Controls:
    - Close window to exit
    """
    print("=" * 60)
    print("Circle Grid Shader - WITH COLUMN MOTION")
    print("=" * 60)
    print("\n✨ NEW: Neighboring columns move DOWN at different random speeds!")
    print("   Each vertical column has its own speed, creating a flowing waterfall effect.")
    print("\nDecomposition analysis included in docstring at top of file.")
    print("Graphtoy.com links provided for all key functions.\n")

    # Create shader instance
    shader = CircleGridShader(width=1400, height=800)

    # Run rendering loop at 60 FPS
    print("Starting render loop...")
    print("Columns flowing downward with random speeds...")
    print("Close the window to exit.")
    print("-" * 60)
    shader.run(fps=60)

    print("\nShader terminated successfully.")
