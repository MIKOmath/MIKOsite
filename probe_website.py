import os
import datetime
from babel.dates import format_datetime, get_timezone
import requests

website_url = 'https://mikomath.org/'
webhook_url = os.environ['WEBHOOK_URL']
embed_color = 16711680
role_id = '1273275208610086983'


def send_webhook(embed):  # Sends an alert to Discord
    json = {'content': f'<@&{role_id}>',  # Mention tech staff
            'embeds': [embed]}
    
    resp = requests.post(webhook_url, json=json)
    print(resp.status_code, resp.content)
    if resp.status_code != 204:
        raise RuntimeError('Webhook failed')


dt = datetime.datetime.now()
poland_tz = get_timezone('Europe/Warsaw')
poland_time = dt.astimezone(poland_tz)
formatted_time = format_datetime(poland_time, format='HH:mm:ss', locale='pl_PL')

try:
    r = requests.get(website_url, timeout=30)
except requests.exceptions.Timeout:
    embed = {'title': f'Przekroczono limit czasu!', 
             'description': (f'`{formatted_time}` Zautomatyzowany test wykrył błąd na {website_url}.\n'
               f'Nie można się połączyć ze stroną. Sprawdź, czy VPS działa poprawnie.'), 
             'url': website_url, 
             'color': embed_color}
    send_webhook(embed)
    raise

if r.status_code != 200:  # Website is not working
    embed = {'title': f'Błąd {r.status_code}!', 
             'description': (f'`{formatted_time}` Zautomatyzowany test wykrył błąd na {website_url}.\n'
               f'Oczekiwano statusu `200`, napotkano `{r.status_code}`. Sprawdź, czy strona działa poprawnie.'), 
             'url': website_url, 
             'color': embed_color}
    send_webhook(embed)
