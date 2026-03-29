# Flask Store

A production-ready Flask ecommerce application with product management, bundles, cart, checkout via PayFast, and a full admin panel.

## Features

- 🛒 Product catalogue with category filtering
- 📦 Product bundles with savings display
- 🛍️ Shopping cart (supports guests via session and logged-in users)
- 💳 PayFast payment integration (South African gateway)
- 👤 User authentication (register / login / logout)
- 🔧 Flask-Admin panel with:
  - Product, bundle, category, supplier management
  - Order and shipping management
  - Revenue report
  - Supplier payout report
  - Shipping report
  - Expense tracking

## Tech Stack

| Layer       | Technology                      |
|-------------|----------------------------------|
| Framework   | Flask 2.3                        |
| ORM         | SQLAlchemy / Flask-SQLAlchemy    |
| Auth        | Flask-Login                      |
| Migrations  | Flask-Migrate (Alembic)          |
| Admin       | Flask-Admin 1.6                  |
| Forms       | Flask-WTF / WTForms              |
| Frontend    | Bootstrap 5 (CDN)                |
| Payments    | PayFast                          |
| DB (dev)    | SQLite (configurable via env)    |

## Prerequisites

Before you begin you need two things installed on your computer:

1. **Python 3.9 or higher** – Download from <https://www.python.org/downloads/>.
   During installation on Windows, **tick the box that says "Add Python to PATH"**.
2. **Git** – Download from <https://git-scm.com/downloads>.
   The default options during installation are fine.

> **Tip:** After installing, open a terminal (Command Prompt or PowerShell on Windows, Terminal on Mac/Linux) and run `python --version` and `git --version` to check they are installed correctly.

## Quick Start (step-by-step)

Open a terminal and follow each step in order.

### 1. Download the project

```bash
git clone https://github.com/AnnillTimothy/flask-store.git
cd flask-store
```

This downloads a copy of all the code to a folder called `flask-store` on your computer, then moves into that folder.

### 2. Create a virtual environment

A virtual environment keeps this project's packages separate from the rest of your system.

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On Mac / Linux
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal prompt — that means it is active.

### 3. Install the dependencies

```bash
pip install -r requirements.txt
```

This installs Flask and all the other libraries the app needs.

### 4. Set up the configuration file

```bash
# On Windows (Command Prompt)
copy .env.example .env

# On Mac / Linux
cp .env.example .env
```

This creates a `.env` file with sensible defaults. You can open it in any text editor to change settings later.

### 5. Create the database

```bash
flask db upgrade
```

The database migration files are already included in the project, so this single command builds all the required tables in a local SQLite database.

### 6. Create the admin user

```bash
python seed_data.py
```

This adds a default admin account you can use to log in straight away.

### 7. Run the app

```bash
python run.py
```

You should see output like:

```
 * Serving Flask app 'app'
 * Running on http://127.0.0.1:5000
```

Open your browser and go to **<http://localhost:5000>** — the store homepage will appear.

### 8. Log in to the admin panel

Go to **<http://localhost:5000/admin>** and sign in with:

| Field    | Value               |
|----------|---------------------|
| Email    | `admin@store.com`   |
| Password | `admin123`          |

From the admin panel you can add suppliers, categories, products and bundles.

> **To stop the server**, press `Ctrl + C` in the terminal.  
> **To start it again later**, open a terminal, `cd` into the project folder, activate the virtual environment (step 2) and run `python run.py`.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `python` is not recognised | Try `python3` instead, or re-install Python and make sure "Add to PATH" is ticked. |
| `pip` is not recognised | Try `pip3`, or run `python -m pip install -r requirements.txt`. |
| `flask` is not recognised | Make sure your virtual environment is activated (you see `(venv)` in the prompt). |
| Port 5000 already in use | Another app is using that port. Stop it, or run `flask run --port 5001` to use a different port. |
| Database errors after pulling new changes | Run `flask db upgrade` again to apply any new migrations. |

---

## Environment Variables

| Variable              | Description                              | Default                  |
|-----------------------|------------------------------------------|--------------------------|
| `SECRET_KEY`          | Flask secret key                         | `dev-secret-key-…`       |
| `DATABASE_URL`        | SQLAlchemy DB URI                        | `sqlite:///store.db`     |
| `PAYFAST_MERCHANT_ID` | Your PayFast merchant ID                 | `10000100` (sandbox)     |
| `PAYFAST_MERCHANT_KEY`| Your PayFast merchant key                | `46f0cd694581a` (sandbox)|
| `PAYFAST_PASSPHRASE`  | PayFast passphrase (optional)            | *(empty)*                |
| `PAYFAST_SANDBOX`     | `True` for sandbox, `False` for live     | `True`                   |

---

## PayFast Setup Guide

1. Create a merchant account at [payfast.co.za](https://www.payfast.co.za/).
2. Under **Settings → Integration**, copy your **Merchant ID** and **Merchant Key**.
3. Optionally set a **Passphrase** for additional signature security.
4. Configure your **Notify URL** to `https://yourdomain.com/checkout/notify`.
5. Update your `.env` with the production values and set `PAYFAST_SANDBOX=False`.

### Sandbox Testing

PayFast provides a sandbox environment at `https://sandbox.payfast.co.za/`.  
Default sandbox credentials are pre-filled in `.env.example`.

---

## Project Structure

```
app/
├── __init__.py          # App factory
├── config.py            # Configuration
├── extensions.py        # db, login_manager, migrate, admin, csrf
├── models/              # SQLAlchemy models
├── routes/              # Blueprint route handlers
├── admin/               # Flask-Admin views & reports
├── services/            # Business logic (cart, orders, PayFast)
├── templates/           # Jinja2 HTML templates
└── static/              # CSS, JS, uploaded images
```

---

## Running in Production

1. Set `SECRET_KEY` to a long random string.
2. Set `DATABASE_URL` to a PostgreSQL or MySQL URI.
3. Set `PAYFAST_SANDBOX=False` and use live PayFast credentials.
4. Serve with **Gunicorn** behind **Nginx**:

```bash
gunicorn -w 4 -b 0.0.0.0:8000 "run:app"
```

---

## License

MIT
