"""One week of the calendar, drawn as a shareable PNG.

The calendar on /kolo/ is a web page, and a web page cannot be pasted into a
Discord announcement or an Instagram post. This draws the same week - seminars,
multi-day events with registration, olympiad stages - as one portrait sheet in
the site's colours, carrying only the time, the theme and the tutors, since
anything more stops being legible once the sheet is a thumbnail on a phone.

The sheet grows downwards with the week rather than squeezing a busy one into a
fixed frame. The bytes are the cached artefact, so the payload behind them is
built fresh: keeping both would hold one week twice, as JSON and as pixels.
"""
import hashlib
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
from io import BytesIO

from babel.dates import format_date
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from cards import brand
from mikosite.dates import format_day_range, seconds_until_next_midnight

from .calendar_data import build_calendar_payload, get_calendar_version


# Public sheet visibility.
WEEKS_BEHIND = 1
WEEKS_AHEAD = 2
WEEK_IMAGE_MAX_TTL = 900  # as for the calendar payload


def week_start_of(day) -> date:
    """The Monday of the week `day` falls in."""
    return day - timedelta(days=day.weekday())


def week_bounds(week_start) -> tuple:
    return week_start, week_start + timedelta(days=6)


def offered_week_starts(today=None) -> list:
    """The Mondays the public sheet is kept for, earliest first."""
    this_week = week_start_of(today or timezone.localdate())
    return [this_week + timedelta(weeks=offset) for offset in range(-WEEKS_BEHIND, WEEKS_AHEAD + 1)]


# --------------------------------------------------------------------------- #
# Palette and metrics
# --------------------------------------------------------------------------- #

SCALE = 2


def px(units: int) -> int:
    """Layout units in device pixels."""
    return units * SCALE


BG = '#06313E'
SURFACE = '#074A59'
RULE = '#0C5A6D'
INK = '#FFFFFF'
INK_MUTED = '#9FC0CC'
ACCENT = '#F2B544'
ALERT = '#F24535'

FONT_PATH = settings.BASE_DIR / 'static' / 'fonts' / 'RubikVariable.ttf'
LOGO_PATH = settings.BASE_DIR / 'static' / 'LOGO_MONO.png'
ELLIPSIS = '…'

WIDTH = px(1080)
PAD_X = px(56)
CONTENT_WIDTH = WIDTH - 2 * PAD_X
MIN_HEIGHT = px(1080)  # a quiet week still comes out square, not a banner
PAGE_BOTTOM = px(44)

HEADER_HEIGHT = px(330)
WATERMARK_SIZE = px(520)
WATERMARK_OPACITY = 0.09

SECTION_HEIGHT = px(74)
BAND_HEIGHT = px(84)
CARD_RADIUS = px(18)
CARD_BAR = px(8)
CARD_PAD_X = px(30)
CARD_PAD_Y = px(18)
CARD_GAP = px(12)
TIME_COLUMN = px(142)
LINE_TITLE = px(40)
LINE_META = px(30)
META_GAP = px(4)
SECOND_LINE = LINE_TITLE + META_GAP
LEGEND_LINE = px(38)
FOOTER_HEIGHT = px(88)
EMPTY_HEIGHT = px(220)

# Whatever does not fit is counted in a line of its own rather than dropped.
MAX_EVENTS = 30


class FontBook:
    """Rubik at the sizes and weights one sheet needs.

    Built per render: a `FreeTypeFont` wraps a single FreeType face, and two
    workers drawing sheets at once must not share one.
    """

    _file_bytes = None

    def __init__(self):
        if FontBook._file_bytes is None:
            FontBook._file_bytes = FONT_PATH.read_bytes()
        self._faces = {}

    def __call__(self, size: int, weight: str = 'Regular') -> ImageFont.FreeTypeFont:
        face = self._faces.get((size, weight))
        if face is None:
            face = ImageFont.truetype(BytesIO(FontBook._file_bytes), size)
            face.set_variation_by_name(weight)
            self._faces[(size, weight)] = face
        return face


def watermark(size: int, opacity: float) -> Image.Image:
    """The MIKO star as a pale tint: the file itself is black on transparent."""
    mark = Image.open(LOGO_PATH).convert('RGBA').resize((size, size), Image.LANCZOS)
    tinted = Image.new('RGBA', (size, size), (255, 255, 255, 255))
    tinted.putalpha(mark.getchannel('A').point(lambda value: int(value * opacity)))
    return tinted


