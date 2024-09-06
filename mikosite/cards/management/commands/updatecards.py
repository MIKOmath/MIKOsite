from tqdm import tqdm
from django.core.management.base import BaseCommand
from cards.static_cards import STATIC_CARDS
from cards.cards import render_social_card


class Command(BaseCommand):
    help = 'Generates static social cards'

    def handle(self, *args, **kwargs):
        for filename, title, description in tqdm(STATIC_CARDS):
            try:
                render_social_card(title, description, filename=filename)
            except ValueError as e:
                print(f"ValueError while rendering {filename}: {e}")
        print("Finished rendering static social cards")
