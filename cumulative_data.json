import pdfplumber
import json
import os
import glob
from datetime import datetime

# Folder where PDFs are (current folder)
pdf_folder = "."

# Cumulative file
cumulative_file = "cumulative_data.json"

# Load or create cumulative data
if os.path.exists(cumulative_file):
    with open(cumulative_file, "r") as f:
        cumulative = json.load(f)
else:
    cumulative = {
        "start_balance": 0.0,
        "start_date": "2026-02-12",
        "daily_entries": []  # list of {date, pnl, cumulative_pnl}
    }

processed_files = {entry["pdf_file"] for entry in cumulative["daily_entries"]}

# Find all Performance.*.pdf files not yet processed
pdf_files = glob.glob(os.path.join(pdf_folder, "Performance.*.pdf"))

new_data_added = False

for pdf_path in sorted(pdf_files):
    pdf_name = os.path.basename(pdf_path)
    if pdf_name in processed_files:
        continue  # already done

    print(f"Processing new file: {pdf_name}")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"

        lines = text.splitlines()
        today = {}
        for line in lines:
            line = line.strip()
            if "Net P/L" in line or "Daily P/L" in line or "P/L" in line:
                try:
                    val = line.split()[-1].replace(',', '')
                    today["pnl"] = float(val)
                except:
                    pass
            # Try to get date from filename if not in text
            if not today.get("date"):
                try:
                    date_str = pdf_name.split('.')[1]
                    dt = datetime.strptime(date_str, "%Y%m%d")
                    today["date"] = dt.strftime("%Y-%m-%d")
                except:
                    today["date"] = datetime.now().strftime("%Y-%m-%d")

        if "pnl" not in today:
            print(f"No PnL found in {pdf_name} — skipping")
            continue

        # Calculate cumulative PnL
        prev_cumulative = cumulative["daily_entries"][-1]["cumulative_pnl"] if cumulative["daily_entries"] else 0.0
        today["cumulative_pnl"] = prev_cumulative + today["pnl"]
        today["pdf_file"] = pdf_name

        cumulative["daily_entries"].append(today)
        new_data_added = True
        print(f"Added: {today['date']} - PnL: {today['pnl']}, Cumulative: {today['cumulative_pnl']}")

    except Exception as e:
        print(f"Error on {pdf_name}: {e}")

if new_data_added:
    # Save updated cumulative
    with open(cumulative_file, "w") as f:
        json.dump(cumulative, f, indent=2)
    print("\nSuccess! cumulative_data.json updated with new day(s).")
else:
    print("\nNo new PDFs found or no PnL data — nothing updated.")

print("Now open GitHub Desktop, commit & push the changes.")
input("Press Enter to close...")