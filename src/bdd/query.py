"""
SQL query definitions for database operations.
"""

from sqlalchemy import text

CHECK_TABLES = text(
    """
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
"""
)

CLEAR_ALL_TABLES = text(
    """
DO $$
DECLARE
    tabname text;
BEGIN
    FOR tabname IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format('TRUNCATE TABLE public.%I RESTART IDENTITY CASCADE;', tabname);
    END LOOP;
END $$;
"""
)


DROP_ALL_TABLES = text(
"""
DO $$
DECLARE
    tabname text;
BEGIN
    FOR tabname IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS public.%I CASCADE;', tabname);
    END LOOP;
END $$;
"""
)

ENABLE_PGCRYPTO = text("""
CREATE EXTENSION IF NOT EXISTS pgcrypto;
""")

POPULATE_TABLES = text("""
INSERT INTO tables (id, name, capacity, location)
VALUES
    (gen_random_uuid(), 'Table 1', 2, 'indoor'),
    (gen_random_uuid(), 'Table 2', 2, 'indoor'),
    (gen_random_uuid(), 'Table 3', 4, 'indoor'),
    (gen_random_uuid(), 'Table 4', 4, 'outdoor'),
    (gen_random_uuid(), 'Table 5', 6, 'outdoor');
""")

POPULATE_FORMULES = text("""
INSERT INTO menu_formules (id, name, price, description)
VALUES
    (gen_random_uuid(), 'Formule Classique', 16.50,
     '1 plat au choix, 1 entrée, 1 boisson'),
    (gen_random_uuid(), 'Formule Gourmande', 22.00,
     '1 entrée, 1 plat, 1 dessert, 1 boisson'),
    (gen_random_uuid(), 'Formule Duo (2 personnes)', 35.00,
     '2 pizzas différentes, 1 entrée à partager, 2 boissons'),
    (gen_random_uuid(), 'Formule Trio (3 personnes)', 50.00,
     '3 pizzas différentes, 2 entrées à partager, 3 boissons, 1 dessert à partager'),
    (gen_random_uuid(), 'Formule Famille (4 personnes)', 60.00,
     '4 pizzas différentes, 2 entrées, 4 boissons, 2 desserts'),
    (gen_random_uuid(), 'Formule Végétarienne', 18.00,
     '1 plat végétarien, 1 entrée végétarienne, 1 boisson, 1 dessert');
""")

