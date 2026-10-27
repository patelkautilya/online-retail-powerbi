"""Prepare and reconcile a Power BI portfolio model from UCI Online Retail."""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import sqlite3
from urllib.request import urlretrieve
import zipfile

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
SOURCE_URL = "https://archive.ics.uci.edu/static/public/352/online+retail.zip"
SOURCE_ZIP = DATA / "online-retail.zip"
START = pd.Timestamp("2011-01-01")
END = pd.Timestamp("2011-12-01")
AS_OF = END
CATALOG_CODE = r"[0-9]{5}[A-Za-z]{0,2}"


def write_csv(frame: pd.DataFrame, filename: str) -> None:
    frame.to_csv(DATA / filename, index=False, float_format="%.2f")


def report_csv(frame: pd.DataFrame, filename: str) -> None:
    frame.to_csv(REPORTS / filename, index=False, float_format="%.2f")


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    if not SOURCE_ZIP.exists():
        urlretrieve(SOURCE_URL, SOURCE_ZIP)

    with zipfile.ZipFile(SOURCE_ZIP) as archive:
        source = pd.read_excel(io.BytesIO(archive.read("Online Retail.xlsx")))
    if source.shape != (541909, 8):
        raise ValueError(f"Unexpected source shape: {source.shape}")

    source["InvoiceNo"] = source["InvoiceNo"].astype(str).str.strip()
    # Case variants of the same code occur in the workbook. Power BI text
    # distinct counts are case insensitive, so standardize before aggregation.
    source["StockCode"] = source["StockCode"].astype(str).str.strip().str.upper()
    source["CustomerID"] = source["CustomerID"].astype("Int64").astype("string")
    source["InvoiceDate"] = pd.to_datetime(source["InvoiceDate"], errors="raise")
    source["LineValue"] = source["Quantity"] * source["UnitPrice"]
    period = source.loc[source["InvoiceDate"].between(START, END, inclusive="left")].copy()
    period["Month"] = period["InvoiceDate"].dt.strftime("%Y-%m")

    cancelled = period["InvoiceNo"].str.upper().str.startswith("C")
    catalog = period["StockCode"].str.fullmatch(CATALOG_CODE)
    positive = (period["Quantity"] > 0) & (period["UnitPrice"] > 0) & ~cancelled
    accepted = positive & catalog
    lines = period.loc[accepted].copy()

    if lines.groupby("InvoiceNo")["Country"].nunique().max() != 1:
        raise ValueError("An invoice has more than one country")
    if lines.groupby("InvoiceNo")["CustomerID"].nunique().max() > 1:
        raise ValueError("An invoice has more than one customer ID")

    lines["SaleValue"] = lines["LineValue"]
    orders = lines.groupby("InvoiceNo", as_index=False).agg(
        InvoiceDate=("InvoiceDate", "min"),
        Country=("Country", "first"),
        CustomerID=("CustomerID", "first"),
        SaleValue=("SaleValue", "sum"),
        Units=("Quantity", "sum"),
        ProductCodes=("StockCode", "nunique"),
    )
    orders["Month"] = orders["InvoiceDate"].dt.strftime("%Y-%m")
    orders["CustomerKnown"] = orders["CustomerID"].notna().astype(int)
    orders["Records"] = 1

    known = orders.loc[orders["CustomerKnown"] == 1].copy()
    customers = known.groupby("CustomerID", as_index=False).agg(
        Country=("Country", "first"),
        Orders=("InvoiceNo", "nunique"),
        SaleValue=("SaleValue", "sum"),
        Units=("Units", "sum"),
        LastOrder=("InvoiceDate", "max"),
    )
    customers["RecencyDays"] = (AS_OF - customers["LastOrder"]).dt.days
    customers["FrequencyBand"] = pd.cut(
        customers["Orders"], bins=[0, 1, 4, float("inf")],
        labels=["01 One order", "02 Two to four", "03 Five or more"],
    ).astype(str)
    customers["RecencyBand"] = pd.cut(
        customers["RecencyDays"], bins=[-1, 30, 90, 180, float("inf")],
        labels=["01 Within 30 days", "02 31–90 days", "03 91–180 days", "04 Over 180 days"],
    ).astype(str)
    customers["RepeatCustomer"] = (customers["Orders"] > 1).astype(int)
    customers["Records"] = 1
    orders = orders.merge(
        customers[["CustomerID", "FrequencyBand", "RecencyBand", "RepeatCustomer"]],
        on="CustomerID", how="left", validate="many_to_one",
    )
    orders[["FrequencyBand", "RecencyBand"]] = orders[
        ["FrequencyBand", "RecencyBand"]
    ].fillna("Unknown customer ID")
    orders["RepeatCustomer"] = orders["RepeatCustomer"].fillna(0).astype(int)

    descriptions = (
        lines.assign(Description=lines["Description"].fillna("").astype(str).str.strip())
        .loc[lambda x: x["Description"] != ""]
        .groupby("StockCode")["Description"]
        .agg(lambda values: values.value_counts().index[0])
    )
    products = lines.groupby(["Month", "StockCode"], as_index=False).agg(
        SaleValue=("SaleValue", "sum"), Units=("Quantity", "sum"),
        LineCount=("StockCode", "size"),
    )
    products["Product"] = products["StockCode"].map(descriptions).fillna(products["StockCode"])
    products["Records"] = 1

    monthly = orders.groupby("Month", as_index=False).agg(
        Orders=("Records", "sum"), SaleValue=("SaleValue", "sum"), Units=("Units", "sum")
    )
    monthly["AverageOrderValue"] = monthly["SaleValue"] / monthly["Orders"]
    country = orders.groupby("Country", as_index=False).agg(
        Orders=("Records", "sum"), SaleValue=("SaleValue", "sum")
    ).sort_values("SaleValue", ascending=False)
    frequency = customers.groupby("FrequencyBand", as_index=False).agg(
        Customers=("Records", "sum"), Orders=("Orders", "sum"),
        SaleValue=("SaleValue", "sum")
    ).sort_values("FrequencyBand")
    recency = customers.groupby("RecencyBand", as_index=False).agg(
        Customers=("Records", "sum"), SaleValue=("SaleValue", "sum")
    ).sort_values("RecencyBand")
    product_summary = products.groupby(["StockCode", "Product"], as_index=False).agg(
        SaleValue=("SaleValue", "sum"), Units=("Units", "sum")
    ).sort_values("SaleValue", ascending=False)

    quality = {
        "source_lines": int(len(source)),
        "source_missing_customer_id_lines": int(source["CustomerID"].isna().sum()),
        "source_missing_description_lines": int(source["Description"].isna().sum()),
        "period_lines": int(len(period)),
        "accepted_catalog_lines": int(accepted.sum()),
        "positive_non_catalog_lines": int((positive & ~catalog).sum()),
        "cancelled_negative_lines": int((cancelled & (period["Quantity"] < 0) & (period["UnitPrice"] > 0)).sum()),
        "other_period_lines": int((~accepted & ~(positive & ~catalog) & ~(cancelled & (period["Quantity"] < 0) & (period["UnitPrice"] > 0))).sum()),
        "accepted_missing_customer_id_lines": int(lines["CustomerID"].isna().sum()),
        "cancelled_negative_line_value_gbp": round(float((-period.loc[cancelled & (period["Quantity"] < 0) & (period["UnitPrice"] > 0), "LineValue"]).sum()), 2),
    }
    if sum(quality[key] for key in ["accepted_catalog_lines", "positive_non_catalog_lines", "cancelled_negative_lines", "other_period_lines"]) != quality["period_lines"]:
        raise ValueError("Line classifications do not reconcile")

    orders = orders.sort_values(["InvoiceDate", "InvoiceNo"])
    customers = customers.sort_values("CustomerID")
    products = products.sort_values(["Month", "StockCode"])
    write_csv(orders.drop(columns=["InvoiceDate"]), "orders.csv")
    write_csv(customers.drop(columns=["LastOrder"]), "customers.csv")
    write_csv(products, "product-month.csv")
    report_csv(monthly, "monthly-summary.csv")
    report_csv(country, "country-summary.csv")
    report_csv(frequency, "frequency-summary.csv")
    report_csv(recency, "recency-summary.csv")
    report_csv(product_summary, "product-summary.csv")

    metrics = {
        "period": "2011-01-01 through 2011-11-30",
        "catalog_sale_value_gbp": round(float(orders["SaleValue"].sum()), 2),
        "catalog_orders": int(len(orders)),
        "average_order_value_gbp": round(float(orders["SaleValue"].sum() / len(orders)), 2),
        "catalog_units": int(orders["Units"].sum()),
        "catalog_product_codes": int(lines["StockCode"].nunique()),
        "known_customers": int(len(customers)),
        "repeat_known_customers": int(customers["RepeatCustomer"].sum()),
        "repeat_known_customer_rate": round(float(customers["RepeatCustomer"].mean()), 6),
        "unknown_customer_order_share": round(float(1 - orders["CustomerKnown"].mean()), 6),
        "unknown_customer_sale_value_share": round(float(orders.loc[orders["CustomerKnown"] == 0, "SaleValue"].sum() / orders["SaleValue"].sum()), 6),
        "uk_sale_value_share": round(float(country.loc[country["Country"] == "United Kingdom", "SaleValue"].iloc[0] / orders["SaleValue"].sum()), 6),
        "source_zip_sha256": hashlib.sha256(SOURCE_ZIP.read_bytes()).hexdigest(),
        "quality": quality,
    }

    # Reconcile the exported report grain through a second calculation engine.
    with sqlite3.connect(":memory:") as conn:
        exported = pd.read_csv(DATA / "orders.csv")
        exported.to_sql("orders", conn, index=False)
        sqlite_count, sqlite_value, sqlite_units = conn.execute(
            "SELECT COUNT(*), SUM(SaleValue), SUM(Units) FROM orders"
        ).fetchone()
    if sqlite_count != metrics["catalog_orders"] or sqlite_units != metrics["catalog_units"]:
        raise ValueError("SQLite order or unit reconciliation failed")
    if abs(sqlite_value - metrics["catalog_sale_value_gbp"]) > 0.01:
        raise ValueError("SQLite value reconciliation failed")
    if abs(products["SaleValue"].sum() - orders["SaleValue"].sum()) > 0.01:
        raise ValueError("Product and order value totals disagree")
    (REPORTS / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in metrics.items() if key not in ["quality", "source_zip_sha256"]}, indent=2))
    print("SQLite and product-grain reconciliation passed")


if __name__ == "__main__":
    main()
