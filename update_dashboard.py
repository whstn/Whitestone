import pdfplumber
import json
import os
import glob
from datetime import datetime

# This folder
pdf_folder = "."

# Cumulative file (will be created if missing)
cumulative_file = "cumulative_data.json"

# Load or initialize cumulative data
if os.path.exists(cumulative_file):
    with open(cumulative_file, "r") as f:
        cumulative = json.load(f)
else:
    cumulative = {
        "start_date": "2026-02-12",
        "start_pnl": 0.0,
        "daily_entries": []   # each day: {"date", "pnl", "cumulative_pnl", "pdf_file"}
    }

# Already processed PDFs (to avoid duplicates)
processed = {entry.get("pdf_file", "") for entry in cumulative["daily_entries"]}

# Find all Performance.*.pdf files
pdf_files = glob.glob(os.path.join(pdf_folder, "Performance.*.pdf"))

new_added = False

for pdf_path in sorted(pdf_files):
    pdf_name = os.path.basename(pdf_path)
    if pdf_name in processed:
        continue  # skip already done

    print(f"New file found: {pdf_name}")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"

        lines = [line.strip() for line in text.splitlines() if line.strip()]

        today = {"pnl": 0.0}
        for line in lines:
            if "Net P/L" in line or "Daily P/L" in line or "P/L" in line or "Profit/Loss" in line:
                parts = line.split()
                for part in parts[-3:]:  # check last few words
                    try:
                        val = float(part.replace(',', ''))
                        today["pnl"] = val
                        break
                    except:
                        pass

        # Date from filename (Performance.YYYYMMDD....pdf)
        try:
            date_part = pdf_name.split('.')[1]
            dt = datetime.strptime(date_part, "%Y%m%d")
            today["date"] = dt.strftime("%Y-%m-%d")
        except:
            today["date"] = datetime.now().strftime("%Y-%m-%d")

        # Cumulative PnL
        last_cumulative = cumulative["daily_entries"][-1]["cumulative_pnl"] if cumulative["daily_entries"] else 0.0
        today["cumulative_pnl"] = round(last_cumulative + today["pnl"], 2)
        today["pdf_file"] = pdf_name

        cumulative["daily_entries"].append(today)
        new_added = True

        print(f"  → Added {today['date']}: Daily PnL ${today['pnl']:.2f} | Cumulative ${today['cumulative_pnl']:.2f}")

    except Exception as e:
        print(f"  → Error reading {pdf_name}: {e}")

if new_added:
    with open(cumulative_file, "w") as f:
        json.dump(cumulative, f, indent=2)
    print("\nUpdated cumulative_data.json with new day(s).")
    print("Now open GitHub Desktop → Commit → Push")
else:
    print("\nNo new PDFs or no PnL found — nothing changed.")

input("\nPress Enter to close...")
