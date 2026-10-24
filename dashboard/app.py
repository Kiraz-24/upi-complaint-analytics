"""UPI App Complaint Analytics - interactive dashboard (24INFS7101 capstone).

Run locally with:  streamlit run app.py
All data files live next to this script (see load_data)."""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

HERE = Path(__file__).parent
APPS = ['BHIM', 'Google Pay', 'Paytm', 'PhonePe']
COLORS = {'BHIM': '#2a78d6', 'Google Pay': '#eb6834', 'Paytm': '#1baf7a', 'PhonePe': '#eda100'}
GENERAL = 'General dissatisfaction'
THEMES = {  # mention column -> business theme (keyword rules from the notebook, cell M1)
    'm_otp': 'Registration, OTP & SIM verification', 'm_security': 'Security / device-integrity blocks',
    'm_login': 'Login & account blocked', 'm_crash': 'App not opening / crashes / updates',
    'm_slow': 'Slow performance', 'm_payment': 'Failed / pending payments', 'm_support': 'Customer support',
    'm_cashback': 'Cashback & rewards', 'm_fees': 'Fees & charges', 'm_upilite': 'UPI Lite & UPI PIN',
    'm_autopay': 'AutoPay / mandates', 'm_qr': 'QR scanning & location',
    'm_receipt': 'Payment receipt / screenshot', 'm_ads': 'Ads, notifications & add-ons'}

SHORT = {'Registration, OTP & SIM verification': 'OTP & SIM', 'Security / device-integrity blocks': 'Security blocks',
         'App not opening / crashes / updates': 'Crashes', 'Failed / pending payments': 'Failed payments',
         'Login & account blocked': 'Login blocked', 'Ads, notifications & add-ons': 'Ads & add-ons',
         'Payment receipt / screenshot': 'Receipts', 'QR scanning & location': 'QR & location'}
PFMT = {'p_value': st.column_config.NumberColumn('p-value', format='%.1e')}

st.set_page_config(page_title='UPI Complaint Analytics', layout='wide')


@st.cache_data
def load_data():
    d = pd.read_parquet(HERE / 'dashboard_data.parquet')
    d['review_date'] = pd.to_datetime(d.review_date)
    t = {name: pd.read_csv(HERE / f'{name}.csv') for name in [
        'priority_matrix', 'release_monitor', 'rating_drivers_all_apps', 'model_results',
        'topic_model_comparison', 'emerging_topics', 'paytm_event_groups', 'paytm_event_tests', 'robustness_crash',
        'statistical_tests_summary']}
    return d, t


def chart(fig, height=None):
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), legend_title_text='', height=height)
    st.plotly_chart(fig, width='stretch')


def pct(x):
    return f'{x:.0%}' if pd.notna(x) else '-'


df, T = load_data()

# ---------------------------------------------------------------- sidebar filters
with st.sidebar:
    st.header('Filters')
    apps = st.multiselect('Apps', APPS, default=APPS)
    dmin, dmax = df.review_date.min().date(), df.review_date.max().date()
    dates = st.date_input('Date range', (dmin, dmax), min_value=dmin, max_value=dmax)
    stars = st.slider('Star rating', 1, 5, (1, 5))
    st.caption('Filters apply to every chart computed from reviews. Tables marked "whole dataset" come from '
               'the notebook and do not change with the filters.')
    with st.expander('About the data'):
        st.markdown(
            f'- {len(df):,} English Google Play reviews, {dmin:%d %b} to {dmax:%d %b %Y}, scraped by the team.\n'
            '- Sentiment: fine-tuned DistilBERT. Complaint = 1-2 stars or model says negative.\n'
            '- Themes: BERTopic on long complaints (5+ words), merged into 15 business themes.\n'
            '- Phone numbers, e-mails and UPI IDs in review texts are masked.')

if not apps:
    st.warning('Select at least one app.')
    st.stop()
d0, d1 = dates if isinstance(dates, (list, tuple)) and len(dates) == 2 else (dmin, dmax)
f = df[df.app.isin(apps) & df.review_date.dt.date.between(d0, d1) & df.rating.between(*stars)]
if f.empty:
    st.info('No reviews match these filters.')
    st.stop()
