import streamlit as st
from supabase import create_client, Client
from streamlit_js_eval import streamlit_js_eval
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px
import time
import os

import streamlit as st
from supabase import create_client
from dotenv import load_dotenv
import os

from supabase import create_client, ClientOptions

st.set_page_config(page_title="BGC Club App", page_icon="🎲")

def collapse_sidebar():
    # Targets the close 'X' or chevron button in the Streamlit sidebar
    streamlit_js_eval(js_expressions='window.parent.document.querySelector("button[kind=\'headerNoPadding\']").click()')

@st.cache_resource
def get_supabase_client():
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    # This forces EVERY auth action to use PKCE (?code=) instead of Implicit (#hash)
    return create_client(url, key, options=ClientOptions(flow_type="pkce"))

supabase = get_supabase_client()

# Initialize session state variables if they don't exist
if "page" not in st.session_state:
    st.session_state.page = None
if "games" not in st.session_state:
    st.session_state.games = 0
# 1. Initialise the page and the player name
if "page" not in st.session_state:
    st.session_state.page = None
if "temp_scores" not in st.session_state:
    st.session_state.temp_scores = False
if "confirm_submit" not in st.session_state:
    st.session_state.confirm_submit = False
if "game_data" not in st.session_state:
    st.session_state.game_data = {}

discord_name = ""
if "user" in st.session_state:
    # Try to get the name from metadata
    discord_name = st.session_state.user.user_metadata.get('full_name') or \
                   st.session_state.user.user_metadata.get('username') or \
                   st.session_state.user.user_metadata.get('name') or ""
    # Also initialize the widget key 'p1_f' if it's not already there
    if "p1_f" not in st.session_state:
        st.session_state.p1_f = discord_name

# 2. THE SESSION "CATCHER" (Must be at the top)
# This handles the redirect from Discord (?code=...)
if "code" in st.query_params:
    try:
        auth_code = st.query_params["code"]
        res = supabase.auth.exchange_code_for_session({"auth_code": auth_code})
        st.session_state.user = res.user
        st.query_params.clear()
        st.rerun()  # Immediately stops this run and starts a fresh one as "Logged In"
    except Exception as e:
        st.error(f"Login Sync Failed: {e}")

# #3. PERSISTENT USER SYNC
#if "user" not in st.session_state:
    #user_resp = supabase.auth.get_user()
    #if user_resp and user_resp.user:
        #st.session_state.user = user_resp.user


# 4. LOGIN FUNCTION
def show_login_screen():
    st.title("BGC Club App Sign In")
    st.info("Please sign in with your Discord to use this app.")

    # # local device testing link
    # redirect_uri = "http://localhost:8501/"
    # # live link
    redirect_uri = "https://bgc-app.streamlit.app/"
    try:
        response = supabase.auth.sign_in_with_oauth({
            "provider": "discord",
            "options": {"redirect_to": redirect_uri},
            "flow_type": "pkce"
        })
        if response and hasattr(response, 'url'):
            st.link_button("Sign in with Discord", response.url)
    except Exception as e:
        st.error(f"Error: {e}")


# 5. THE ROUTER (The only place UI is drawn)
if "user" not in st.session_state:
    show_login_screen()
    st.stop()  # CRITICAL: Prevents anything below from loading if not logged in
