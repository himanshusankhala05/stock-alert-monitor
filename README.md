# Stock Alert Monitor

A Python-based real-time stock monitoring system that tracks NSE and BSE stocks, fetches live market prices using Yahoo Finance, updates Google Sheets automatically, and generates audio alerts when predefined price levels are reached.

## Overview

Stock Alert Monitor helps traders and investors automate stock price tracking during market hours. The application continuously monitors a watchlist, compares live prices against configured target levels, and notifies users through audio alerts when conditions are met.

The system integrates with Google Sheets for centralized watchlist management and maintains detailed logs for monitoring and troubleshooting.

---

## Features

### Real-Time Stock Monitoring

* Live stock price fetching using Yahoo Finance
* Supports NSE and BSE listed stocks
* Automatic data refresh at configurable intervals
* Retry mechanism for failed requests

### Smart Price Alerts

* High-price alerts when price crosses above a target
* Low-price alerts when price falls below a target
* Configurable alert conditions per stock
* Audio notifications for triggered alerts

### Google Sheets Integration

* Reads stock watchlist from Google Sheets
* Updates current market prices automatically
* Maintains last updated timestamps
* Centralized cloud-based stock management

### Market Hours Awareness

* Operates only during Indian market hours
* Market Open: 9:15 AM IST
* Market Close: 3:30 PM IST
* Automatic shutdown after market close

### Audio Notifications

* Startup notification
* Price alert notification
* Market closing notification
* Failure/error notification

### Logging & Monitoring

* Daily log file generation
* Price monitoring history
* Alert tracking
* Error and exception logging

---

## Project Structure

```text
Stock-Alert-Monitor/
│
├── main.py
│
├── Audio/
│   ├── intro.wav
│   ├── alert.wav
│   ├── closing.wav
│   └── failure.wav
│
├── Data/
│   └── Stock Alerts.xlsx
│
├── Logs/
│
├── google_creds.json
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Technology Stack

### Python Libraries

```bash
pip install pandas yfinance gspread google-auth pytz tabulate openpyxl
```

Libraries Used:

* pandas
* yfinance
* gspread
* google-auth
* pytz
* openpyxl
* logging
* winsound
* tabulate

---

## Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/stock-alert-monitor.git
cd stock-alert-monitor
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Google Sheets API

1. Create a project in Google Cloud Console.
2. Enable:

   * Google Sheets API
   * Google Drive API
3. Create a Service Account.
4. Download the credentials JSON file.
5. Save it as:

```text
google_creds.json
```

6. Share your Google Sheet with the Service Account email.

---

## Google Sheet Configuration

Create a Google Sheet named:

```text
Stock Alerts
```

Suggested columns:

| Column          | Description  |
| --------------- | ------------ |
| stock_name      | Company Name |
| symbol          | Stock Symbol |
| exchange        | NSE / BSE    |
| alert_price     | Target Price |
| alert_for       | high / low   |
| current_price   | Auto Updated |
| last_updated    | Auto Updated |
| current_entry   | Entry Price  |
| last_exit_price | Exit Price   |

Example:

| stock_name | symbol   | exchange | alert_price | alert_for |
| ---------- | -------- | -------- | ----------- | --------- |
| Reliance   | RELIANCE | NSE      | 1600        | high      |
| TCS        | TCS      | NSE      | 3400        | low       |

---

## Configuration

Example path setup using pathlib:

```python
from pathlib import Path

AUDIO_DIR = Path("Audio")
DATA_DIR = Path("Data")

EXCEL_PATH = DATA_DIR / "Stock Alerts.xlsx"

INTRO_SOUND_PATH = AUDIO_DIR / "intro.wav"
ALERT_SOUND_PATH = AUDIO_DIR / "alert.wav"
CLOSING_SOUND_PATH = AUDIO_DIR / "closing.wav"
FAILURE_SOUND_PATH = AUDIO_DIR / "failure.wav"
```

---

## Running the Application

```bash
python main.py
```

Or execute using a batch file:

```bash
stock_alert.bat
```

---

## Alert Logic

### High Alert

Triggered when:

```text
Current Price >= Alert Price
```

### Low Alert

Triggered when:

```text
Current Price <= Alert Price
```

---

## Logs

Daily logs are automatically generated and stored in the Logs directory.

Example:

```text
Logs/stock_alert_2026-06-10.log
```

Logs include:

* Application startup
* Market status
* Price checks
* Triggered alerts
* Errors and warnings
* Shutdown events

---

## Future Enhancements

* Telegram notifications
* WhatsApp alerts
* Email alerts
* Portfolio tracking
* Technical indicator alerts
* Web dashboard
* Cloud deployment
* Option chain monitoring
* Multi-watchlist support

---

## Security Notes

Do not commit sensitive files:

```text
google_creds.json
```

Add the following to `.gitignore`:

```gitignore
google_creds.json
Logs/
*.log
__pycache__/
*.pyc
venv/
.env
```

---

## Disclaimer

This project is intended for educational and personal trading assistance purposes only.

It does not provide financial advice, investment recommendations, or trading signals. Users should perform their own research and risk assessment before making investment decisions.

---

## Author

**Himanshu Sankhala**

Automation | Python Development | Financial Markets | Data Analytics

---

## License

This project is licensed for personal and educational use.
