# Inventory Tracker - how to run

Tracks purchases, sales, stock and profit per item. See [README_STATS.md](README_STATS.md) for what each number in the dashboard means.

## Step 1: install uv (one time)
uv installs the right Python and the dependencies for you.

**Mac / Linux** (Terminal):

    curl -LsSf https://astral.sh/uv/install.sh | sh
or `brew install uv`.

**Windows** (PowerShell: press the Windows key, type "PowerShell", open it):

    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
or `winget install astral-sh.uv`.

Then **close and reopen** the terminal, and check it works:

    uv --version

## Step 2: run the app
Unzip the folder, then open a terminal inside it.

- **Mac:** open Terminal, type `cd ` (with a space), drag the folder into the window, press Enter.
- **Windows:** open the unzipped folder in File Explorer, click the address bar, type `powershell`, press Enter.

Then run:

    uv sync
    uv run python app.py

Open **http://localhost:5050** in your browser. Press Ctrl+C in the terminal to stop the app. To start it again later, run only `uv run python app.py` from the same folder.

The first `uv sync` needs internet (it downloads Python 3.11+ if missing, and Flask).

**Windows notes**
- If PowerShell says scripts are disabled when installing uv, the `-ExecutionPolicy ByPass` command above avoids that.
- If `uv` is "not recognized", close and reopen PowerShell. If it still fails, sign out and back in.
- Windows Firewall may ask about Python. You can click Cancel: the app only needs to run on this computer.
- Your data is saved in `inventory.db` in this folder.

## Alternative: double-click (no uv)
Needs Python 3 from python.org (on Windows, tick "Add python.exe to PATH").
**Mac:** double-click `start.command`. **Windows:** double-click `start.bat`.
If it does nothing:
- **Mac:** right-click the file > Open and confirm. Or in Terminal run `chmod +x start.command` then `./start.command`.
- **Windows:** if SmartScreen blocks it, click "More info" > "Run anyway".
- Delete any `.venv` folder that came with the zip, then try again. The uv steps above always work.

## Using it
1. The app starts empty. **Add entry > New item**: create each item (code, name, category).
2. **Add entry > Record a purchase** when stock comes in.
3. **Add entry > Record a sale** when you sell. A sale larger than the stock on hand is rejected, so enter the purchase first.
4. Open the **Dashboard** to see sales, profit and stock. **Transactions** lists entries, lets you delete mistakes, and has the backup download links.

## Your data and backups
Everything is saved in `inventory.db` next to the app. Nothing is sent anywhere. The app only runs on this computer (localhost) and cannot be opened from other devices.

**Automatic protection**
- **Daily backup:** the first time the app starts or you save anything each day, a copy is saved to the `backups` folder (next to `inventory.db`) as `daily-YYYY-MM-DD.db`. The last 30 are kept.
- **Backup before every delete:** a copy named `before-delete-<date>_<time>.db` is saved just before any entry is deleted, so a mistaken delete can be undone. The last 30 are kept.
- SQLite itself is crash-safe, so a power cut while saving will not corrupt the file.

**Manual downloads** (Transactions tab)
- *Download all data (CSV)*: a zip with `items.csv`, `purchases.csv` and `sales.csv`, which open in Excel.
- *Download database file*: a complete copy of `inventory.db`.
Both go to your browser's Downloads folder.

**Restore from a backup**
1. Stop the app (close the terminal window).
2. Copy the backup file you want from `backups/` over `inventory.db`.
3. Start the app again.

**Limit:** `backups/` is on the same computer as the database. If the disk fails or the laptop is lost, both are lost. Now and then, copy `backups/` or a downloaded export to cloud storage or a USB drive. To change the backup folder, edit `BACKUP_DIR` in `db.py`.
# inventory-tracker
