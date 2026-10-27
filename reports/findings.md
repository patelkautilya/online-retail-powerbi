# Findings and limits

**Window:** 1 January–30 November 2011, complete months only. **Currency:** GBP. **Headline metric:** sum of Quantity × UnitPrice for positive catalog invoice lines, excluding cancellations and non-catalog codes.

| Observation | Evidence | Interpretation |
| --- | --- | --- |
| November is the highest complete month. | £1,457,742.24 across 2,751 orders; January is £671,914.94 across 1,081 orders. | Peak observed value may reflect demand, customer activity, order size, or calendar effects; the dataset alone does not prove a cause. |
| The UK dominates the period aggregate. | 84.12% of catalog sale value comes from UK orders. | Present total and non-UK views together when considering geography. |
| One catalog item leads the product ranking. | `REGENCY CAKESTAND 3 TIER` (`22423`) contributes £140,607.91 of accepted catalog line value. | Drill into month-by-month product patterns before calling it a consistent bestseller. |
| Many identifiable customers return. | 2,609 of 4,168 known customers have >1 accepted catalog order (62.60%). | Repeat rate is descriptive for identifiable customers, not a population-wide retention or cohort rate. |
| Missing IDs affect customer analysis. | 6.75% of accepted orders and 13.49% of accepted sale value lack a CustomerID. | Customer counts, frequency, and recency views omit those orders. |
| The highest frequency band contributes a large share of known-customer value. | The 968 customers with >=5 orders account for £5,322,008.04 of £7,680,345.50 known-customer sale value (69.29%). | This is concentration, not causal evidence that more orders cause value. |

## Quality and reconciliation

- Original workbook: **541,909** invoice lines; **135,080** lines lack CustomerID and **1,454** lack Description.
- Complete-month window: **473,903** lines, partitioned into **461,385** accepted catalog lines, **2,128** positive non-catalog lines, **8,200** cancelled negative lines, and **2,190** other lines. These groups sum exactly to the window total.
- The accepted catalog lines form **17,407** invoices and **3,709** distinct catalog codes after case normalization. The unnormalized source has **3,806** case-sensitive code variants. Order-level and product-month sale-value totals reconcile within £0.01. An independent SQLite sum of the exported order CSV also agrees within £0.01.

## What the data cannot answer

This project has no cost, margin, inventory, marketing spend, or fulfillment fields, so it cannot establish profit, ROI, or stock efficiency. Excluding cancellation lines means the headline positive catalog line value is **not net revenue**. Customer recency uses the final full-month boundary, 1 December 2011. The source ends on 9 December 2011, making December unsuitable for comparison with full months. The dataset is historical; use it to inspect methods rather than to guide current operations.
