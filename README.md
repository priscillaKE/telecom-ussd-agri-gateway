# KilimoMoMo USSD Agriculture Service

KilimoMoMo is a Flask-based USSD service for farmers who need crop prices and seed delivery without a smartphone or mobile data. It accepts the form payload used by common telecom USSD gateways, returns `CON`/`END` responses, and records completed interactions in SQLite.

## What This Demonstrates

- Designing a multi-step USSD menu with predictable session input handling
- Building a Flask integration endpoint for telecom gateway requests
- Persisting auditable transactions with parameterized SQLite queries
- Separating production data from tests through database injection
- Testing both business logic and the HTTP boundary
- Adding a health endpoint suitable for deployment monitoring

## Run Locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

The service runs on `http://127.0.0.1:5000`.

## Try It

Check service status:

```powershell
curl.exe http://127.0.0.1:5000/health
```

Start the seed-order flow:

```powershell
curl.exe -X POST http://127.0.0.1:5000/ussd -d "sessionId=demo-1" -d "phoneNumber=0772000000" -d "text=2"
curl.exe -X POST http://127.0.0.1:5000/ussd -d "sessionId=demo-1" -d "phoneNumber=0772000000" -d "text=2*1"
```

Inspect recorded interactions:

```powershell
python check_db.py
```

## Test

The test suite uses temporary SQLite databases, so it never modifies local production data:

```powershell
python -m unittest -v
```

## Gateway Contract

`POST /ussd` accepts these form fields:

| Field | Purpose |
| --- | --- |
| `sessionId` | Gateway session identifier used for request tracing |
| `phoneNumber` | Farmer phone number stored with completed interactions |
| `text` | Asterisk-delimited menu path, such as `2*1` |

Responses begin with `CON` while the session continues and `END` when it completes. Set `USSD_DB_NAME` to point the service at a different SQLite database.

## Project Structure

| File | Responsibility |
| --- | --- |
| `app.py` | Flask HTTP gateway and health endpoint |
| `ussd_app.py` | USSD menu logic and transaction persistence |
| `test_app.py` | Business logic and endpoint tests |
| `check_db.py` | Local audit utility for recorded transactions |