POPULATE_MENU_ITEMS = text("""
INSERT INTO menu_items (id, name, description, price, type, vegetarian, halal, gluten_free, lactose_free)
VALUES
-- ========= ENTRÉES =========
    (gen_random_uuid(), 'Bruschetta Classica',
     'pain grillé, tomates cerises, basilic, ail, huile d''olive',
     7.50, 'entrée', TRUE, TRUE, FALSE, TRUE),
    (gen_random_uuid(), 'Salade Caprese',
     'mozzarella di bufala, tomates, basilic, huile d''olive, vinaigre balsamique',
     9.00, 'entrée', TRUE, TRUE, TRUE, FALSE),
    (gen_random_uuid(), 'Antipasto Italiano',
     'charcuteries italiennes, fromages, olives, artichauts marinés',
     12.50, 'entrée', FALSE, FALSE, TRUE, FALSE),
    (gen_random_uuid(), 'Soupe Minestrone',
     'légumes variés, haricots, pâtes, bouillon de légumes',
     8.00, 'entrée', TRUE, TRUE, FALSE, TRUE),
    (gen_random_uuid(), 'Carpaccio de bœuf',
     'fines tranches de bœuf cru, roquette, parmesan, citron, huile d''olive',
     13.00, 'entrée', FALSE, TRUE, TRUE, FALSE),
    (gen_random_uuid(), 'Focaccia Romarin & Sel Marin',
     'pâte à pain, huile d''olive, romarin, sel de mer',
     6.50, 'entrée', TRUE, TRUE, FALSE, TRUE),
    (gen_random_uuid(), 'Arancini Siciliani',
     'riz, mozzarella, sauce tomate, chapelure',
     9.50, 'entrée', FALSE, TRUE, FALSE, FALSE),
    (gen_random_uuid(), 'Salade César Italienne',
     'laitue romaine, poulet grillé, croûtons, parmesan, sauce César',
     11.00, 'entrée', FALSE, TRUE, FALSE, FALSE),

-- ========= PLATS =========
    (gen_random_uuid(), 'Pizza Margherita',
     'sauce tomate, mozzarella, basilic',
     11.50, 'plat', TRUE, TRUE, FALSE, FALSE),
    (gen_random_uuid(), 'Pizza 4 fromages',
     'mozzarella, gorgonzola, parmesan, ricotta',
     13.50, 'plat', TRUE, TRUE, FALSE, FALSE),
    (gen_random_uuid(), 'Pizza Diavola',
     'sauce tomate, mozzarella, salami piquant',
     13.00, 'plat', FALSE, FALSE, FALSE, FALSE),
    (gen_random_uuid(), 'Pizza Prosciutto',
     'sauce tomate, mozzarella, jambon, champignons',
     13.50, 'plat', FALSE, FALSE, FALSE, FALSE),
    (gen_random_uuid(), 'Pizza Végétarienne',
     'sauce tomate, mozzarella, poivrons, courgettes, aubergines, oignons',
     12.50, 'plat', TRUE, TRUE, FALSE, FALSE),
    (gen_random_uuid(), 'Pizza Tonno',
     'sauce tomate, mozzarella, thon, oignons rouges',
     13.00, 'plat', FALSE, TRUE, FALSE, FALSE),
    (gen_random_uuid(), 'Pizza Parma',
     'sauce tomate, mozzarella, jambon de Parme, roquette, parmesan',
     14.00, 'plat', FALSE, FALSE, FALSE, FALSE),
    (gen_random_uuid(), 'Pizza Truffe Blanche',
     'crème, mozzarella, truffe blanche, champignons',
     15.50, 'plat', TRUE, TRUE, FALSE, FALSE),
    (gen_random_uuid(), 'Lasagnes bolognaises',
     'pâtes fraîches, sauce bolognaise, béchamel, mozzarella, parmesan',
     13.00, 'plat', FALSE, TRUE, FALSE, FALSE),
    (gen_random_uuid(), 'Pâtes Carbonara',
     'spaghetti, pancetta, œufs, parmesan, poivre noir',
     12.50, 'plat', FALSE, FALSE, FALSE, FALSE),
    (gen_random_uuid(), 'Pâtes Arrabiata',
     'penne, sauce tomate épicée, ail, huile d’olive',
     11.00, 'plat', TRUE, TRUE, FALSE, TRUE),
    (gen_random_uuid(), 'Risotto aux Champignons',
     'riz arborio, champignons, bouillon de légumes, parmesan',
     13.50, 'plat', TRUE, TRUE, TRUE, FALSE),
    (gen_random_uuid(), 'Risotto aux Fruits de Mer',
     'riz arborio, crevettes, calamars, moules, vin blanc',
     15.00, 'plat', FALSE, TRUE, TRUE, TRUE),
    (gen_random_uuid(), 'Gnocchi à la Sorrentina',
     'gnocchi, sauce tomate, mozzarella, basilic',
     12.50, 'plat', TRUE, TRUE, FALSE, FALSE),
    (gen_random_uuid(), 'Escalope Milanaise',
     'escalope de veau panée, citron, salade verte',
     14.50, 'plat', FALSE, TRUE, FALSE, TRUE),
    (gen_random_uuid(), 'Poulet parmesan',
     'poulet pané, sauce tomate, mozzarella, parmesan',
     14.00, 'plat', FALSE, TRUE, FALSE, FALSE),
    (gen_random_uuid(), 'Tagliatelles aux Truffes',
     'tagliatelles fraîches, crème, truffe noire, parmesan',
     15.50, 'plat', TRUE, TRUE, FALSE, FALSE),
    (gen_random_uuid(), 'Pizza Calzone',
     'pâte à pizza, jambon, mozzarella, champignons, sauce tomate',
     13.00, 'plat', FALSE, FALSE, FALSE, FALSE),


-- ========= DESSERTS =========
    (gen_random_uuid(), 'Tiramisu',
     'mascarpone, œufs, sucre, café, cacao, biscuits cuillère',
     7.50, 'dessert', FALSE, TRUE, FALSE, FALSE),
    (gen_random_uuid(), 'Panna Cotta Fruits Rouges',
     'crème, sucre, gélatine, coulis de fruits rouges',
     7.00, 'dessert', FALSE, FALSE, TRUE, FALSE),
    (gen_random_uuid(), 'Glace Italienne (3 parfums au choix)',
     'lait, sucre, arômes naturels (vanille, chocolat, pistache, citron)',
     6.50, 'dessert', FALSE, TRUE, TRUE, FALSE),
    (gen_random_uuid(), 'Cannoli Siciliani',
     'pâte croustillante, ricotta sucrée, éclats de pistache',
     7.00, 'dessert', FALSE, TRUE, FALSE, FALSE),
    (gen_random_uuid(), 'Affogato au café',
     'glace vanille, espresso chaud',
     6.50, 'dessert', FALSE, TRUE, TRUE, FALSE),
    (gen_random_uuid(), 'Tarte au Citron Meringuée',
     'pâte sablée, crème citron, meringue',
     6.50, 'dessert', FALSE, TRUE, FALSE, FALSE),
    (gen_random_uuid(), 'Profiteroles au Chocolat',
     'choux, crème chantilly, sauce chocolat',
     7.50, 'dessert', FALSE, TRUE, FALSE, FALSE),

-- ========= BOISSONS =========
    (gen_random_uuid(), 'Eau Minérale (plate ou gazeuse)',
     'eau naturelle',
     3.00, 'boisson', TRUE, TRUE, TRUE, TRUE),
    (gen_random_uuid(), 'Coca-Cola',
     'eau gazeuse, sucre, arômes naturels',
     4.00, 'boisson', TRUE, TRUE, TRUE, TRUE),
    (gen_random_uuid(), 'Jus de Fruits Bio',
     'jus pressé 100% fruit (orange, pomme, ananas)',
     4.50, 'boisson', TRUE, TRUE, TRUE, TRUE),
    (gen_random_uuid(), 'Vin Rouge Chianti',
     'vin rouge italien',
     6.00, 'boisson', FALSE, FALSE, TRUE, TRUE),
    (gen_random_uuid(), 'Vin Blanc Pinot',
     'vin blanc italien',
     6.00, 'boisson', FALSE, FALSE, TRUE, TRUE),
    (gen_random_uuid(), 'Bière Peroni',
     'eau, malt d’orge, houblon, levure',
     5.50, 'boisson', FALSE, FALSE, FALSE, TRUE),
    (gen_random_uuid(), 'Cappuccino',
     'espresso, lait chaud, mousse de lait',
     3.50, 'boisson', FALSE, TRUE, TRUE, FALSE),
    (gen_random_uuid(), 'Espresso Italien',
     'café moulu 100% arabica',
     2.50, 'boisson', TRUE, TRUE, TRUE, TRUE),
    (gen_random_uuid(), 'Thé Noir ou Vert Bio',
     'feuilles de thé séchées',
     3.00, 'boisson', TRUE, TRUE, TRUE, TRUE);
""")


