import streamlit as st
# import supabase
from supabase import create_client, Client
from streamlit_js_eval import streamlit_js_eval
from dotenv import load_dotenv
from pandas import DataFrame
import plotly.express as px
import time
import os

import streamlit as st
from supabase import create_client
from dotenv import load_dotenv
import os

from supabase import create_client, ClientOptions

@st.cache_resource
def get_supabase_client():
    load_dotenv()
    url = os.getenv("SUPABASE_URL_2")
    key = os.getenv("SUPABASE_KEY_2")
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

# 3. PERSISTENT USER SYNC
if "user" not in st.session_state:
    user_resp = supabase.auth.get_user()
    if user_resp and user_resp.user:
        st.session_state.user = user_resp.user


# 4. LOGIN FUNCTION
def show_login_screen():
    st.title("BGC Club App Sign In")
    st.info("Please sign in with your Discord to use this app.")

    redirect_uri = "http://localhost:8501/"

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
    if st.sidebar.button("Home"):
        st.session_state.page = None
        st.rerun()
    if st.sidebar.button("Log Games"):
        st.session_state.page = "Log Games"
        st.rerun()
    if st.sidebar.button("Events"):
        st.session_state.page = "Events"
        st.rerun()
    if st.sidebar.button("Personal Stats"):
        st.session_state.page = "Personal Stats"
        st.rerun()
    if st.sidebar.button("Log Out"):
        supabase.auth.sign_out()
        del st.session_state.user
        st.rerun()

    if st.session_state.page is None:
        st.header("BGC Club App")
        st.write(f"Welcome back, {st.session_state.user.user_metadata.get('full_name')}!")
        # st.text(f"Here we will be hosting all of our club game data for you to use and analyse however you'd like!\n\n"
        #         f"If you have any issues or want to submit a request for something new (new game system added, graph, etc.) then please contact scottpaisey in our Discord.")
        st.divider()

    elif st.session_state.page == "Log Games":
        st.header("Log Games")
        st.divider()
        st.subheader("Step 1: Please Choose the Systme you are logging")
        if st.button("Warhammer 40,000"):
            st.session_state.page = "40k"
            st.rerun()
        if st.button("Age of Sigmar", disabled=True):
            st.session_state.page = "AoS"
            st.rerun()
        if st.button("Kill Team", disabled=True):
            st.session_state.page = "KillTeam"
            st.rerun()
        if st.button("Middle Earth: SBG", disabled=True):
            st.session_state.page = "MESBG"
            st.rerun()
        if st.button("Warhammer: Old World", disabled=True):
            st.session_state.page = "OldWorld"
            st.rerun()

    elif st.session_state.page == "40k":
        st.header("Warhammer 40,000 Game")
        st.divider()

        # Your 40k form goes here
        try:
            p1_response_system_factions = supabase.table("system_factions").select("*").execute()
            p1_df_system_factions = DataFrame(p1_response_system_factions.data)
            p2_response_system_factions = supabase.table("system_factions").select("*").execute()
            p2_df_system_factions = DataFrame(p2_response_system_factions.data)
        except Exception as e:
            print(e)

        st.subheader("Game Details")

        col1, col2 = st.columns(2)

        game_size = st.selectbox('Game Size', ['Strike Force', 'Incursion', 'Combat Partol'], index=None,
                                 placeholder="Choose...", key="game_s")
        # mission_pack = st.selectbox(st.selectbox('Mission Pack',['Strike Force (2k)', 'Incursion (1k)', 'Combat Partol'], index=None, placeholder="Choose...")


        with col1:
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

        with col2:
            st.write("**Opponent Details**")

            # 1. Fetch all profiles from Supabase to check names against
            # You should wrap this in st.cache_data if your club gets very large
            profiles_resp = supabase.table("profiles").select("id, full_name").execute()
            db_profiles = profiles_resp.data  # List of dicts: {'id': '...', 'full_name': '...'}
            # 2. Text Input for Opponent
            p2_input = st.text_input("Opponent Name*", key="p2_username",
                                     help="Type their Discord User Name to link their profile")
            # 3. Validation Step
            p2_name = None
            p2_id = None
            p2_custom_name = None
            system_id = None

            if p2_input:
                # Check if the typed name matches any full_name in our DB
                matched_user = next((p for p in db_profiles if p['username'].lower() == p2_input.lower()), None)

                if matched_user:
                    p2_id = matched_user['id']
                    st.success(f"✅ User found! This game will be linked to **{matched_user['full_name']}**.")
                else:
                    p2_custom_name = p2_input
                    st.warning("⚠️ User not found. This will be recorded as a 'Guest' game.")
                p2_name = p2_input

            # --- Opponent Faction Logic (Same as P1) ---
            # Copy your p1_all, p1_fac logic here for the opponent
            # p2_first = st.text_input("First Name*", key="p2_f")
            # p2_last = st.text_input("Surname", key="p2_l")
            # p2_known = st.text_input("Known As", key="p2_k")

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
            if attacking_player == "You":
                attacker_id == p1_name
                defender_id == p2_name
            else:
                attacker_id == p2_name
                defender_id == p1_name

            if went_first == "You":
                went_first_id == p1_name
            else:
                went_first_id == p2_name

            # one_goes_first = (p1_wf != p2_wf)  # Logical XOR: one must be True, one False
            # 2. Check the conditions
            if not names_entered:
                st.error("❌ Both player names are mandatory.")
            elif not factions_selected:
                st.error("❌ Both players must select a Faction.")
            # elif not one_goes_first:
            #     st.error("❌ Exactly one player must be marked as 'Went First'.")
            else:
                # --- LOOKUP IDs FOR PLAYER 1 ---
                # We find the row in df_2 where the name matches what was chosen in the selectbox
                p1_row = p1_df_system_factions[p1_df_system_factions['subfaction'] == p1_sub].iloc[0]
                # p1_all_id = int(p1_row['allegiance_id'])
                p1_fac_id = p1_row['faction_id']
                # p1_sub_id = int(p1_row['sub_faction_id'])

                # --- LOOKUP IDs FOR PLAYER 2 ---
                p2_row = p2_df_system_factions[p2_df_system_factions['subfaction'] == p2_sub].iloc[0]
                # p2_all_id = int(p2_row['allegiance_id'])
                p2_fac_id = p2_row['faction_id']
                # p2_sub_id = int(p2_row['sub_faction_id'])

                system_id = p1_row['system_id']

                # 3. If all clear, SAVE to session_state and MOVE ON
                st.session_state.game_data = {
                    "system_id": system_id,     # matches.game_system_id
                    "game_size": game_size,     # matches.game_size
                    "p1_first": p1_name,
                    # "p1_last": p1_last,
                    # "p1_known": p1_known,
                    "p1_fac_id": p1_fac_id,     # matches.p1_faction_id
                    "p1_all": p1_all,
                    "p1_fac": p1_fac,
                    "p1_sub": p1_sub,
                    "p2_first": p2_name,
                    # "p2_last": p2_last,
                    # "p2_known": p2_known,
                    "p2_fac_id": p2_fac_id,     # matches.p2_faction_id
                    "p2_all": p2_all,
                    "p2_fac": p2_fac,
                    "p2_sub": p2_sub,
                    "attacker_id": attacker_id,
                    "defender_id": defender_id,
                    "went_first_id": went_first_id
                }
                st.session_state.page = "40k_scores"
                st.rerun()

    elif st.session_state.page == "40k_scores":

        st.subheader("Game Scores")
        st.divider()

        game_size = st.session_state.game_data.get("game_size", None)

        attacker_id = st.session_state.game_data.get("attacker_id", None)
        defender_id = st.session_state.game_data.get("defender_id", None)
        went_first_id = st.session_state.game_data.get("went_first_id", None)

        p1_name = st.session_state.game_data.get("p1_first", None)
        p1_fac_id = st.session_state.game_data.get("p1_fac_id", None)
        p1_all = st.session_state.game_data.get("p1_all", None)
        p1_fac = st.session_state.game_data.get("p1_fac", None)
        p1_sub = st.session_state.game_data.get("p1_sub", None)
        # p1_wf     = st.session_state.game_data.get("p1_wf", None)

        p2_name = st.session_state.game_data.get("p2_first", None)
        p2_fac_id = st.session_state.game_data.get("p2_fac_id", None)
        p2_all = st.session_state.game_data.get("p2_all", None)
        p2_fac = st.session_state.game_data.get("p2_fac", None)
        p2_sub = st.session_state.game_data.get("p2_sub", None)
        # p2_wf     = st.session_state.game_data.get("p2_wf", None)

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
            # Calculate Totals
            p1_total = scores['p1_pri'] + scores['p1_sec'] + scores['p1_br']
            p2_total = scores['p2_pri'] + scores['p2_sec'] + scores['p2_br']

            # Determine Results
            if p1_total > p2_total:
                winner_id, loser_id = p1_name, p2_name
                is_draw = False
            elif p2_total > p1_total:
                winner_id, loser_id = p2_name, p1_name
                is_draw = False
            else:
                winner_id, loser_id = None, None
                is_draw = True

            col_a, col_b = st.columns(2)
            col_a.write(f"Name: **{setup['p1_first']}**"
                        f"\n\nFaction: {setup['p1_fac']}"
                        f"\n\nDetatchment: {setup['p1_sub']}"
                        f"\n\nPrimary: {scores['p1_pri']}"
                        f"\n\nSecondary: {scores['p1_sec']}"
                        f"\n\nBattle Ready: {scores['p1_br']}")
            col_b.write(f"Name: **{setup['p2_first']}**"
                        f"\n\nFaction: {setup['p2_fac']}"
                        f"\n\nDetatchment: {setup['p2_sub']}"
                        f"\n\nPrimary: {scores['p2_pri']}"
                        f"\n\nSecondary: {scores['p2_sec']}"
                        f"\n\nBattle Ready: {scores['p2_br']}")

            c1, c2 = st.columns(2)
            if c1.button("✅ Yes, Post Results", type="primary", use_container_width=True):
                # --- DATABASE INSERT LOGIC HERE ---

                game_payload = {
                    "system_id": 1,  # Stored from your 40k page lookup
                    "game_size": setup['game_size'],  # Or a variable if you have one
                    "status": "completed"
                }

                # inserting game data into table

                game_resp = supabase.table("bgc_games").insert(game_payload).execute()
                # Grab the auto-generated ID to link the players
                new_game_id = game_resp.data[0]['id']

                # inserting game data into table
                player_entries = [
                    {
                        "game_system_id": setup['system_id'],
                        "game_id": new_game_id,
                        "player_1_id": p1_name,
                        "faction_id": p1_fac_id,
                        "primary_score": scores['p1_pri'],
                        "secondary_score": scores['p1_sec'],
                        "bonus_score": 10 if scores['p1_br'] else 0,
                        "went_first": scores['p1_wf'],
                        "result": p1_res,
                        "is_winner": p1_win,
                        "score_diff": p1_total - p2_total

                        # matches.game_system_id
                        # matches.event_id
                        # matches.round_id
                        # matches.mission_id
                        # matches.game_size
                        # matches.player_1_id
                        # matches.player_2_id
                        # matches.p1_faction_id
                        # matches.p2_faction_id
                        # matches.p1_score_01
                        # matches.p1_score_02
                        # matches.p1_score_03
                        # matches.p1_score_04
                        # matches.p1_score_05
                        # matches.p2_score_01
                        # matches.p2_score_02
                        # matches.p2_score_03
                        # matches.p2_score_04
                        # matches.p2_score_05
                        # matches.p1_score_mar
                        # matches.p2_score_mar
                        # matches.went_first_id
                        # matches.winner_id
                        # matches.attacker_id
                        # matches.is_draw
                        # matches.played_at
                        # matches.recorded_by
                        # matches.club_id


                    }
                ]

                supabase.table("matches").insert(player_entries).execute()

                st.success("Game posted to Supabase!")

                st.session_state.game_data = {}
                st.session_state.temp_scores = {}
                st.session_state.confirm_submit = False
                # st.session_state.page = None  # Go back to home
                # st.rerun()
                st.session_state.selected_system = "40K"
                st.session_state.page = "bgc_games"
                st.rerun()

            if c2.button("❌ No, Edit Scores", use_container_width=True):
                st.session_state.confirm_submit = False
                st.rerun()



    # matches.id
    # matches.game_system_id
    # matches.event_id
    # matches.round_id
    # matches.mission_id
    # matches.game_size
    # matches.player_1_id
    # matches.player_2_id
    # matches.p1_faction_id
    # matches.p2_faction_id
    # matches.p1_score_01
    # matches.p1_score_02
    # matches.p1_score_03
    # matches.p1_score_04
    # matches.p1_score_05
    # matches.p2_score_01
    # matches.p2_score_02
    # matches.p2_score_03
    # matches.p2_score_04
    # matches.p2_score_05
    # matches.p1_score_mar
    # matches.p2_score_mar
    # matches.went_first_id
    # matches.winner_id
    # matches.attacker_id
    # matches.is_draw
    # matches.played_at
    # matches.recorded_by
    # matches.club_id


    elif st.session_state.page == "Events":
        st.header("Events")
        st.divider()
        # Your 40k form goes here



