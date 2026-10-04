import csv
import io
import tempfile
import zipfile
from collections import defaultdict
from datetime import date, datetime, timedelta

from flask import Flask, Response, jsonify, request, send_file, send_from_directory

import db

app = Flask(__name__, static_folder="static", static_url_path="")
db.init()
db.daily_backup()


@app.before_request
def protect_data():
    if request.method != "GET":
        db.daily_backup()
    if request.method == "DELETE":
        db.backup_before_delete()

# ---------- helpers ----------
def period_range(name):
    t = date.today()
    y = t - timedelta(days=1)
    first_this_month = t.replace(day=1)
    last_month_end = first_this_month - timedelta(days=1)
    ranges = {
        "today": (t, t),
        "yesterday": (y, y),
        "last7": (t - timedelta(days=7), y),
        "last30": (t - timedelta(days=30), y),
        "this_month": (first_this_month, t),
        "last_month": (last_month_end.replace(day=1), last_month_end),
        "last90": (t - timedelta(days=90), y),
        "all": (date(2000, 1, 1), t),
    }
    return ranges[name]


def get_range():
    if request.args.get("from") and request.args.get("to"):
        return request.args["from"], request.args["to"]
    a, b = period_range(request.args.get("period", "last30"))
    return a.isoformat(), b.isoformat()


def ledger(con, item=None):
    """Replay all transactions chronologically and compute, per sale, the cost of goods
    using the weighted-average cost at that moment. Returns (sales_rows, stock, stock_value)."""
    q = "SELECT item_code, date_of_purchase d, quantity q, purchased_price p, 0 kind FROM purchases {w} " \
        "UNION ALL SELECT item_code, date_of_sold, quantity_sold, sold_price, 1 FROM sales {w} ORDER BY d, kind"
    w, args = ("WHERE item_code=?", [item, item]) if item else ("", [])
    qty, avg = defaultdict(int), defaultdict(float)
    sales = []
    for r in con.execute(q.format(w=w), args):
        c = r["item_code"]
        if r["kind"] == 0:
            total = qty[c] * avg[c] + r["q"] * r["p"]
            qty[c] += r["q"]
            avg[c] = total / qty[c]
        else:
            qty[c] -= r["q"]
            sales.append({"item_code": c, "date": r["d"], "qty": r["q"],
                          "revenue": r["q"] * r["p"], "cogs": r["q"] * avg[c]})
    return sales, dict(qty), {c: qty[c] * avg[c] for c in qty}


def bucket(d, group):
    dt = datetime.strptime(d, "%Y-%m-%d").date()
    if group == "week":
        return (dt - timedelta(days=dt.weekday())).isoformat()
    if group == "month":
        return dt.strftime("%Y-%m-01")
    return d


# ---------- read API ----------
@app.get("/api/items")
def items():
    with db.connect() as con:
        _, stock, value = ledger(con)
        rows = [dict(r) | {"stock": stock.get(r["item_code"], 0), "stock_value": round(value.get(r["item_code"], 0), 2)}
                for r in con.execute("SELECT * FROM items ORDER BY item_code")]
    return jsonify(rows)


@app.post("/api/items")
def add_item():
    j = request.get_json()
    try:
        with db.connect() as con:
            con.execute("INSERT INTO items VALUES (?,?,?)",
                        (j["item_code"].strip(), j["name"].strip(), j.get("category", "General").strip() or "General"))
    except Exception as e:
        return jsonify(error=str(e)), 400
    return jsonify(ok=True)


@app.get("/api/summary")
def summary():
    """KPIs for a period, compared with the previous period of equal length."""
    a, b = get_range()
    item = request.args.get("item") or None
    da, dbb = datetime.strptime(a, "%Y-%m-%d").date(), datetime.strptime(b, "%Y-%m-%d").date()
    n = (dbb - da).days + 1
    pa, pb = (da - timedelta(days=n)).isoformat(), (da - timedelta(days=1)).isoformat()
    with db.connect() as con:
        sales, stock, value = ledger(con, item)
        bought = con.execute("SELECT COALESCE(SUM(quantity),0) q, COALESCE(SUM(quantity*purchased_price),0) s FROM purchases "
                             "WHERE date_of_purchase BETWEEN ? AND ?" + (" AND item_code=?" if item else ""),
                             [a, b] + ([item] if item else [])).fetchone()

    def agg(lo, hi):
        rs = [s for s in sales if lo <= s["date"] <= hi]
        rev, cogs = sum(s["revenue"] for s in rs), sum(s["cogs"] for s in rs)
        return {"units_sold": sum(s["qty"] for s in rs), "revenue": rev, "cogs": cogs, "profit": rev - cogs,
                "margin": (rev - cogs) / rev if rev else 0}

    cur = agg(a, b)
    cur.update(units_bought=bought["q"], purchase_spend=bought["s"],
               stock_units=sum(stock.values()), stock_value=sum(value.values()))
    return jsonify(range=[a, b], prev_range=[pa, pb], current=cur, previous=agg(pa, pb))


