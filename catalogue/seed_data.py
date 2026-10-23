"""Starter Farmers Choice catalogue.

Names and pack sizes follow https://farmerschoice.co.ke/shop/ (checked
23 Oct 2026). `reference_price` is the public shop price in KES at that date,
loaded as the retail price for the owner to confirm. Buying and wholesale
prices are left at 0 until the owner enters their own. Butchery cuts the shop
breaks down itself have no reference price.
"""

# (name, category, unit, reference_price)
FARMERS_CHOICE_PRODUCTS = [
    # Sausages
    ("Beef Chipolatas 200gms", "Sausages", "packet", 185.00),
    ("Beef Chipolatas 1kg", "Sausages", "packet", 880.50),
    ("Beef Choma Sausage 1kg", "Sausages", "packet", 945.50),
    ("Beef Sausage Catering 1kg", "Sausages", "packet", 690.50),
    ("Beef Sausage Meat 3kgs", "Sausages", "packet", 2395.00),
    ("Beef Sausages (Safari) 500gms", "Sausages", "packet", 345.00),
    ("Boerewors Beef 500gms", "Sausages", "packet", 595.00),
    ("Boerewors Pork 500gms", "Sausages", "packet", 595.00),
    ("Chicken Sausages 400gms", "Sausages", "packet", 345.00),
    ("Chicken Sausages Value Pack 1kg", "Sausages", "packet", 695.50),
    ("Classic Pork Sausages 500gms", "Sausages", "packet", 345.00),
    ("Lamb Sausages 1kg", "Sausages", "packet", 895.50),
    ("Low Fat Beef Sausage 400gms", "Sausages", "packet", 370.00),
    ("Low Fat Pork Sausage 400gms", "Sausages", "packet", 370.00),
    ("Meaty Beef Sausages 400gms", "Sausages", "packet", 370.00),
    ("Meaty Beef Sausages 1kg", "Sausages", "packet", 810.00),
    ("Spicy Beef Sausages 400gms", "Sausages", "packet", 0),
    # Smokies and economical lines
    ("Beef Smokies", "Smokies & Economical", "piece", 0),
    ("Beef Smokies Pack", "Smokies & Economical", "packet", 0),
    ("Eazy Peel Sausages", "Smokies & Economical", "packet", 0),
    ("Nyamabite", "Smokies & Economical", "packet", 0),
    ("Mini Bites", "Smokies & Economical", "packet", 0),
    ("Danish Pork Hotdogs 500gms", "Smokies & Economical", "packet", 320.50),
    # Bacon
    ("Back Bacon 200gms", "Bacon", "packet", 510.00),
    ("Back Bacon 400gms", "Bacon", "packet", 835.50),
    ("Back Bacon 1kg", "Bacon", "packet", 1738.50),
    ("Beef Bacon 200gms", "Bacon", "packet", 536.00),
    ("Beef Bacon 400gms", "Bacon", "packet", 1050.50),
    ("Beef Bacon 1kg", "Bacon", "packet", 2174.00),
    ("Collar Bacon 100gms", "Bacon", "packet", 210.00),
    ("Collar Bacon 400gms", "Bacon", "packet", 693.50),
    ("Collar Bacon 1kg", "Bacon", "packet", 1565.00),
    # Hams, brawns and sandwich cuts
    ("Beef Brawn Sliced 500gms", "Hams & Sandwich Cuts", "packet", 316.00),
    ("Chicken Brawn Sliced 200gms", "Hams & Sandwich Cuts", "packet", 105.50),
    ("Chicken Sandwich Slices 200gms", "Hams & Sandwich Cuts", "packet", 284.00),
    ("Chicken Sandwich Bulk", "Hams & Sandwich Cuts", "kg", 982.00),
    ("Beef Pastrami Bulk", "Hams & Sandwich Cuts", "kg", 2385.00),
    ("Gammon Ham", "Hams & Sandwich Cuts", "kg", 0),
    # Delicatessen, polony and viennas
    ("Beef Garlic Salami 200gms", "Delicatessen", "packet", 326.00),
    ("Beef Polony Bulk", "Polony & Viennas", "kg", 982.00),
    ("Chicken Polony", "Polony & Viennas", "packet", 0),
    ("Beef Viennas", "Polony & Viennas", "packet", 0),
    ("Poultry Viennas", "Polony & Viennas", "packet", 0),
    ("Krainer", "Delicatessen", "packet", 0),
    ("Kabanossi", "Delicatessen", "packet", 0),
    # Burgers
    ("Chicken Burger 400gms", "Burgers", "packet", 320.50),
    # Fresh beef (per kg)
    ("Beef Fillet", "Beef", "kg", 2063.50),
    ("Beef Casserole", "Beef", "kg", 577.50),
    ("Barbecue Beef Ribs", "Beef", "kg", 735.00),
    ("Cubed Meat on Bone (Beef)", "Beef", "kg", 766.50),
    ("Beef Stew (Steak & Bone)", "Beef", "kg", 0),
    ("Beef Mince", "Beef", "kg", 0),
    ("Beef Boneless Topside", "Beef", "kg", 0),
    ("Beef T-Bone", "Beef", "kg", 0),
    ("Beef Liver", "Beef", "kg", 0),
    # Pork and lamb (per kg)
    ("Pork Loin Chops", "Pork", "kg", 0),
    ("Pork Belly Ribs", "Pork", "kg", 0),
    ("Pork Leg", "Pork", "kg", 0),
    ("Cubed Boneless Lamb (Diced)", "Lamb", "kg", 1220.00),
    # Poultry (per kg); capon breaks down into the cuts below
    ("Chicken Capon", "Poultry", "kg", 0),
    ("Whole Chicken", "Poultry", "kg", 0),
    ("Chicken Breast", "Poultry", "kg", 0),
    ("Chicken Thighs", "Poultry", "kg", 0),
    ("Chicken Boneless", "Poultry", "kg", 0),
    ("Chicken Back", "Poultry", "kg", 0),
    ("Chicken Wings", "Poultry", "kg", 0),
    ("Chicken Drumsticks", "Poultry", "kg", 0),
    ("Duck Breast", "Poultry", "kg", 2125.00),
    ("Duck Legs", "Poultry", "kg", 1375.00),
    # Eggs
    ("Eggs (Tray of 30)", "Eggs", "tray", 0),
    ("Eggs (Single)", "Eggs", "piece", 0),
]