comp = f[f.is_complaint]
named = comp[comp.theme.notna() & (comp.theme != GENERAL)]

# ---------------------------------------------------------------- header and KPIs
st.title('UPI App Complaint Analytics')
st.caption('What Google Play reviews of BHIM, Google Pay, Paytm and PhonePe say each app should fix first.')
k = st.columns(5)
k[0].metric('Reviews', f'{len(f):,}')
k[1].metric('Average rating', f'{f.rating.mean():.2f} stars')
k[2].metric('Negative (model)', pct((f.bert_label == 'negative').mean()))
top = named.theme.mode().iat[0] if len(named) else '-'
k[3].metric('Top complaint theme', SHORT.get(top, top), help=top)
k[4].metric('Complaints answered', pct(comp.replied.mean()) if len(comp) else '-')

tabs = st.tabs(['Overview', 'Trends', 'Complaint themes', 'Fix priorities', 'Releases', 'Emerging topics',
                'Company replies', 'Models & tests', 'Review explorer'])

# ---------------------------------------------------------------- 1 overview
with tabs[0]:
    st.subheader('App comparison for the current selection')
    rows = []
    for a in apps:
        s, c = f[f.app == a], comp[comp.app == a]
        if s.empty:
            continue
        nm = named[named.app == a]
        rows.append({'App': a, 'Reviews': len(s), 'Avg stars': round(s.rating.mean(), 2),
                     '% 1-star': round((s.rating == 1).mean() * 100, 1),
                     '% negative (model)': round((s.bert_label == 'negative').mean() * 100, 1),
                     'Hidden complaints (4-5 stars, negative text)': int(((s.rating >= 4) & (s.bert_label == 'negative')).sum()),
                     'Top specific complaint': nm.theme.mode().iat[0] if len(nm) else '-',
                     '% complaints answered': round(c.replied.mean() * 100, 1) if len(c) else None,
                     'Median reply time (h)': round(c[c.replied].reply_hours.median(), 1) if c.replied.any() else None})
    ov = pd.DataFrame(rows)
    st.dataframe(ov, hide_index=True, width='stretch')
    c1, c2 = st.columns(2)
    with c1:
        chart(px.bar(ov, x='App', y='Avg stars', color='App', color_discrete_map=COLORS, text='Avg stars',
                     title='Average star rating', range_y=[0, 5]))
    with c2:
        dist = (f.groupby(['app', 'rating']).size() / f.groupby('app').size()).mul(100).rename('share').reset_index()
        chart(px.bar(dist, x='app', y='share', color='rating', title='Star distribution (% of reviews)',
                     color_continuous_scale='RdYlGn', labels={'app': '', 'share': '% of reviews', 'rating': 'Stars'}))
    st.subheader('Key findings (whole dataset)')
    st.markdown(
        '1. **Each app has a different #1 problem:** BHIM registration/OTP/SIM (37-44% of specific complaints), '
        'Paytm security blocks (29-36%), Google Pay failed payments (24-29%), PhonePe customer support (~24%).\n'
        '2. **Blocking problems cost the most stars:** AutoPay -1.22, crashes -1.10, security blocks -1.10; '
        'slowness -0.52 (OLS, all reviews, controlling for app and length).\n'
        '3. **Fix first:** BHIM onboarding could lift its average by about +0.18 stars, the largest single gain.\n'
        '4. **Paytm 10.84.5** nearly doubled 1-star reviews (9.2% to 17.6%); the next update fixed it (p < 0.001).\n'
        '5. **Replies:** BHIM answers 98% of complaints, but after a median of 46 hours with templates; '
        'Google Pay answers 44%.\n'
        '6. **Emerging:** PhonePe crash complaints and BHIM QR/location and cashback complaints are rising '
        'significantly; BHIM onboarding complaints are falling.')

