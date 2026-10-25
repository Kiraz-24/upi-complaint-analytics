# Dataset description

## 1. Overview

| Item | Description |
|---|---|
| Name | UPI app reviews (Google Play Store) |
| Apps | BHIM, Google Pay, Paytm, PhonePe |
| Source | Public Google Play Store reviews, India store, English interface |
| Collection tool | [`google-play-scraper`](https://pypi.org/project/google-play-scraper/) (open-source Python library), own script [`src/scrape_reviews.py`](../src/scrape_reviews.py) |
| Collection period of reviews | 18 May 2026 – 18 October 2026 (varies by app) |
| Size | 86,056 reviews scraped; 85,150 used for text models |
| Unit of analysis | One review: text, star rating and metadata |
| Licence and use | Public data, collected for academic analysis only; raw data not redistributed |

## 2. Why this dataset

App-store reviews are unprompted, public, current and already labelled by the writer with a star rating, which makes them a direct measure of customer experience at a scale no survey can reach. The project brief required self-collected data, so no ready-made dataset was used.

## 3. Collection method

1. **Stage 1:** the newest 10,000 reviews per app (sorted by date).
2. **Stage 2 (top-up):** most Paytm and PhonePe reviews are one or two words long ("good app"). To have enough text to analyse *what* goes wrong, scraping continued until every app had at least **5,000 reviews of five or more words** (with a safety cap of 60,000 reviews per app). Short reviews were kept, because dropping them would bias ratings towards the longer, angrier reviews.

A one-second pause between requests kept the load on the store low. Reviewer names and profile images were never stored.

| App | Reviews | First review | Last review | Average stars | 1-star | 5-star | Median words | 5+ words |
|---|---|---|---|---|---|---|---|---|
| BHIM | 10,000 | 21 Jun 2026 | 14 Oct 2026 | 2.7 | 45.6% | 29.2% | 11 | 70.3% |
| Google Pay | 18,221 | 18 May 2026 | 18 Oct 2026 | 4.0 | 18.5% | 65.3% | 2 | 27.7% |
| Paytm | 27,614 | 26 Jul 2026 | 18 Oct 2026 | 4.5 | 10.4% | 81.2% | 2 | 18.2% |
| PhonePe | 30,221 | 19 Aug 2026 | 18 Oct 2026 | 4.4 | 9.3% | 73.7% | 2 | 16.6% |

## 4. Fields

| Field | Type | Description | Missing |
|---|---|---|---|
| `app` | text | App name | 0 |
| `review_id` | text | Play Store review identifier (used for joins; not published) | 0 |
| `review_text` | text | Review content | 0 empty |
| `rating` | integer 1–5 | Star rating given by the reviewer | 0 |
| `helpful_votes` | integer | Number of other users who marked the review as helpful | 0 |
| `app_version` | text | App version the reviewer had installed | 13,040 (15.2%) |
| `review_date` | datetime | Date and time of the review | 0 |
| `company_reply` | text | The company's public reply, if any | 39,999 (46.5%) |
| `reply_date` | datetime | Date and time of the reply | 39,999 (46.5%) |

## 5. Data quality

- **Duplicates:** many identical short texts ("good", "nice app") are posted by different users and are genuine; they were kept. Only 104 long reviews (5+ words) appear more than once.
- **Junk:** 77 reviews with no usable text (symbol strings, decorative fonts) were removed.
- **Language:** 829 reviews written only in Indian scripts (Devanagari, Bengali, Telugu, Gujarati and others) were kept for rating statistics but excluded from the English text models. About 10–14% of long reviews mix Hindi and English in Latin script (Hinglish); common Hinglish words were translated.
- **Imbalance:** after labelling by stars, 18.5% of reviews are negative, 3.9% neutral and 77.6% positive. Macro-averaged F1 is therefore used to evaluate models.
- **Self-selection:** dissatisfied users are more likely to write long reviews (median 11 words at 1 star, 1–2 words at 4–5 stars).

## 6. Cleaning funnel

| App | Scraped | Junk removed | Indian-script only | English-text reviews | Long (5+ words) |
|---|---|---|---|---|---|
| BHIM | 10,000 | 2 | 82 | 9,916 | 6,951 |
| Google Pay | 18,221 | 35 | 207 | 17,979 | 4,930 |
| Paytm | 27,614 | 13 | 272 | 27,329 | 4,841 |
| PhonePe | 30,221 | 27 | 268 | 29,926 | 4,829 |
| **Total** | **86,056** | **77** | **829** | **85,150** | **21,551** |

## 7. Derived datasets

| File | Rows | Content |
|---|---|---|
| `clean_reviews.parquet` | 85,979 | Cleaned text in two versions (`text_light`, `text_full`), emoji list, length and language flags |
| `model_data.parquet` | 85,150 | Labels (`label3`, `label2`), train/validation/test split, engineered features |
| `reviews_with_sentiment.parquet` | 85,150 | DistilBERT predictions and class probabilities |
| `complaints_with_themes.parquet` | 12,202 | Long complaints with BERTopic topic and business theme |
| `theme_mentions.parquet` | 85,150 | Keyword indicators for the 14 problem themes, used in the rating-driver regressions |
| `dashboard/dashboard_data.parquet` | 85,150 | Published, privacy-safe subset used by the dashboard |

Column definitions: [data/README.md](../data/README.md).

## 8. Privacy and ethics

Only public reviews were collected. Reviewer names were never stored. Review IDs are not published. In all published text, phone numbers, email addresses, UPI IDs and long account-style numbers are masked. The data is used solely for academic analysis.
