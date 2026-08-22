import datetime
from dataclasses import dataclass

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import migrations
from django.utils.text import slugify

from mainSite.models import BIO_IMAGE_SIZE
from mikosite.images import to_webp

PHOTO_DIR = 'aboutPhotos'
USERNAME_PREFIX = 'bio-'
EMAIL_DOMAIN = 'bio.invalid'
PLACEHOLDER_BIRTHDAY = datetime.date(2000, 1, 1)

POLISH_TO_ASCII = str.maketrans({
    'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n',
    'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
    'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N',
    'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z',
})


@dataclass
class BadgeSpec:
    text: str
    color: str
    icon: str
    order: int


@dataclass
class Card:
    first_name: str
    last_name: str
    photo: str | None
    badges: list
    description: str
    order: int

    @property
    def slug(self) -> str:
        return slugify(f"{self.first_name} {self.last_name}".translate(POLISH_TO_ASCII))

    @property
    def username(self) -> str:
        return f"{USERNAME_PREFIX}{self.slug}"


BADGES = [
    BadgeSpec("CEO", "executive", "badge", 0),
    BadgeSpec("CTO", "executive", "badge", 1),
    BadgeSpec("Organizator eventów", "executive", "badge", 2),
    BadgeSpec("Redaktor materiałów", "executive", "badge", 3),
    BadgeSpec("POZDRO 2026", "executive", "badge", 4),
    BadgeSpec("Matematyka", "normal", "co_present", 10),
    BadgeSpec("Informatyka", "normal", "co_present", 11),
    BadgeSpec("AI", "normal", "co_present", 12),
    BadgeSpec("Designer", "normal", "palette", 13),
    BadgeSpec("IMO Gold", "award", "workspace_premium", 20),
    BadgeSpec("IOAI Gold", "award", "workspace_premium", 21),
    BadgeSpec("IOL Gold", "award", "workspace_premium", 22),
    BadgeSpec("Laureat OM", "award", "workspace_premium", 30),
    BadgeSpec("Laureat OI", "award", "workspace_premium", 31),
    BadgeSpec("Laureat OAI", "award", "workspace_premium", 32),
    BadgeSpec("Laureat OS", "award", "workspace_premium", 33),
    BadgeSpec("Finalista OM", "award", "workspace_premium", 40),
    BadgeSpec("Finalista OI", "award", "workspace_premium", 41),
    BadgeSpec("Finalista OLM", "award", "workspace_premium", 42),
    BadgeSpec("Finalista OS", "award", "workspace_premium", 43),
]


