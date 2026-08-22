"""The MIKO stamp shared by the social cards and the timetable sheet."""
from io import BytesIO

from django.conf import settings
from django.test import SimpleTestCase
from PIL import Image, ImageDraw, ImageFont

from cards import brand

FONT_PATH = settings.BASE_DIR / 'static' / 'fonts' / 'RubikVariable.ttf'
BG = (6, 49, 62)


def stamp(anchor='la', size=90):
    """Draw the wordmark on its own canvas and hand back the image and width."""
    font = ImageFont.truetype(BytesIO(FONT_PATH.read_bytes()), size)
    font.set_variation_by_name(brand.WEIGHT)
    image = Image.new('RGB', (600, 300), BG)
    width = brand.draw_wordmark(ImageDraw.Draw(image), (40, 80), font, anchor=anchor)
    return image, width


def ink_rows(image, color, tolerance=40):
    """The rows carrying pixels of roughly `color`."""
    pixels = image.load()
    return [
        y for y in range(image.height)
        if any(all(abs(pixels[x, y][band] - color[band]) < tolerance for band in range(3))
               for x in range(image.width))
    ]


class WordmarkTests(SimpleTestCase):
    def test_the_full_stop_is_the_accent_colour(self):
        image, _ = stamp()

        self.assertTrue(ink_rows(image, (242, 181, 68)))

    def test_the_full_stop_sits_on_the_baseline_whatever_the_anchor(self):
        """A `t` anchor measures each glyph's own ink, so a stamp drawn glyph by
        glyph floats the full stop up unless the anchor is resolved once."""
        for anchor in ('la', 'lt', 'ls'):
            with self.subTest(anchor=anchor):
                image, _ = stamp(anchor=anchor)

                letters = ink_rows(image, (255, 255, 255))
                dot = ink_rows(image, (242, 181, 68))

                # Not equality: the round O overshoots the baseline by a pixel.
                self.assertLessEqual(max(letters) - max(dot), 3)

    def test_the_reported_width_covers_the_whole_stamp(self):
        image, width = stamp()
        painted = [
            x for x in range(image.width)
            if any(image.load()[x, y] != BG for y in range(image.height))
        ]

        self.assertLessEqual(max(painted), 40 + width)
        self.assertGreater(max(painted), 40 + width * 0.9)