else:
    # --- EVERYTHING BELOW RUNS ONLY WHEN LOGGED IN ---
    st.sidebar.success(f"Logged in as {st.session_state.user.user_metadata.get('full_name')}")
    # st.sidebar.code(f"DEBUG: Current Page = {st.session_state.page}")
    if st.sidebar.button("Home"):
        st.session_state.page = None
        collapse_sidebar()
        st.rerun()
    if st.sidebar.button("Log Games"):
        st.session_state.page = "Log Games"
        collapse_sidebar()
        st.rerun()
    if st.sidebar.button("Events"):
        st.session_state.page = "Events"
        collapse_sidebar()
        st.rerun()
    if st.sidebar.button("Graphs"):
        st.session_state.page = "Graphs"
        collapse_sidebar()
        st.rerun()
    if st.sidebar.button("Personal Stats"):
        st.session_state.page = "Personal Stats"
        collapse_sidebar()
        st.rerun()
    #if st.sidebar.button("Log Out"):
        #supabase.auth.sign_out()
        #del st.session_state.user
        #st.rerun()
    if st.sidebar.button("Log Out"):
        supabase.auth.sign_out()
        # Clear session state completely to be safe
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

        

    if st.session_state.page is None:
        st.header("BGC Club App")
        st.write(f"Welcome back, {st.session_state.user.user_metadata.get('full_name')}!")
        # st.text(f"Here we will be hosting all of our club game data for you to use and analyse however you'd like!\n\n"
        #         f"If you have any issues or want to submit a request for something new (new game system added, graph, etc.) then please contact scottpaisey in our Discord.")
        st.divider()
        st.write(f"Most recent matches logged")

        # Fetch from your new view
        res = supabase.table("match_results").select("*").order("game_date", desc=True).limit(10).execute()
        if res.data:
            recent_df = pd.DataFrame(res.data)
            st.subheader("Latest 10 Battle Reports")
            st.dataframe(
                recent_df,
                column_order=(
                    "game_date",
                    "system_name",
                    "display_p1_name",
                    "p1_faction",
                    "p1_score_total",
                    "display_p2_name",
                    "p2_faction",
                    "p2_score_total"
                ),
                column_config={
                    "game_date": "Date",
                    "system_name": "System",
                    "display_p1_name": "Player 1",
                    "p1_faction": "P1 Faction",
                    "p1_score_total": "P1 Score",
                    "display_p2_name": "Player 2",
                    "p2_faction": "P2 Faction",
                    "p2_score_total": "P2 Score"
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No match history found yet. Go log some games!")

    elif st.session_state.page == "Log Games":
        st.header("Log Games")
        st.divider()
        st.subheader("Step 1: Please Choose the System you are logging")
        if st.button("Warhammer 40,000"):
            st.session_state.page = "40k"
            st.rerun()
        if st.button("Age of Sigmar", disabled=True):
            st.session_state.page = "AoS"
            st.rerun()

    elif st.session_state.page == "40k":
        st.header("Warhammer 40,000 Game")
        st.divider()

        try:
            p1_response_system_factions = supabase.table("system_factions").select("*").execute()
            p1_df_system_factions = pd.DataFrame(p1_response_system_factions.data)
            p2_response_system_factions = supabase.table("system_factions").select("*").execute()
            p2_df_system_factions = pd.DataFrame(p2_response_system_factions.data)
            p2_response_account = supabase.table("profiles").select("*").execute()
            p2_df_account = pd.DataFrame(p2_response_account.data)
        except Exception as e:
            print(e)
        st.subheader("Game Details")
        game_size = st.selectbox('Game Size', ['Strike Force', 'Incursion', 'Other'], index=None,
                                 placeholder="Choose...", key="game_s")
        # mission_pack = st.selectbox(st.selectbox('Mission Pack',['Strike Force (2k)', 'Incursion (1k)', 'Combat Partol'], index=None, placeholder="Choose...")
        st.write("**Your Details**")
        # Extract the name from Discord metadata
        p1_name = st.text_input("Your Discord Name*", value=discord_name, key="p1_username")
        # p1_last = st.text_input("Surname", key="p1_l")
        # p1_known = st.text_input("Known As", key="p1_k")
        # 1. Allegiance Dropdown
        p1_all_df = p1_df_system_factions[p1_df_system_factions['short_name'] == '40K']
        p1_all = st.selectbox("Your Allegiance", p1_all_df['allegiance'].unique(), index=None,
                              placeholder="Choose...", key="p1_all_sel")
        # 2. Faction Dropdown (MUST use filtered options)
        if p1_all:
            # We filter the dataframe here
            p1_fac_df = p1_all_df[p1_all_df['allegiance'] == p1_all]
            # We use faction_df to get the unique names for the options
            p1_fac = st.selectbox("Your Faction", p1_fac_df['faction'].unique(), index=None,
                                  placeholder="Choose...", key="p1_fac_sel")
        else:
            p1_fac = st.selectbox("Your Faction", [], disabled=True)
        # 3. Sub-Faction Dropdown (MUST use filtered options)
        if p1_fac:
            p1_sub_df = p1_fac_df[p1_fac_df['faction'] == p1_fac]
            p1_sub = st.selectbox("Your Sub-Faction", p1_sub_df['subfaction'].unique(), index=None,
                                  placeholder="Choose...", key="p1_sub_sel")
        else:
            p1_sub = st.selectbox("Your Sub-Faction", [], disabled=True)
        # p1_wf = st.toggle("Went First?*", key="p1_wf_key", on_change=handle_wf_toggle, args=("p1",))

        st.write("**Opponent Details**")

        # 1. Fetch all profiles from Supabase to check names against
        # You should wrap this in st.cache_data if your club gets very large
        profiles_resp = supabase.table("profiles").select("id, full_name").execute()
        db_profiles = profiles_resp.data  # List of dicts: {'id': '...', 'full_name': '...'}
        # 2. Text Input for Opponent
        p2_input = st.text_input("Opponent Name*", key="p2_username",
                                 help="Type their Discord User Name to link their profile")
        # 3. Validation Step
        p2_id = None
        p2_name = None
        p2_custom_name = None

        if p2_input:
            search_term = p2_input.strip().lower()

            # Use fillna to prevent crashes on nulls in DB
            mask = (p2_df_account['username'].fillna('').str.lower() == search_term) | \
                   (p2_df_account['full_name'].fillna('').str.lower() == search_term)

            matched_rows = p2_df_account[mask]

            if not matched_rows.empty:
                user_row = matched_rows.iloc[0]
                p2_id = user_row['id']
                # Assign the found name to p2_name
                p2_name = user_row['full_name'] if user_row['full_name'] else user_row['username']
                st.success(f"✅ User found! Linked to **{p2_name}**.")
            else:
                p2_id = None
                p2_name = p2_input
                st.warning("⚠️ User not found. Recording as 'Guest'.")

        # 1. Allegiance Dropdown
        p2_all_df = p2_df_system_factions[p2_df_system_factions['short_name'] == '40K']
        p2_all = st.selectbox("Opponents Allegiance", p2_all_df['allegiance'].unique(), index=None,
                              placeholder="Choose...", key="p2_all_sel")
        # 2. Faction Dropdown (MUST use filtered options)
        if p2_all:
            # We filter the dataframe here
            p2_fac_df = p2_all_df[p2_all_df['allegiance'] == p2_all]
            # We use faction_df to get the unique names for the options
            p2_fac = st.selectbox("Opponents Faction", p2_fac_df['faction'].unique(), index=None,
                                  placeholder="Choose...", key="p2_fac_sel")
        else:
            p2_fac = st.selectbox("Opponents Faction", [], disabled=True)
        # 3. Sub-Faction Dropdown (MUST use filtered options)
        if p2_fac:
            p2_sub_df = p2_fac_df[p2_fac_df['faction'] == p2_fac]
            p2_sub = st.selectbox("Opponents Sub-Faction", p2_sub_df['subfaction'].unique(), index=None,
                                  placeholder="Choose...", key="p2_sub_sel")
        else:
            p2_sub = st.selectbox("Opponents Sub-Faction", [], disabled=True)
        # p2_wf = st.toggle("Went First?*", key="p2_wf_key", on_change=handle_wf_toggle, args=("p1",))

        attacker_id = None
        defender_id = None
        went_first_id = None

        options = ["You", "Opponent"]
        went_first = st.segmented_control(
            "Who went first?", options, selection_mode="single", key="went_first"
        )
        attacking_player = st.segmented_control(
            "Who is the attacker?", options, selection_mode="single", key="attacking_player"
        )

        if st.button("Proceed to Scoring"):
            # 1. Define your conditions
            names_entered = p1_name and p2_name
            allegiance_selected = p1_all and p2_all
            factions_selected = p1_fac and p2_fac
            sub_factions_selected = p1_sub and p2_sub
            actual_p2_id = p2_id if (p2_id and p2_id != p2_name) else None

            if not names_entered:
                st.error("❌ Both player names are mandatory.")
            elif not sub_factions_selected:
                st.error("❌ Both players must select an Allegiance, Faction and Subfaction.")
            else:
                # 2. Assign Attacker / Defender
                if attacking_player == "You":
                    attacker_id = st.session_state.user.id
                    defender_id = actual_p2_id
                else:
                    attacker_id = actual_p2_id
                    defender_id = st.session_state.user.id
                # 3. Assign Went First
                if went_first == "You":
                    went_first_id = st.session_state.user.id
                else:
                    went_first_id = actual_p2_id

                # Lookup IDs
                p1_row = p1_df_system_factions[p1_df_system_factions['subfaction'] == p1_sub].iloc[0]
                p2_row = p2_df_system_factions[p2_df_system_factions['subfaction'] == p2_sub].iloc[0]

                # Store data for the next page
                st.session_state.game_data = {
                    "system_id": p1_row['system_id'],
                    "p1_id": st.session_state.user.id,
                    "p1_name": p1_name,
                    "p1_all": p1_all,
                    "p1_fac": p1_fac,
                    "p1_sub": p1_sub,
                    "p2_id": actual_p2_id,
                    "p2_name": p2_name,
                    "p1_all": p1_all,
                    "p2_fac": p2_fac,
                    "p2_sub": p2_sub,
                    "p1_fac_id": p1_row['faction_id'],
                    "p2_fac_id": p2_row['faction_id'],
                    "attacker_id": attacker_id,
                    "defender_id": defender_id,
                    "went_first_id": went_first_id,
                    "game_size": game_size
                }

                # FIX 2: Switch the page and rerun
                st.session_state.page = "40k_scores"
                st.rerun()

    elif st.session_state.page == "40k_scores":

        st.subheader("Game Scores")
        st.divider()

        system_id = st.session_state.game_data.get("system_id", None)
        game_size = st.session_state.game_data.get("game_size", None)

        attacker_id = st.session_state.game_data.get("attacker_id", None)
        defender_id = st.session_state.game_data.get("defender_id", None)
        went_first_id = st.session_state.game_data.get("went_first_id", None)

        p1_id = st.session_state.game_data.get("p1_id", None)
        p1_name = st.session_state.game_data.get("p1_name", None)
        p1_fac_id = st.session_state.game_data.get("p1_fac_id", None)
        p1_all = st.session_state.game_data.get("p1_all", None)
        p1_fac = st.session_state.game_data.get("p1_fac", None)
        p1_sub = st.session_state.game_data.get("p1_sub", None)

        p2_id = st.session_state.game_data.get("p2_id", None)
        p2_name = st.session_state.game_data.get("p2_name", None)
        p2_fac_id = st.session_state.game_data.get("p2_fac_id", None)
        p2_all = st.session_state.game_data.get("p2_all", None)
        p2_fac = st.session_state.game_data.get("p2_fac", None)
        p2_sub = st.session_state.game_data.get("p2_sub", None)

        # 1. The Data Entry Form
        if not st.session_state.confirm_submit:
            with st.form("score_submission_form"):
                col3, col4 = st.columns(2)
                with col3:
                    st.subheader(f"{p1_name}")
                    st.write(f"**{p1_fac}**")
                    st.write(f"{p1_sub}")
                    p1_pri = st.number_input("Primary Score*", 0, 45, key="p1_p")
                    p1_sec = st.number_input("Secondary Score*", 0, 45, key="p1_s")
                    if st.toggle("Battle Ready?*", key="p1_br"):
                        p1_br = 10
                    else:
                        p1_br = 0
                with col4:
                    st.subheader(f"{p2_name}")
                    st.write(f"**{p2_fac}**")
                    st.write(f"{p2_sub}")
                    p2_pri = st.number_input("Primary Score*", 0, 45, key="p2_p")
                    p2_sec = st.number_input("Secondary Score*", 0, 45, key="p2_s")
                    if st.toggle("Battle Ready?*", key="p2_br"):
                        p2_br = 10
                    else:
                        p2_br = 0

                # Use the form submit button to move to confirmation
                submit_scores = st.form_submit_button("Review Results")

                if submit_scores:
                    st.session_state.temp_scores = {
                        "p1_pri": p1_pri, "p1_sec": p1_sec, "p1_br": p1_br,
                        "p2_pri": p2_pri, "p2_sec": p2_sec, "p2_br": p2_br
                    }
                    st.session_state.confirm_submit = True
                    st.rerun()

        # 2. The "Are You Sure?" Pop-up (Visualised as a Container)
        else:
            st.warning("⚠️ **Confirm Game Results**")
            st.write("Please review the details below. **These cannot currently be changed after posting.**")
            # Display all gathered info
            setup = st.session_state.game_data
            scores = st.session_state.temp_scores
            # Calculate Totals
            p1_total = scores['p1_pri'] + scores['p1_sec'] + scores['p1_br']
            p2_total = scores['p2_pri'] + scores['p2_sec'] + scores['p2_br']

            # Determine Results
            if p1_total > p2_total:
                winner_id, loser_id = setup['p1_id'], setup['p2_id']
                is_draw = False
            elif p2_total > p1_total:
                winner_id, loser_id = setup['p2_id'], setup['p1_id']
                is_draw = False
            else:
                winner_id, loser_id = None, None
                is_draw = True

            col_a, col_b = st.columns(2)
            col_a.write(f"Name: **{setup['p1_name']}**"
                        f"\n\nFaction: {setup['p1_fac']}"
                        f"\n\nDetatchment: {setup['p1_sub']}"
                        f"\n\nPrimary: {scores['p1_pri']}"
                        f"\n\nSecondary: {scores['p1_sec']}"
                        f"\n\nBattle Ready: {scores['p1_br']}")
            col_b.write(f"Name: **{setup['p2_name']}**"
                        f"\n\nFaction: {setup['p2_fac']}"
                        f"\n\nDetatchment: {setup['p2_sub']}"
                        f"\n\nPrimary: {scores['p2_pri']}"
                        f"\n\nSecondary: {scores['p2_sec']}"
                        f"\n\nBattle Ready: {scores['p2_br']}")

            c1, c2 = st.columns(2)


            def clean_id(val):
                # If the value is 'krystal' or any other name string, return None
                if isinstance(val, str) and len(val) < 30:
                    return None
                return val

            if c1.button("✅ Yes, Post Results", type="primary", use_container_width=True):
                # --- DATABASE INSERT LOGIC HERE ---
                # inserting game data into table
                match_details = {
                        "game_system_id": setup['system_id'],
                        "event_id": None,
                        "round_id": None,
                        "mission_id": None,
                        "game_size": setup['game_size'],
                        "player_1_id": setup['p1_id'],
                        "p1_faction_id": setup['p1_fac_id'],
                        "p1_score_01": scores['p1_pri'],
                        "p1_score_02": scores['p1_sec'],
                        "p1_score_03": scores['p1_br'],
                        "p1_score_04": 0,
                        "p1_score_05": 0,
                        "p1_score_total": scores['p1_pri'] + scores['p1_sec'] + scores['p1_br'],
                        "p1_score_mar": p1_total - p2_total,
                        "player_2_id": clean_id(setup['p2_id']),
                        "player_2_name": setup['p2_name'],
                        "p2_faction_id": setup['p2_fac_id'],
                        "p2_score_01": scores['p2_pri'],
                        "p2_score_02": scores['p2_sec'],
                        "p2_score_03": scores['p2_br'],
                        "p2_score_04": 0,
                        "p2_score_05": 0,
                        "p2_score_total": scores['p2_pri'] + scores['p2_sec'] + scores['p2_br'],
                        "p2_score_mar": p2_total - p1_total,
                        "went_first_id": clean_id(setup['went_first_id']),
                        "winner_id": clean_id(winner_id),
                        "loser_id": clean_id(loser_id),
                        "attacker_id": clean_id(setup['attacker_id']),
                        "defender_id": clean_id(setup['defender_id']),
                        "is_draw": is_draw,
                        # "played_at": ,
                        "recorded_by":  setup['p1_id']
                        # "club_id": ,
                    }

                # --- DEBUG MONITOR ---
                with st.sidebar.expander("🔍 Variable Monitor", expanded=True):
                    st.write(f"**p2_id:** `{p2_id}`")
                    st.write(f"**p2_name:** `{p2_name}`")
                    st.write(f"**Type of p2_id:** `{type(p2_id).__name__}`")
                    st.write("### 🚨 Database Submission Debug")
                    for key, value in match_details.items():
                        if value == "krystal":
                            st.error(
                                f"FOUND THE ERROR: The column **'{key}'** is trying to send 'krystal' but it needs to be NULL (None).")
                    st.json(match_details)  # This shows you the whole dictionary
                # -----------------------------

                supabase.table("matches").insert(match_details).execute()

                st.success("Game posted to Supabase!")

                st.session_state.game_data = {}
                st.session_state.temp_scores = {}
                st.session_state.confirm_submit = False
                # st.session_state.page = None  # Go back to home
                # st.rerun()
                st.session_state.selected_system = "40K"
                st.session_state.page = None
                st.rerun()

            if c2.button("❌ No, Edit Scores", use_container_width=True):
                st.session_state.confirm_submit = False
                st.rerun()

    elif st.session_state.page == "Events":
        st.header("Events")
        st.divider()

        # --- STEP 1: DEFINE ALL REPORT FUNCTIONS ---

        def show_leaderboard(df):
            st.subheader(f"🏆 {selected_event} Rankings")
            p1_data = df[['display_p1_name', 'p1_score_total', 'display_p2_name']].copy()
            p1_data.columns = ['player', 'score', 'opponent']
            p1_data['is_win'] = df['p1_score_total'] > df['p2_score_total']

            p2_data = df[['display_p2_name', 'p2_score_total', 'display_p1_name']].copy()
            p2_data.columns = ['player', 'score', 'opponent']
            p2_data['is_win'] = df['p2_score_total'] > df['p1_score_total']

            combined = pd.concat([p1_data, p2_data])
            leaderboard = combined.groupby('player').agg(
                Played=('player', 'count'),
                Wins=('is_win', 'sum'),
                Total_Points=('score', 'sum')
            ).reset_index()

            leaderboard = leaderboard.sort_values(by=['Wins', 'Total_Points'], ascending=False)
            leaderboard.insert(0, 'Rank', range(1, len(leaderboard) + 1))

            st.dataframe(
                leaderboard,
                column_config={
                    "Rank": st.column_config.NumberColumn("Rank", format="#%d"),
                    "player": "Player Name",
                    "Played": "Games",
                    "Wins": "Wins ✅",
                    "Total_Points": st.column_config.NumberColumn("Total Points", format="%d pts"),
                },
                hide_index=True,
                use_container_width=True
            )
            return leaderboard

        def show_event_awards(df, leaderboard):
            st.subheader("🎖️ The Sector Awards")
            
            # --- PRE-CALCULATIONS ---
            leaderboard['Avg_Score'] = (leaderboard['Total_Points'] / leaderboard['Played']).round(1)
            
            # 1. Warmaster & Penitent
            warmaster = leaderboard.iloc[0]['player']
            penitent = leaderboard.iloc[-1]['player']
            
            # 2. Master of the Tactica
            top_tactician = leaderboard.sort_values('Avg_Score', ascending=False).iloc[0]
            
            # 3. Exterminatus Protocol (Max Margin)
            max_idx = df[['p1_score_mar', 'p2_score_mar']].max(axis=1).idxmax()
            max_mar_row = df.loc[max_idx]
            if max_mar_row['p1_score_mar'] > max_mar_row['p2_score_mar']:
                ex_player, max_mar = max_mar_row['display_p1_name'], max_mar_row['p1_score_mar']
            else:
                ex_player, max_mar = max_mar_row['display_p2_name'], max_mar_row['p2_score_mar']
        
            # --- TOP ROW METRICS ---
            col1, col2, col3 = st.columns(3)
            col1.metric("⚔️ Warmaster", warmaster, "1st Place")
            col2.metric("📜 Master of Tactica", top_tactician['player'], f"{top_tactician['Avg_Score']} Avg")
            col3.metric("💥 Exterminatus", ex_player, f"+{max_mar} Margin")
            
            st.divider()
        
            # --- NEW: SECTOR COMMANDERS (Top Performer per Allegiance) ---
            st.write("### 🛡️ Sector Commanders")
            # We unpivot to find which player performed best for each allegiance
            p1 = df[['display_p1_name', 'p1_allegiance', 'p1_score_total']].rename(columns={'display_p1_name':'player', 'p1_allegiance':'allg', 'p1_score_total':'score'})
            p2 = df[['display_p2_name', 'p2_allegiance', 'p2_score_total']].rename(columns={'display_p2_name':'player', 'p2_allegiance':'allg', 'p2_score_total':'score'})
            all_perf = pd.concat([p1, p2])
            
            # Group by Allegiance and Player to find the best in each category
            commander_stats = all_perf.groupby(['allg', 'player']).agg(Total_VP=('score', 'sum'), Games=('score', 'count')).reset_index()
            
            # Create columns for the top 3 (or however many allegiances you have)
            allg_list = sorted(all_perf['allg'].unique())
            cols = st.columns(len(allg_list))
            
            for i, allg in enumerate(allg_list):
                # Find the player with highest VP in this allegiance
                top_in_allg = commander_stats[commander_stats['allg'] == allg].sort_values('Total_VP', ascending=False).iloc[0]
                cols[i].metric(f"🚩 {allg}", top_in_allg['player'], f"{top_in_allg['Total_VP']} VP")
        
            st.divider()
        
            # # --- NARRATIVE AWARDS ---
            # st.write("### 🕵️ Intelligence Reports")
            # n1, n2, n3 = st.columns(3)
        
            # # 1. Tzeentch’s Plaything: High VP, Low Wins
            # plaything = leaderboard[leaderboard['Wins'] < 2].sort_values('Total_Points', ascending=False)
            # if not plaything.empty:
            #     n1.info(f"**Tzeentch’s Plaything**\n\n**{plaything.iloc[0]['player']}** ({plaything.iloc[0]['Total_Points']} VP)")
        
            # # 2. The Eternal Martyr: Most losses, High average
            # martyr = leaderboard.sort_values(['Wins', 'Avg_Score'], ascending=[True, False])
            # n2.info(f"**The Eternal Martyr**\n\n**{martyr.iloc[0]['player']}** ({martyr.iloc[0]['Avg_Score']} Avg)")
        
            # # 3. The Broken Spearhead: Most "Went First" with lowest win rate
            # # We calculate 'Went First' counts from the raw match data
            # wf_counts = df['went_first'].value_counts().reset_index()
            # wf_counts.columns = ['player', 'Starts']
            # # Join to leaderboard to check win rates
            # spearhead_data = pd.merge(wf_counts, leaderboard, on='player')
            # spearhead_data['Win_Rate'] = spearhead_data['Wins'] / spearhead_data['Played']
            # # Filter for people who went first at least twice, then sort by win rate ascending
            # spearhead = spearhead_data[spearhead_data['Starts'] >= 2].sort_values('Win_Rate', ascending=True)
            # if not spearhead.empty:
            #     n3.info(f"**The Broken Spearhead**\n\n**{spearhead.iloc[0]['player']}** (Went first {spearhead.iloc[0]['Starts']} times)")

            # --- NARRATIVE AWARDS ---
            st.write("### 🕵️ Intelligence Reports")
            n1, n2, n3 = st.columns(3)
        
            # # 1. Tzeentch’s Plaything: High VP, Low Wins
            # plaything = leaderboard[leaderboard['Wins'] < 2].sort_values('Total_Points', ascending=False)
            # if not plaything.empty:
            #     n1.info(f"**Tzeentch’s Plaything**\n\n**{plaything.iloc[0]['player']}** ({plaything.iloc[0]['Total_Points']} VP)")
        
            # # 2. The Eternal Martyr: Most losses, High average
            # martyr = leaderboard.sort_values(['Wins', 'Avg_Score'], ascending=[True, False])
            # n2.info(f"**The Eternal Martyr**\n\n**{martyr.iloc[0]['player']}** ({martyr.iloc[0]['Avg_Score']} Avg)")
        
            # # 3. The Broken Spearhead: Most "Went First" with lowest win rate
            # # We calculate 'Went First' counts from the raw match data
            # wf_counts = df['went_first'].value_counts().reset_index()
            # wf_counts.columns = ['player', 'Starts']
            # # Join to leaderboard to check win rates
            # spearhead_data = pd.merge(wf_counts, leaderboard, on='player')
            # spearhead_data['Win_Rate'] = spearhead_data['Wins'] / spearhead_data['Played']
            # # Filter for people who went first at least twice, then sort by win rate ascending
            # spearhead = spearhead_data[spearhead_data['Starts'] >= 2].sort_values('Win_Rate', ascending=True)
            # if not spearhead.empty:
            #     n3.info(f"**The Broken Spearhead**\n\n**{spearhead.iloc[0]['player']}** (Went first {spearhead.iloc[0]['Starts']} times)")
        
            # 1. Tzeentch’s Plaything
            plaything = leaderboard[leaderboard['Wins'] < 2].sort_values('Total_Points', ascending=False)
            if not plaything.empty:
                p_row = plaything.iloc[0]
                n1.info(
                    f"**Tzeentch’s Plaything**\n\n"
                    f"**{p_row['player']}** accumulated a massive **{p_row['Total_Points']}** total points, "
                    f"despite only securing **{p_row['Wins']}** wins. The Changer of Ways is pleased with this complexity."
                )
        
            # 2. The Eternal Martyr
            martyr = leaderboard.sort_values(['Wins', 'Avg_Score'], ascending=[True, False])
            if not martyr.empty:
                m_row = martyr.iloc[0]
                n2.info(
                    f"**The Eternal Martyr**\n\n"
                    f"**{m_row['player']}** fought bravely to the bitter end. Despite the losses, "
                    f"they maintained a high average of **{m_row['Avg_Score']} pts** per game. Their sacrifice is noted."
                )
        
            # 3. The Broken Spearhead
            # We calculate 'Went First' counts from the raw match data
            wf_counts = df['went_first'].value_counts().reset_index()
            wf_counts.columns = ['player', 'Starts']
            spearhead_data = pd.merge(wf_counts, leaderboard, on='player')
            spearhead_data['Win_Rate'] = spearhead_data['Wins'] / spearhead_data['Played']
            # Filter for people who went first at least twice, then sort by win rate ascending
            spearhead = spearhead_data[spearhead_data['Starts'] >= 2].sort_values('Win_Rate', ascending=True)
            if not spearhead.empty:
                s_row = spearhead.iloc[0]
                n3.warning(
                    f"**The Broken Spearhead**\n\n"
                    f"**{s_row['player']}** seized the initiative in **{s_row['Starts']}** separate matches, "
                    f"yet found no victory in the charge. The best-laid plans often crumble upon contact."
                )

        
        # def show_faction_win_rates(df):
        #     st.subheader(f"📊 {selected_event} Faction Meta")
        #     p1_data = df[['p1_faction', 'p1_score_total', 'p2_score_total']].copy()
        #     p1_data.columns = ['faction', 'score', 'opp_score']
        #     p2_data = df[['p2_faction', 'p2_score_total', 'p1_score_total']].copy()
        #     p2_data.columns = ['faction', 'score', 'opp_score']
        #     combined = pd.concat([p1_data, p2_data])
        #     combined['is_win'] = combined['score'] > combined['opp_score']
        #     stats = combined.groupby('faction').agg(Total=('faction', 'count'), Wins=('is_win', 'sum')).reset_index()
        #     stats['Win_Rate'] = (stats['Wins'] / stats['Total'] * 100).round(1)
        #     stats = stats.sort_values(by='Win_Rate', ascending=False)
        #     fig = px.bar(stats, x='faction', y='Win_Rate', text='Win_Rate', color='Win_Rate', color_continuous_scale='RdYlGn', height=400)
        #     fig.update_layout(yaxis_range=[0, 110])
        #     st.plotly_chart(fig, use_container_width=True)

        def show_faction_turnout(df):
            st.subheader(f"🍕 {selected_event} Faction Turnout")
            combined = pd.concat([df[['p1_faction']].rename(columns={'p1_faction':'f'}), df[['p2_faction']].rename(columns={'p2_faction':'f'})])
            stats = combined['f'].value_counts().reset_index()
            stats.columns = ['Faction', 'Count']
            fig = px.pie(stats, values='Count', names='Faction', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)

                # --- REPORT 5: ROUND-BY-ROUND PERFORMANCE (GROUPED BAR CHART) ---
        def show_round_averages_chart(df):
            st.subheader(f"📊 {selected_event} Round Performance")
            
            # 1. Identify winner and loser score for every row
            # (Note: Using awards_event_df ensures 'Not Played' results don't skew the averages)
            df['Winner_Score'] = df[['p1_score_total', 'p2_score_total']].max(axis=1)
            df['Loser_Score'] = df[['p1_score_total', 'p2_score_total']].min(axis=1)
            
            # 2. Group by round and calculate averages
            round_stats = df.groupby('round_number').agg({
                'Winner_Score': 'mean',
                'Loser_Score': 'mean'
            }).reset_index()
            
            # 3. 'Melt' the data for Plotly (changes columns into rows)
            melted_df = round_stats.melt(
                id_vars='round_number', 
                value_vars=['Winner_Score', 'Loser_Score'],
                var_name='Result Type', 
                value_name='Average Score'
            )
            
            # 4. Create the Grouped Bar Chart
            fig = px.bar(
                melted_df,
                x='round_number',
                y='Average Score',
                color='Result Type',
                barmode='group', # Puts bars side-by-side
                text_auto='.1f', # Shows 1 decimal place on the bars
                labels={'round_number': 'Round Number', 'Average Score': 'Avg Score'},
                title=f"Avg Winning vs. Losing Score by Round",
                color_discrete_map={
                    'Winner_Score': '#00cc66', # Green for winner
                    'Loser_Score': '#ff4d4d'    # Red for loser
                }
            )
            
            # Ensure all 5 rounds show on the X-axis
            fig.update_layout(xaxis=dict(tickmode='linear', tick0=1, dtick=1))
            
            st.plotly_chart(fig, use_container_width=True)

        def show_allegiance_points_pie(df):
            st.subheader(f"🍰 {selected_event} Points per Allegiance")
            p1 = df[['p1_allegiance', 'p1_score_total']].rename(columns={'p1_allegiance':'a', 'p1_score_total':'s'})
            p2 = df[['p2_allegiance', 'p2_score_total']].rename(columns={'p2_allegiance':'a', 'p2_score_total':'s'})
            combined = pd.concat([p1, p2])
            agg = combined.groupby('a')['s'].sum().reset_index().sort_values('s', ascending=False)
            agg['label'] = agg['a'] + " (" + agg['s'].astype(str) + " pts)"
            fig = px.pie(agg, values='s', names='label', hole=0.5, title=f"Total Event Points: {agg['s'].sum():,}")
            fig.update_traces(textinfo='percent+label')
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        # --- STEP 2: FETCH & FILTER DATA ---
        # Get unique events for the dropdown
        event_res = supabase.table("match_results").select("event_name").execute()
        if event_res.data:
            event_options = sorted(list(set([row['event_name'] for row in event_res.data if row['event_name']])))
            selected_event = st.selectbox("Select Event to View Reports", event_options)
    
            # Fetch filtered data
            res = supabase.table("match_results").select("*").eq("event_name", selected_event).execute()
            if res.data:
                raw_df = pd.DataFrame(res.data)
                
                # Apply Global Pre-Filters
                event_df = raw_df[
                    (raw_df['status'] != 'Not Logged') & 
                    (raw_df['p1_status'] == 'Checked In') & 
                    (raw_df['p2_status'] == 'Checked In')
                ].copy()

                        # Apply Global Pre-Filters
                awards_df = raw_df[
                    (raw_df['status'] == 'Logged') & 
                    (raw_df['p1_status'] == 'Checked In') & 
                    (raw_df['p2_status'] == 'Checked In')
                ].copy()

                if not event_df.empty:
                    # --- STEP 3: RUN REPORTS IN ORDER ---
                    ranking_data = show_leaderboard(event_df)
                    st.divider()
                    show_event_awards(awards_df, ranking_data)
                    st.divider()
                    show_round_averages_chart(awards_df)
                    st.divider()
                    # show_faction_win_rates(event_df)
                    # st.divider()
                    show_faction_turnout(event_df)
                    st.divider()
                    show_allegiance_points_pie(event_df)
        
                else:
                    st.warning("No valid match data found after filtering out Dropped/Unplayed results.")
        else:
            st.info("No events found in the database.")
        
        # show_leaderboard(raw_df)
        # show_leaderboard(event_df)
        # show_leaderboard(awards_df)
    

    elif st.session_state.page == "Graphs":
        st.header("Graphs")
        st.divider()
        
        # 2. Fetch matches where the user is P1 OR P2
        # We use the .or_() filter on the view's column names
        res = supabase.table("v_system_faction_data") \
            .select("*") \
            .execute()
            # .order("game_date", desc=True) \
            # .limit(10) \
            
        if res.data:
            recent_df = pd.DataFrame(res.data)
            st.subheader("Faction Win Rates")
            st.dataframe(
                recent_df,
                use_container_width=True,
                hide_index=True
            )


    elif st.session_state.page == "Personal Stats":
        st.header("Personal Stats")
        st.divider()
        # 1. Get the current user's name for filtering
        # (Assuming discord_name is established from st.session_state.user at the top)
        current_user = discord_name

        # 2. Fetch matches where the user is P1 OR P2
        # We use the .or_() filter on the view's column names
        res = supabase.table("match_results") \
            .select("*") \
            .or_(f"display_p1_name.eq.{current_user},display_p2_name.eq.{current_user}") \
            .order("game_date", desc=True) \
            .limit(10) \
            .execute()

        if res.data:
            recent_df = pd.DataFrame(res.data)
            st.subheader("Your Latest 10 Battle Reports")
            st.dataframe(
                recent_df,
                column_order=(
                    "game_date",
                    "system_name",
                    "display_p1_name",
                    "p1_faction",
                    "p1_score_total",
                    "display_p2_name",
                    "p2_faction",
                    "p2_score_total"
                ),
                column_config={
                    "game_date": "Date",
                    "system_name": "System",
                    "display_p1_name": "Player 1",
                    "p1_faction": "P1 Faction",
                    "p1_score_total": "P1 Score",
                    "display_p2_name": "Player 2",
                    "p2_faction": "P2 Faction",
                    "p2_score_total": "P2 Score"
                },
                use_container_width=True,
                hide_index=True
            )

        else:
            st.info("You haven't logged any games yet. Get to the table!")

