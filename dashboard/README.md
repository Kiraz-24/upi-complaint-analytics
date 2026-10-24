# Dashboard

Interactive Streamlit dashboard for product teams. Built in notebook 08 (cells D5–D7).

| View | What it shows |
|---|---|
| Overview | App comparison for the current filters and the key findings |
| Trends | Weekly or monthly average rating, % negative, % 1-star, review volume |
| Complaint themes | Theme shares per app (bar chart or heatmap) and one theme over time |
| Fix priorities | Priority matrix per app, "what if we fixed it" calculator, stars lost per problem |
| Releases | Release monitor and a live release investigator (Mann-Whitney and chi-square tests) |
| Emerging topics | Themes rising or falling in the last four weeks, with significance |
| Company replies | Reply rate, speed and template share for 1–2 star reviews |
| Models & tests | Sentiment and topic model comparison, every statistical test |
| Review explorer | Search the reviews, filter hidden complaints, download as CSV |

Filters (app, date range, star rating) apply to every view computed from reviews.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Files

`app.py` (the application), `dashboard_data.parquet` (85,150 reviews, personal details masked, no review IDs) and the result tables it reads (`*.csv`).
