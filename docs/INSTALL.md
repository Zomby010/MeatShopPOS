# Installing MeatPOS at a branch

Each branch runs MeatPOS on one PC (the "branch PC"). Tills, tablets and the
manager's laptop open it in a web browser over the shop's Wi-Fi or network
cable. **No internet is needed to sell.**

There are two ways to install. Option A is simplest on Windows.

## Option A: Windows, without Docker

1. **Install Python 3.12** from python.org. On the first screen of the
   installer, tick **"Add python.exe to PATH"**.
2. **Get MeatPOS.** Download the repository as a ZIP from GitHub and unzip it
   to `C:\MeatPOS`.
3. **Open Command Prompt** (Start → type `cmd`) and run:

   ```bat
   cd C:\MeatPOS
   py -3.12 -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py seed_catalogue
   python manage.py createsuperuser
   ```

   `createsuperuser` makes the owner's login. Pick a strong password.
4. **Set this PC's branch and secret key.** Still in Command Prompt:

   ```bat
   setx DJANGO_SECRET_KEY "type-a-long-random-sentence-here"
   setx DJANGO_DEBUG 0
   setx MEATPOS_BRANCH_CODE MAIN
   ```

   Close and reopen Command Prompt so the settings take effect, then:

   ```bat
   cd C:\MeatPOS
   .venv\Scripts\activate
   python manage.py collectstatic --noinput
   ```
5. **Start the server:**

   ```bat
   waitress-serve --listen=0.0.0.0:8000 config.wsgi:application
   ```

   To start it automatically, put that command (after the `cd` and `activate`
   lines) in `C:\MeatPOS\start.bat` and add a shortcut to it in the Startup
   folder (Win+R → `shell:startup`).
6. **Allow it through the firewall.** The first time, Windows asks whether to
   allow Python on private networks. Click **Allow**.
7. **Find the PC's address.** Run `ipconfig` and note the IPv4 address,
   for example `192.168.1.20`. Give the PC a fixed address in the router
   settings so it does not change.
8. **Open it on a till:** browse to `http://192.168.1.20:8000`.

## Option B: Docker (Windows, Linux or a mini PC)

1. Install Docker Desktop (Windows) or Docker Engine (Linux).
2. Copy `.env.example` to `.env` and fill in the values.
3. Run `docker compose up -d --build`.
4. Create the owner login: `docker compose exec web python manage.py createsuperuser`.
5. Load the catalogue: `docker compose exec web python manage.py seed_catalogue`.
6. Open `http://<pc-address>:8000` on the tills.

This uses PostgreSQL, which is recommended for production. Option A uses
SQLite by default; set `DATABASE_URL` to use PostgreSQL there too.

## First steps after installing

1. Log in as the owner. Under **Branches**, create each branch with a short
   code (e.g. `MAIN`, `MARKET`). The code should match `MEATPOS_BRANCH_CODE`
   on that branch's PC.
2. Under **Staff**, add managers and cashiers, each with a home branch and a
   4 to 6 digit PIN for quick till login.
3. Under **Products**, confirm prices. The seed loads the public Farmers
   Choice shop price as the retail price and leaves buying and wholesale
   prices at 0. Or upload your own list under **Import products**.
4. Enter opening stock, either in the import file or per product with
   **Set opening stock**.

## Backups

Back up the database every day to a USB drive or cloud folder.

- SQLite (Option A): copy `C:\MeatPOS\db.sqlite3` while the server is stopped.
- PostgreSQL (Option B):
  `docker compose exec db pg_dump -U meatpos meatpos > backup-YYYY-MM-DD.sql`

## Checking stock integrity

`python manage.py rebuild_stock` compares every stock level with the stock
movement history and lists any difference. `--fix` rebuilds the levels from
the history.
