
import logging
import pandas as pd
import yfinance as yf
import winsound
from typing import Dict
from datetime import datetime, time as t
import time
import pytz
import os
from tabulate import tabulate
import gspread
from google.oauth2.service_account import Credentials



# -------------- Setup Logging ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_DATE = datetime.now().strftime("%Y-%m-%d")
LOG_FILE = os.path.join(LOG_DIR, f"stock_alert_{LOG_DATE}.log")

# ---------- Google Sheets Config ----------
GOOGLE_CREDS_FILE = os.path.join(BASE_DIR, "google_creds.json")
GOOGLE_SHEET_NAME = "Stock Alerts"     # Exact sheet name
GOOGLE_WORKSHEET_NAME = "Sheet1"       # Tab name
UPDATE_COLUMNS = ["current_price", "last_updated"]

# ================= CONFIG =================

EXCEL_PATH = r"Audio\stocks.xlsx"
INTRO_SOUND_PATH = r"Audio\intro.wav"
ALERT_SOUND_PATH = r"Audio\alert.wav"
CLOSING_SOUND_PATH = r"Audio\closing.wav"
FAILURE_SOUND_PATH = r"Audio\failure.wav"

CHECK_INTERVAL_SECONDS = 60  # 3 minutes

REQUEST_TIMEOUT = 10
MAX_RETRIES = 3

# =========================================

# Track alert state to avoid repeated alerts
alert_state: Dict[str, bool] = {}

# -------------- Logging -------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
# -------------- Market Hours --------------
IST = pytz.timezone("Asia/Kolkata")

# -------------Google sheet ----------------

def get_gsheet_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_file(
        GOOGLE_CREDS_FILE,
        scopes=scopes
    )

    return gspread.authorize(creds)

def current_ist_timestamp() -> str:
     return datetime.now(IST).strftime("%Y-%m-%d %I:%M:%S %p")

def is_market_open() -> bool:
    now = datetime.now(IST)

    # Monday = 0, Sunday = 6
    if now.weekday() >= 5:
        
        return False  # Weekend


    market_open = t(9, 15)
    market_close = t(15, 30)
    
    return market_open <= now.time() <= market_close

# -------------- Core Functions ------------

def read_google_sheet():
    try:
        client = get_gsheet_client()
        sheet = client.open(GOOGLE_SHEET_NAME)
        worksheet = sheet.worksheet(GOOGLE_WORKSHEET_NAME)

        records = worksheet.get_all_records()
        df = pd.DataFrame(records)

        if df.empty:
            raise ValueError("Google Sheet is empty")

        # Normalize
        df["exchange"] = df["exchange"].str.upper().str.strip()
        df["symbol"] = df["symbol"].str.strip()
        df["alert_for"] = df["alert_for"].str.lower().str.strip()

        # IMPORTANT: track actual sheet row numbers (header = row 1)
        df["_sheet_row"] = range(2, len(df) + 2)

        return df, worksheet

    except Exception as e:
        logging.error(f"Failed to read Google Sheet: {e}")
        return pd.DataFrame(), None

def update_google_sheet_cells(worksheet, df):
    try:
        cell_updates = []

        for _, row in df.iterrows():
            sheet_row = row["_sheet_row"]

            if "current_price" in df.columns:
                cell_updates.append(
                    gspread.Cell(sheet_row,
                                 df.columns.get_loc("current_price") + 1,
                                 row["current_price"])
                )

            if "last_updated" in df.columns:
                cell_updates.append(
                    gspread.Cell(
                    sheet_row,
                        df.columns.get_loc("last_updated") + 1,
                        row["last_updated"]
                    )
                )

        if cell_updates:
            worksheet.update_cells(cell_updates)


    except Exception as e:
        logging.error(f"Failed to update Google Sheet cells: {e}")


def update_google_sheet(df: pd.DataFrame):
    try:
        client = get_gsheet_client()
        sheet = client.open(GOOGLE_SHEET_NAME)
        worksheet = sheet.worksheet(GOOGLE_WORKSHEET_NAME)

        worksheet.clear()
        worksheet.update(
            [df.columns.values.tolist()] + df.values.tolist()
        )

    except Exception as e:
        logging.error(f"Failed to update Google Sheet: {e}")

def read_excel() -> pd.DataFrame:
    #Read and validate stock alert Excel file.
    try:
        df = pd.read_excel(EXCEL_PATH)
        required_cols = {"stock_name", "symbol", "exchange", "alert_price"}

        if not required_cols.issubset(df.columns):
            raise ValueError(f"Excel must contain columns: {required_cols}")

        df["exchange"] = df["exchange"].str.upper().str.strip()
        df["symbol"] = df["symbol"].str.strip()

        return df

    except Exception as e:
        logging.error(f"Failed to read Excel file: {e}")
        return pd.DataFrame()


