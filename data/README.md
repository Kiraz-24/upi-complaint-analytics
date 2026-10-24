# Data

The raw and processed review files are **not published** in this repository: they contain full review texts linked to Play Store review IDs. They live in the project's Google Drive folder (`MyDrive/upi-complaint-analytics/data/`). To build a fresh dataset, run [`src/scrape_reviews.py`](../src/scrape_reviews.py) and the notebooks in order.

A privacy-safe subset (no review IDs, personal details masked) is published for the dashboard: [`dashboard/dashboard_data.parquet`](../dashboard/dashboard_data.parquet).

## Folder layout used by the notebooks

```
upi-complaint-analytics/            (Google Drive)
├── data/
│   ├── raw/          raw_reviews.csv (stage 1), raw_reviews_v2.csv (stage 1 + top-up)
│   └── processed/    parquet files, TF-IDF matrix, embeddings, trained models
├── reports/          result tables and figures (published here under reports/)
└── dashboard/        dashboard app and data (published here under dashboard/)
```

## Data dictionary

### Raw reviews (`raw_reviews_v2.csv`, 86,056 rows)

| Column | Description |
|---|---|
| `app` | App name: BHIM, Google Pay, Paytm or PhonePe |
| `review_id` | Play Store review identifier |
| `review_text` | Review text as written |
| `rating` | Star rating, 1–5 |
| `helpful_votes` | Number of users who marked the review as helpful |
| `app_version` | App version installed by the reviewer (missing for 15%) |
| `review_date` | Date and time of the review |
| `company_reply` | Public reply from the company, if any |
| `reply_date` | Date and time of the reply |

### Added in preprocessing (`clean_reviews.parquet`, 85,979 rows)

| Column | Description |
|---|---|
| `text_light` | Lightly cleaned text: lower case, contractions expanded, Hinglish and slang translated (input for transformer models) |
| `text_full` | Fully cleaned text: lemmatised, stop words, emojis and brand names removed, negations kept (input for TF-IDF and topic words) |
| `emojis` | Emojis found in the review |
| `words_no_emoji` | Number of words, emojis excluded |
| `is_long` | Review has 5 or more words |
| `has_indic` / `indic_only` | Review contains / consists only of Indian-script text |

### Added in feature engineering (`model_data.parquet`, 85,150 rows)

| Column | Description |
|---|---|
| `label3` | Sentiment label from stars: negative (1–2), neutral (3), positive (4–5) |
| `label2` | Two-class label (3-star reviews left empty) |
| `split` | train (70%), val (15%) or test (15%), stratified by app and label |
| `tfidf_text` | Text used for TF-IDF, including emoji tokens |
| `vader` | VADER compound sentiment score (−1 to +1) |
| `n_words`, `n_exclaim`, `caps_ratio`, `n_emojis` | Length, exclamation marks, share of capital letters, emoji count |
| `has_money`, `has_negation` | Review mentions money words / a negation |
| `has_reply` | Company replied (business analysis only, not a model input) |

### Added by the sentiment model (`reviews_with_sentiment.parquet`)

| Column | Description |
|---|---|
| `bert_label` | DistilBERT prediction: negative, neutral or positive |
| `bert_conf` | Probability of the predicted class |
| `p_negative`, `p_neutral`, `p_positive` | Class probabilities |

### Complaint themes (`complaints_with_themes.parquet`, 12,202 rows)

| Column | Description |
|---|---|
| `is_complaint` | 1–2 stars or DistilBERT says negative |
| `topic` / `topic_core` | BERTopic topic number (after / before outlier reassignment; −1 = outlier) |
| `theme_bertopic` | Business theme from the topic-to-theme mapping |
| `theme` | Final theme (outliers grouped as "General dissatisfaction") |
| `theme_method` | Whether the theme came from a core topic or a reassigned outlier |

### Theme mentions (`theme_mentions.parquet`, 85,150 rows)

`m_otp`, `m_security`, `m_login`, `m_crash`, `m_slow`, `m_payment`, `m_support`, `m_cashback`, `m_fees`, `m_upilite`, `m_autopay`, `m_qr`, `m_receipt`, `m_ads`: 1 if the review mentions the problem (keyword rules in notebook 07, cell M1), otherwise 0.

### Dashboard data (`dashboard/dashboard_data.parquet`, 85,150 rows, published)

`app`, `review_date`, `rating`, `review_text` (masked), `bert_label`, `app_version`, `helpful_votes`, the 14 `m_*` mention columns, `theme`, `is_complaint`, `replied`, `template` (reply text sent 20+ times), `reply_hours`.
