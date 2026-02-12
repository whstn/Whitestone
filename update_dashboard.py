import pdfplumber
import json
import os
from datetime import datetime

# CHANGE THIS LINE TO YOUR PDF FILE NAME EACH DAY
pdf_file = "daily_statement.pdf"  # Put today's PDF in this folder and rename it

cumulative_file = "cumulative_data.json"

# Load existing cumulative data (or start fresh)
if os.path.exists(cumulative_file):
    with open(cumulative_file, "r") as f:
        cumulative = json.load(f)
else:
    cumulative = {
        "history": [],  # list of daily entries
        "start_equity": 1000.0,  # your starting balance
        "start_date": "2025-12-18"
    }

# Extract today's data from PDF
today_data = {}
try:
    with pdfplumber.open(pdf_file) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"

    lines = text.splitlines()
    for line in lines:
        line = line.strip()
        if "Ending Equity" in line or "Account Equity" in line:
            today_data["equity"] = float(line.split()[-1].replace(',', ''))
        if "Net P/L" in line or "Daily P/L" in line:
            today_data["pnl"] = float(line.split()[-1].replace(',', ''))
        if "Date" in line and ("Equity" in line or "Statement" in line):
            today_data["date"] = line.split()[1]

    if not today_data.get("date"):
        today_data["date"] = datetime.now().strftime("%Y-%m-%d")

    # Calculate running totals
    prev_equity = cumulative["history"][-1]["equity"] if cumulative["history"] else cumulative["start_equity"]
    today_data["cumulative_pnl"] = prev_equity + today_data.get("pnl", 0) - cumulative["start_equity"]
    today_data["running_equity"] = today_data["equity"]

    # Add to history
    cumulative["history"].append(today_data)

    # Save updated cumulative file
    with open(cumulative_file, "w") as f:
        json.dump(cumulative, f, indent=2)

    print("Success! cumulative_data.json updated with today's data.")
    print("Now push this file to GitHub using GitHub Desktop.")

except Exception as e:
    print("Error reading PDF:", e)
    print("Make sure the file is named 'daily_statement.pdf' and in this folder.")

input("Press Enter to close...")