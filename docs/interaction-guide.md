# Report interaction guide

## 01 Retail Overview

**Question:** How did catalog sale value and order activity change during the complete months of 2011, and where was value concentrated?

Use KPI cards for sale value, orders, average order value, and units; a month trend; and a country visual. Select a month or country to cross-filter compatible order-based visuals. Reset selections before reading the full-period KPIs. Show GBP units and an explicit `Jan–Nov 2011` subtitle.

## 02 Product Mix

**Question:** Which products contribute most to catalog line value, and is their performance steady by month?

Use product-month data for a product-code KPI, ranked bar chart of product names/codes, and a monthly mix or product detail table. Use a Top N filter for readability. Avoid summing `orders[SaleValue]` and `product-month[SaleValue]` in one visual: they represent the same underlying lines.

## 03 Customer Patterns

**Question:** How are known customers distributed by frequency and recency, and what portion of catalog value has no customer ID?

Use customers for cards and frequency/recency visuals. `orders` supplies the missing-ID KPI, but a separate customer table visual does not inherit an order-table selection without a relationship. The repeat rate denominator is only the 4,168 known customers. Recency is measured on 1 December 2011, not today's date.

## Expected interactions to verify

1. Selecting November changes order-based value and order cards to **£1,457,742.24** and **2,751**; clearing returns them to **£8,877,678.99** and **17,407**.
2. Selecting United Kingdom gives about **84.12%** of full-period catalog line value.
3. A frequency-band selection changes customer counts and value on customer-based visuals; clearing restores **4,168** known customers.

These checks use data files as the reference. Cross-filter appearance and measure labels should be inspected in the saved Power BI report, not assumed from the model alone.