POPULATE_RESTAURANT_INFOS = text("""
INSERT INTO restaurant_info (
    id,
    name,
    address,
    metro,
    rer,
    parking,
    phone_number,
    website,
    cuisine,
    specialties,
    terrace,
    takeaway,
    delivery,
    child_friendly,
    pets_allowed,
    payment_methods,
    ambiance,
    accessibility,
    lunch_open,
    lunch_close,
    dinner_open,
    dinner_close,
    open_days
)
VALUES (
    gen_random_uuid(),
    'Pizza Royal',
    '2 bis Avenue Foch, 75016 Paris',
    'Étoile (lignes 1, 2, 6)',
    'Charles de Gaulle - Étoile (RER A)',
    'Parking Vinci Park à 100m, Avenue Foch',
    '+33 1 45 23 98 76',
    'https://pizzaroyal.fr',
    'Italienne et pizzeria traditionnelle',
    '["Pizza Regina au feu de bois", "Burrata crémeuse", "Tiramisu maison"]',
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    FALSE,
    '["Carte bancaire", "Espèces", "Tickets restaurant"]',
    'Chaleureuse, idéale pour un dîner entre amis ou en famille',
    'Accessible aux personnes à mobilité réduite',
    '11h30',
    '14h30',
    '18h30',
    '23h00',
    'Tous les jours'
);
""")

POPULATE_RESTAURANT_SETTINGS = text("""
INSERT INTO restaurant_settings (
    average_duration_minutes,
    buffer_time_minutes
)
VALUES (
    120,
    15
);
""")

GET_MENU_ITEMS = text("""
SELECT name,description,price,type,vegetarian
FROM menu_items
""")

GET_FORMULE_ITEMS = text("""
SELECT name,price,description
FROM menu_formules
""")

GET_INFORMATIONS = text("""
SELECT
  "name",
  "address",
  "metro",
  "rer",
  "parking",
  "phone_number",
  "website",
  "cuisine",
  "specialties",
  "terrace",
  "takeaway",
  "delivery",
  "child_friendly",
  "pets_allowed",
  "payment_methods",
  "ambiance",
  "accessibility",
  "lunch_open",
  "lunch_close",
  "dinner_open",
  "dinner_close",
  "open_days"
FROM
  "restaurant_info";
""")

GET_ITEM_PRICE = text("SELECT price FROM menu_items WHERE name = :name")
GET_FORMULE_PRICE = text("SELECT price FROM menu_formules WHERE name = :name")
GET_ITEM_ID_BY_NAME = text("SELECT id FROM menu_items WHERE name = :name")
GET_FORMULE_ID_BY_NAME = text("SELECT id, price FROM menu_formules WHERE name = :name")

INSERT_ORDER = text("""
    INSERT INTO orders (id, customer_name, customer_phone, is_validated)
    VALUES (:id, :customer_name, :customer_phone, :is_validated)
    RETURNING id
""")

INSERT_ORDER_ITEM = text("""
    INSERT INTO order_items (id, order_id, item_id, quantity, indications)
    VALUES (:id, :order_id, :item_id, :quantity, :indications)
""")

INSERT_ORDER_FORMULE = text("""
    INSERT INTO order_formules (id, order_id, formule_id, formule_name, formula_base_price, quantity)
    VALUES (:id, :order_id, :formule_id, :formule_name, :formula_base_price, :quantity)
    RETURNING id
""")

INSERT_ORDER_FORMULE_ITEM = text("""
    INSERT INTO order_formule_items (id, order_formule_id, item_id, indications)
    VALUES (:id, :order_formule_id, :item_id, :indications)
""")