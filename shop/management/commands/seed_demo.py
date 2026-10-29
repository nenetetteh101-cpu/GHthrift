from decimal import Decimal

from django.core.management.base import BaseCommand

from shop.models import Dress

SAMPLES = [
    {
        "title": "Emerald wrap midi dress",
        "description": (
            "A flattering emerald wrap dress with a tie waist and soft viscose fabric. "
            "Great for weddings, church and dinner dates. Fits true to size with a little stretch. "
            "Measurements: bust 92cm, waist 74cm, length 112cm."
        ),
        "price": "145.00",
        "size": Dress.Size.M,
        "color": "Emerald green",
        "style": "Wrap midi",
        "condition": Dress.Condition.LIKE_NEW,
        "occasion": Dress.Occasion.WEDDING,
        "is_featured": True,
    },
    {
        "title": "Terracotta linen day dress",
        "description": (
            "Breathable linen-blend day dress in warm terracotta with side pockets. "
            "An easy throw-on piece for market runs and brunch. "
            "Measurements: bust 96cm, waist 80cm, length 105cm."
        ),
        "price": "120.00",
        "size": Dress.Size.L,
        "color": "Terracotta",
        "style": "A-line",
        "condition": Dress.Condition.GOOD,
        "occasion": Dress.Occasion.CASUAL,
        "is_featured": True,
    },
    {
        "title": "Black satin evening slip",
        "description": (
            "Classic black satin slip dress with adjustable straps and a subtle side slit. "
            "Layer it with a blazer for work or wear it alone for a party. "
            "Measurements: bust 88cm, waist 70cm, length 118cm."
        ),
        "price": "185.00",
        "size": Dress.Size.S,
        "color": "Black",
        "style": "Slip",
        "condition": Dress.Condition.LIKE_NEW,
        "occasion": Dress.Occasion.PARTY,
        "is_featured": True,
    },
    {
        "title": "Indigo print shirt dress",
        "description": (
            "Structured shirt dress in an indigo floral print with a matching belt. "
            "Works for the office and weekend lunches. "
            "Measurements: bust 100cm, waist 84cm, length 108cm."
        ),
        "price": "135.00",
        "size": Dress.Size.XL,
        "color": "Indigo",
        "style": "Shirt dress",
        "condition": Dress.Condition.GOOD,
        "occasion": Dress.Occasion.WORK,
        "is_featured": False,
    },
    {
        "title": "Cream crochet beach dress",
        "description": (
            "Lightweight cream crochet dress with a relaxed fit and scalloped hem. "
            "Perfect over swimwear or with sandals for a resort look. "
            "Measurements: bust 94cm, waist free, length 96cm."
        ),
        "price": "110.00",
        "size": Dress.Size.M,
        "color": "Cream",
        "style": "Crochet",
        "condition": Dress.Condition.GOOD,
        "occasion": Dress.Occasion.CASUAL,
        "is_featured": False,
    },
    {
        "title": "Burgundy velvet occasion dress",
        "description": (
            "Rich burgundy velvet dress with a sweetheart neckline and fitted bodice. "
            "A statement piece for evening events and December parties. "
            "Measurements: bust 90cm, waist 72cm, length 110cm."
        ),
        "price": "210.00",
        "size": Dress.Size.S,
        "color": "Burgundy",
        "style": "Bodycon",
        "condition": Dress.Condition.NEW,
        "occasion": Dress.Occasion.EVENING,
        "is_featured": True,
    },
    {
        "title": "Sage green pleated midi",
        "description": (
            "Soft sage pleated midi with a high neck and long sleeves. "
            "Modest and elegant for church or a formal lunch. "
            "Measurements: bust 98cm, waist 78cm, length 116cm."
        ),
        "price": "155.00",
        "size": Dress.Size.L,
        "color": "Sage green",
        "style": "Pleated midi",
        "condition": Dress.Condition.LIKE_NEW,
        "occasion": Dress.Occasion.CHURCH,
        "is_featured": False,
    },
    {
        "title": "Mustard button-front dress",
        "description": (
            "Mustard yellow dress with a button front, collar and removable belt. "
            "A cheerful workwear piece that transitions to after-work drinks. "
            "Measurements: bust 96cm, waist 80cm, length 104cm."
        ),
        "price": "125.00",
        "size": Dress.Size.M,
        "color": "Mustard",
        "style": "Button-front",
        "condition": Dress.Condition.GOOD,
        "occasion": Dress.Occasion.WORK,
        "is_featured": False,
    },
]


class Command(BaseCommand):
    help = "Create sample dresses for local development."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing dresses before seeding.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            Dress.objects.all().delete()

        created = 0
        for sample in SAMPLES:
            data = dict(sample)
            data["price"] = Decimal(data["price"])
            _, was_created = Dress.objects.get_or_create(
                title=data["title"], defaults=data
            )
            created += int(was_created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete. Created {created} dress(es); total {Dress.objects.count()}."
            )
        )
