"""The MIKO wordmark, as `.site-footer__wordmark` sets it: extra bold, barely
tracked, white, closed by a yellow full stop.

Shared by the social cards and the weekly timetable sheet so the two cannot
drift apart. Kept out of `cards.cards`, whose cairosvg import wants a Cairo
library that has no business being loaded to answer a request.
"""

LETTERS = "MIKO"
DOT = "."
WEIGHT = 'ExtraBold'
TRACKING_EM = 0.01
INK = '#FFFFFF'
DOT_INK = '#F2B544'


def draw_tracked(draw, position, text, font, fill, tracking, anchor='ls') -> float:
    """Letter-spaced text, which Pillow has no setting for. Returns its width."""
    x, y = position
    for character in text:
        draw.text((x, y), character, font=font, fill=fill, anchor=anchor)
        x += font.getlength(character) + tracking
    return x - position[0]


def _baseline(top, font, anchor: str) -> float:
    if anchor[1] == 's':
        return top
    ascent, _ = font.getmetrics()
    # A `t` anchor measures a glyph's own ink, so resolving it per glyph would
    # lift the full stop to the cap line instead of leaving it on the floor.
    ink_top = font.getbbox(LETTERS)[1] if anchor[1] == 't' else 0
    return top + ascent - ink_top


def draw_wordmark(draw, position, font, *, ink=INK, dot_ink=DOT_INK, anchor='la') -> float:
    """Stamp "MIKO." at `position`; returns how wide it turned out."""
    x, baseline = position[0], _baseline(position[1], font, anchor)
    width = draw_tracked(draw, (x, baseline), LETTERS, font, ink, font.size * TRACKING_EM)
    draw.text((x + width, baseline), DOT, font=font, fill=dot_ink, anchor='ls')
    return width + font.getlength(DOT)
