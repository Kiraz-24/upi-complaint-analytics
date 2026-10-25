# Statistical tests

Every business conclusion in this project is backed by a statistical test. This folder holds the results; the summary below explains each test in plain language. All tables are produced by the notebooks named in the "Where" column.

**How to read a p-value.** The p-value is the probability of seeing a difference at least this large purely by chance if there were really no effect. Below 0.05 we call a result statistically significant. When many tests are run at once (38 app versions, 33 app–theme combinations), the threshold is divided by the number of tests (Bonferroni correction) to avoid false alarms.

## Summary

| Test | Where | Business question | Result |
|---|---|---|---|
| **OLS regression, HC3 robust errors** | **Notebook 07, cell M2** | **How many stars does a review lose when it mentions each problem?** | **12 of 14 problems significant. AutoPay −1.22, crashes −1.10, security blocks −1.10, fees −0.86, OTP −0.84 stars; slowness −0.52. Not significant: QR scanning, payment receipts. R² = 0.38** |
| OLS regression per app | Notebook 07, cell M3 | What should each app fix first, and what is it worth? | BHIM registration/OTP/SIM: −0.99 stars per mention, potential gain +0.18 stars (largest) |
| Mann-Whitney U | Notebook 07, cell V1 | Were Paytm 10.84.5 ratings different from earlier and later versions? | Yes: p = 9.5 × 10⁻⁴³ (earlier vs 10.84.5) and 6.4 × 10⁻⁷² (10.84.5 vs later) |
| Chi-square | Notebook 07, cell V1 | Did the share of 1-star reviews, crash and security mentions change with 10.84.5? | 1-star share 9.2% → 17.6% → 6.7%; all p < 10⁻⁶ |
| Mann-Whitney U + Bonferroni | Notebook 07, cell V2 | Which of 38 app versions were rated differently from the rest of their app? | 5 significantly worse: Paytm 10.84.5, Google Pay 331.1.2 and 351.1.1, BHIM 4.0.24 and 4.0.26 |
| OLS regression (robustness) | Notebook 07, cell C1 | Does the crash effect survive a stricter keyword definition? | Yes: −1.10 → −0.91 stars, still significant |
| Chi-square + Bonferroni | Notebook 08, cell D5 | Which complaint themes grew or shrank in the last four weeks? | 8 of 33 changes significant; rising: PhonePe crashes (+8.3 points), BHIM QR/location, BHIM cashback; falling: BHIM onboarding (−15.2 points) |
| McNemar | Notebook 05, cell X2 | Is fine-tuned DistilBERT significantly better than TF-IDF + logistic regression? | Yes: right on 1,035 test reviews TF-IDF gets wrong vs 204 the other way; χ² = 556, p = 6 × 10⁻¹²³ |

## The key model: rating drivers (cell M2)

**Question.** If a review mentions a given problem, how many fewer stars does it give, compared with a similar review that does not?

**Method.** Ordinary least squares regression on all 85,150 reviews:

`rating ~ 14 problem-mention indicators + log(review length) + app`

- *All reviews, not only complaints:* problem mentions can appear in happy reviews too, so the comparison is not circular.
- *Controlling for the app* compares reviews within the same app (BHIM's ratings are lower overall).
- *Controlling for review length* removes the fact that longer reviews are both more negative and more likely to mention any problem.
- *HC3 robust standard errors* keep the p-values valid although rating spread differs between groups.

**Result.** Problems that **block the user** (AutoPay taking money, the app not opening, a security lock-out) cost about 1.1–1.2 stars per review that mentions them, twice as much as annoyances such as slowness (0.52). This turns a list of complaints into a ranked list of what to fix first. The coefficients describe association, not proven cause; a company can confirm the effect of a fix with a staged rollout or A/B test.

## Files

| File | Content |
|---|---|
| `statistical_tests_summary.csv` | The summary table above |
| `rating_drivers_all_apps.csv` | Cell M2: effect, 95% confidence interval, p-value and mention rate for each problem |
| `priority_matrix.csv` | Cell M3: per-app effect, p-value, prevalence and potential rating gain for each problem |
| `paytm_event_groups.csv`, `paytm_event_tests.csv` | Cell V1: Paytm 10.84.5 before/during/after figures and test p-values |
| `release_monitor.csv` | Cell V2: every version with 300+ reviews, rating difference, p-value, Bonferroni decision |
| `robustness_crash.csv` | Cell C1: crash effect with the broad and the strict keyword definition |
| `emerging_topics.csv` | Cell D5: theme share last 4 weeks vs earlier, chi-square p-value, Bonferroni decision |
| `mcnemar_test.csv` | Cell X2: paired comparison of DistilBERT and TF-IDF on the test set |
