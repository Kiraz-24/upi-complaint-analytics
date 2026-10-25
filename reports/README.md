# Reports

Results produced by the notebooks. In Colab all files are written to one `reports/` folder; here they are grouped for easier reading.

## [statistical_tests/](statistical_tests)
Every hypothesis test and regression, with a plain-language summary. Start here for the business evidence.

## [tables/](tables)

| File | Notebook | Content |
|---|---|---|
| `model_results.csv` | 05 | Accuracy and F1 per class for every sentiment model, 3-class and 2-class |
| `topic_model_comparison.csv` | 06 | Coherence (NPMI) and diversity of LDA and BERTopic |
| `theme_by_app.csv` | 06 | Complaints per theme and app, average rating, share of the app's complaints |
| `reply_analysis.csv` | 07 | Reply rate, median reply time and template share per app |
| `text_stats_by_app.csv` | 04 | Review length, vocabulary, emoji, negation and money-word use per app |
| `distinctive_words_sentiment.csv` | 04 | Words most typical of complaints and of praise (log-odds z-scores) |
| `distinctive_words_by_app.csv` | 04 | Words most typical of each app's complaints |
| `complaint_bigrams_by_app.csv` | 04 | Most frequent word pairs in each app's complaints |

## [figures/](figures)

| Figure | Notebook | Shows |
|---|---|---|
| 01_rating_distribution | 04 | Star ratings per app |
| 02_length_by_rating | 04 | Review length by star rating |
| 03_weekly_trends | 04 | Reviews and average rating per week |
| 07_theme_heatmap | 06 | Share of each app's complaints by theme (all complaints) |
| 08_themes_over_time | 06 | Weekly share of the top themes per app |
| 09_rating_drivers | 07 | Stars lost per problem with 95% confidence intervals (cell M2) |
| 10_priority_matrix | 07 | Frequency against severity of each problem, per app |
| 11_theme_heatmap_specific | 08 | Share of specific complaints by theme (PNG and interactive HTML) |
| 12_model_comparison | 08 | Macro F1 of the sentiment models |
| 13_paytm_release_event | 08 | Paytm 10.84.5: 1-star share and crash and security mentions |
| 14_complaint_replies | 08 | Reply rate, speed and templates for 1–2 star reviews |
| 15_distinctive_words_sentiment | 04 | Words typical of complaints vs praise |
| 16_distinctive_words_by_app | 04 | Words typical of each app's complaints |
| 17_wordclouds | 04 | Word clouds of complaints and praise, weighted by distinctiveness |

Figure numbers 04–06 are not used.
