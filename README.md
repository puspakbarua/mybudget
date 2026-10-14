# MyBudget

A small personal budgeting app built with Django.

## Setup

1. Create and activate your virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run migrations:

```bash
python manage.py migrate
```

4. Start the development server:

```bash
python manage.py runserver
```

## Project structure

- `manage.py` — Django management script
- `config/` — project settings, URLs, and WSGI
- `apps/` — application packages
- `templates/` — shared templates
- `static/` — static assets

## Notes

- Your Django apps are organized under `apps/`.
- `.gitignore` excludes the virtualenv, database file, and editor artifacts.