def format_symbol(symbol: str, exchange: str) -> str:
    """Convert symbol to Yahoo Finance format."""
    if exchange == "NSE":
        return f"{symbol}.NS"
    elif exchange == "BSE":
        return f"{symbol}.BO"
    else:
        raise ValueError(f"Unsupported exchange: {exchange}")


def fetch_price(yahoo_symbol: str) -> float | None:
    """Fetch current market price reliably for Indian stocks."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            ticker = yf.Ticker(yahoo_symbol)

            # Attempt 1: fast_info (may be None for NSE/BSE)
            try:
                price = ticker.fast_info.get("last_price")
                if price:
                    return float(price)
            except Exception:
                pass

            # Attempt 2: intraday data (most reliable during market hours)
            hist = ticker.history(period="1d", interval="1m")
            if not hist.empty:
                return float(hist["Close"].iloc[-1])

            # Attempt 3: daily close (works even after market hours)
            hist = ticker.history(period="1d")
            if not hist.empty:
                return float(hist["Close"].iloc[-1])

            raise ValueError("No price data returned")

        except Exception as e:
            logging.warning(
                f"[{yahoo_symbol}] Price fetch failed (attempt {attempt}): {e}"
            )
            time.sleep(2)

    logging.error(f"[{yahoo_symbol}] All retries failed")
    return None


def play_alert(path=ALERT_SOUND_PATH,name="alert"):
    """Play alert sound (non-blocking)."""
    try:
        print(f"Playing {name} sound...")
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        time.sleep(10) # Let the sound play for 10 seconds
    except Exception as e:
        logging.error(f"Failed to play alert sound: {e}")


def check_alerts(df: pd.DataFrame, worksheet):
    updated_rows = []

    for idx, row in df.iterrows():
        try:
            yahoo_symbol = format_symbol(row["symbol"], row["exchange"])
            alert_price = float(row["alert_price"])
            alert_for = row["alert_for"].strip().lower()

            last_price = row["last_exit_price"]
            current_price = fetch_price(yahoo_symbol)

            #logging.info(f"Checked {row['stock_name']} ({yahoo_symbol}): {current_price}")

            if current_price is None:
                continue

            # ---------- Alert logic ----------
            alert_triggered = False

            if alert_for == "high":
                if current_price >= alert_price:
                    alert_triggered = True

            elif alert_for == "low":
                if current_price <= alert_price:
                    alert_triggered = True

            else:
                logging.warning(f"Invalid alert_for value: {alert_for}")
                continue

            if alert_triggered:
                logging.info(
                    f"ALERT | {row['stock_name']} | "
                    f"{alert_for.upper()} | "
                    f"Last Exit Price: {last_price} | "
                    f"Price: {current_price} | "
                    f"Alert: {alert_price}"
                )
                play_alert()

            # ---------- Update dataframe ----------
            df.at[idx, "last_updated"] = current_ist_timestamp()
            df.at[idx, "current_price"] = round(current_price, 2)
            #df.at[idx, "last_exit_price"] = round(current_price, 2)

            updated_rows.append([
                row["stock_name"],
                row["symbol"],
                alert_for,
                row["current_entry"],
                last_price,
                alert_price,
                round(current_price, 2)
            ])

        except Exception as e:
            logging.error(f"Row error {row['stock_name']}: {e}")

    # ---------- Write back to Excel ----------
    #df.to_excel(EXCEL_PATH, index=False)
    update_google_sheet_cells(worksheet, df)

    # ---------- Console display ----------
    """if updated_rows:
        print("\n" + tabulate(
            updated_rows,
            headers=["Stock", "Symbol", "Alert For", "Last Exit Price", "Alert Price", "Current Price"],
            tablefmt="pretty"
        ))"""


def main_loop():

    logging.info("Stock alert service started")
    
    if not is_market_open():
        logging.info("Market is closed — shutting down application")
        play_alert(FAILURE_SOUND_PATH, "shutting down")
        return  # Clean exit
    logging.info("Market is open — starting monitoring")
    play_alert(INTRO_SOUND_PATH)
    while True:
        try:
            logging.info("Checking stock prices...")
            if is_market_open():
                #df = read_excel()
                """df = read_google_sheet()
                if not df.empty:
                    check_alerts(df)"""
                df, worksheet = read_google_sheet()
                if not df.empty:
                    check_alerts(df, worksheet)
            else:
                logging.info("Market closed during runtime — shutting down")
                break

        except Exception as e:
            logging.critical(f"Unhandled error: {e}")

        logging.info("Checking Completed. Sleeping...")
        time.sleep(CHECK_INTERVAL_SECONDS)

    logging.info("Stock alert service stopped")
    play_alert(CLOSING_SOUND_PATH, "closing")


# -------------- Entry Point ----------------

if __name__ == "__main__":
    main_loop()
