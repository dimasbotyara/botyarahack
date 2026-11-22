"""Общая конфигурация игры (общая для tkinter- и pygame-версий).

THEMES и ASCII_LOGOS сгенерированы из legacy/hacker-app.py, чтобы не
разъезжаться. Проверка соответствия — tests/test_gamedev.py.
"""

VERSION = '5.0.0'
TITLE = f'SECURITY EXPLOIT KIT v{VERSION}'

# ── Логическое разрешение ────────────────────────────────────────────
# Вся вёрстка считается в этих координатах, а на экран масштабируется
# целиком (см. gamedev/display.py). Так интерфейс одинаков на любом мониторе.
#
# Холст намеренно меньше «старых» 1350×850: окно упирается в размер
# монитора, поэтому чем мельче координаты вёрстки, тем крупнее всё
# выглядит на экране (шрифты, кнопки, строки). Запас по ширине нужен
# шапке: заголовок + индикаторы + режимы + кнопки ≈ 940 px.
LOGICAL_W = 1152
LOGICAL_H = 726

# ── Масштаб окна ─────────────────────────────────────────────────────
# 'auto' — подобрать под монитор. Иначе — доля от логического размера.
WINDOW_PRESETS = [
    ('auto', 'Авто (по монитору)'),
    ('0.6', 'Компактный 60%'),
    ('0.75', 'Средний 75%'),
    ('0.9', 'Крупный 90%'),
    ('1.0', 'Полный 100%'),
]
WINDOW_SCALE_DEFAULT = 'auto'
MIN_SCALE = 0.5          # меньше — текст нечитаем
MAX_SCALE = 2.0          # потолок на 4K-мониторах
AUTO_MAX_SCALE = 1.75    # авто-режим не раздувается больше этого
FIT_W = 0.94             # какую долю ширины монитора занимать
FIT_H = 0.89             # какую долю высоты (место под панель задач и рамку)

THEMES = {
    "matrix": {
        "name": "Matrix Green",
        "bg_dark": "#0a0a0a",
        "bg_medium": "#0d1a0d",
        "bg_light": "#1a331a",
        "fg_main": "#00cc00",
        "fg_dim": "#007700",
        "accent": "#00ff00",
        "border": "#1a3a1a",
        "error": "#ff4444",
        "warning": "#ffcc00",
        "data": "#44aaff",
        "matrix_fg": "#005500",
        "graph_line": "#00ff00",
        "graph_fill": "#003300",
        "danger_bg": "#1a0d0d",
        "info": "#00cccc",
        "magic": "#cc66ff",
        "muted": "#666666",
        "alert": "#ff8800",
        "glitch_alt": "#cc44cc",
        "matrix_bg": "#020502",
    },
    "cyberpunk": {
        "name": "Cyberpunk",
        "bg_dark": "#0a0510",
        "bg_medium": "#1a0d20",
        "bg_light": "#2a1a35",
        "fg_main": "#ff00ff",
        "fg_dim": "#880088",
        "accent": "#00ffff",
        "border": "#3a1a4a",
        "error": "#ff3333",
        "warning": "#ffff00",
        "data": "#00ffff",
        "matrix_fg": "#440066",
        "graph_line": "#ff00ff",
        "graph_fill": "#330033",
        "danger_bg": "#1a0510",
        "info": "#00ffff",
        "magic": "#ff66ff",
        "muted": "#775577",
        "alert": "#ffaa00",
        "glitch_alt": "#8800aa",
        "matrix_bg": "#05020a",
    },
    "blood": {
        "name": "Blood Red",
        "bg_dark": "#0a0505",
        "bg_medium": "#1a0808",
        "bg_light": "#2a1010",
        "fg_main": "#ff3333",
        "fg_dim": "#882222",
        "accent": "#ff0000",
        "border": "#3a1515",
        "error": "#ff0000",
        "warning": "#ff8800",
        "data": "#ff6666",
        "matrix_fg": "#330000",
        "graph_line": "#ff0000",
        "graph_fill": "#330000",
        "danger_bg": "#1a0505",
        "info": "#ff8888",
        "magic": "#ff66cc",
        "muted": "#775555",
        "alert": "#ffaa00",
        "glitch_alt": "#aa2222",
        "matrix_bg": "#0a0202",
    },
    "ocean": {
        "name": "Ocean Blue",
        "bg_dark": "#050a10",
        "bg_medium": "#0a1520",
        "bg_light": "#102535",
        "fg_main": "#00aaff",
        "fg_dim": "#005588",
        "accent": "#00ddff",
        "border": "#153045",
        "error": "#ff4444",
        "warning": "#ffcc00",
        "data": "#88ddff",
        "matrix_fg": "#002244",
        "graph_line": "#00aaff",
        "graph_fill": "#001133",
        "danger_bg": "#0a0510",
        "info": "#00ccff",
        "magic": "#aa88ff",
        "muted": "#557788",
        "alert": "#ffaa44",
        "glitch_alt": "#3388cc",
        "matrix_bg": "#02050a",
    },
    "amber": {
        "name": "Retro Amber",
        "bg_dark": "#0a0800",
        "bg_medium": "#1a1205",
        "bg_light": "#2a2010",
        "fg_main": "#ffaa00",
        "fg_dim": "#885500",
        "accent": "#ffcc00",
        "border": "#3a2a10",
        "error": "#ff4444",
        "warning": "#ffff00",
        "data": "#ffdd88",
        "matrix_fg": "#332200",
        "graph_line": "#ffaa00",
        "graph_fill": "#332200",
        "danger_bg": "#1a0f00",
        "info": "#ffcc66",
        "magic": "#ff88cc",
        "muted": "#776644",
        "alert": "#ff8800",
        "glitch_alt": "#cc8844",
        "matrix_bg": "#0a0700",
    },
}

# ── ASCII-логотипы для сплэша/шапки ──────────────────────────────────
ASCII_LOGOS = [
    '\n\t██╗  ██╗ █████╗  ██████╗██╗  ██╗███████╗██████╗\n\t██║  ██║██╔══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗\n\t███████║███████║██║     █████╔╝ █████╗  ██████╔╝\n\t██╔══██║██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗\n\t██║  ██║██║  ██║╚██████╗██║  ██╗███████╗██║  ██║\n\t╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝\n\t',
    '\n\t  ___ ___ ___ _  _ ___ ___ _____   __\n\t / __| __/ __| || | _ \\_ _|_   _\\ \\/ /\n\t \\__ \\ _| (__| __ |   /| |  | |  >  <\n\t |___/___\\___|_||_|_|_\\___| |_| /_/\\_\\\n\t',
]
