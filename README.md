# Matematyczne Internetowe Koło Olimpijskie

Witamy w repozytorium strony internetowej Matematycznego Internetowego Koła Olimpijskiego. Strona jest napisana za pomocą frameworku Django w języku Python.

## Uruchomienie projektu lokalnie

Aby uruchomić projekt lokalnie, należy wykonać następujące kroki:

1. Sklonuj repozytorium:

``git clone https://github.com/MIKOmath/MIKOprod``

2. Utwórz wirtualne środowisko (venv):
- Windows: `python -m venv venv`
- Linux: `python3 -m venv venv`

3. Aktywuj wirtualne środowisko:
- Windows: `venv\Scripts\activate.bat`
- Linux: `source venv/bin/activate`

4. Zainstaluj zależności:
- Windows: `python -m pip install -r requirements.txt`
- Linux: `python3 -m pip install -r requirements.txt`

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
Aby strona działała należy postawić serwer Redis (instrukcję instalacji można znaleźć np. tu: https://pypi.org/project/django-redis/). Można jednak debugować stronę bez Redisa. 
Należy zakomentować następujące linijki w pliku `settings.py`:
```python
# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": "redis://127.0.0.1:6379/1",
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#         }
#     }
# }
# 
# SESSION_ENGINE = "django.contrib.sessions.backends.cache"
# CACHE_BACKEND = 'redis_cache.cache://127.0.0.1:6379/1'
# SESSION_CACHE_ALIAS = "default"

```
## Konfiguracja haseł i tokenów
Utwórz plik secrets.py w tym samym folderze co plik settings.py:
```
SECRET_KEY = '4b%nh=m5*7du0gmq2+h4%&wd%=ok#i0_jakiś_długi_token_do_szyfrowania'
DB_PASSWORD = 'hasło do użytkownika postgres w PostgreSQL'
```

## Migracja bazy danych
### Wykonaj następujące polecenia:
```
Windows:
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

Linux:
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py createsuperuser
```

Po wykonaniu tych kroków, projekt powinien być gotowy do uruchomienia lokalnie. 

``python manage.py runserver``