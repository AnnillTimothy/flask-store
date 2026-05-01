# Flask Store — The Bodhi Tree

A production-ready Flask e-commerce application with product management, bundles, experiences, discount codes, AI chat, cart, PayFast checkout, email notifications, and a full admin panel.

## Features

- 🛒 **Product catalogue** with category filtering, featured products, and sale prices
- 📦 **Bundles** with inline item editing and savings display
- ✨ **Experiences** — immersive, full-screen experience pages with video/audio backgrounds
- 🎁 **Discount codes** — percentage or fixed, with expiry, usage limits, and minimum order amounts
- 🛍️ **Shopping cart** — supports guests (session) and logged-in users
- 💳 **PayFast payment integration** (South African gateway) with ITN notify, success, and cancel flows
- 👤 **User authentication** — register / login / logout / profile with order history
- 📧 **Flask-Mail** — newsletter subscribe with welcome email, admin notification on new subscribers
- 🤖 **Mistral AI** — Bodhi AI guide orb powered by Mistral, with full store context (products, prices, experiences, discount codes)
- 🔍 **SEO** — meta description, Open Graph, Twitter Card, JSON-LD structured data (OnlineStore, Product) on all key pages
- 🏢 **Company Settings** — single-row admin config for store name, tagline, social links (Instagram, X/Twitter, Facebook), contact info, landing video/audio, shipping cost, about/privacy/terms text
- 🔧 **Flask-Admin panel** with:
  - Product, bundle, bundle items, category, supplier management
  - Experience management with video/image/audio uploads
  - Order management with status workflow (11 statuses)
  - Discount code management
  - Shipping management and report
  - Expense tracking
  - Revenue report
  - Supplier payout report
  - Company settings (branding, social URLs, uploads)
- 🚨 **Custom error pages** — 404 and 500 with on-brand design
- 🎂 **Age verification gate** (18+) with localStorage persistence
- 🍪 **Cookie consent banner**
- 💌 **Email popup** with newsletter signup and 10% discount welcome email

## Tech Stack

| Layer       | Technology                          |
|-------------|--------------------------------------|
| Framework   | Flask 3.x                            |
| ORM         | SQLAlchemy / Flask-SQLAlchemy        |
| Auth        | Flask-Login                          |
| Migrations  | Flask-Migrate (Alembic)              |
| Admin       | Flask-Admin 1.6                      |
| Forms       | Flask-WTF / WTForms                  |
| Email       | Flask-Mail                           |
| AI          | Mistral AI API (`mistral-small-latest`) |
| Frontend    | Bootstrap 5 (CDN), GSAP 3            |
| Payments    | PayFast                              |
| DB (dev)    | SQLite (configurable via env)        |
| Production  | Gunicorn + PostgreSQL/MySQL          |

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
# Edit .env — set SECRET_KEY, MAIL credentials, MISTRAL_API_KEY, and PayFast details
```

### 3. Initialise the database

```bash
flask db upgrade
```

### 4. Seed demo data (optional)

```bash
python seed_data.py
```

### 5. Run the development server

```bash
python run.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

