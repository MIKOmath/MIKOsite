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
