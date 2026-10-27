# Source and attribution

**Dataset:** [Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail), UCI Machine Learning Repository. The repository cites Chen, D. (2015), *Online Retail* [Dataset], UCI Machine Learning Repository, DOI [10.24432/C5BW33](https://doi.org/10.24432/C5BW33).

**Original file:** `Online Retail.xlsx` in the [official ZIP download](https://archive.ics.uci.edu/static/public/352/online+retail.zip). The ZIP SHA-256 used for this analysis is `f5385cbb54bbebf7196389109c6b0621faab0c304e3702548165e71c84aede8b`.

**License:** [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/), as stated by UCI. This repository attributes the source and documents changes. The CSVs here are transformed extracts, not the original workbook: they filter to complete months, classify lines, exclude non-catalog entries and cancellations, aggregate to order/customer/product-month grains, and add derived customer bands.

UCI describes transactions from 1 December 2010 to 9 December 2011 for a UK-based online retailer. The recorded country is the customer's country of residence. This analysis uses the 11 complete months in 2011 and does not infer prices, margins, refunds, or shipping cost beyond the available fields.
