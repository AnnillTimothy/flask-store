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

## Quick Start

### 1. Clone & install dependencies

```bash
git clone <repo-url>
cd flask-store
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set SECRET_KEY etc.
```

### 3. Initialise the database

```bash
flask db init
flask db migrate -m "initial migration"
flask db upgrade
```

### 4. Seed demo data

```bash
python seed_data.py
```

### 5. Run the development server

```bash
python run.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

Admin panel: [http://localhost:5000/admin](http://localhost:5000/admin)
Login: `admin@store.com` / `admin123`

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