# ---------------------------------------------------------------- 2 trends
with tabs[1]:
    c1, c2 = st.columns([2, 1])
    metric = c1.selectbox('Measure', ['Average stars', '% negative (model)', '% 1-star', 'Number of reviews'])
    freq = c2.radio('Period', ['Week', 'Month'], horizontal=True)
    g = (f.groupby(['app', pd.Grouper(key='review_date', freq='W' if freq == 'Week' else 'MS')])
          .agg(n=('rating', 'size'), stars=('rating', 'mean'),
               neg=('bert_label', lambda s: (s == 'negative').mean() * 100),
               one=('rating', lambda s: (s == 1).mean() * 100)).reset_index())
    col = {'Average stars': 'stars', '% negative (model)': 'neg', '% 1-star': 'one', 'Number of reviews': 'n'}[metric]
    if col != 'n':
        g = g[g.n >= 30]
    chart(px.line(g, x='review_date', y=col, color='app', markers=True, color_discrete_map=COLORS,
                  labels={'review_date': freq, col: metric}, title=f'{metric} per {freq.lower()}'), 450)
    st.caption('Periods with fewer than 30 reviews are hidden for percentages and averages. '
               'Watch for sudden jumps: they often line up with an app release (see the Releases tab).')

# ---------------------------------------------------------------- 3 complaint themes
with tabs[2]:
    themed = comp[comp.theme.notna()]
    if named.empty:
        st.info('No specific complaints in this selection.')
    else:
        view = st.radio('View', ['Bar chart', 'Heatmap'], horizontal=True)
        share = (named.groupby(['app', 'theme']).size() / named.groupby('app').size()).mul(100).rename('share').reset_index()
        if view == 'Bar chart':
            chart(px.bar(share, x='share', y='theme', color='app', barmode='group', orientation='h',
                         color_discrete_map=COLORS, labels={'share': '% of specific complaints', 'theme': ''},
                         title='What do users complain about?'), 650)
        else:
            hm = share.pivot(index='theme', columns='app', values='share').fillna(0)
            hm = hm.loc[hm.mean(1).sort_values().index]
            chart(px.imshow(hm, text_auto='.1f', color_continuous_scale='Reds', aspect='auto',
                            labels={'color': '% of complaints', 'x': '', 'y': ''},
                            title='Share of each app\'s specific complaints (%)'), 650)
        st.caption(f'{(themed.theme == GENERAL).mean():.0%} of long complaints in this selection name no specific '
                   'problem ("worst app") and are not shown.')
        st.subheader('One theme over time')
        th = st.selectbox('Theme', sorted(named.theme.unique()))
        w = themed.groupby(['app', pd.Grouper(key='review_date', freq='W')])
        tw = (w.theme.apply(lambda s: (s == th).mean() * 100).rename('share').reset_index()
              .merge(w.size().rename('n').reset_index()))
        chart(px.line(tw[tw.n >= 20], x='review_date', y='share', color='app', markers=True,
                      color_discrete_map=COLORS, labels={'review_date': 'Week', 'share': '% of long complaints'},
                      title=f'{th}: weekly share of long complaints'))