def _channels(color: str) -> tuple:
    return tuple(int(color[index:index + 2], 16) for index in (1, 3, 5))


def _luminance(color: str) -> float:
    def linear(channel):
        ratio = channel / 255
        return ratio / 12.92 if ratio <= 0.03928 else ((ratio + 0.055) / 1.055) ** 2.4

    red, green, blue = (linear(channel) for channel in _channels(color))
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _contrast(first: str, second: str) -> float:
    lighter, darker = sorted((_luminance(first), _luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def _lift(color: str, amount: float) -> str:
    return '#%02X%02X%02X' % tuple(
        round(channel + (255 - channel) * amount) for channel in _channels(color)
    )


def readable_accent(color) -> str:
    """A group colour that still reads as a stripe on a dark card.

    Group colours are chosen to sit on the white calendar, and the default one
    is the card colour itself, so each is lifted only as far as it has to be.
    """
    if not color:
        return INK_MUTED
    lifted = color
    for _ in range(8):
        if _contrast(lifted, SURFACE) >= 2.0:
            break
        lifted = _lift(lifted, 0.18)
    return lifted


def _clip(text: str, font, max_width: int) -> str:
    if font.getlength(text) <= max_width:
        return text
    trimmed = text
    while trimmed and font.getlength(trimmed.rstrip() + ELLIPSIS) > max_width:
        trimmed = trimmed[:-1]
    return trimmed.rstrip() + ELLIPSIS


def _wrap(text: str, font, max_width: int, max_lines: int) -> list:
    lines = []
    for word in text.split():
        if lines and font.getlength(f"{lines[-1]} {word}") <= max_width:
            lines[-1] = f"{lines[-1]} {word}"
        else:
            lines.append(word)
    if len(lines) > max_lines:
        lines = lines[:max_lines - 1] + [' '.join(lines[max_lines - 1:])]
    return [_clip(line, font, max_width) for line in lines] or ['']


def _largest_fitting(sizes, text: str, fonts, weight: str, max_width: int):
    for size in sizes:
        font = fonts(size, weight)
        if font.getlength(text) <= max_width:
            return font
    return fonts(sizes[-1], weight)


def week_label(week_start, locale=settings.BABEL_LOCALE) -> str:
    """"17-23 sierpnia 2026", with both years spelled out across a new year."""
    start, end = week_bounds(week_start)
    span = format_day_range(start, end, locale=locale)
    return span if start.year != end.year else f"{span} {end.year}"


def _day_label(day, locale=settings.BABEL_LOCALE) -> str:
    weekday = format_date(day, format='EEEE', locale=locale)
    return f"{weekday} · {format_date(day, format='d MMMM', locale=locale)}".upper()


def _polish_meeting_unit(count: int, locale=settings.BABEL_LOCALE) -> str:
    plural_form = locale.plural_form(count)
    if plural_form == 'one':
        return 'spotkanie'
    if plural_form == 'few':
        return 'spotkania'
    return 'spotkań'


# --------------------------------------------------------------------------- #
# Blocks
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Block:
    """A horizontal slice of the sheet: how tall it is, and how to paint it.

    A block closes over the lines it wrapped to work out its height, so the
    measuring and the painting cannot drift apart.
    """

    height: int
    paint: Callable


class Sheet:
    __slots__ = ('image', 'draw')

    def __init__(self, image):
        self.image = image
        self.draw = ImageDraw.Draw(image)


def _draw_card(draw, top, bottom, accent=None):
    """A rounded panel, optionally striped down its left edge."""
    draw.rounded_rectangle((PAD_X, top, WIDTH - PAD_X, bottom),
                           radius=CARD_RADIUS, fill=accent or SURFACE)
    if accent:
        draw.rounded_rectangle((PAD_X + CARD_BAR, top, WIDTH - PAD_X, bottom), radius=CARD_RADIUS,
                               fill=SURFACE, corners=(False, True, True, False))


def _header_block(week_start, fonts) -> Block:
    headline = week_label(week_start)
    mark = watermark(WATERMARK_SIZE, WATERMARK_OPACITY)

    def paint(sheet, top):
        draw = sheet.draw
        sheet.image.paste(mark, (WIDTH - px(400), top - px(60)), mark)

        wordmark = fonts(px(66), brand.WEIGHT)
        stamp_width = brand.draw_wordmark(draw, (PAD_X, top + px(46)), wordmark, ink=INK)
        byline_x = PAD_X + round(stamp_width) + px(22)
        byline = fonts(px(23))
        draw.text((byline_x, top + px(58)), "Matematyczne Internetowe",
                  font=byline, fill=INK_MUTED, anchor='la')
        draw.text((byline_x, top + px(88)), "Koło Olimpijskie",
                  font=byline, fill=INK_MUTED, anchor='la')

        brand.draw_tracked(draw, (PAD_X, top + px(168)), "PLAN SPOTKAŃ",
                           fonts(px(24), 'SemiBold'), ACCENT, px(4), anchor='la')

        title_font = _largest_fitting([px(56), px(48), px(40)], headline, fonts, 'SemiBold', CONTENT_WIDTH)
        draw.text((PAD_X, top + px(210)), headline, font=title_font, fill=INK, anchor='la')

        bar_top = top + px(288)
        draw.rounded_rectangle((PAD_X, bar_top, PAD_X + px(76), bar_top + px(6)),
                               radius=px(3), fill=ACCENT)

    return Block(HEADER_HEIGHT, paint)


def _section_block(label: str, fonts, *, today_marker=False) -> Block:
    def paint(sheet, top):
        draw = sheet.draw
        font = fonts(px(25), 'SemiBold')
        text_top = top + px(26)
        draw.text((PAD_X, text_top), label, font=font, fill=ACCENT, anchor='la')
        rule_x = PAD_X + round(font.getlength(label)) + px(20)

        if today_marker:
            pill_font = fonts(px(20), 'Bold')
            pill_width = round(pill_font.getlength("DZIŚ")) + px(26)
            draw.rounded_rectangle((rule_x, text_top - px(3), rule_x + pill_width, text_top + px(31)),
                                   radius=px(15), fill=ACCENT)
            draw.text((rule_x + pill_width // 2, text_top + px(14)), "DZIŚ",
                      font=pill_font, fill=BG, anchor='mm')
            rule_x += pill_width + px(20)

        rule_y = text_top + px(15)
        if rule_x < WIDTH - PAD_X:
            draw.rectangle((rule_x, rule_y, WIDTH - PAD_X, rule_y + px(2)), fill=RULE)

    return Block(SECTION_HEIGHT, paint)


def _band_block(entry: dict, fonts) -> Block:
    """A registration event or an olympiad stage: it owns days, not an hour."""
    accent = ALERT if entry.get('kind') == 'registration_event' else ACCENT
    range_font = fonts(px(24))
    title_font = fonts(px(29), 'SemiBold')
    range_label = entry.get('date_range') or ''
    title_room = CONTENT_WIDTH - CARD_BAR - 2 * CARD_PAD_X - round(range_font.getlength(range_label)) - px(24)
    title = _clip(entry.get('title') or '', title_font, max(title_room, px(80)))

    def paint(sheet, top):
        draw = sheet.draw
        bottom = top + BAND_HEIGHT - CARD_GAP
        _draw_card(draw, top, bottom, accent)
        middle = (top + bottom) // 2
        draw.text((PAD_X + CARD_BAR + CARD_PAD_X, middle), title, font=title_font, fill=INK, anchor='lm')
        draw.text((WIDTH - PAD_X - CARD_PAD_X, middle), range_label,
                  font=range_font, fill=INK_MUTED, anchor='rm')

    return Block(BAND_HEIGHT, paint)


def _seminar_block(seminar: dict, fonts) -> Block:
    group = seminar.get('group') or {}
    accent = readable_accent(group.get('color'))

    starts = seminar.get('time') or ''
    _, _, ends = (seminar.get('time_label') or '').partition('-')
    end_label = f"-{ends}" if ends else ''
    tutors = ' · '.join(seminar.get('tutors') or [])

    title_font = fonts(px(33), 'SemiBold')
    start_font = fonts(px(34), 'SemiBold')
    # One face for both second lines.
    meta_font = fonts(px(25))
    body_x = PAD_X + CARD_BAR + CARD_PAD_X + TIME_COLUMN
    body_width = WIDTH - PAD_X - CARD_PAD_X - body_x
    title_lines = _wrap(seminar.get('theme') or '', title_font, body_width, 2)
    meta = _clip(tutors, meta_font, body_width) if tutors else ''

    body_height = len(title_lines) * LINE_TITLE + (META_GAP + LINE_META if meta else 0)
    time_height = LINE_TITLE + (META_GAP + LINE_META if end_label else 0)
    height = 2 * CARD_PAD_Y + max(body_height, time_height) + CARD_GAP

    def paint(sheet, top):
        draw = sheet.draw
        _draw_card(draw, top, top + height - CARD_GAP, accent)

        time_x = PAD_X + CARD_BAR + CARD_PAD_X
        text_top = top + CARD_PAD_Y
        draw.text((time_x, text_top), starts, font=start_font, fill=INK, anchor='la')
        if end_label:
            right_edge = time_x + max(start_font.getlength(starts), meta_font.getlength(end_label))
            draw.text((right_edge, text_top + SECOND_LINE), end_label,
                      font=meta_font, fill=INK_MUTED, anchor='ra')

        line_top = text_top
        for line in title_lines:
            draw.text((body_x, line_top), line, font=title_font, fill=INK, anchor='la')
            line_top += LINE_TITLE
        if meta:
            draw.text((body_x, line_top + META_GAP), meta, font=meta_font, fill=INK_MUTED, anchor='la')

    return Block(height, paint)


def _overflow_block(count: int, fonts) -> Block:
    label = f"…i jeszcze {count} {_polish_meeting_unit(count)} - pełny plan na mikomath.org"

    def paint(sheet, top):
        sheet.draw.text((PAD_X, top + px(8)), label, font=fonts(px(25)), fill=INK_MUTED, anchor='la')

    return Block(px(52), paint)


def _empty_block(fonts, height: int) -> Block:
    """Stretched over whatever the week left unused, so an empty sheet reads as
    a deliberate panel rather than a page that ran out."""

    def paint(sheet, top):
        draw = sheet.draw
        bottom = top + height - CARD_GAP
        _draw_card(draw, top, bottom)
        middle_x, middle_y = WIDTH // 2, (top + bottom) // 2
        draw.text((middle_x, middle_y - px(24)), "Brak spotkań w tym tygodniu",
                  font=fonts(px(36), 'SemiBold'), fill=INK, anchor='mm')
        draw.text((middle_x, middle_y + px(30)), "Nowe terminy pojawiają się w kalendarzu na mikomath.org",
                  font=fonts(px(25)), fill=INK_MUTED, anchor='mm')

    return Block(height, paint)


def _legend_block(groups: list, fonts):
    """Colour is all a card says about its group, so decode it once at the foot."""
    if not groups:
        return None

    font = fonts(px(23))
    dot = px(13)
    gap = px(30)
    rows, row, used = [], [], 0
    for label, color in groups:
        width = dot + px(10) + round(font.getlength(label))
        advance = width if not row else gap + width
        if row and used + advance > CONTENT_WIDTH:
            rows.append(row)
            row, used, advance = [], 0, width
        row.append((label, color, width))
        used += advance
    rows.append(row)

    def paint(sheet, top):
        draw = sheet.draw
        line_top = top + px(16)
        for entries in rows:
            x = PAD_X
            middle = line_top + LEGEND_LINE // 2
            for label, color, width in entries:
                draw.ellipse((x, middle - dot // 2, x + dot, middle + dot // 2), fill=color)
                draw.text((x + dot + px(10), middle), label, font=font, fill=INK_MUTED, anchor='lm')
                x += width + gap
            line_top += LEGEND_LINE

    return Block(px(16) + LEGEND_LINE * len(rows), paint)


def _footer_block(week_start, fonts) -> Block:
    span = week_label(week_start)

    def paint(sheet, top):
        draw = sheet.draw
        rule_y = top + px(20)
        draw.rectangle((PAD_X, rule_y, WIDTH - PAD_X, rule_y + px(2)), fill=RULE)
        draw.text((PAD_X, rule_y + px(34)), "mikomath.org/kolo",
                  font=fonts(px(29), 'SemiBold'), fill=INK, anchor='la')
        draw.text((WIDTH - PAD_X, rule_y + px(40)), span,
                  font=fonts(px(22)), fill=INK_MUTED, anchor='ra')

    return Block(FOOTER_HEIGHT, paint)


# --------------------------------------------------------------------------- #
# Assembling the sheet
# --------------------------------------------------------------------------- #

def _multi_day_blocks(payload: dict, fonts) -> list:
    entries = list(payload.get('registration_events') or []) + list(payload.get('olympiad_stages') or [])
    if not entries:
        return []
    entries.sort(key=lambda entry: (entry['date_begin'], entry['date_end'], entry.get('title') or ''))
    return [_section_block("WYDARZENIA", fonts)] + [_band_block(entry, fonts) for entry in entries]


def _seminar_blocks(payload: dict, week_start, today, fonts) -> list:
    by_day = defaultdict(list)
    for seminar in payload.get('seminars') or []:
        by_day[date.fromisoformat(seminar['date'])].append(seminar)

    blocks, shown, skipped = [], 0, 0
    for offset in range(7):
        day = week_start + timedelta(days=offset)
        seminars = by_day.get(day, [])
        drawn = seminars[:max(MAX_EVENTS - shown, 0)]
        skipped += len(seminars) - len(drawn)
        shown += len(drawn)
        if not drawn:
            continue
        blocks.append(_section_block(_day_label(day), fonts, today_marker=day == today))
        blocks.extend(_seminar_block(seminar, fonts) for seminar in drawn)

    if skipped:
        blocks.append(_overflow_block(skipped, fonts))
    return blocks


def _legend_entries(payload: dict) -> list:
    groups = {}
    for seminar in payload.get('seminars') or []:
        group = seminar.get('group')
        if group:
            groups[group['id']] = (group['short_label'], readable_accent(group['color']))
    return sorted(groups.values(), key=lambda entry: entry[0].lower())


def render_week(payload: dict, week_start, today=None) -> bytes:
    """The week as PNG bytes. Takes a built payload, so it never queries."""
    today = today or timezone.localdate()
    fonts = FontBook()

    legend = _legend_block(_legend_entries(payload), fonts)
    tail = [block for block in (legend, _footer_block(week_start, fonts)) if block is not None]
    tail_height = sum(block.height for block in tail)

    body = [_header_block(week_start, fonts)]
    body += _multi_day_blocks(payload, fonts)
    body += _seminar_blocks(payload, week_start, today, fonts)
    if len(body) == 1:
        slack = MIN_HEIGHT - (body[0].height + tail_height + PAGE_BOTTOM)
        body.append(_empty_block(fonts, max(EMPTY_HEIGHT, slack)))

    height = max(MIN_HEIGHT, sum(block.height for block in body) + tail_height + PAGE_BOTTOM)

    sheet = Sheet(Image.new('RGB', (WIDTH, height), BG))
    top = 0
    for block in body:
        block.paint(sheet, top)
        top += block.height

    top = height - PAGE_BOTTOM - tail_height
    for block in tail:
        block.paint(sheet, top)
        top += block.height

    buffer = BytesIO()
    # Not `optimize=True`: on a sheet this size it triples the time spent here
    # to shave two percent off a file that is cached anyway.
    sheet.image.save(buffer, format='PNG')
    return buffer.getvalue()


# --------------------------------------------------------------------------- #
# Building and caching one week
# --------------------------------------------------------------------------- #

def week_image_cache_key(week_start) -> str:
    return f"timetable-image:{week_start.isoformat()}"


def week_image_ttl() -> int:
    """Never past midnight: the sheet marks today, and the weeks on offer move on."""
    return min(WEEK_IMAGE_MAX_TTL, seconds_until_next_midnight())


def build_week_image(week_start, *, include_unpublished=False) -> bytes:
    start, end = week_bounds(week_start)
    payload = build_calendar_payload(start, end, include_unpublished=include_unpublished)
    return render_week(payload, week_start)


def image_etag(png: bytes) -> str:
    return hashlib.blake2b(png, digest_size=16).hexdigest()


def get_week_image(week_start) -> tuple:
    """The public sheet for a week, drawn at most once per calendar version.

    One slot per week, keyed by the Monday alone, so a newer version overwrites
    the bytes in place rather than stranding the old sheet under a key nobody
    will ask for again. Every slot expires by midnight and only the weeks on
    offer are written, so at most four sheets are held and none hit the disk.
    """
    cache_key = week_image_cache_key(week_start)
    version = get_calendar_version()

    cached = cache.get(cache_key)
    if cached is not None and cached.get('version') == version:
        return cached['png'], cached['etag']

    png = build_week_image(week_start)
    entry = {'version': version, 'png': png, 'etag': image_etag(png)}
    cache.set(cache_key, entry, week_image_ttl())
    return entry['png'], entry['etag']
