import cairosvg
from io import BytesIO
from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw, ImageFont


FONT_PATH = "mikosite/static/fonts/RubikVariable.ttf"
LOGO_PATH = "mikosite/static/logoNoCircle.svg"
TEMPLATE_PATH = "mikosite/media/cards/template.png"
CARD_WIDTH = 1200
CARD_HEIGHT = 630
BG_COLOR = "#06313e"  # Dark blue from brand identification
LOGO_SIZE = (700, 700)
LOGO_POS = (600, 50)  # From top left
STAMP_TEXT = "MIKO"
STAMP_POS = (50, 65)  # From top left
AUTHOR_LINE_1 = "Matematyczne Internetowe"
AUTHOR_LINE_2 = "Koło Olimpijskie"
TEXT_WIDTH = 700
DESC_POS = (50, 75)  # From bottom left
DESC_MIN_LINES = 3
DESC_MAX_LINES = 4
DESC_TITLE_SPACE = 30


def read_svg_to_image(svg_path: str, output_size: tuple[int, int]):
    """
    Read contents of an SVG file to an Image object.

    Args:
        svg_path (str): Path to the SVG file.
        output_size (tuple): Desired output size as a tuple (width, height).

    Returns:
        PIL.Image.Image: PNG image created from the SVG file.
    """
    with open(svg_path, 'rb') as svg_file:
        svg_content = svg_file.read()
        png_data = cairosvg.svg2png(bytestring=svg_content,
                                    output_width=output_size[0], output_height=output_size[1])
        return Image.open(BytesIO(png_data))


def wrap_description_text(description: str, font: ImageFont.FreeTypeFont, width: int):
    """
    Wrap the description text into multiple lines to fit within a specified width.

    Args:
        description (str): The text to wrap.
        font (ImageFont.FreeTypeFont): The font object used to measure the width of the text.
        width (int): The maximum allowed width for each line.

    Returns:
        tuple:
            str: The wrapped text with lines separated by newline characters.
            int: The number of lines in the wrapped text.
    """
    lines = []
    for word in description.split(' '):
        # Try to extend the last line
        if len(lines) and font.getlength(lines[-1] + ' ' + word) <= width:
            lines[-1] += ' ' + word
        else:
            # Create a new line only if necessary
            lines.append(word)
    return '\n'.join(lines), len(lines)


def wrap_title_text(title: str, font: ImageFont.FreeTypeFont, width: int):
    """
    Wrap the title text into one or two lines to fit within a specified width.
    The case of two lines is optimized for a visually balanced look.

    Args:
        title (str): The title text to wrap.
        font (ImageFont.FreeTypeFont): The font object used to measure the width of the text.
        width (int): The maximum allowed width for each line.

    Returns:
        tuple:
            str: The wrapped title text with lines separated by newline characters.
            int: The number of lines in the wrapped title (either 1 or 2).

    Raises:
        ValueError: If the title is too long to fit in two lines.
    """
    if font.getlength(title) <= width:
        # No wrapping needed if everything fits in one line
        return title, 1

    word_list = title.split(' ')
    min_width = width + 1
    out = ""

    # Try every breaking position and find one with minimum width
    for pos in range(1, len(word_list)):
        line1 = ' '.join(word_list[:pos])
        line2 = ' '.join(word_list[pos:])
        this_width = max(font.getlength(line1), font.getlength(line2))
        if this_width < min_width:
            min_width = this_width
            out = line1 + '\n' + line2

    if min_width > width:
        raise ValueError('Title too long.')
    return out, 2