# ---------------------------------------------------------------- 4 fix priorities
with tabs[3]:
    pri = T['priority_matrix']
    a = st.selectbox('App', apps, key='pri_app')
    p = pri[(pri.app == a) & (pri.reviews_mentioning >= 30)].copy()
    sig = p[(p.stars_effect < 0) & (p.p_value < 0.05)].assign(stars_lost=lambda x: -x.stars_effect)
    c1, c2 = st.columns([3, 2])
    with c1:
        fig = px.scatter(sig, x='prevalence_%', y='stars_lost', size='reviews_mentioning', text='theme',
                         color_discrete_sequence=[COLORS[a]], size_max=45,
                         labels={'prevalence_%': '% of reviews mentioning the problem',
                                 'stars_lost': 'Stars lost when mentioned'},
                         title=f'{a}: priority matrix (top-right = fix first)')
        fig.update_traces(textposition='top center', textfont_size=10)
        if len(sig):
            fig.update_xaxes(range=[-0.1 * sig['prevalence_%'].max(), sig['prevalence_%'].max() * 1.3])
            fig.add_vline(x=sig['prevalence_%'].median(), line_dash='dash', line_color='grey')
            fig.add_hline(y=sig.stars_lost.median(), line_dash='dash', line_color='grey')
        chart(fig, 520)
    with c2:
        st.markdown('**What if we fixed it?**')
        base = float(p.current_avg.iloc[0])
        options = sig.sort_values('gain_if_fixed', ascending=False).theme.tolist()
        chosen = st.multiselect('Problems to fix', options, default=options[:1])
        solved = st.slider('Share of each problem solved', 0, 100, 100, step=10, format='%d%%')
        gain = sig[sig.theme.isin(chosen)].gain_if_fixed.sum() * solved / 100
        st.metric(f'{a} average rating', f'{base + gain:.2f} stars', f'{gain:+.2f}')
        st.caption('Each review that mentions a fixed problem gets its average star penalty back (capped at 5). '
                   'Gains are added up, so overlapping problems are slightly over-counted. '
                   'Based on association, not a forecast.')
    st.dataframe(p.sort_values('gain_if_fixed', ascending=False)[
        ['theme', 'reviews_mentioning', 'prevalence_%', 'stars_effect', 'p_value', 'gain_if_fixed']],
        hide_index=True, width='stretch', column_config=PFMT)
    st.subheader('Stars lost per problem, all apps (whole dataset)')
    rd = T['rating_drivers_all_apps'].sort_values('stars_effect', ascending=False)
    fig = go.Figure(go.Bar(x=rd.stars_effect, y=rd.theme, orientation='h',
                           marker_color=np.where(rd.p_value < 0.05, '#c0392b', '#b0b7c3'),
                           error_x=dict(type='data', symmetric=False, array=rd.ci_high - rd.stars_effect,
                                        arrayminus=rd.stars_effect - rd.ci_low)))
    fig.update_layout(title='Change in stars when a review mentions the problem (95% confidence interval; grey = not significant)',
                      xaxis_title='Stars')
    chart(fig, 520)

# ---------------------------------------------------------------- 5 releases
with tabs[4]:
    mon = T['release_monitor']
    m = mon[mon.app.isin(apps)].copy()
    m['label'] = m.app + ' ' + m.version.str.replace(r' \(.*\)', '', regex=True)
    m['result'] = np.where(~m.significant, 'Not significant', np.where(m['diff'] < 0, 'Significantly worse', 'Significantly better'))
    chart(px.bar(m.sort_values('diff'), x='diff', y='label', color='result', orientation='h', height=900,
                 color_discrete_map={'Significantly worse': '#c0392b', 'Significantly better': '#27ae60',
                                     'Not significant': '#b0b7c3'},
                 hover_data=['first_seen', 'reviews', 'avg_rating', 'p_value', 'mentions_rising_most'],
                 labels={'diff': 'Rating difference vs rest of the app (stars)', 'label': ''},
                 title='Release monitor: versions with 300+ reviews vs the rest of the same app').update_yaxes(dtick=1, tickfont_size=10))
    st.caption(f'Mann-Whitney test per version, Bonferroni-corrected: significant only if p < 0.05 / {len(mon)} '
               f'= {0.05 / len(mon):.4f}.')
    st.markdown('**Significantly worse releases**')
    st.dataframe(m[m.result == 'Significantly worse'][['app', 'version', 'first_seen', 'reviews', 'avg_rating',
                                                       'rest_of_app', 'diff', 'p_value', 'mentions_rising_most']],
                 hide_index=True, width='stretch', column_config=PFMT)

    st.subheader('Release investigator')
    st.caption('Pick any version: the dashboard compares it with all other versions of the same app and runs '
               'the tests live (whole period, star filter ignored).')
    c1, c2 = st.columns(2)
    ia = c1.selectbox('App', apps, key='inv_app')
    s = df[(df.app == ia) & df.app_version.notna()]
    vc = s.app_version.value_counts()
    vers = vc[vc >= 50].index.tolist()
    first = s.groupby('app_version').review_date.min()
    vers = sorted(vers, key=lambda v: first[v], reverse=True)
    default = vers.index('10.84.5') if '10.84.5' in vers else 0
    iv = c2.selectbox('Version (50+ reviews, newest first)', vers, index=default)
    A, B = s[s.app_version == iv], s[s.app_version != iv]
    mw = stats.mannwhitneyu(A.rating, B.rating).pvalue
    one = stats.chi2_contingency([[(A.rating == 1).sum(), (A.rating != 1).sum()],
                                  [(B.rating == 1).sum(), (B.rating != 1).sum()]])[1]
    r = st.columns(4)
    r[0].metric('Reviews of this version', f'{len(A):,}')
    r[1].metric('Average stars', f'{A.rating.mean():.2f}', f'{A.rating.mean() - B.rating.mean():+.2f} vs other versions')
    r[2].metric('% 1-star', f'{(A.rating == 1).mean():.1%}',
                f'{((A.rating == 1).mean() - (B.rating == 1).mean()) * 100:+.1f} pts', delta_color='inverse')
    r[3].metric('First seen', f'{first[iv]:%d %b %Y}')
    rise = pd.DataFrame({'Problem': list(THEMES.values()),
                         'This version %': [A[c].mean() * 100 for c in THEMES],
                         'Other versions %': [B[c].mean() * 100 for c in THEMES]})
    rise['Change (pts)'] = rise['This version %'] - rise['Other versions %']
    st.dataframe(rise.sort_values('Change (pts)', ascending=False).head(5).round(2), hide_index=True, width='stretch')
    verdict = 'significantly different from' if mw < 0.05 / len(mon) else 'not significantly different from'
    st.info(f'Ratings of {ia} {iv}: Mann-Whitney p = {mw:.1e}; 1-star share: chi-square p = {one:.1e}. '
            f'Using the monitor\'s Bonferroni threshold ({0.05 / len(mon):.4f}), this version is {verdict} '
            'the rest of the app.')
    with st.expander('Case study: Paytm 10.84.5 (from the notebook, cell V1)'):
        st.dataframe(T['paytm_event_groups'], hide_index=True, width='stretch')
        st.dataframe(T['paytm_event_tests'], hide_index=True, width='stretch')

