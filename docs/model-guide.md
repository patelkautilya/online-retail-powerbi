# Semantic model and metric definitions

## Import tables

| Table | Grain | Main fields | Expected rows |
| --- | --- | --- | ---: |
| `orders` | InvoiceNo | Month, Country, CustomerID, SaleValue, Units, FrequencyBand, RecencyBand | 17,407 |
| `product-month` | Month × uppercased StockCode | Product, SaleValue, Units, LineCount | Month/product combinations |
| `customers` | known CustomerID | Orders, SaleValue, RecencyDays, FrequencyBand, RecencyBand, RepeatCustomer | 4,168 |

All three tables are **separate aggregate views of the same accepted catalog lines**. Do not append or sum across them. In a simple service report, keep the tables unrelated and use each table on its matching page. A relationship between `orders` and `customers` on CustomerID may be added for a dedicated model, but the separately aggregated `product-month` table cannot be related to `orders` solely on Month without double counting.

`Month` is a first-of-month date after Power Query's CSV type detection. Format it `MMM yyyy`; turn off automatic date hierarchy when a plain monthly axis is wanted. Treat `CustomerID`, `InvoiceNo`, and `StockCode` as identifiers rather than measures. Text IDs preserve leading zeros if present; this export has string IDs.

## Core measures

Use these DAX definitions if recreating a model with custom measures:

```DAX
Catalog Sale Value = SUM(orders[SaleValue])
Catalog Orders = COUNTROWS(orders)
Average Order Value = DIVIDE([Catalog Sale Value], [Catalog Orders])
Catalog Units = SUM(orders[Units])
Known Customers = DISTINCTCOUNT(orders[CustomerID])
Unknown ID Order Share =
    DIVIDE(CALCULATE(COUNTROWS(orders), orders[CustomerKnown] = 0), COUNTROWS(orders))

Catalog Product Codes = DISTINCTCOUNT('product-month'[StockCode])
Product Sale Value = SUM('product-month'[SaleValue])
Product Units = SUM('product-month'[Units])

Customers = COUNTROWS(customers)
Repeat Customers = SUM(customers[RepeatCustomer])
Repeat Rate, Known IDs = DIVIDE([Repeat Customers], [Customers])
```

Format money in GBP to two decimals for tooltips, usually display `£m` or `£k` on charts; rates to two percentage decimals. For the all-period cards, the validated values are in `reports/metrics.json`.

## Selection behavior

The customer frequency and recency bands are calculated **for the full January–November window** as of 1 December 2011. Filtering the order table to one month does not recompute the customer's full-period band. A month chart cross-filtering a card does change the displayed order and sale-value measures to the selected month. A country filter on `orders` should not be assumed to affect unrelated `product-month` or `customers` visuals.

## Line inclusion

A line is accepted when the invoice date is within `[2011-01-01, 2011-12-01)`, InvoiceNo does not start `C`, Quantity and UnitPrice are positive, and StockCode matches five digits optionally followed by up to two letters. StockCode is uppercased before aggregation because the source contains case variants and Power BI treats text distinct counts case insensitively. This catalog rule excludes non-catalog entries such as postage and adjustments. Accepted invoice lines are summed into orders; customer and product-month tables are then derived from the same accepted set. Cancellations are examined separately, not netted against positive sales. See `scripts/analyze.py` for the executable definition.
