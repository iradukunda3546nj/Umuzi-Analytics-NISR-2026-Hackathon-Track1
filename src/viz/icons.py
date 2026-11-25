"""Line icons drawn for Umuzi Analytics (24 x 24 grid, stroke = currentColor).

Hand-made simple geometry, no third-party icon set, so there is no licence to
track. `icon(name, size)` returns inline SVG markup.
"""
from __future__ import annotations

_P = {
    "target": "<circle cx='12' cy='12' r='9'/><circle cx='12' cy='12' r='5'/><circle cx='12' cy='12' r='1.5' fill='currentColor'/>",
    "repeat": "<rect x='3' y='5' width='18' height='16' rx='2'/><path d='M3 10h18M8 3v4M16 3v4'/><path d='M8 15l2 2 4-4'/>",
    "seed": "<path d='M12 21v-9'/><path d='M12 12c0-4 3-7 8-7 0 5-3 7-8 7z'/><path d='M12 15c0-3-2.5-5-7-5 0 4 2.5 5 7 5z'/><path d='M7 21h10'/>",
    "bag": "<path d='M7 6h10l2 15H5L7 6z'/><path d='M9 6V4h6v2'/><path d='M9 12h6M9 15.5h6'/>",
    "megaphone": "<path d='M3 10v4h3l8 5V5L6 10H3z'/><path d='M17 9a4 4 0 010 6'/><path d='M7 14l1.5 6h3L10 15.5'/>",
    "question": "<circle cx='12' cy='12' r='9'/><path d='M9.5 9.5a2.5 2.5 0 015 .3c0 1.7-2.5 2.2-2.5 4'/><circle cx='12' cy='17' r='.9' fill='currentColor'/>",
    "check": "<circle cx='12' cy='12' r='9'/><path d='M8 12.5l3 3 5-6'/>",
    "cross": "<circle cx='12' cy='12' r='9'/><path d='M9 9l6 6M15 9l-6 6'/>",
    "dash": "<circle cx='12' cy='12' r='9'/><path d='M8 12h8'/>",
    "rain": "<path d='M7 15a4 4 0 01.5-8 5 5 0 019.5 1.5A3.5 3.5 0 0117 15H7z'/><path d='M8 18l-1 2M12 18l-1 2M16 18l-1 2'/>",
    "clock": "<circle cx='12' cy='12' r='9'/><path d='M12 7v5l3 2'/>",
    "coin": "<ellipse cx='12' cy='7' rx='7' ry='3'/><path d='M5 7v5c0 1.7 3 3 7 3s7-1.3 7-3V7'/><path d='M5 12v5c0 1.7 3 3 7 3s7-1.3 7-3v-5'/>",
    "soil": "<path d='M3 9h18M3 14h18M3 19h18'/><path d='M12 9V4M12 4l-2 2M12 4l2 2'/>",
    "slope": "<path d='M3 20l7-11 4 6 2-3 5 8H3z'/><path d='M14 7l1.5-2.5L17 7'/>",
    "field": "<path d='M3 20l4-10h10l4 10H3z'/><path d='M12 10v10M8 15h8'/>",
    "store": "<path d='M4 10h16v10H4z'/><path d='M3 10l2-6h14l2 6'/><path d='M10 20v-5h4v5'/>",
    "share": "<circle cx='6' cy='12' r='2.5'/><circle cx='18' cy='6' r='2.5'/><circle cx='18' cy='18' r='2.5'/><path d='M8.2 11l7.6-3.8M8.2 13l7.6 3.8'/>",
    "map": "<path d='M9 4L3 6v14l6-2 6 2 6-2V4l-6 2-6-2z'/><path d='M9 4v14M15 6v14'/>",
    "chat": "<path d='M4 5h16v11H9l-5 4V5z'/><path d='M8 9.5h8M8 12.5h5'/>",
    "arrow": "<path d='M5 12h14M13 6l6 6-6 6'/>",
    "pin": "<path d='M12 21s-6-5.5-6-11a6 6 0 0112 0c0 5.5-6 11-6 11z'/><circle cx='12' cy='10' r='2.2'/>",
    "data": "<ellipse cx='12' cy='6' rx='7' ry='2.5'/><path d='M5 6v12c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5V6'/><path d='M5 12c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5'/>",
}


def icon(name: str, size: int = 24, stroke: float = 1.8, cls: str = "") -> str:
    return (f"<svg class='umz-ic {cls}' width='{size}' height='{size}' viewBox='0 0 24 24' fill='none' "
            f"stroke='currentColor' stroke-width='{stroke}' stroke-linecap='round' stroke-linejoin='round' "
            f"aria-hidden='true'>{_P[name]}</svg>")
