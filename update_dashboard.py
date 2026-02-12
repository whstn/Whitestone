import pdfplumber
import json
import os
import glob
from datetime import datetime

print("Starting cumulative PnL tracker...")
print("Script folder:", os.path.dirname(os.path.abspath(__file__)))

script_folder = os.path.dirname(os.path.abspath(__file__))
pdf_folder = script_folder

cumulative_file = os.path.join(script_folder, "cumulative_data.json")

# Load or initialize
if os.path.exists(cumulative_file):
    try:
        with open(cumulative_file, "r") as f:
            cumulative = json.load(f)
    except json.JSONDecodeError:
        print("cumulative_data.json corrupted — starting fresh")
        cumulative = {
            "start_date": "2026-02-12",
            "start_pnl": 0.0,
            "daily_entries": []
        }
else:
    cumulative = {
        "start_date": "2026-02-12",
        "start_pnl": 0.0,
        "daily_entries": []
    }

processed = {entry.get("pdf_file", "") for entry in cumulative["daily_entries"]}

pdf_files = glob.glob(os.path.join(pdf_folder, "**", "*Performance*.pdf"), recursive=True)

print(f"Found {len(pdf_files)} PDF files:")
for f in pdf_files:
    print(" -", os.path.basename(f))

new_added = False

for pdf_path in sorted(pdf_files):
    pdf_name = os.path.basename(pdf_path)
    if pdf_name in processed:
        print(f"Already processed: {pdf_name}")
        continue

    print(f"\nProcessing: {pdf_name}")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            all_tables = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                all_tables.extend(page.extract_tables())

        today = {"pnl": 0.0}

        # Text fallback for summary (e.g. "Total P/L $1,335.90")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in lines:
            if "Total P/L" in line or "Gross P/L" in line:
                parts = line.split()
                for part in reversed(parts):
                    try:
                        val = float(part.replace(',', '').replace('$', ''))
                        today["pnl"] = val
                        print(f"  Found summary Total P/L: ${val:.2f}")
                        break
                    except:
                        pass

        # Table extraction - look for trades table (has "P&L" header or numeric last column)
        for table in all_tables:
            if len(table) > 1:
                header = [str(cell).strip().lower() for cell in table[0]]
                if "p&l" in header or "profit/loss" in header or "pnl" in header:
                    pnl_col = header.index("p&l") if "p&l" in header else -1
                    print(f"  Found trades table with {len(table)-1} trades. P&L column: {pnl_col}")
                    for row in table[1:]:
                        if len(row) > pnl_col and row[pnl_col]:
                            pnl_str = str(row[pnl_col]).strip().replace(',', '').replace('$', '').replace('(', '-').replace(')', '')
                            try:
                                pnl_val = float(pnl_str)
                                today["pnl"] += pnl_val
                                print(f"  Added trade PnL: ${pnl_val:.2f}")
                            except ValueError:
                                print(f"  Could not parse: '{pnl_str}'")

        if today["pnl"] == 0.0:
            print("  No PnL found — skipping")
            continue

        # Date from filename
        try:
            date_part = pdf_name.split('.')[1]
            dt = datetime.strptime(date_part, "%Y%m%d")
            today["date"] = dt.strftime("%Y-%m-%d")
        except:
            today["date"] = datetime.now().strftime("%Y-%m-%d")

        # Cumulative
        last_cumulative = cumulative["daily_entries"][-1]["cumulative_pnl"] if cumulative["daily_entries"] else 0.0
        today["cumulative_pnl"] = round(last_cumulative + today["pnl"], 2)
        today["pdf_file"] = pdf_name

        cumulative["daily_entries"].append(today)
        new_added = True

        print(f"  Added {today['date']}: Daily PnL ${today['pnl']:.2f} | Cumulative ${today['cumulative_pnl']:.2f}")

    except Exception as e:
        print(f"  Error on {pdf_name}: {e}")

if new_added:
    with open(cumulative_file, "w") as f:
        json.dump(cumulative, f, indent=2)
    print("\nSuccess! cumulative_data.json updated.")
    print("Now open GitHub Desktop → Commit → Push")
else:
    print("\nNo new PDFs or no PnL found.")
    print("Folder checked:", pdf_folder)

input("\nPress Enter to close...")