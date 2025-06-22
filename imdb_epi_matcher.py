import streamlit as st
import pandas as pd
from difflib import get_close_matches

# Load IMDb data (replace with your local files)
@st.cache_data
def load_data():
    basics = pd.read_csv('title.basics.tsv', sep='\t', dtype=str, na_values='\\N')
    episodes = pd.read_csv('title.episode.tsv', sep='\t', dtype=str, na_values='\\N')
    return basics, episodes

basics, episodes = load_data()

st.title("🎬 IMDb Title ID Fetcher")

# Input series name
series_name = st.text_input("Enter the series name:")

# Input episodes (multi-line)
episode_input = st.text_area("Provide episode names (or leave blank to get all):")

if series_name:
    your_episodes = [line.strip() for line in episode_input.strip().splitlines() if line.strip()]
    
    # Match series
    candidates = basics[(basics['titleType'] == 'tvSeries') & (basics['primaryTitle'].str.lower() == series_name.lower())]
    if candidates.empty:
        st.error(f"❌ Could not find series '{series_name}' in IMDb data.")
    else:
        series_id = candidates.iloc[0]['tconst']
        st.success(f"✅ Found series: {candidates.iloc[0]['primaryTitle']} (IMDb ID: {series_id})")

        # Get episodes
        series_episodes = episodes[episodes['parentTconst'] == series_id]
        merged = series_episodes.merge(basics, on='tconst')

        valid_titles = merged['primaryTitle'].dropna().unique().tolist()
        matched_rows = []

        if your_episodes:
            # Match provided episodes
            for input_title in your_episodes:
                close = get_close_matches(input_title, valid_titles, n=1, cutoff=0.6)
                if close:
                    row = merged[merged['primaryTitle'] == close[0]].iloc[0]
                    matched_rows.append({
                        'InputTitle': input_title,
                        'MatchedTitle': row['primaryTitle'],
                        'seasonNumber': row.get('seasonNumber', ''),
                        'episodeNumber': row.get('episodeNumber', ''),
                        'tconst': row['tconst']
                    })
                else:
                    matched_rows.append({
                        'InputTitle': input_title,
                        'MatchedTitle': '',
                        'seasonNumber': '',
                        'episodeNumber': '',
                        'tconst': ''
                    })
        else:
            # No input → output all episodes
            for _, row in merged.iterrows():
                matched_rows.append({
                    'InputTitle': row['primaryTitle'],
                    'MatchedTitle': row['primaryTitle'],
                    'seasonNumber': row.get('seasonNumber', ''),
                    'episodeNumber': row.get('episodeNumber', ''),
                    'tconst': row['tconst']
                })

        # Create DataFrame + sort
        df_out = pd.DataFrame(matched_rows)
        df_out['seasonNumber'] = pd.to_numeric(df_out['seasonNumber'], errors='coerce')
        df_out['episodeNumber'] = pd.to_numeric(df_out['episodeNumber'], errors='coerce')
        df_out = df_out.sort_values(['seasonNumber', 'episodeNumber'], na_position='last')

        st.dataframe(df_out)

        # Show match info
        st.info(f"📌 Matched: {df_out['MatchedTitle'].astype(bool).sum()} / {len(df_out)} episodes")

        # Download
        csv = df_out.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, "matched_episodes.csv", "text/csv")
