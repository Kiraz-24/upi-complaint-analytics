"""Data collection for the UPI App Complaint Analytics project.

Scrapes the newest English Google Play reviews (India store) of four UPI apps. For each app it collects
at least MIN_TOTAL reviews and continues until TARGET_LONG reviews have 5+ words (or MAX_TOTAL is reached),
keeping every short review to avoid length bias. Reviewer names are not stored.

    pip install google-play-scraper pandas
    python scrape_reviews.py
"""
import time
import pandas as pd
from google_play_scraper import reviews, Sort

APPS = {
    'BHIM': 'in.org.npci.upiapp',
    'Google Pay': 'com.google.android.apps.nbu.paisa.user',
    'Paytm': 'net.one97.paytm',
    'PhonePe': 'com.phonepe.app',
}
MIN_TOTAL, TARGET_LONG, MAX_TOTAL = 10000, 5000, 60000


def scrape(app_id):
    out, token, n_long = [], None, 0
    while (len(out) < MIN_TOTAL or n_long < TARGET_LONG) and len(out) < MAX_TOTAL:
        batch, token = reviews(app_id, lang='en', country='in', sort=Sort.NEWEST,
                               count=200, continuation_token=token)
        if not batch:
            break
        out.extend(batch)
        n_long += sum(len(str(r['content'] or '').split()) >= 5 for r in batch)
        if token is None:
            break
        time.sleep(1)                      # polite delay between requests
    return out


def main():
    rows = []
    for name, app_id in APPS.items():
        print('Scraping', name)
        for r in scrape(app_id):
            r['app'] = name
            rows.append(r)
    df = pd.DataFrame(rows)[['app', 'reviewId', 'content', 'score', 'thumbsUpCount',
                             'reviewCreatedVersion', 'at', 'replyContent', 'repliedAt']]
    df = df.rename(columns={'reviewId': 'review_id', 'content': 'review_text', 'score': 'rating',
                            'thumbsUpCount': 'helpful_votes', 'reviewCreatedVersion': 'app_version',
                            'at': 'review_date', 'replyContent': 'company_reply', 'repliedAt': 'reply_date'})
    df = df.drop_duplicates(subset='review_id')
    df.to_csv('raw_reviews.csv', index=False, encoding='utf-8-sig')
    print(len(df), 'reviews saved to raw_reviews.csv')


if __name__ == '__main__':
    main()