@app.get("/api/timeseries")
def timeseries():
    a, b = get_range()
    group = request.args.get("group", "day")
    item = request.args.get("item") or None
    with db.connect() as con:
        sales, _, _ = ledger(con, item)
        pur = con.execute("SELECT date_of_purchase d, quantity*purchased_price s FROM purchases WHERE date_of_purchase BETWEEN ? AND ?"
                          + (" AND item_code=?" if item else ""), [a, b] + ([item] if item else [])).fetchall()
    out = defaultdict(lambda: {"revenue": 0, "cogs": 0, "units": 0, "purchases": 0})
    for s in sales:
        if a <= s["date"] <= b:
            o = out[bucket(s["date"], group)]
            o["revenue"] += s["revenue"]; o["cogs"] += s["cogs"]; o["units"] += s["qty"]
    for p in pur:
        out[bucket(p["d"], group)]["purchases"] += p["s"]
    rows = [{"bucket": k, **{m: round(v, 2) for m, v in o.items()}, "profit": round(o["revenue"] - o["cogs"], 2)}
            for k, o in sorted(out.items())]
    return jsonify(rows)


@app.get("/api/item-stats")
def item_stats():
    """One row per item: the 'which products matter' table."""
    a, b = get_range()
    with db.connect() as con:
        sales, stock, value = ledger(con)
        names = {r["item_code"]: dict(r) for r in con.execute("SELECT * FROM items")}
        bought = {r["item_code"]: r["q"] for r in con.execute(
            "SELECT item_code, SUM(quantity) q FROM purchases WHERE date_of_purchase BETWEEN ? AND ? GROUP BY item_code", (a, b))}
    agg = defaultdict(lambda: {"units_sold": 0, "revenue": 0.0, "cogs": 0.0})
    for s in sales:
        if a <= s["date"] <= b:
            g = agg[s["item_code"]]
            g["units_sold"] += s["qty"]; g["revenue"] += s["revenue"]; g["cogs"] += s["cogs"]
    days = max(1, (datetime.strptime(b, "%Y-%m-%d") - datetime.strptime(a, "%Y-%m-%d")).days + 1)
    rows = []
    only = request.args.get("item") or None
    for c, meta in names.items():
        if only and c != only:
            continue
        g = agg[c]; rev = g["revenue"]
        daily = g["units_sold"] / days
        rows.append({**meta, **g, "profit": rev - g["cogs"], "margin": (rev - g["cogs"]) / rev if rev else 0,
                     "units_bought": bought.get(c, 0), "stock": stock.get(c, 0), "stock_value": value.get(c, 0),
                     "days_cover": round(stock.get(c, 0) / daily, 1) if daily else None})
    return jsonify(rows)


@app.get("/api/transactions")
def transactions():
    item = request.args.get("item") or None
    w, args = (" WHERE item_code=?", [item, item]) if item else ("", [])
    with db.connect() as con:
        rows = con.execute(
            "SELECT 'purchase' type, id, item_code, date_of_purchase date, quantity qty, purchased_price price FROM purchases" + w +
            " UNION ALL SELECT 'sale', id, item_code, date_of_sold, quantity_sold, sold_price FROM sales" + w +
            " ORDER BY date DESC, id DESC LIMIT 200", args).fetchall()
    return jsonify([dict(r) for r in rows])


# ---------- write API ----------
def _validate(j):
    if not j.get("item_code") or not j.get("date"):
        raise ValueError("item_code and date are required")
    datetime.strptime(j["date"], "%Y-%m-%d")
    q, p = int(j["quantity"]), float(j["price"])
    if q <= 0 or p < 0:
        raise ValueError("quantity must be > 0 and price >= 0")
    return j["item_code"], j["date"], q, p


@app.post("/api/purchases")
def add_purchase():
    try:
        c, d, q, p = _validate(request.get_json())
        with db.connect() as con:
            con.execute("INSERT INTO purchases (item_code,date_of_purchase,quantity,purchased_price) VALUES (?,?,?,?)", (c, d, q, p))
    except Exception as e:
        return jsonify(error=str(e)), 400
    return jsonify(ok=True)


@app.post("/api/sales")
def add_sale():
    try:
        c, d, q, p = _validate(request.get_json())
        with db.connect() as con:
            _, stock, _ = ledger(con, c)
            if stock.get(c, 0) < q:
                raise ValueError(f"Only {stock.get(c, 0)} units of {c} in stock")
            con.execute("INSERT INTO sales (item_code,date_of_sold,quantity_sold,sold_price) VALUES (?,?,?,?)", (c, d, q, p))
    except Exception as e:
        return jsonify(error=str(e)), 400
    return jsonify(ok=True)


@app.delete("/api/<kind>/<int:rid>")
def delete(kind, rid):
    if kind not in ("purchases", "sales"):
        return jsonify(error="bad kind"), 404
    with db.connect() as con:
        con.execute(f"DELETE FROM {kind} WHERE id=?", (rid,))
    return jsonify(ok=True)


@app.get("/api/export.zip")
def export_zip():
    """All data as CSV files (opens in Excel), zipped."""
    buf = io.BytesIO()
    with db.connect() as con, zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for table in ("items", "purchases", "sales"):
            cur = con.execute(f"SELECT * FROM {table}")
            out = io.StringIO()
            w = csv.writer(out)
            w.writerow([c[0] for c in cur.description])
            w.writerows(cur.fetchall())
            z.writestr(f"{table}.csv", out.getvalue())
    buf.seek(0)
    return send_file(buf, mimetype="application/zip", as_attachment=True,
                     download_name=f"inventory-export-{date.today()}.zip")


@app.get("/api/export.db")
def export_db():
    """A consistent copy of the whole database file."""
    return send_file(db._snapshot("download.db", tempfile.gettempdir()), as_attachment=True,
                     download_name=f"inventory-{date.today()}.db")


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


if __name__ == "__main__":
    # Local only: reachable from this computer at http://localhost:5050
    app.run(host="127.0.0.1", port=5050)
