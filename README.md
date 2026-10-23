# MeatPOS

Point of sale and stock system for a Farmers Choice meat retailer and
wholesaler with several branches. Built with Django; each branch runs it
locally, so selling never depends on the internet.

## Status

| Phase | Scope | State |
|---|---|---|
| 1 | Branches, staff and roles, PIN login, catalogue, suppliers, customers, stock ledger, product history, import, API | Done |
| 2 | Receiving, multi-output conversions, recounts with approval, transfers | Next |
| 3 | Till, payments, receipts, deliveries, shifts, reports | Planned |
| 4 | Branch sync and website API | Planned |

## Quick start (development)

```bash
python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py seed_demo       # demo branches, staff, Farmers Choice catalogue, opening stock
python manage.py runserver 0.0.0.0:8000
```

Demo logins (password `meatpos-demo`, or tap the name on the PIN screen):

| User | Role | Branch | PIN |
|---|---|---|---|
| owner | Owner/Admin | all | 1111 |
| manager | Branch Manager | Main Shop | 2222 |
| cashier1 | Cashier | Main Shop | 3333 |
| cashier2 | Cashier | Market Branch | 4444 |

Installing at a shop: see [docs/INSTALL.md](docs/INSTALL.md).

## Roles

- **Cashier**: views products, stock and product history; adds customers.
- **Branch Manager**: everything a cashier can do, plus products, prices,
  categories, import, opening stock, suppliers, customer credit limits, and
  cashiers in their own branch. Sees costs and margins.
- **Owner/Admin**: everything, across all branches. Manages branches and all
  staff, and can switch the working branch from the sidebar.

## How stock works

Stock is never edited directly. Every change is a row in the stock movement
ledger (`inventory.StockMovement`) with the type, quantity before and after,
cost, reason, staff member and time. Movements cannot be edited or deleted;
mistakes are fixed with a new movement. All changes go through
`inventory/services.py`, which locks the stock row and writes the movement
and the new level in one transaction.

The **Stock history** page on each product lists its movements, so you can
follow stock from delivery through conversion, recount, transfer and sale.
`python manage.py rebuild_stock [--fix]` checks the cached levels against
the ledger.

Money is stored with 2 decimal places and quantities with 3 (grams), always
as `Decimal`. Times are stored in UTC and shown in Nairobi time. A product's
average cost follows its buying price until it has stock history; after that
only stock movements (purchases and conversions, from Phase 2) change it.

## Layout

| App | Contents |
|---|---|
| `core` | Shared base models (UUID ids for sync), branches, staff profiles, roles, PIN login, dashboard |
| `catalogue` | Categories, units, products, price history, Farmers Choice seed, CSV/Excel import |
| `parties` | Suppliers and customers |
| `inventory` | Branch stock, stock movement ledger, product history, opening stock |
| `api` | REST API at `/api/v1/` (products, categories, stock, movements) |

## Commands

| Command | What it does |
|---|---|
| `seed_catalogue` | Loads the starter Farmers Choice catalogue (safe to re-run) |
| `seed_demo` | Demo branches, staff, prices, customers and opening stock |
| `import_products FILE --branch CODE` | Imports a CSV/XLSX product list (Bizkit template columns) |
| `rebuild_stock [--fix]` | Checks stock levels against the ledger |

## Tests

```bash
pytest
```
