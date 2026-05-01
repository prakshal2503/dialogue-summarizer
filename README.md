---
title: Dialogue Summarizer
emoji: 🎙️
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---


# ⬡ Dialogue Summarizer — Cloud Framework
### A Django + MongoDB Web Application

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- MongoDB (local or Atlas)
- pip

### Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run migrations (SQLite for sessions)
python manage.py migrate

# 3. Start the server
python manage.py runserver
```

Or simply run:
```bash
chmod +x run.sh && ./run.sh
```

Visit: **http://localhost:8000**

---

## 🔐 Default Admin Credentials

```
Username: admin
Password: Admin@123!
```

> ⚠️ Change these immediately in production via environment variables.

---

## 🌍 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URI` | `mongodb://localhost:27017/` | MongoDB connection string |
| `MONGODB_DATABASE` | `dialogue_summarizer_db` | Database name |
| `ADMIN_USERNAME` | `admin` | Admin username |
| `ADMIN_EMAIL` | `admin@dialoguesummarizer.com` | Admin email |
| `ADMIN_PASSWORD` | `Admin@123!` | Admin password |
| `RECAPTCHA_PUBLIC_KEY` | *(test key)* | Google reCAPTCHA v2 site key |
| `RECAPTCHA_PRIVATE_KEY` | *(test key)* | Google reCAPTCHA v2 secret key |
| `SECRET_KEY` | *(dev key)* | Django secret key |

Set via `.env` file or export before running:
```bash
export MONGODB_URI="mongodb+srv://user:pass@cluster.mongodb.net/"
export ADMIN_PASSWORD="MySecurePassword123!"
export RECAPTCHA_PUBLIC_KEY="your_google_recaptcha_site_key"
export RECAPTCHA_PRIVATE_KEY="your_google_recaptcha_secret_key"
```

---

## 📐 Project Structure

```
dialogue_summarizer/
├── manage.py
├── requirements.txt
├── run.sh
├── dialogue_summarizer/
│   ├── settings.py          # All configuration
│   ├── urls.py              # Root URL routing
│   └── wsgi.py
└── core/
    ├── apps.py              # App config + MongoDB init
    ├── db.py                # MongoDB CRUD layer
    ├── forms.py             # Django forms + validation
    ├── views.py             # All views (auth, dashboard, upload)
    ├── urls.py              # App URL patterns
    ├── middleware.py        # Security middleware
    ├── context_processors.py # Sidebar history injection
    └── templates/
        └── core/
            ├── base.html            # Layout with sidebar
            ├── login.html           # Login page
            ├── register.html        # Registration page
            ├── user_dashboard.html  # User dashboard
            ├── admin_dashboard.html # Admin overview
            ├── admin_users.html     # User management
            ├── admin_activity.html  # Activity log
            ├── upload.html          # File upload
            ├── summarize.html       # Dialogue summarizer
            ├── history.html         # History view
            └── profile.html         # Profile settings
```

---

## 🔒 Security Features

### Password Hashing
- **Algorithm**: PBKDF2-HMAC-SHA256
- **Iterations**: 310,000 (OWASP recommended 2024)
- **Salt**: 256-bit cryptographically random per user
- **Comparison**: Constant-time via `hmac.compare_digest()`

### File Security
- Every upload gets a **SHA-256 hash** computed server-side
- Files stored with hash-prefixed names to prevent enumeration
- Strict file extension allowlist (`.txt`, `.pdf`, `.docx`, `.csv`, `.json`)
- 10MB file size limit enforced

### Authentication & Session Security
- **reCAPTCHA v2** on login and registration
- **Brute-force protection**: 5 failed attempts → 15-minute IP lockout
- Sessions expire after 1 hour (configurable)
- `HttpOnly` and `SameSite=Lax` cookie flags
- All failed logins logged to `security.log`

### HTTP Security Headers
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`

### Access Control
- Login-required middleware protects all routes
- Role-based access: `admin` vs `user`
- Only **one admin** (created at startup)
- Admin cannot be deleted or deactivated

---

## 🧩 Integrating Your ML Model

Open `core/views.py` and replace `_generate_summary()`:

### Example: HuggingFace Transformers
```python
from transformers import pipeline

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def _generate_summary(text: str) -> str:
    result = summarizer(text, max_length=130, min_length=30, do_sample=False)
    return result[0]['summary_text']
```

### Example: OpenAI API
```python
import openai

def _generate_summary(text: str) -> str:
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Summarize the following dialogue concisely."},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content
```

### Example: Your Cloud Framework API
```python
import requests

def _generate_summary(text: str) -> str:
    r = requests.post("https://your-cloud-api.com/summarize", 
                      json={"text": text},
                      headers={"Authorization": "Bearer YOUR_KEY"})
    return r.json()["summary"]
```

---

## 📊 MongoDB Collections

| Collection | Purpose |
|-----------|---------|
| `users` | User accounts (hashed passwords, profiles, stats) |
| `upload_history` | Every upload/summarize action with SHA-256 hashes |
| `login_attempts` | Brute-force protection tracking (auto-expires) |
| `django_session` | Session storage |

---

## 🌐 URL Routes

| URL | Access | Description |
|-----|--------|-------------|
| `/login/` | Public | Login page with reCAPTCHA |
| `/register/` | Public | Registration with password strength |
| `/logout/` | Auth | Session logout |
| `/dashboard/` | User | User dashboard with stats |
| `/upload/` | User | File upload with SHA-256 |
| `/summarize/` | User | Dialogue summarization |
| `/history/` | User | Full activity history |
| `/profile/` | User | Profile settings |
| `/admin-dashboard/` | Admin | Admin overview |
| `/admin/users/` | Admin | User management |
| `/admin/activity/` | Admin | All platform activity |
| `/api/history/` | User | JSON history API (sidebar) |

---

## 🐳 Production Deployment (Example)

```bash
# 1. Set production environment variables
export DEBUG=False
export SECRET_KEY="your-very-long-random-secret-key"
export MONGODB_URI="mongodb+srv://..."
export ALLOWED_HOSTS="yourdomain.com"

# 2. Collect static files
python manage.py collectstatic

# 3. Run with Gunicorn
pip install gunicorn
gunicorn dialogue_summarizer.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

Use **Nginx** as reverse proxy + **SSL certificate** (Let's Encrypt) for HTTPS in production.

---

## 🎓 reCAPTCHA Setup

1. Go to https://www.google.com/recaptcha/admin/create
2. Choose **reCAPTCHA v2** → "I'm not a robot"
3. Add your domain
4. Copy **Site Key** → `RECAPTCHA_PUBLIC_KEY`
5. Copy **Secret Key** → `RECAPTCHA_PRIVATE_KEY`

The included test keys work on `localhost` for development.