# ---------------------------------------------------------------- 6 emerging topics
with tabs[5]:
    em = T['emerging_topics']
    em = em[em.app.isin(apps)].copy()
    em['result'] = np.where(~em.significant, 'Not significant', np.where(em.change_pp > 0, 'Rising', 'Falling'))
    em['label'] = em.app + ': ' + em.theme
    chart(px.bar(em.sort_values('change_pp'), x='change_pp', y='label', color='result', orientation='h',
                 color_discrete_map={'Rising': '#c0392b', 'Falling': '#27ae60', 'Not significant': '#b0b7c3'},
                 hover_data=['earlier_%', 'last_4_weeks_%', 'complaints_last_4_weeks', 'p_value'],
                 labels={'change_pp': 'Change in share of the app\'s complaints (percentage points)', 'label': ''},
                 title='Last 4 weeks vs earlier: which complaint themes are growing?').update_yaxes(dtick=1, tickfont_size=10), 850)
    st.caption('Chi-square test per app and theme (themes with 20+ complaints in the last 4 weeks), '
               f'Bonferroni-corrected across {len(T["emerging_topics"])} tests. Whole dataset.')
    st.dataframe(em.sort_values('change_pp', ascending=False)[
        ['app', 'theme', 'earlier_%', 'last_4_weeks_%', 'change_pp', 'complaints_last_4_weeks', 'p_value', 'significant']],
        hide_index=True, width='stretch', column_config=PFMT)