Admin panel: [http://localhost:5000/admin](http://localhost:5000/admin)  
Default seed login: `admin@store.com` / `admin123`

---

## Environment Variables

| Variable               | Description                                        | Default                    |
|------------------------|----------------------------------------------------|----------------------------|
| `SECRET_KEY`           | Flask secret key                                   | `dev-secret-key-…`         |
| `DATABASE_URL`         | SQLAlchemy DB URI                                  | `sqlite:///store.db`       |
| `PAYFAST_MERCHANT_ID`  | Your PayFast merchant ID                           | `10000100` (sandbox)       |
| `PAYFAST_MERCHANT_KEY` | Your PayFast merchant key                          | `46f0cd694581a` (sandbox)  |
| `PAYFAST_PASSPHRASE`   | PayFast passphrase (optional)                      | *(empty)*                  |
| `PAYFAST_SANDBOX`      | `True` for sandbox, `False` for live              | `True`                     |
| `MAIL_SERVER`          | SMTP server hostname                               | `smtp.gmail.com`           |
| `MAIL_PORT`            | SMTP port                                          | `587`                      |
| `MAIL_USE_TLS`         | Enable TLS                                         | `True`                     |
| `MAIL_USERNAME`        | SMTP username (your email address)                 | *(empty)*                  |
| `MAIL_PASSWORD`        | SMTP password / app password                       | *(empty)*                  |
| `MAIL_DEFAULT_SENDER`  | From address for outgoing emails                   | *(empty)*                  |
| `MAIL_ADMIN`           | Admin email to receive new subscriber notifications| *(empty)*                  |
| `MISTRAL_API_KEY`      | Mistral AI API key for the Bodhi AI guide          | *(empty — AI disabled)*    |

> **Note:** If `MAIL_USERNAME` is not set, email sending is silently skipped (best-effort).  
> If `MISTRAL_API_KEY` is not set, the AI orb shows a configuration message.

---

## PayFast Setup Guide

1. Create a merchant account at [payfast.co.za](https://www.payfast.co.za/).
2. Under **Settings → Integration**, copy your **Merchant ID** and **Merchant Key**.
3. Optionally set a **Passphrase** for additional signature security.
4. Configure your **Notify URL** to `https://yourdomain.com/checkout/notify`.
5. Update your `.env` with the production values and set `PAYFAST_SANDBOX=False`.

### Sandbox Testing

PayFast provides a sandbox at `https://sandbox.payfast.co.za/`.  
Default sandbox credentials are pre-filled in `.env.example`.

---

## Mistral AI Setup

1. Create a free account at [console.mistral.ai](https://console.mistral.ai/).
2. Generate an API key and copy it.
3. Set `MISTRAL_API_KEY=<your-key>` in `.env`.
4. The Bodhi AI orb will automatically pull live product, experience, and discount data from the database.

---

## Flask-Mail Setup (Gmail example)

1. Enable 2-Factor Authentication on your Gmail account.
2. Generate an **App Password** under Google Account → Security.
3. Set `MAIL_USERNAME`, `MAIL_PASSWORD`, and `MAIL_DEFAULT_SENDER` in `.env`.
4. Emails are sent on newsletter subscribe (welcome + admin notification). Failures are logged silently so they don't break the flow.

---

## Company Social Media & Branding

Configure social media links and other settings in the Admin panel under **Settings → Company**:

- **Instagram URL** — linked from footer Instagram icon
- **X (Twitter) URL** — linked from footer X icon
- **Facebook URL** — linked from footer Facebook icon
- **Logo, landing video, landing audio** — uploadable media
- **Store hero title/sub, wisdom quotes** — editorial content

---

## Project Structure

```
app/
├── __init__.py          # App factory + error handlers (404, 500)
├── config.py            # Configuration
├── extensions.py        # db, login_manager, migrate, admin, csrf, mail
├── context_processors.py# Injects branding into every template
├── models/              # SQLAlchemy models
│   ├── company_setting.py  # Single-row config (social URLs, branding, media)
│   ├── discount_code.py    # Discount codes (percent/fixed, expiry, usage)
│   ├── experience.py       # Immersive experience pages
│   └── ...
├── routes/              # Blueprint route handlers
│   ├── main.py          # Store, experiences, profile, AI chat
│   ├── checkout.py      # Checkout, PayFast, success, cancel
│   └── ...
├── admin/               # Flask-Admin views & reports
├── services/            # Business logic (cart, orders, PayFast, uploads)
├── templates/
│   ├── base.html        # SEO meta, OG, Twitter Card, JSON-LD, footer social icons
│   ├── errors/          # 404.html, 500.html
│   ├── checkout/        # checkout.html, success.html, cancel.html
│   └── ...
└── static/              # CSS, JS, uploaded images
```

---

## Running in Production

1. Set `SECRET_KEY` to a long random string.
2. Set `DATABASE_URL` to a PostgreSQL or MySQL URI.
3. Set `PAYFAST_SANDBOX=False` and use live PayFast credentials.
4. Serve with **Gunicorn** behind **Nginx**:

```bash
gunicorn "wsgi:application" --workers 4 --bind 0.0.0.0:8000
```

---

## License

MIT
