# GHthrift

GHthrift is an online marketplace for curated, affordable thrift dresses in Ghana. This repository contains the responsive, mobile-first website that powers the storefront: browsing, search and filtering, user accounts, cart and checkout with local payment options, order tracking, and a simple admin dashboard.

We are currently in the **website creation phase**. This README describes the product, the chosen stack, and how the website will be built with **Django** and **htmx**.

---

## Table of Contents

- [Project Overview](#project-overview)
- [MVP Features](#mvp-features)
- [Tech Stack](#tech-stack)
- [Why Django + htmx](#why-django--htmx)
- [Architecture](#architecture)
- [Data Model](#data-model)
- [UI/UX Priorities](#uiux-priorities)
- [Build Plan](#build-plan)
- [Project Structure](#project-structure)
- [Local Development](#local-development)
- [Environment Variables](#environment-variables)
- [Deployment](#deployment)
- [Payments, Delivery, and Notifications](#payments-delivery-and-notifications)
- [Testing and QA](#testing-and-qa)
- [Security](#security)
- [Roadmap](#roadmap)

---

## Project Overview

GHthrift sells one-of-a-kind thrift dresses sourced in Ghana, positioned as a sustainable, budget-friendly fashion alternative. The business model centers on the founder sourcing dresses personally and handling sales, payments, and logistics.

The plan calls for a **web-first, mobile-first** experience because the majority of Ghanaian shoppers browse on Android phones. A PWA and native companion app may follow after product-market fit, but they are out of scope for this phase.

Primary personas:

| Persona | Age | Motivations | Pain Points |
|---------|-----|-------------|-------------|
| Urban Fashion-Conscious | 18-35 | Stay trendy, express individuality, budget-friendly luxury | Limited unique pieces in local malls |
| Budget Shoppers | 16-30 | Maximize wardrobe variety for minimal cost | Concerns about quality and authenticity |
| Eco-Conscious | 20-40 | Reduce fashion waste, support circular economy | Difficulty finding trustworthy thrift platforms |

---

## MVP Features

- Product listings with photos, descriptions, sizes, colors, and prices.
- Advanced search and filtering by size, color, price range, and style/occasion.
- User accounts: register/login, wishlist, order history.
- Cart and secure checkout with Ghana Mobile Money (MTN, Airtel) and card payments via Paystack/Flutterwave.
- Order tracking lifecycle: `pending -> paid -> shipped -> delivered`.
- Admin dashboard to add/edit items, view orders, and export sales.
- Basic contact/chat with the seller (optional).
- Trust signals: verified seller badge, secure payment icons, clear return/refund policy.

---

## Tech Stack

Django and htmx replace the JavaScript/React and Laravel options listed in the original plan. The rest of the plan (data model, flows, sprints) is unchanged.

| Layer | Choice |
|-------|--------|
| **Framework** | Django 5.2+ (Python 3.12+) |
| **Templating** | Django Templates + htmx for dynamic interactions |
| **Styling** | Custom mobile-first CSS (`static/css/site.css`) with no build step |
| **Interactivity** | htmx (vendored at `static/js/htmx.min.js`) for partial page updates |
| **Database** | PostgreSQL (SQLite for local development) |
| **Auth** | Django's built-in auth (`django.contrib.auth`) |
| **Admin** | Django Admin, customized for inventory and orders |
| **Media/Storage** | Local media in development, S3-compatible storage (or Cloudinary) in production |
| **Payments** | Paystack (Mobile Money + cards), Flutterwave optional |
| **Notifications** | Mailgun/SendGrid for email, Twilio/Bulksms Ghana for SMS/USSD |
| **Hosting** | Render (Blueprint included) then an InterServer VPS with Gunicorn + Nginx |
| **Static files** | WhiteNoise or S3-compatible storage |

---

## Why Django + htmx

- **Server-rendered, fast on low-end Android devices.** Django renders HTML on the server, so there is no heavy client-side framework to download or hydrate. This matters for 3G users and older phones.
- **One language, one codebase.** Business logic, templates, and admin live in Python. There is no separate API layer to build and maintain for the MVP.
- **Batteries included.** Auth, sessions, CSRF protection, ORM, migrations, forms, and a production-ready admin come out of the box, which covers most of the MVP checklist.
- **htmx gives interactivity without an SPA.** Search, filtering, cart updates, and order status changes can swap in HTML fragments from Django views, keeping the app simple and progressively enhanced.
- **SEO-friendly.** Pages are real HTML, which helps organic search for terms like "affordable thrift dress Ghana".
- **Fast to ship.** The MVP can be delivered within the 6-8 week sprint plan without splitting effort across frontend and backend frameworks.

---

## Architecture

GHthrift uses a **server-rendered Django monolith** with htmx handling partial updates.

```
Browser (HTML + htmx + custom CSS)
        |
        |  full-page GET/POST  or  hx-* requests (partial HTML)
        v
Django application
  - URL routing
  - Views (full pages + htmx fragments)
  - Forms and validation
  - Templates
  - Business logic / services
        |
        v
PostgreSQL  +  Media storage (S3/Cloudinary)  +  Django Admin
        |
        +--> Paystack / Flutterwave (payments)
        +--> Twilio / Bulksms Ghana (SMS)
        +--> Mailgun / SendGrid (email)
```

### How htmx fits in

htmx is used for interactions that should not require a full page reload:

- **Search and filtering** on the product listing. The filter form uses `hx-get` with `hx-trigger="change, keyup changed delay:300ms"` to request an updated results grid fragment.
- **Pagination** via `hx-get` and `hx-target` on the results container.
- **Add to cart / update quantity / remove item** using `hx-post` and `hx-delete`, swapping the cart widget and showing a toast.
- **Wishlist toggle** using `hx-post` with a button that swaps its own state.
- **Checkout steps** where each step returns the next partial.
- **Admin order status updates** ("Mark as shipped") using `hx-post`, returning the updated order row.
- **Form validation feedback** by re-rendering a form partial with errors.

Each htmx endpoint is a normal Django view that checks `request.htmx` (via `django-htmx`) and returns either a full template or a fragment.

### Example: filterable product grid

```python
# shop/views.py
from django.shortcuts import render
from .models import Dress
from .filters import DressFilter


def product_list(request):
    filterset = DressFilter(request.GET, queryset=Dress.objects.filter(is_available=True))
    template = "shop/partials/product_grid.html" if request.htmx else "shop/product_list.html"
    return render(request, template, {"filterset": filterset})
```

```html
<!-- templates/shop/product_list.html -->
<form hx-get="{% url 'shop:product_list' %}"
      hx-target="#product-grid"
      hx-trigger="change, keyup changed delay:300ms from:input[name='q']"
      hx-push-url="true">
  {{ filterset.form.as_p }}
</form>

<div id="product-grid">
  {% include "shop/partials/product_grid.html" %}
</div>
```

```html
<!-- templates/shop/partials/product_grid.html -->
<div class="grid grid-cols-2 gap-4 md:grid-cols-4">
  {% for dress in filterset.qs %}
    {% include "shop/partials/product_card.html" with dress=dress %}
  {% empty %}
    <p>No dresses match your filters.</p>
  {% endfor %}
</div>
```

---

## Data Model

The Django models mirror the entities in the plan.

| Model | Key Fields |
|-------|-----------|
| **User** | `id, name, email, phone, password_hash, addresses, created_at` (extends Django's `AbstractUser`) |
| **Address** | `id, user, line1, city, region, phone, is_default` |
| **Dress** | `id, title, description, price, size, color, style, condition, category, is_available, created_at, seller` |
| **DressImage** | `id, dress, image, alt_text, position` |
| **WishlistItem** | `id, user, dress, created_at` |
| **Cart / CartItem** | `id, user_or_session, dress, quantity, added_at` |
| **Order** | `id, user, status, total_price, payment_method, transaction_id, shipping_address, created_at, shipped_at, delivered_at` |
| **OrderItem** | `id, order, dress, quantity, unit_price` |
| **Payment** | `id, order, amount, provider, provider_ref, status, captured_at` |
| **Delivery** | `id, order, partner_name, tracking_number, status, notes, delivered_at` |

Order status transitions are enforced in the model/service layer:

```
pending -> paid -> shipped -> delivered
                 \-> cancelled / refunded
```

---

## UI/UX Priorities

- **Mobile-first** layouts with large touch targets and thumb-friendly navigation.
- **Fast loading**: compressed WebP images, lazy loading, minimal JavaScript.
- **Size guide** with body measurements in cm, since Ghanaian sizing differs from US/EU labels.
- **Trust signals**: verified seller badge, secure payment icons, clear return/refund policy.
- **Progressive enhancement**: core flows work with plain HTML; htmx adds speed and polish.
- **Local context**: UI in English, with optional Twi/Ga labels for key terms.

---

## Build Plan

The website creation phase follows the sprint plan from the source document, adapted to Django and htmx.

| Sprint | Duration | Key Tasks |
|--------|----------|-----------|
| **Sprint 1 - Foundations** | 1-2 weeks | Set up repo and CI; create Django project/apps; configure PostgreSQL, settings, and static/media; implement registration and login; base templates and custom CSS. |
| **Sprint 2 - Product Catalogue** | 2 weeks | `Dress` and `DressImage` models; admin CRUD with image upload; public listing; search/filter with htmx; product detail page. |
| **Sprint 3 - Cart & Checkout** | 2 weeks | Session/user cart with htmx updates; checkout form; Paystack sandbox integration; order creation; email receipt. |
| **Sprint 4 - Order & Delivery Tracker** | 1-2 weeks | Order status lifecycle; admin "Mark as shipped"; customer order history and tracking display; delivery tracking numbers. |
| **Sprint 5 - Polish & QA** | 1 week | Mobile responsiveness, image optimization, form validation, htmx edge cases, security review (XSS/CSRF/HTTPS). |
| **Sprint 6 - Soft Launch** | 1 week | Invite friends/family, collect feedback, iterate on UI/UX, add missing filters. |

**Total estimate:** 6-8 weeks at roughly 20 hours/week.

---

## Project Structure

```
GHthrift/
├── manage.py
├── requirements.txt
├── build.sh                # Render/VPS build: install, collectstatic, migrate
├── Procfile                # Gunicorn process definition
├── render.yaml             # Render Blueprint (web service + Postgres + disk)
├── config/                 # Django settings and root URLs
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/               # Custom user, addresses, auth views
├── shop/                   # Dresses, images, filtering, wishlist, seed command
├── cart/                   # Session/user cart and htmx cart endpoints
├── orders/                 # Checkout, Paystack, order tracking, email receipts
├── core/                   # Landing page, contact page, health check
├── templates/
│   ├── base.html
│   ├── <app>/              # Per-app templates
│   └── <app>/partials/     # htmx fragments
├── static/
│   ├── css/site.css
│   └── js/htmx.min.js
├── media/                  # Uploaded dress photos (not committed)
└── deploy/                 # systemd + nginx samples for the VPS
```

---

## Local Development

### Prerequisites

- Python 3.12+
- PostgreSQL 15+ for production parity (SQLite works out of the box locally)
- A Paystack test account for sandbox payments (optional)

No Node.js or frontend build step is required. htmx is vendored and the CSS is a
single static file.

### Setup

```bash
git clone <repository-url>
cd GHthrift

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# edit .env with your database and provider credentials

python manage.py migrate
python manage.py seed_demo        # optional sample dresses
python manage.py createsuperuser
python manage.py runserver
```

The site is available at `http://127.0.0.1:8000`, and the admin at
`http://127.0.0.1:8000/admin/`. Without Paystack keys, sandbox payments are
approved automatically because `PAYSTACK_ALLOW_MOCK=True` in development.

### Common commands

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py test
python manage.py seed_demo --reset
python manage.py collectstatic
```

---

## Environment Variables

Create a `.env` file (never commit it). Typical values:

```
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
SITE_URL=http://localhost:8000

# Omit DATABASE_URL to use SQLite locally.
DATABASE_URL=postgres://user:password@localhost:5432/ghthrift
DB_SSL_REQUIRE=False

MEDIA_ROOT=/var/data/media

# Cloudflare R2 media storage (recommended in production)
CLOUDFLARE_R2_BUCKET=ghthrift-media
CLOUDFLARE_R2_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
CLOUDFLARE_R2_ACCESS_KEY_ID=
CLOUDFLARE_R2_SECRET_ACCESS_KEY=
CLOUDFLARE_R2_CUSTOM_DOMAIN=media.your-domain.com
CLOUDFLARE_R2_MEDIA_LOCATION=media

PAYSTACK_PUBLIC_KEY=
PAYSTACK_SECRET_KEY=
PAYSTACK_CURRENCY=GHS
PAYSTACK_ALLOW_MOCK=True
DELIVERY_FEE=30.00

EMAIL_HOST=
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=orders@ghthrift.com

# Optional generic S3-compatible media storage (ignored when R2 is configured)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
AWS_S3_REGION_NAME=us-east-1

# First admin, created by build.sh when all three are present
DJANGO_SUPERUSER_USERNAME=
DJANGO_SUPERUSER_EMAIL=
DJANGO_SUPERUSER_PASSWORD=
```

---

## Deployment

The app is configured to run on Render first and then move to an InterServer VPS
without code changes. Both targets use Gunicorn, WhiteNoise for static files,
PostgreSQL through `DATABASE_URL`, and environment-driven settings.

### Render

1. Push the repository to GitHub.
2. In Render, choose **New -> Blueprint** and select the repo. `render.yaml`
   provisions a Python web service, Postgres database, and a 5 GB disk mounted
   at `/var/data`.
3. Set the `sync: false` variables in the dashboard: `SITE_URL`
   (e.g. `https://ghthrift.onrender.com`), Paystack keys, email credentials, and
   the `DJANGO_SUPERUSER_*` values for the first admin.
4. Deploy. `build.sh` installs dependencies, collects static files, migrates the
   database, and creates the admin if the superuser variables are set.
5. Health checks use `/healthz/`. The disk keeps uploaded photos by default.
   To push uploads to Cloudflare R2 instead, create an R2 bucket, an R2 API
   token, and a public custom domain (or r2.dev URL) for the bucket, then set
   `CLOUDFLARE_R2_BUCKET`, `CLOUDFLARE_R2_ENDPOINT_URL`,
   `CLOUDFLARE_R2_ACCESS_KEY_ID`, `CLOUDFLARE_R2_SECRET_ACCESS_KEY`, and
   `CLOUDFLARE_R2_CUSTOM_DOMAIN` in the dashboard. You can then remove the disk
   block. The older `AWS_*` variables still work for generic S3 storage.
6. Add your custom domain in Render, then set `DJANGO_ALLOWED_HOSTS` to include
   it and `DJANGO_CSRF_TRUSTED_ORIGINS=https://your-domain.com`.

### InterServer VPS (Ubuntu)

Provision Ubuntu 22.04/24.04, point your domain's A record at the server, then:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip postgresql nginx certbot python3-certbot-nginx git

sudo useradd --system --create-home --shell /bin/bash ghthrift
sudo mkdir -p /var/www/ghthrift
sudo chown ghthrift:www-data /var/www/ghthrift

sudo -u ghthrift git clone <repository-url> /var/www/ghthrift
cd /var/www/ghthrift
sudo -u ghthrift python3 -m venv venv
sudo -u ghthrift venv/bin/pip install -r requirements.txt

# Create the database and user
sudo -u postgres psql -c "CREATE USER ghthrift WITH PASSWORD 'change-me';"
sudo -u postgres psql -c "CREATE DATABASE ghthrift OWNER ghthrift;"

sudo -u ghthrift cp .env.example .env
sudo -u ghthrift nano .env   # set DEBUG=False, DATABASE_URL, SITE_URL, hosts, keys

sudo -u ghthrift venv/bin/python manage.py collectstatic --noinput
sudo -u ghthrift venv/bin/python manage.py migrate
sudo -u ghthrift venv/bin/python manage.py createsuperuser
```

Install the service and nginx config:

```bash
sudo cp deploy/ghthrift.service /etc/systemd/system/ghthrift.service
sudo systemctl daemon-reload
sudo systemctl enable --now ghthrift

sudo cp deploy/nginx.conf /etc/nginx/sites-available/ghthrift
sudo ln -s /etc/nginx/sites-available/ghthrift /etc/nginx/sites-enabled/ghthrift
sudo nginx -t && sudo systemctl reload nginx

sudo certbot --nginx -d ghthrift.com -d www.ghthrift.com
```

Deploys after that are:

```bash
cd /var/www/ghthrift
sudo -u ghthrift git pull
sudo -u ghthrift venv/bin/pip install -r requirements.txt
sudo -u ghthrift venv/bin/python manage.py migrate
sudo -u ghthrift venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart ghthrift
```

### Production checklist

- `DJANGO_DEBUG=False` and a strong `DJANGO_SECRET_KEY`.
- `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` contain the live domain.
- HTTPS enabled; HSTS is on automatically when `DEBUG=False` (override with
  `DJANGO_SECURE_HSTS_SECONDS`).
- Persistent media storage (disk or S3) and regular database backups.
- Paystack live keys set and `PAYSTACK_ALLOW_MOCK=False`.
- `SITE_URL` matches the public URL so payment callbacks and emails link correctly.

---

## Payments, Delivery, and Notifications

### Payments

- **Paystack** is the primary provider, supporting MTN/Airtel Mobile Money and cards. Use the sandbox during development.
- Checkout creates a pending order and sends the customer to Paystack. The callback verifies the transaction server-side, and the `/orders/paystack/webhook/` endpoint verifies the `X-Paystack-Signature` before marking an order paid.
- With no Paystack keys in development (`PAYSTACK_ALLOW_MOCK=True`), payment is approved automatically so the full flow can be tested. Set `PAYSTACK_ALLOW_MOCK=False` in production.
- Pay-on-delivery is supported and records a pending COD payment until the order is delivered.
- Never store raw card data. Store only the provider reference and status.
- Flutterwave remains a possible secondary provider.

### Delivery

Supported partners from the plan: Ghana Post, Flash Express, DHL eCommerce, and ride-hailing couriers (Bolt/Uber) for same-day Accra/Kumasi delivery.

Admin order flow:

1. Verify payment status.
2. Pack the dress and attach the shipping label.
3. Hand over to the partner and obtain a tracking number.
4. Enter the tracking number and mark the order `shipped`.
5. Send the customer an SMS with the tracking link.
6. Mark `delivered` on confirmation.

### Notifications

- **Email receipts** via Mailgun or SendGrid on order creation and status changes.
- **SMS/USSD alerts** via Twilio or Bulksms Ghana for confirmed, shipped, and delivered orders.
- **In-app notifications** for PWA users later.

### Returns

7-day return window from delivery; item must be unworn, unwashed, and tagged. Refunds are processed within 3-5 business days after inspection. Return shipping is on the customer unless the item is defective or mis-described.

---

## Testing and QA

- **Functional tests** with Django's test runner: registration, login, add-to-cart, checkout (sandbox), order creation, status updates, admin CRUD.
- **Usability testing** with 5-7 Ghanaian peers across the personas.
- **Performance**: Lighthouse target under 3 seconds on throttled 3G; optimize images and keep htmx payloads small.
- **Security**: ORM parameterized queries, Argon2 password hashing, CSP headers, CSRF protection, HTTPS only.
- **Cross-browser**: Chrome, Firefox, Safari (mobile), and Android WebView.

Run the suite with:

```bash
python manage.py test
```

---

## Security

- Use Django's built-in protections: CSRF tokens in forms and htmx requests, secure session cookies, and `X-Frame-Options`.
- Set `DEBUG=False` and configure `ALLOWED_HOSTS` in production.
- Hash passwords with Argon2 (`django.contrib.auth.hashers.Argon2PasswordHasher`).
- Validate and verify all payment webhooks.
- Serve the site over HTTPS and set HSTS.
- Restrict admin access and keep dependencies patched.

---

## Roadmap

- **Now:** the Django + htmx MVP is scaffolded and running: catalogue, search/filter, accounts, wishlist, cart, checkout, Paystack/mock payments, order tracking, admin, email receipts, tests, and Render/VPS deployment config.
- **Next:** configure live Paystack and email credentials, upload real inventory photos, and complete the Sprint 5 QA pass.
- **After launch:** add PWA support (service worker + manifest) for an app-like experience.
- **Later:** native companion app (React Native or Flutter) after product-market fit, plus seller/marketplace features and expanded logistics coverage.

---

*Based on the GHthrift Comprehensive Plan v1.0 (October 2026).*
