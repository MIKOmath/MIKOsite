"""Shared fixtures for the about-page card tests. Not named test_*, so the
runner collects it as a helper rather than a suite."""
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image as PILImage

from accounts.models import User
from mainSite.models import Bio

from .auth_base import PASSWORD

ABOUT_URL = '/about/'
PROFILE_URL = '/profile/'
BIOS_CACHE_KEY = 'mainsite-bios-display-data'

# The thank-you card at the end of the grid is written into the template rather
# than stored, so it is on the page even when nothing is.
FIXED_CARD_NAME = "Prowadzący koła"

# The data migration carries the hand-written cards in, so fixtures sit after.
TEST_ORDER = 1000


def photo(size=(1200, 1200), name='portrait.png') -> SimpleUploadedFile:
    """A square, so the 3:2 crop has something to take off."""
    buffer = BytesIO()
    PILImage.new('RGB', size, (10, 74, 89)).save(buffer, format='PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')


def make_person(username, first_name="Marek", last_name="Testowy") -> User:
    return User.objects.create_user(
        username=username,
        email=f"{username}@test.invalid",
        password=PASSWORD,
        first_name=first_name,
        last_name=last_name,
    )


def make_bio(username, badges=(), description="Opis.", **kwargs) -> Bio:
    names = {key: kwargs.pop(key) for key in ('first_name', 'last_name') if key in kwargs}
    kwargs.setdefault('order', TEST_ORDER)
    bio = Bio.objects.create(
        user=make_person(username, **names), description=description, **kwargs,
    )
    bio.badges.set(badges)
    return bio


def card_names(response) -> list:
    """The names the grid shows, in the order it shows them."""
    body = response.content.decode()
    start = body.index('team-tiles')
    grid = body[start:body.index('</section>', start)]
    return [chunk.split('</h2>')[0] for chunk in grid.split('<h2>')[1:]]
