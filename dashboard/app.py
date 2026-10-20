"""UPI App Complaint Analytics - interactive dashboard (24INFS7101 capstone).
Run locally with:  streamlit run app.py"""
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

HERE = Path(__file__).parent
APPS = ['BHIM', 'Google Pay', 'Paytm', 'PhonePe']
COLORS = {'BHIM': '#2a78d6', 'Google Pay': '#eb6834', 'Paytm': '#1baf7a', 'PhonePe': '#eda100'}

st.set_page_config(page_title='UPI Complaint Analytics', layout='wide')


@st.cache_data
def load():
    d = pd.read_parquet(HERE / 'dashboard_data.parquet')
    d['review_date'] = pd.to_datetime(d.review_date)
    return d, pd.read_csv(HERE / 'priority_matrix.csv'), pd.read_csv(HERE / 'release_monitor.csv')


df, pri, mon = load()

st.title('UPI App Complaint Analytics')
st.caption('Google Play reviews of BHIM, Google Pay, Paytm and PhonePe (May-Oct 2026), '
           'analysed with fine-tuned DistilBERT (sentiment) and BERTopic (complaint themes).')

with st.sidebar:
    st.header('Filters')
    apps = st.multiselect('Apps', APPS, default=APPS)
    dmin, dmax = df.review_date.min().date(), df.review_date.max().date()
    dates = st.date_input('Date range', (dmin, dmax), min_value=dmin, max_value=dmax)
    stars = st.slider('Star rating', 1, 5, (1, 5))

if not apps:
    st.warning('Select at least one app.')
    st.stop()
d0, d1 = dates if isinstance(dates, (list, tuple)) and len(dates) == 2 else (dmin, dmax)
f = df[df.app.isin(apps) & df.review_date.dt.date.between(d0, d1) & df.rating.between(*stars)]
if f.empty:
    st.info('No reviews match these filters.')
    st.stop()

comp = f[f.is_complaint]
named = comp[comp.theme.notna() & (comp.theme != 'General dissatisfaction')]
k = st.columns(5)
k[0].metric('Reviews', f'{len(f):,}')
k[1].metric('Average rating', f'{f.rating.mean():.2f} stars')
k[2].metric('Negative (model)', f"{(f.bert_label == 'negative').mean():.0%}")
k[3].metric('Top complaint theme', named.theme.mode().iat[0] if len(named) else '-')
k[4].metric('Complaints answered', f'{comp.replied.mean():.0%}' if len(comp) else '-')

t1, t2, t3, t4 = st.tabs(['Trends', 'Complaint themes', 'Releases', 'Review explorer'])

with t1:
    w = (f.groupby(['app', pd.Grouper(key='review_date', freq='W')])
          .agg(reviews=('rating', 'size'), avg_rating=('rating', 'mean'),
               negative=('bert_label', lambda s: (s == 'negative').mean() * 100))
          .reset_index())
    w = w[w.reviews >= 30]
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.line(w, x='review_date', y='avg_rating', color='app', markers=True, color_discrete_map=COLORS,
                            labels={'review_date': 'Week', 'avg_rating': 'Average stars', 'app': 'App'},
                            title='Average star rating per week'), width='stretch')
    c2.plotly_chart(px.line(w, x='review_date', y='negative', color='app', markers=True, color_discrete_map=COLORS,
                            labels={'review_date': 'Week', 'negative': '% negative', 'app': 'App'},
                            title='Share of reviews the model reads as negative'), width='stretch')
    st.caption('Weeks with fewer than 30 reviews are hidden.')

with t2:
    themed = comp[comp.theme.notna()]
    if named.empty:
        st.info('No specific complaints in this selection.')
    else:
        share = (named.groupby(['app', 'theme']).size() / named.groupby('app').size()).mul(100).rename('share').reset_index()
        st.plotly_chart(px.bar(share, x='share', y='theme', color='app', barmode='group', orientation='h',
                               color_discrete_map=COLORS, height=650,
                               labels={'share': '% of specific complaints', 'theme': '', 'app': 'App'},
                               title='What do users complain about? (share of specific complaints)'), width='stretch')
        st.caption(f"{(themed.theme == 'General dissatisfaction').mean():.0%} of long complaints in this selection "
                   'name no specific problem and are not shown.')
    st.subheader('Fix priorities (whole dataset)')
    st.caption('Stars lost when a review mentions the theme, and the potential gain in average rating if fixed. '
               'Regression on all reviews; association, not proof of cause.')
    p = pri[pri.app.isin(apps) & (pri.reviews_mentioning >= 30)].sort_values(['app', 'gain_if_fixed'], ascending=[True, False])
    st.dataframe(p.groupby('app').head(5)[['app', 'theme', 'prevalence_%', 'stars_effect', 'gain_if_fixed']],
                 hide_index=True, width='stretch')

with t3:
    st.caption('Versions with 300+ reviews compared with the rest of the same app '
               '(Mann-Whitney test, Bonferroni-corrected).')
    m = mon[mon.app.isin(apps)].copy()
    m['label'] = m.app + ' ' + m.version.str.replace(r' \(.*\)', '', regex=True)
    m = m.sort_values('diff')
    st.plotly_chart(px.bar(m, x='diff', y='label', color='app', orientation='h', color_discrete_map=COLORS, height=750,
                           hover_data=['first_seen', 'reviews', 'avg_rating', 'mentions_rising_most', 'significant'],
                           labels={'diff': 'Rating difference vs rest of the app (stars)', 'label': '', 'app': 'App'},
                           title='Which releases were rated worse?'), width='stretch')
    st.markdown('**Significantly worse releases**')
    st.dataframe(m[m.significant][['app', 'version', 'first_seen', 'reviews', 'avg_rating', 'rest_of_app', 'diff',
                                   'mentions_rising_most']], hide_index=True, width='stretch')

with t4:
    q = st.text_input('Search review text (e.g. otp, refund, security alert)')
    th = st.multiselect('Complaint theme', sorted(f.theme.dropna().unique()))
    e = f
    if q:
        e = e[e.review_text.str.contains(q, case=False, na=False, regex=False)]
    if th:
        e = e[e.theme.isin(th)]
    st.write(f'{len(e):,} reviews - showing the 200 most helpful')
    st.dataframe(e.sort_values('helpful_votes', ascending=False).head(200)[
                     ['app', 'review_date', 'rating', 'bert_label', 'theme', 'helpful_votes', 'review_text']],
                 hide_index=True, width='stretch',
                 column_config={'review_text': st.column_config.TextColumn('Review', width='large')})