CARDS = [
    Card(
        first_name="Filip",
        last_name="Manijak",
        photo="Filip.webp",
        badges=["CEO", "Matematyka", "AI", "Laureat OM", "Laureat OAI"],
        description=(
            "Studiuję na UJ i&nbsp;jestem absolwentem LO Prezentek w&nbsp;Rzeszowie. "
            "Zajmuję się kwestami organizacyjnymi. Lubię jeździć na rowerze i&nbsp;grać "
            "w&nbsp;cywilizacje."
        ),
        order=0,
    ),
    Card(
        first_name="Karol",
        last_name="Musieliński",
        photo="Karol.webp",
        badges=["CTO", "Matematyka", "Informatyka", "Laureat OM", "Laureat OI"],
        description=(
            "Jestem absolwentem VIII Liceum w&nbsp;Poznaniu i&nbsp;studiuję JSIM "
            "na&nbsp;Uniwersytecie Warszawskim. Najbardziej interesuje mnie matematyka "
            "dyskretna oraz algorytmika i&nbsp;sztuczna inteligencja."
        ),
        order=1,
    ),
    Card(
        first_name="Konstanty",
        last_name="Smolira",
        photo="Konstanty.webp",
        badges=["Matematyka", "IMO Gold"],
        description=(
            "Rozpoczynam studia na&nbsp;Uniwersytecie Jagiellońskim. MIKO to dla mnie "
            "okazja, by odwdzięczyć się społeczności za pomoc, którą sam swojego czasu "
            "dostałem."
        ),
        order=2,
    ),
    Card(
        first_name="Antoni",
        last_name="Łuczak",
        photo="Antoni.webp",
        badges=["Matematyka", "Laureat OM"],
        description=(
            "Jestem absolwentem XIV LO w&nbsp;Warszawie, studiuję JSIM "
            "na&nbsp;Uniwersytecie Warszawskim. Interesuję się algebrą przemienną, "
            "głównie geometrią algebraiczną oraz teorią liczb."
        ),
        order=3,
    ),
    Card(
        first_name="Łukasz",
        last_name="Próchniak",
        photo="Łukasz.webp",
        badges=["Matematyka", "Finalista OM", "Finalista OS"],
        description=(
            "Absolwent PLO im.&nbsp;Królowej Jadwigi w&nbsp;Lublinie. Aktualnie "
            "studiuję JSIM na&nbsp;Uniwersytecie Warszawskim. Poza studiami grinduję "
            "cyfrę na&nbsp;baldach i&nbsp;od czasu do&nbsp;czasu robię zdjęcia na tyle "
            "przekonujące, że ludzie myślą, że wiem, co robię."
        ),
        order=4,
    ),
    Card(
        first_name="Kordian",
        last_name="Pisarek",
        photo="Kordian.webp",
        badges=["Organizator eventów", "Designer", "Finalista OM", "Finalista OI"],
        description=(
            "Jestem absolwentem V Liceum w&nbsp;Krakowie. Studiuję JSIM "
            "na&nbsp;Uniwersytecie Warszawskim. Jestem członkiem kadry narodowej biegu "
            "na&nbsp;orientację. W&nbsp;życiu chciałbym spróbować wszystkiego, ale "
            "zwykle niestety brakuje mi czasu."
        ),
        order=5,
    ),
    Card(
        first_name="Tymoteusz",
        last_name="Stępkowski",
        photo="Tymoteusz.webp",
        badges=["AI", "IOAI Gold", "Laureat OM", "Laureat OI"],
        description=(
            "Jestem studentem JSIM na&nbsp;Uniwersytecie Warszawskim. Pasjonuję się "
            "informatyką, a&nbsp;w&nbsp;szczególności sztuczną inteligencją "
            "i&nbsp;programowaniem."
        ),
        order=6,
    ),
    Card(
        first_name="Antoni",
        last_name="Bryłowski",
        photo="AntoniB.webp",
        badges=["Matematyka", "IOL Gold", "Laureat OM", "Laureat OS"],
        description=(
            "Uczę się w&nbsp;PLO im.&nbsp;Królowej Jadwigi w&nbsp;Lublinie. Interesuję "
            "się matematyką, lingwistyką teoretyczną i&nbsp;językami, "
            "a&nbsp;w&nbsp;wolnym czasie trenuję bouldering i&nbsp;gram "
            "na&nbsp;fortepianie."
        ),
        order=7,
    ),
    Card(
        first_name="Michał",
        last_name="Oprocha",
        photo="Michal.webp",
        badges=["Redaktor materiałów", "Matematyka", "Finalista OI"],
        description=(
            "Uczę się w&nbsp;V&nbsp;LO im.&nbsp;Augusta Witkowskiego w&nbsp;Krakowie. "
            "W&nbsp;MIKO odpowiadam za redakcję materiałów z&nbsp;poprzednich lat. "
            "W&nbsp;wolnym czasie jeżdzę na rowerze, pływam i&nbsp;co tydzień chodzę "
            "do&nbsp;kina."
        ),
        order=8,
    ),
    Card(
        first_name="Tomasz",
        last_name="Kossakowski",
        photo="Tomasz.webp",
        badges=["Matematyka", "Finalista OLM", "Finalista OS"],
        description=(
            "Uczę się w&nbsp;OSM II&nbsp;st. w&nbsp;klasie dyrygentury w&nbsp;Kielcach. "
            "Interesuje się matematyką, lingwistyką oraz muzyką, a&nbsp;w&nbsp;czasie "
            "wolnym chodzę na&nbsp;piesze wędrówki oraz uczę się języków obcych, "
            "w&nbsp;szczególności niemieckiego i&nbsp;chińskiego."
        ),
        order=9,
    ),
    Card(
        first_name="Miłosz",
        last_name="Płatek",
        photo="Miłosz.webp",
        badges=["POZDRO 2026", "Matematyka", "Laureat OM"],
        description=(
            "Jestem absolwentem V Liceum w&nbsp;Krakowie. Poza matematyką trenuję grę "
            "w&nbsp;szachy, a w&nbsp;wolnym czasie uprawiam różne sporty."
        ),
        order=10,
    ),
    Card(
        first_name="Oleksii",
        last_name="Iermolenko",
        photo="Oleksii.webp",
        badges=["Matematyka", "Finalista OM"],
        description=(
            "Jestem absolwentem XI Liceum w&nbsp;Krakowie, studiuję JSIM na "
            "Uniwersytecie Warszawskim, interesuję się matematyką, informatyką "
            "i&nbsp;gram w&nbsp;szachy."
        ),
        order=11,
    ),
]


def attach_photo(bio, card):
    target = f"bios/{card.slug}.webp"
    storage = bio.image.storage

    if storage.exists(target):
        bio.image.name = target
        bio.save(update_fields=['image'])
        return

    source = settings.BASE_DIR / 'static' / PHOTO_DIR / card.photo
    if not source.exists():
        return

    with source.open('rb') as handle:
        bio.image.save(f"{card.slug}.webp", to_webp(handle, BIO_IMAGE_SIZE), save=True)


def load(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    Badge = apps.get_model('mainSite', 'Badge')
    Bio = apps.get_model('mainSite', 'Bio')

    badges = {}
    for spec in BADGES:
        badges[spec.text], _ = Badge.objects.get_or_create(
            text=spec.text,
            defaults={'color': spec.color, 'icon': spec.icon, 'order': spec.order},
        )

    for card in CARDS:
        user, _ = User.objects.get_or_create(
            username=card.username,
            defaults={
                'email': f"{card.slug}@{EMAIL_DOMAIN}",
                'first_name': card.first_name,
                'last_name': card.last_name,
                'region': 'NA',
                'date_of_birth': PLACEHOLDER_BIRTHDAY,
                'is_active': False,
                'password': make_password(None),
            },
        )
        bio, _ = Bio.objects.update_or_create(
            user=user,
            defaults={
                'description': card.description.replace('&nbsp;', '\u00a0'),
                'order': card.order,
            },
        )
        bio.badges.set([badges[text] for text in card.badges])

        if card.photo:
            attach_photo(bio, card)


def undo(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    Badge = apps.get_model('mainSite', 'Badge')

    User.objects.filter(username__in=[card.username for card in CARDS]).delete()
    Badge.objects.filter(text__in=[spec.text for spec in BADGES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('mainSite', '0011_badge_bio'),
    ]

    operations = [
        migrations.RunPython(load, undo),
    ]