# ---------------------------------------------------------------- 7 company replies
with tabs[6]:
    neg = f[f.rating <= 2]
    if neg.empty:
        st.info('No 1-2 star reviews in this selection; widen the star filter.')
    else:
        rep = neg.groupby('app').agg(
            complaints=('rating', 'size'), answered=('replied', 'mean'),
            median_hours=('reply_hours', 'median'),
            template=('template', lambda s: s[neg.loc[s.index, 'replied']].mean())).reset_index()
        rep['answered'] *= 100
        rep['template'] *= 100
        c1, c2, c3 = st.columns(3)
        with c1:
            chart(px.bar(rep, x='app', y='answered', color='app', color_discrete_map=COLORS, text_auto='.0f',
                         labels={'app': '', 'answered': '%'}, title='% of 1-2 star reviews answered'))
        with c2:
            chart(px.bar(rep, x='app', y='median_hours', color='app', color_discrete_map=COLORS, text_auto='.1f',
                         labels={'app': '', 'median_hours': 'hours'}, title='Median reply time (hours)'))
        with c3:
            chart(px.bar(rep, x='app', y='template', color='app', color_discrete_map=COLORS, text_auto='.0f',
                         labels={'app': '', 'template': '%'}, title='% of replies that are templates'))
        st.caption('Only reviews with 1-2 stars inside the selected filters. A template is an identical reply text '
                   'sent 20 or more times.')
        st.subheader('Which complaints do other users agree with?')
        hv = (named[named.app.isin(apps)].groupby(['app', 'theme']).helpful_votes.agg(['size', 'sum'])
              .rename(columns={'size': 'complaints', 'sum': 'helpful votes'}).reset_index()
              .sort_values('helpful votes', ascending=False))
        st.dataframe(hv.groupby('app').head(3), hide_index=True, width='stretch')

# ---------------------------------------------------------------- 8 models and tests
with tabs[7]:
    st.subheader('Sentiment models (test set, whole dataset)')
    mr = T['model_results']
    chart(px.bar(mr, x='macro_f1', y='model', color='task', barmode='group', orientation='h', text_auto='.3f',
                 labels={'macro_f1': 'Macro F1', 'model': ''}, range_x=[0, 1],
                 title='Macro F1 on the held-out test set (higher is better)'), 420)
    st.dataframe(mr, hide_index=True, width='stretch')
    st.caption('Macro F1 averages the F1 score of every class equally, so the small negative and neutral classes '
               'count as much as the large positive class. Split: 70/15/15, stratified by stars.')
    st.subheader('Topic models')
    st.dataframe(T['topic_model_comparison'], hide_index=True, width='stretch')
    st.caption('Coherence: NPMI of each topic\'s top 10 words (-1 to +1), same vocabulary for both models. '
               'Diversity: share of unique words across all topics.')
    st.subheader('Statistical tests used in the project')
    st.dataframe(T['statistical_tests_summary'], hide_index=True, width='stretch',
                 column_config={'question': st.column_config.TextColumn('Question', width='large'),
                                'result': st.column_config.TextColumn('Result', width='large')})
    st.subheader('Robustness check: stricter crash keywords')
    st.dataframe(T['robustness_crash'], hide_index=True, width='stretch')

# ---------------------------------------------------------------- 9 review explorer
with tabs[8]:
    c1, c2, c3 = st.columns([2, 2, 1])
    q = c1.text_input('Search review text (e.g. otp, refund, security alert)')
    th = c2.multiselect('Complaint theme', sorted(f.theme.dropna().unique()))
    sent = c3.multiselect('Model sentiment', ['negative', 'neutral', 'positive'])
    hidden = st.checkbox('Only hidden complaints (4-5 stars, but the model reads the text as negative)')
    e = f
    if q:
        e = e[e.review_text.str.contains(q, case=False, na=False, regex=False)]
    if th:
        e = e[e.theme.isin(th)]
    if sent:
        e = e[e.bert_label.isin(sent)]
    if hidden:
        e = e[(e.rating >= 4) & (e.bert_label == 'negative')]
    cols = ['app', 'review_date', 'app_version', 'rating', 'bert_label', 'theme', 'helpful_votes', 'review_text']
    st.write(f'{len(e):,} reviews match - showing the 200 most helpful')
    st.dataframe(e.sort_values('helpful_votes', ascending=False).head(200)[cols], hide_index=True, width='stretch',
                 column_config={'review_text': st.column_config.TextColumn('Review', width='large')})
    st.download_button('Download matching reviews (CSV)', e[cols].to_csv(index=False).encode('utf-8'),
                       file_name='upi_reviews_selection.csv', mime='text/csv')
