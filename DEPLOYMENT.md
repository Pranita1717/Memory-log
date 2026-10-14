# Memory Log deployment

## Render settings
- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`

## Required environment variables on Render
- `MONGO_URI`: MongoDB Atlas connection string (do not commit it)
- `SECRET_KEY`: a long random secret string

`database.json` is intentionally excluded from Git because it contains sample account credentials and potentially personal/location data. This app uses MongoDB via `db.py`; data from a local MongoDB database is not automatically copied to Atlas.
