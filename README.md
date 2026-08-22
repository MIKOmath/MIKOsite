# Matematyczne Internetowe Koło Olimpijskie

Witamy w repozytorium strony internetowej Matematycznego Internetowego Koła Olimpijskiego. Strona jest napisana za pomocą frameworku Django w języku Python.

## Uruchomienie projektu lokalnie

Aby uruchomić projekt lokalnie, należy wykonać następujące kroki:

1. Sklonuj repozytorium:

- ``git clone https://github.com/MIKOmath/MIKOsite``

2. Utwórz wirtualne środowisko (venv):
- `python -m venv venv`

3. Aktywuj wirtualne środowisko:
- Windows: `venv\Scripts\activate.bat`
- Linux: `source venv/bin/activate`

4. Zainstaluj zależności:
- `python -m pip install -r requirements.txt`

## Tryb deweloperski
Aby uruchomić projekt w trybie deweloperskim, należy ustawić w pliku `settings.py`:
```python
DEBUG = True
```
Ustawienie to jest szczególnie polecane podczas pierwszego uruchomienia projektu lokalnie.
Pamiętaj, aby nie używać tego ustawienia w środowisku produkcyjnym oraz nie dodawać go do repozytorium.

## Konfiguracja baz danych

### Opcja 1: SQLite3 (na szybko)
Aby używać SQLite3, wystarczy utworzyć plik `db.sqlite3` w tym samym folderze co plik `manage.py`.

### Opcja 2: PostgreSQL
Aby użyć PostgreSQL:

1. Utwórz nową bazę danych o nazwie `mikodb`:
- ``sudo -u postgres psql``
- ``CREATE DATABASE mikodb;``
2. Skonfiguruj połączenie w pliku `settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mikodb',
        'USER': 'postgres',
        'PASSWORD': DB_PASSWORD,
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Redis (opcjonalnie)
Domyślnie projekt nie używa Redisa, jeśli `debug=True` w `settings.py`.
Aby używać Redisa (zalecane w środowisku produkcyjnym), należy postawić serwer Redis
(instrukcję instalacji można znaleźć np. tu: https://pypi.org/project/django-redis/)
oraz skonfigurować połączenie w pliku `settings.py`:

```python
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
CACHE_BACKEND = 'redis_cache.cache://127.0.0.1:6379/1'
SESSION_CACHE_ALIAS = "default"
```
Aby używać Redisa z `debug=True`, należy ustawić w `settings.py`:
```python
USE_REDIS_WITH_DEBUG = True
```

## Konfiguracja haseł i tokenów
Utwórz plik `secrets.py` w tym samym folderze co plik `settings.py`:
```
SECRET_KEY = '4b%nh=m5*7du0gmq2+h4%&wd%=ok#i0_jakiś_długi_token_do_szyfrowania'
```
Jeśli używasz PostgreSQL, dodaj również:
```
DB_PASSWORD = 'hasło użytkownika postgres w PostgreSQL'
```

### Konta i logowanie (django-allauth)
Rejestracja, logowanie, weryfikacja adresów email, reset hasła i logowanie
przez Google/Discord obsługuje django-allauth (strony pod `/accounts/...`).

* **Turnstile** - rejestracja i prośba o reset hasła wymagają przejścia
  Cloudflare Turnstile. Bez skonfigurowanych kluczy formularze odmawiają
  przyjęcia zgłoszenia. Do pracy lokalnej można użyć [oficjalnych kluczy
  testowych Cloudflare](https://developers.cloudflare.com/turnstile/troubleshooting/testing/)
  (uwaga: ich endpoint testowy nie odsyła pola `action`, więc weryfikacja
  akcji formularza je odrzuci - do pełnego testu lokalnego użyj prawdziwych
  kluczy w trybie testowym).
* **OAuth** - przyciski Google/Discord pojawiają się dopiero, gdy w
  `secrets.py` (lub zmiennych środowiskowych) są klucze:
  `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`,
  `DISCORD_OAUTH_CLIENT_ID`, `DISCORD_OAUTH_CLIENT_SECRET`.
  Konto założone przez Google/Discord ma potwierdzony email od ręki.
* **Email** - przy `DEBUG = True` wiadomości trafiają na konsolę serwera.
  Produkcja wysyła przez relay Google Workspace (`smtp-relay.gmail.com:587`),
  który przyjmuje pocztę wyłącznie z adresu IP produkcji - relay trzeba
  skonfigurować w panelu Workspace (allowlist IP + TLS + DKIM).
* Konta Google/Discord połączone z kontem MIKO przechowuje tabela allauth
  (`SocialAccount`) - API udostępnia ją pod `/api/linked-accounts/` z polami
  `platform` i `external_id`, widać ją też w panelu admina.

## Migracja bazy danych, pliki statyczne, konta
Przed uruchomieniem serwera testowego należy utworzyć bazę danych poleceniem `migrate`.
Następnie należy wygenerować automatyczne pliki statyczne oraz wykonać kompresję django-compressor.

### Tryb debug
Zanim przejdziesz dalej, upewnij się, że w `settings.py` jest ustawione (o ile chcesz używać tego ustawienia):
```python
DEBUG = True
```

### Wykonaj następujące polecenia:
```
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py compress --force
```

### Konto administratora
Przed pierwszym uruchomieniem warto utworzyć konto administratora:
```
python manage.py createsuperuser
```

### Uruchomienie
Po wykonaniu tych kroków projekt jest gotowy do uruchomienia lokalnie:
``python manage.py runserver``

## API
Aby zobaczyć listę dostępnych endpointów, wejdź na `/api/`. Po zalogowaniu do Django można swobodnie prototypować w przeglądarce. 

Produkcyjny dostęp do API powinien być autoryzowany tokenem uzyskanym komendą
``python manage.py drf_create_token <username>``
Autoryzacja przebiega wtedy poprzez podanie headera:
```
Authorization: Token <token>
```

### Poziomy dostępu
API rozróżnia dwa poziomy dostępu:

* **publiczny** - każdy, zalogowany lub anonimowy, użytkownik może czytać kalendarz, 
  spotkania, grupy, ogłoszenia, partnerów, wydarzenia z zapisami, olimpiady, etapy olimpiad, 
  poprzednie edycje oraz profil pojedynczego użytkownika. Zalogowany użytkownik widzi dodatkowo
  swój pełny profil (`/api/users/me/`) i swoje punkty za aktywnośc.
* **administratora** - zapis w całym API oraz odczyt danych wewnętrznych: szablonów
  formularzy, przypomnień, kont powiązanych, listy użytkowników wraz z uprawnieniami
  (`is_staff`, `is_superuser`, `groups`, `user_permissions`, `last_login`). Administrator
  to **superużytkownik** (`is_superuser`). Samo `is_staff` daje dostęp wyłącznie do
  panelu admina i nie ma wpływu na poziom dostępu do API.

Wpisy oznaczone jako niepublikowane (partnerzy, wydarzenia z zapisami, etapy olimpiad,
poprzednie edycje, nieaktywne olimpiady) są widoczne wyłącznie dla administratora - także
w kalendarzu.
