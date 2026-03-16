import streamlit as st
# import supabase
from supabase import create_client, Client
from dotenv import load_dotenv
from pandas import DataFrame
import plotly.express as px
import time
import os

SUPABASE_URL= "https://czjtoigjqywaccmkdead.supabase.co"
SUPABASE_KEY= "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN6anRvaWdqcXl3YWNjbWtkZWFkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEyNDk1NzMsImV4cCI6MjA4NjgyNTU3M30.3Hf0nRDg9uAIXqIkQH8WGJyAG3Q-f3VOuUbMVfl9968"

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

# st.session_state = 'app'

@st.cache_resource
def get_supabase_client():
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return create_client(url, key)


supabase = get_supabase_client()

# Loading Bar - to show that things are happening?
progress_text = "Operation in progress. Please wait."
my_bar = st.progress(0, text=progress_text)
for percent_complete in range(100):
    time.sleep(0.01)
    my_bar.progress(percent_complete + 1, text=progress_text)
time.sleep(1)
my_bar.empty()



df = None
option = None  # Add this line here

# Testing connection to custom view
try:
    response_1 = supabase.table("v_league_data_sum_v1").select("*").execute()
    df = DataFrame(response_1.data)
except Exception as e:
    st.error(f"Error fetching data: {e}")

st.title("League Data")

# 2. Only show the selectbox if df was successfully created and isn't empty
if df is not None and not df.empty:
    option = st.selectbox(
        "Please select a League",
        df['league_name'].unique(),
        index=None,
        placeholder="Choose one...",
    )
else:
    st.warning("No data available to display.")

### Printing Dataframe - no editing though
if option:
    st.header("League Results")
    # st.subheader("st.dataframe")

    tab1, tab2 = st.tabs(["Placings", "Faction Data"])

    display_df = df[df['league_name'] == option].copy()
    display_df = display_df.sort_values(by='sorting', ascending=False)
    display_df.insert(0, 'rank', range(1, len(display_df) + 1))
    display_df['record'] = (
            display_df['win'].astype(str) + "/" +
            display_df['draw'].astype(str) + "/" +
            display_df['loss'].astype(str)
    )

    with tab1:
        st.subheader("Current Rankings in Event")
        st.dataframe(
            display_df[['rank', 'player_name', 'faction_name', 'sub_faction_name', 'record', 'total_score',
                        'score_difference']],
            hide_index=True,
            column_config={
                "rank": "Rank",
                "player_name": "Player",
                "faction_name": "Faction",
                "sub_faction_name": "Detatchment",
                "record": "W/D/L",
                "total_score": "Total Score",
                "score_difference": "+/- Margin"
            },
            use_container_width=True
        )

    with tab2:
        ### Printing Dataframe - no editing though
        st.subheader("Faction Win Rates")
        # st.subheader("st.plotly_chart")
        # x_vals = df.loc[df['league_name'] == option, 'faction_name']
        # y_vals = df.loc[df['league_name'] == option, 'total_score']
        # fig = px.bar(x=x_vals, y=y_vals)
        # st.plotly_chart(fig,  width="stretch")

        # TESTING PIE CHART and FACTION WIN RATES
        league_df = df[df['league_name'] == option]

        # Count occurrences of each faction
        faction_counts = league_df['faction_name'].value_counts().reset_index()
        faction_counts.columns = ['faction_name', 'count']

        st.subheader("Faction Turnout")
        fig_pie = px.pie(faction_counts, values='count', names='faction_name', hole=0.3)
        st.plotly_chart(fig_pie)

        # 1. Group by faction and sum the stats
        stats = league_df.groupby('faction_name')[['win', 'loss', 'draw']].sum().reset_index()

        # 2. Calculate Win Rate: Wins / Total Games
        # (Using a small check to avoid division by zero)
        stats['total_games'] = stats['win'] + stats['loss'] + stats['draw']
        stats['win_rate'] = (stats['win'] / stats['total_games']) * 100

        st.subheader("Faction Win Rate (%)")

        # 3. Create Horizontal Bar Chart
        # Use orientation='h' and swap x and y
        fig_bar = px.bar(
            stats,
            x='win_rate',
            y='faction_name',
            orientation='h',
            text_auto='.1f',  # Shows the percentage on the bar
            labels={'win_rate': 'Win Rate (%)', 'faction_name': 'Faction'}
        )

        # Sort the chart so the highest win rate is at the top
        fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'})

        st.plotly_chart(fig_bar)

        # Count occurrences of each allegiance
        allegiance_counts = league_df['allegiance_name'].value_counts().reset_index()
        allegiance_counts.columns = ['allegiance_name', 'count']

        st.subheader("Allegiance Turnout")
        fig_pie_2 = px.pie(allegiance_counts, values='count', names='allegiance_name', hole=0.3)
        st.plotly_chart(fig_pie_2)

        # 1. Group by allegiance and sum the stats
        allegiance_stats = league_df.groupby('allegiance_name')[['win', 'loss', 'draw']].sum().reset_index()

        # 2. Calculate Win Rate: Wins / Total Games
        # (Using a small check to avoid division by zero)
        allegiance_stats['total_games'] = allegiance_stats['win'] + allegiance_stats['loss'] + allegiance_stats[
            'draw']
        allegiance_stats['win_rate'] = (allegiance_stats['win'] / allegiance_stats['total_games']) * 100

        st.subheader("Allegiance Win Rate (%)")

        # 3. Create Horizontal Bar Chart
        # Use orientation='h' and swap x and y
        fig_bar_2 = px.bar(
            allegiance_stats,
            x='win_rate',
            y='allegiance_name',
            orientation='h',
            text_auto='.1f',  # Shows the percentage on the bar
            labels={'win_rate': 'Win Rate (%)', 'allegiance_name': 'Allegiance'}
        )

        # Sort the chart so the highest win rate is at the top
        fig_bar_2.update_layout(yaxis={'categoryorder': 'total ascending'})

        st.plotly_chart(fig_bar_2)