def update_template():
    """
    Refresh the template used for rendering social cards by creating a new image
    using the configured layout, logo and font.

    This function:
    - Creates the cards directory if it doesn't exist.
    - Initializes a blank card image with specified background color and dimensions.
    - Adds the logo (supports both SVG and bitmap formats).
    - Draws a custom stamp and author text using specified fonts and positions.
    - Saves the updated template image as a PNG file.

    Returns:
        str: The file path of the updated template image.
    """
    output_dir = Path(TEMPLATE_PATH).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    image = Image.new('RGB', (CARD_WIDTH, CARD_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(image)

    # Both vector and bitmap graphics are supported
    if LOGO_PATH.endswith('.svg'):
        logo = read_svg_to_image(LOGO_PATH, LOGO_SIZE)
    else:
        logo = Image.open(LOGO_PATH).resize(LOGO_SIZE)
    image.paste(logo, LOGO_POS, logo)

    font_stamp = ImageFont.truetype(FONT_PATH, 90)
    font_author = ImageFont.truetype(FONT_PATH, 30)
    font_stamp.set_variation_by_name('Bold')

    draw.text(STAMP_POS, STAMP_TEXT, font=font_stamp, fill="white", anchor='lt')
    stamp_box = font_stamp.getbbox(STAMP_TEXT)
    stamp_length = stamp_box[2] - stamp_box[0]
    stamp_height = stamp_box[3] - stamp_box[1]

    draw.text((STAMP_POS[0] + stamp_length + 25, STAMP_POS[1] + 5),
              AUTHOR_LINE_1, font=font_author, fill="white", anchor='lt')
    draw.text((STAMP_POS[0] + stamp_length + 25, STAMP_POS[1] + stamp_height - 5),
              AUTHOR_LINE_2, font=font_author, fill="white", anchor='ls')

    image.save(TEMPLATE_PATH, "PNG")
    return TEMPLATE_PATH


def render_social_card(title: str, description: str, filename: Optional[str] = None, output_path: Optional[str] = None):
    """
    Render a social media card with a specified title and description on a predefined template.

    This function:
    - Loads an existing template image or refreshes it if needed.
    - Wraps the title and description text to fit the space.
    - Draws the wrapped title and description onto the image at specific positions.
    - Saves the generated social card as a PNG file in the cards directory or to a specified path.

    Args:
        title (str): The title text to display on the social card.
        description (str): The description text to display below the title.
        filename (Optional[str]): The filename used if no output path is provided.
        output_path (Optional[str]): The full path to save the generated image.

    Returns:
        str: The file path of the saved social card image.

    Raises:
        ValueError: If the title or description is too long.
        ValueError: If neither filename nor output_path is passed to this function.
    """
    if not Path(TEMPLATE_PATH).exists():
        update_template()
    image = Image.open(TEMPLATE_PATH)
    draw = ImageDraw.Draw(image)

    font_title = ImageFont.truetype(FONT_PATH, 60)
    font_desc = ImageFont.truetype(FONT_PATH, 40)
    font_title.set_variation_by_name('SemiBold')

    description, line_count = wrap_description_text(description, font_desc, width=TEXT_WIDTH)
    if line_count > DESC_MAX_LINES:
        raise ValueError('Description too long.')

    desc_box = font_desc.getbbox(description)
    desc_height = desc_box[3] - desc_box[1]
    desc_vertical_pos = CARD_HEIGHT - DESC_POS[1] - desc_height * min(max(line_count, DESC_MIN_LINES), DESC_MAX_LINES)
    draw.text((DESC_POS[0], desc_vertical_pos), description, font=font_desc, fill="white")

    title, line_count = wrap_title_text(title, font_title, width=TEXT_WIDTH - 20)
    title_box = font_title.getbbox(title)
    title_height = title_box[3] - title_box[1]
    title_vertical_pos = desc_vertical_pos - DESC_TITLE_SPACE - title_height * (line_count - 1)
    draw.text((DESC_POS[0], title_vertical_pos), title, font=font_title, fill="white", anchor='ls')

    if output_path is None:
        if filename is None:
            raise ValueError('No output path or filename specified.')
        output_path = Path(TEMPLATE_PATH).parent / filename
    image.save(output_path, "PNG")
    return output_path
