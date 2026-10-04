# Understanding the numbers in the dashboard

## Filters (top of the Dashboard)
| Control | What it does |
|---|---|
| **Date range** | Which days are counted: Yesterday, Last 7d, Last 30d, Last month (previous calendar month), Last 90d, All. "Last N days" ends yesterday and does not include today. |
| **Item** | Type an item code or name to see only that item. Click the ✕ to go back to all items. |
| **Chart bucket size** | How the two time charts group the days: Daily, Weekly (weeks start on Monday) or Monthly. It does not change the KPI cards or the table. |

The line under the filters shows the exact dates being shown and the exact dates used for "previous".

## KPI cards
| Card | Meaning |
|---|---|
| **Revenue** | Money from sales in the range: quantity sold × selling price, added up. |
| **Profit** | Revenue minus the cost of the goods sold (see "How profit is worked out"). |
| **Margin** | Profit ÷ Revenue. The card shows the previous period's margin for comparison. |
| **Units sold** | Total quantity sold in the range. |
| **Purchase spend** | Money spent buying stock in the range: quantity bought × purchase price. The card also shows units bought. |
| **Stock on hand** | Units in stock right now: everything ever purchased minus everything ever sold. It is *not* limited to the date range. |
| **Stock on hand: "worth ₹X at cost"** | The money tied up in that stock, at the current average purchase cost. |

### The "vs previous period" arrows
Revenue, Profit and Units sold show ▲ or ▼ with a percentage. The comparison is against the period of **equal length immediately before** the one selected:

- Last 7d is compared with the 7 days before those.
- Last 30d is compared with the 30 days before those.
- Yesterday is compared with the day before.

Green means better than before, red means worse. If the previous period has no sales, the card says "no prior data". Purchase spend and Stock on hand have no arrows.

## How profit is worked out
Each sale is costed at the **average purchase price of the stock you held on the day of the sale** (weighted by quantity).

Example: you buy 10 units at ₹100 and later 10 more at ₹120, so your average cost is ₹110. Selling 5 units at ₹150 gives revenue ₹750, cost ₹550, profit ₹200.

The cost is not simply that day's purchase price, so profit does not jump because you restocked on a given day.

## Charts
| Chart | What it shows |
|---|---|
| **Revenue and profit over time** | Two lines on the same ₹ scale. Hover for the values on a date. |
| **Purchases vs units sold** | Bars of money spent on purchases per bucket. Hover to also see units sold. |
| **Profit by item** | Profit per item in the date range. Not shown when a single item is selected. Losses show as an empty bar, so check the table for negative profit. |
| **Days of stock cover** | How long current stock lasts at the recent sales pace. Bars under 7 days are red: reorder soon. Not shown when a single item is selected. |

## Item breakdown table
One row per item. Click a header to sort, click a row to filter the dashboard to that item.

| Column | Meaning |
|---|---|
| **Code, Item** | The item code and name. |
| **Sold** | Units sold in the range. |
| **Revenue** | Sales value in the range. |
| **Profit** | Revenue minus cost of goods sold. Negative profit shows in red. |
| **Margin** | Profit ÷ Revenue. |
| **Bought** | Units purchased in the range. |
| **Stock** | Units on hand right now. |
| **Stock value** | Stock × current average cost. |
| **Days cover** | Stock ÷ average units sold per day in the range. Shows "—" if nothing sold in the range. Red when under 7. |

## Things to keep in mind
- **Stock, Stock value and Days cover are "right now" numbers.** Changing the date range does not change Stock, but it does change Days cover, because the sales pace comes from the range.
- **Short ranges are noisy.** Days cover from "Yesterday" is based on one day of sales. Use Last 30d for a steadier number.
- **Deleting is permanent in the app.** Deleted entries disappear from every number. A copy taken just before each delete is in the `backups` folder (see README.md).
- **Entering an old date changes past profit.** The average cost is rebuilt from all entries in date order, so adding or deleting a back-dated purchase can change profit figures for sales after it.
- **Item category** is only a label on the item (default "General"). It is shown in the single-item header and is not used for filtering yet.
- Amounts are shown in ₹ and assume prices are per unit.
