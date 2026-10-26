import os
from datetime import UTC, datetime, timedelta

from dotenv import load_dotenv

from app import models
from app.database import sessionLocal
from app.enums import ProductStatus

load_dotenv()

# Products are owned by the seeded admin by default (run app/seeders/seeds.py first).
OWNER_USERNAME = os.environ.get("SEED_OWNER_USERNAME") or os.environ["ADMIN_USERNAME"]
AUCTION_DURATION = timedelta(days=7)

# (name, description, start_price) -> name max 50 chars, description max 200 chars
PRODUCTS = [
    ("Leica M6 Rangefinder Camera", "35mm film rangefinder, 1988. Shutter tested at all speeds, clean viewfinder.", 1800),
    ("Omega Seamaster 300 (1967)", "Automatic dive watch with original dial and bezel. Serviced last year.", 3200),
    ("Eames Lounge Chair Replica", "Walnut veneer and black leather lounge chair with ottoman. Minor wear.", 950),
    ("Gibson Les Paul Standard 2014", "Honeyburst finish, hard case included. Plays beautifully.", 1700),
    ("Fender Stratocaster MIM", "Sunburst Mexican Strat, new strings and setup.", 520),
    ("Vintage Rolex Datejust 1601", "Steel and white gold, pie-pan dial. Box not included.", 5400),
    ("Nintendo Game Boy (1989)", "Original DMG-01, working screen, includes Tetris cartridge.", 90),
    ("Sony Walkman WM-2", "Restored cassette player with new belts. A true classic.", 260),
    ("Persian Tabriz Rug 2x3m", "Hand-knotted wool rug, deep reds and blues. Professionally cleaned.", 1400),
    ("Danish Teak Sideboard", "Mid-century teak sideboard with sliding doors and four drawers.", 780),
    ("First Edition 'Dune' (1965)", "Chilton first printing, dust jacket shows light edge wear.", 4200),
    ("Hasselblad 500C/M Kit", "Medium format body, 80mm Planar lens, A12 back.", 2100),
    ("Apple Macintosh 128K", "Original 1984 Mac, boots to desktop. Keyboard and mouse included.", 1900),
    ("Montblanc Meisterstück 149", "Fountain pen, 14k gold nib (M). Writes smoothly.", 380),
    ("Brass Ship's Telescope", "Three-draw brass telescope with leather grip, early 1900s.", 210),
    ("Art Deco Bronze Sculpture", "Signed bronze dancer on marble base, approx. 40cm tall.", 1250),
    ("Le Creuset Dutch Oven 5.5qt", "Flame orange, enamel in excellent condition.", 120),
    ("Bang & Olufsen Beogram 4000", "Tangential turntable, recently serviced, new stylus.", 1100),
    ("Signed Michael Jordan Card", "1997 Upper Deck, autographed, with certificate of authenticity.", 2600),
    ("Vintage Levi's 501 (1970s)", "Big E red tab, waist 32. Great fade.", 340),
    ("Herman Miller Aeron Chair", "Size B, fully adjustable, graphite frame.", 420),
    ("Moroccan Brass Lantern", "Hand-pierced brass hanging lantern, casts beautiful patterns.", 95),
    ("Canon AE-1 Program", "With 50mm f/1.8 lens, light seals replaced.", 230),
    ("Victorian Mahogany Desk", "Partners desk with green leather inlay, nine drawers.", 1600),
    ("Lego Millennium Falcon 75192", "UCS set, complete with minifigures and box.", 650),
    ("Tiffany Style Table Lamp", "Stained glass dragonfly shade, bronze-finish base.", 310),
    ("Bose QuietComfort 45", "Noise-cancelling headphones, barely used, with case.", 160),
    ("Antique Pocket Watch (Elgin)", "14k gold-filled case, running, circa 1910.", 280),
    ("Japanese Katana (Decorative)", "Display katana with stand, folded steel look.", 190),
    ("Vintage Coca-Cola Sign", "Enamel porcelain sign, 1950s, light patina.", 540),
    ("Wedgwood Jasperware Vase", "Classic blue and white, no chips or cracks.", 140),
    ("DJI Mavic 3 Drone", "Fly More combo, three batteries, under 10 flight hours.", 1350),
    ("Steinway Piano Bench", "Ebony finish bench with music storage.", 260),
    ("Oil Painting: Coastal Sunset", "Original oil on canvas, 60x90cm, framed. Signed.", 720),
    ("Rare Stamp Collection Album", "Over 600 stamps, 1890-1960, worldwide.", 480),
    ("Vintage Polaroid SX-70", "Folding instant camera, tested with fresh film.", 240),
    ("Silver Tea Service Set", "Sterling silver, five pieces with tray, hallmarked.", 2300),
    ("PlayStation 5 Disc Edition", "Two controllers, boxed, excellent condition.", 380),
    ("Marklin HO Train Set", "Starter set with locomotive, wagons and track.", 175),
    ("Barbour Bedale Wax Jacket", "Olive, size 40, re-waxed this season.", 150),
    ("Chanel Classic Flap Bag", "Black caviar leather, gold hardware, with dust bag.", 4800),
    ("Mid-Century Arc Floor Lamp", "Chrome arc with marble base, rewired.", 290),
    ("Antique Globe on Stand", "Hand-coloured terrestrial globe, wooden stand.", 680),
    ("Vinyl Collection: 70s Rock", "120 LPs incl. Led Zeppelin, Pink Floyd, Bowie.", 900),
    ("Breitling Navitimer 806", "Chronograph, black dial, recent service.", 3900),
    ("Kitchenaid Stand Mixer", "Artisan 5qt in empire red, with attachments.", 180),
    ("Handmade Oak Dining Table", "Solid oak, seats eight, oiled finish.", 1150),
    ("Ray-Ban Wayfarer (USA)", "Bausch & Lomb era, original case.", 130),
    ("Meteorite Fragment (Campo)", "Iron meteorite, 210g, with certificate.", 350),
    ("Vintage Typewriter Olivetti", "Lettera 22, new ribbon, types cleanly.", 170),
]


def seed_products():
    db = sessionLocal()

    try:
        owner = (
            db.query(models.User).filter(models.User.username == OWNER_USERNAME).first()
        )
        if not owner:
            raise RuntimeError(
                f"Owner '{OWNER_USERNAME}' not found. Run app/seeders/seeds.py first."
            )

        now = datetime.now(UTC)
        created = 0

        for name, description, start_price in PRODUCTS:
            existing_product = (
                db.query(models.Product)
                .filter(
                    models.Product.name == name, models.Product.owner_id == owner.id
                )
                .first()
            )
            if existing_product:
                continue

            db.add(
                models.Product(
                    name=name,
                    description=description,
                    start_price=start_price,
                    current_price=start_price,
                    owner_id=owner.id,
                    status=ProductStatus.ACTIVE,
                    auction_started_at=now,
                    auction_ends_at=now + AUCTION_DURATION,
                )
            )
            created += 1

        db.commit()
        print(
            f"Created {created} active products "
            f"({len(PRODUCTS) - created} already existed), owned by '{owner.username}'."
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_products()
