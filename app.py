import streamlit as st
# import supabase
from supabase import create_client, Client
from dotenv import load_dotenv
from pandas import DataFrame
import plotly.express as px
import time
import os

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

@st.cache_resource
def get_supabase_client():
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return create_client(url, key)

supabase = get_supabase_client()

# supabase: Client = create_client(url, key)

# Creating session states
if "page" not in st.session_state:
    st.session_state.page = None
if "temp_scores" not in st.session_state:
    st.session_state.temp_scores = False
if "confirm_submit" not in st.session_state:
    st.session_state.confirm_submit = False
if "game_data" not in st.session_state:
    st.session_state.game_data = {}
if "p1_wf_key" not in st.session_state:
    st.session_state.p1_wf_key = False
if "p2_wf_key" not in st.session_state:
    st.session_state.p2_wf_key = False

# Creating functions
def back_home():
    if st.button("Back Home"):
        st.session_state.page = None
        st.rerun()

def handle_wf_toggle(player):
    if player == "p1" and st.session_state.p1_wf_key:
        st.session_state.p2_wf_key = False
    elif player == "p2" and st.session_state.p2_wf_key:
        st.session_state.p1_wf_key = False

if st.session_state.page is None:
    st.header("BGC App")
    st.text(f"Here we will be hosting all of our club game data for you to use and analyse however you'd like!\n\n"
            f"If you have any issues or want to submit a request for something new (new game system added, graph, etc.) then please contact scottpaisey in our Discord.")
    # home_tab1, home_tab2, home_tab3, = st.tabs(["Enter Game Results", "Graphs & Data", "Admin"])
    home_tab1, home_tab2, = st.tabs(["Enter Game Results", "Graphs & Data"])
    with home_tab1:
        st.subheader("Logging Games")
        st.text("Please select a system you'd like to log your game in:")

        if st.button("Warhammer 40,000"):
            st.session_state.page = "40k"
            st.rerun()
        if st.button("Age of Sigmar"):
            st.session_state.page = "AoS"
            st.rerun()
        # st.text("Coming Soon...")
        # if st.button("Age of Sigmar", disabled=True):
        #     st.session_state.page = "AOS"
        #     st.rerun()
        # if st.button("Middle Earth: Strategy Battle Game", disabled=True):
        #     st.session_state.page = "MESBG"
        #     st.rerun()
    with home_tab2:
        st.subheader("Dashboards")
        st.text("Please select the type of data you want to view")
        if st.button("BGC Games"):
            st.session_state.page = "bgc_games"
            st.rerun()
        if st.button("League Data"):
            st.session_state.page = "league_data"
            st.rerun()
        # st.text("Coming Soon...")
        # if st.button("Event Data"):
        #     st.session_state.page = "event_data"
        #     st.rerun()

        # if st.session_state['games'] == 1:
        # st.write(st.session_state)
        # Creating connection\
    # with home_tab3:
    #     import streamlit as st
    #     import pandas as pd
    #     from pandas import DataFrame
    #
    #
    #     # --- 1. SETUP & MAPPING ---
    #     def admin_score_editor_ui():
    #         st.subheader("🛠️ Admin: Edit League Scores")
    #         st.caption("Changes made here update the source database. Opponents are grouped by Round & Table.")
    #
    #         # A. Fetch Reference Data for Mapping (Names & Statuses)
    #         # Get Players: {42: "Scott"}
    #         player_data = supabase.table("league_players_v1").select("id, first_name").execute()
    #         player_df = DataFrame(player_data.data)
    #         player_map = dict(zip(player_df['id'], player_df['first_name']))
    #         inv_player_map = {v: k for k, v in player_map.items()}
    #
    #         # Get Statuses: {1: "Confirmed"}
    #         status_data = supabase.table("league_status_descr_v1").select("status_no, status").execute()
    #         status_df = DataFrame(status_data.data)
    #         status_map = dict(zip(status_df['status_no'], status_df['status']))
    #         inv_status_map = {v: k for k, v in status_map.items()}
    #
    #         # --- 2. FETCH & PREPARE DATA ---
    #         # B. Fetch from the VIEW (v_admin_score_editor)
    #         # This view already handles the sorting by League, Round, and Table
    #         response = supabase.table("v_admin_score_editor").select("*").execute()
    #
    #         if not response.data:
    #             st.info("No game records found to edit.")
    #             return
    #
    #         display_df = DataFrame(response.data)
    #
    #         # C. Map IDs to Strings for the UI
    #         # We use .map() so the admin sees "Scott" instead of "42"
    #         display_df['player_id'] = display_df['player_id'].map(player_map)
    #         display_df['status_id'] = display_df['status_id'].map(status_map)
    #
    #         # --- 3. THE DATA EDITOR ---
    #         # D. Display the editable grid
    #         edited_df = st.data_editor(
    #             display_df,
    #             hide_index=True,
    #             column_config={
    #                 "entry_id": None,  # Hide the internal ID from the user
    #                 "league_games_id": None,  # Hide the game link ID
    #                 "league_name": "League",  # Readable header
    #                 "round_no": "Rd",
    #                 "table_no": "Tbl",
    #                 "player_id": st.column_config.SelectboxColumn(
    #                     "Player Name",
    #                     options=list(player_map.values()),
    #                     required=True
    #                 ),
    #                 "status_id": st.column_config.SelectboxColumn(
    #                     "Status",
    #                     options=list(status_map.values()),
    #                     required=True
    #                 ),
    #                 "score_total": st.column_config.NumberColumn("Total Score", min_value=0),
    #                 "result": st.column_config.SelectboxColumn("Result", options=["Win", "Loss", "Draw"]),
    #                 "went_first": st.column_config.CheckboxColumn("Started?")
    #             },
    #             use_container_width=True
    #         )
    #
    #         # --- 4. SAVE CHANGES ---
    #         if st.button("💾 Save All Changes", type="primary"):
    #             # E. Prepare the data for the SOURCE table
    #             save_df = edited_df.copy()
    #
    #             # F. UNMAP: Convert names/status back to bigint IDs
    #             save_df['player_id'] = save_df['player_id'].map(inv_player_map)
    #             save_df['status_id'] = save_df['status_id'].map(inv_status_map)
    #
    #             # G. RENAME: 'entry_id' must go back to being called 'id' for the upsert
    #             save_df = save_df.rename(columns={'entry_id': 'id'})
    #
    #             # H. FILTER: Only keep columns that exist in 'league_game_players_v1'
    #             # We discard 'league_name', 'round_no', etc. because they don't live in this table
    #             db_cols = ['id', 'league_games_id', 'player_id', 'status_id', 'score_total', 'went_first', 'result']
    #
    #             # Ensure we only send rows that have all required columns
    #             payload = save_df[db_cols].to_dict(orient='records')
    #
    #             try:
    #                 # I. UPSERT to the SOURCE table
    #                 supabase.table("league_game_players_v1").upsert(payload).execute()
    #                 st.success("✅ Records successfully updated!")
    #                 st.rerun()  # Refresh to show updated data
    #             except Exception as e:
    #                 st.error(f"❌ Database Error: {e}")
    #
    #     # Run the UI function
    #     admin_score_editor_ui()

elif st.session_state.page == "40k":

    back_home()

    try:
        response = supabase.table("test_report").select("*").execute()
        df = DataFrame(response.data)
        response_2 = supabase.table("v_faction_choices").select("*").execute()
        df_2 = DataFrame(response_2.data)
    except Exception as e:
        print(e)

    st.divider()
    st.subheader("Game Details")

    col1, col2 = st.columns(2)

    game_size = st.selectbox('Game Size',['Strike Force (2k)', 'Incursion (1k)', 'Combat Partol'], index=None, placeholder="Choose...", key="game_s")
    # mission_pack = st.selectbox(st.selectbox('Mission Pack',['Strike Force (2k)', 'Incursion (1k)', 'Combat Partol'], index=None, placeholder="Choose...")

    with col1:
        st.write("**Your Details**")
        p1_first = st.text_input("First Name*", key="p1_f")
        p1_last = st.text_input("Surname", key="p1_l")
        p1_known = st.text_input("Known As", key="p1_k")
        # 1. Allegiance Dropdown
        p1_all_df = df_2[df_2['system_name'] == 'Warhammer 40,000']
        p1_all    = st.selectbox("Your Allegiance", p1_all_df['allegiance_name'].unique(), index=None, placeholder="Choose...", key="p1_all_sel")
        # 2. Faction Dropdown (MUST use filtered options)
        if p1_all:
            # We filter the dataframe here
            p1_fac_df = p1_all_df[p1_all_df['allegiance_name'] == p1_all]
            # We use faction_df to get the unique names for the options
            p1_fac = st.selectbox("Your Faction", p1_fac_df['faction_name'].unique(), index=None, placeholder="Choose...", key="p1_fac_sel")
        else:
            p1_fac = st.selectbox("Your Faction", [], disabled=True)
        # 3. Sub-Faction Dropdown (MUST use filtered options)
        if p1_fac:
            p1_sub_df = df_2[df_2['faction_name'] == p1_fac]
            p1_sub = st.selectbox("Your Sub-Faction", p1_sub_df['sub_faction_name'].unique(), index=None, placeholder="Choose...", key="p1_sub_sel")
        else:
            p1_sub = st.selectbox("Your Sub-Faction", [], disabled=True)
        p1_wf = st.toggle("Went First?*", key="p1_wf_key", on_change=handle_wf_toggle, args=("p1",))

    with col2:
        st.write("**Opponent Details**")
        p2_first = st.text_input("First Name*", key="p2_f")
        p2_last = st.text_input("Surname", key="p2_l")
        p2_known = st.text_input("Known As", key="p2_k")

        # 1. Allegiance Dropdown
        p2_all_df = df_2[df_2['system_name'] == 'Warhammer 40,000']
        p2_all    = st.selectbox("Opponents Allegiance", p2_all_df['allegiance_name'].unique(), index=None, placeholder="Choose...", key="p2_all_sel")
        # 2. Faction Dropdown (MUST use filtered options)
        if p2_all:
            # We filter the dataframe here
            p2_fac_df = p2_all_df[p2_all_df['allegiance_name'] == p2_all]
            # We use faction_df to get the unique names for the options
            p2_fac = st.selectbox("Opponents Faction", p2_fac_df['faction_name'].unique(), index=None, placeholder="Choose...", key="p2_fac_sel")
        else:
            p2_fac = st.selectbox("Opponents Faction", [], disabled=True)
        # 3. Sub-Faction Dropdown (MUST use filtered options)
        if p2_fac:
            p2_sub_df = df_2[df_2['faction_name'] == p2_fac]
            p2_sub = st.selectbox("Opponents Sub-Faction", p2_sub_df['sub_faction_name'].unique(), index=None, placeholder="Choose...", key="p2_sub_sel")
        else:
            p2_sub = st.selectbox("Opponents Sub-Faction", [], disabled=True)
        p2_wf = st.toggle("Went First?*", key="p2_wf_key", on_change=handle_wf_toggle, args=("p2",))

    if st.button("Proceed to Scoring"):
        # 1. Define your conditions
        names_entered = p1_first and p2_first
        allegiance_selected = p1_all and p2_all
        factions_selected = p1_fac and p2_fac
        sub_factions_selected = p1_sub and p2_sub
        one_goes_first = (p1_wf != p2_wf)  # Logical XOR: one must be True, one False
        # 2. Check the conditions
        if not names_entered:
            st.error("❌ Both player names are mandatory.")
        elif not factions_selected:
            st.error("❌ Both players must select a Faction.")
        elif not one_goes_first:
            st.error("❌ Exactly one player must be marked as 'Went First'.")
        else:
            # --- LOOKUP IDs FOR PLAYER 1 ---
            # We find the row in df_2 where the name matches what was chosen in the selectbox
            p1_row = df_2[df_2['sub_faction_name'] == p1_sub].iloc[0]
            p1_all_id = int(p1_row['allegiance_id'])
            p1_fac_id = int(p1_row['faction_id'])
            p1_sub_id = int(p1_row['sub_faction_id'])

            # --- LOOKUP IDs FOR PLAYER 2 ---
            p2_row = df_2[df_2['sub_faction_name'] == p2_sub].iloc[0]
            p2_all_id = int(p2_row['allegiance_id'])
            p2_fac_id = int(p2_row['faction_id'])
            p2_sub_id = int(p2_row['sub_faction_id'])

            # 3. If all clear, SAVE to session_state and MOVE ON
            st.session_state.game_data = {
                "system_id": 1,
                "game_size": game_size,
                "p1_first": p1_first,
                "p1_last": p1_last,
                "p1_known": p1_known,
                "p1_all_id": p1_all_id,
                "p1_all": p1_all,
                "p1_fac_id": p1_fac_id,
                "p1_fac": p1_fac,
                "p1_sub_id": p1_sub_id,
                "p1_sub": p1_sub,
                "p1_wf": p1_wf,
                "p2_first": p2_first,
                "p2_last": p2_last,
                "p2_known": p2_known,
                "p2_all_id": p2_all_id,
                "p2_all": p2_all,
                "p2_fac_id": p2_fac_id,
                "p2_fac": p2_fac,
                "p2_sub_id": p2_sub_id,
                "p2_sub": p2_sub,
                "p2_wf": p2_wf
            }
            st.session_state.page = "40k_scores"
            st.rerun()

    # Pack the backpack before leaving the page!

elif st.session_state.page == "40k_scores":

    back_home()

    st.subheader("Game Scores")

    game_size = st.session_state.game_data.get("game_size", None)

    p1_first  = st.session_state.game_data.get("p1_first", None)
    p1_last   = st.session_state.game_data.get("p1_last", None)
    p1_known  = st.session_state.game_data.get("p1_known", None)
    p1_all_id = st.session_state.game_data.get("p1_all_id", None)
    p1_all    = st.session_state.game_data.get("p1_all", None)
    p1_fac_id = st.session_state.game_data.get("p1_fac_id", None)
    p1_fac    = st.session_state.game_data.get("p1_fac", None)
    p1_sub_id = st.session_state.game_data.get("p1_sub_id", None)
    p1_sub    = st.session_state.game_data.get("p1_sub", None)
    p1_wf     = st.session_state.game_data.get("p1_wf", None)

    p2_first  = st.session_state.game_data.get("p2_first", None)
    p2_last   = st.session_state.game_data.get("p2_last", None)
    p2_known  = st.session_state.game_data.get("p2_known", None)
    p2_all_id = st.session_state.game_data.get("p2_all_id", None)
    p2_all    = st.session_state.game_data.get("p2_all", None)
    p2_fac_id = st.session_state.game_data.get("p2_fac_id", None)
    p2_fac    = st.session_state.game_data.get("p2_fac", None)
    p2_sub_id = st.session_state.game_data.get("p2_sub_id", None)
    p2_sub    = st.session_state.game_data.get("p2_sub", None)
    p2_wf     = st.session_state.game_data.get("p2_wf", None)

    # 1. The Data Entry Form
    if not st.session_state.confirm_submit:
        with st.form("score_submission_form"):
            col3, col4 = st.columns(2)
            with col3:
                st.subheader(f"{p1_first}")
                # st.write(f"{p1_all}")
                st.write(f"**{p1_fac}**")
                st.write(f"{p1_sub}")
                p1_pri = st.number_input("Primary Score*", 0, 45, key="p1_p")
                p1_sec = st.number_input("Secondary Score*", 0, 45, key="p1_s")
                if st.toggle("Battle Ready?*", key="p1_br"):
                    p1_br = 10
                else:
                    p1_br = 0
            with col4:
                st.subheader(f"{p2_first}")
                # st.write(f"{p2_all}")
                st.write(f"**{p2_fac}**")
                st.write(f"{p2_sub}")
                p2_pri = st.number_input("Primary Score*", 0, 45, key="p2_p")
                p2_sec = st.number_input("Secondary Score*", 0, 45, key="p2_s")
                if st.toggle("Battle Ready?*", key="p2_br"):
                    p2_br = 10
                else:
                    p2_br = 0

            # submit_button = st.form_submit_button("Submit Game")

            # # --- 3. Mandatory Field Validation ---
            # if submit_button:
            #     if not p1_br or not p2_br:
            #         st.error("Battle Ready Flag is mandatory for both players!")
            #     else:
            #         st.success(f"Scores for {p1_first} vs {p2_first} are ready for the database.")
            #         # Database logic goes here next

            if st.form_submit_button("Preview Submission"):
                # Save scores to session state
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
            p1_res, p2_res = "Win", "Loss"
            p1_win, p2_win = True, False
        elif p2_total > p1_total:
            p1_res, p2_res = "Loss", "Win"
            p1_win, p2_win = False, True
        else:
            p1_res, p2_res = "Draw", "Draw"
            p1_win, p2_win = False, False

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
                    "game_id": new_game_id,
                    "first_name": p1_first,
                    "surname": p1_last,
                    "known_as": p1_known,
                    "allegiance_id": p1_all_id,
                    "faction_id": p1_fac_id,
                    "sub_faction_id": p1_sub_id,
                    "primary_score": scores['p1_pri'],
                    "secondary_score": scores['p1_sec'],
                    "bonus_score": 10 if scores['p1_br'] else 0,
                    "went_first": p1_wf,
                    "result": p1_res,
                    "is_winner": p1_win,
                    "score_diff": p1_total - p2_total
                },
                {
                    "game_id": new_game_id,
                    "first_name": p2_first,
                    "surname": p2_last,
                    "known_as": p2_known,
                    "allegiance_id": p2_all_id,
                    "faction_id": p2_fac_id,
                    "sub_faction_id": p2_sub_id,
                    "primary_score": scores['p2_pri'],
                    "secondary_score": scores['p2_sec'],
                    "bonus_score": 10 if scores['p2_br'] else 0,
                    "went_first": p2_wf,
                    "result": p2_res,
                    "is_winner": p2_win,
                    "score_diff": p2_total - p1_total
                }
            ]

            supabase.table("bgc_game_details").insert(player_entries).execute()

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

elif st.session_state.page == "AoS":

    back_home()

    try:
        # response = supabase.table("test_report").select("*").execute()
        # df = DataFrame(response.data)
        response_2 = supabase.table("v_faction_choices").select("*").execute()
        df_2 = DataFrame(response_2.data)
    except Exception as e:
        print(e)

    st.divider()
    st.subheader("Game Details")

    col1, col2 = st.columns(2)

    game_size = st.selectbox('Game Size',['2,000', '1,000'], index=None, placeholder="Choose...", key="game_s")
    # mission_pack = st.selectbox(st.selectbox('Mission Pack',['Strike Force (2k)', 'Incursion (1k)', 'Combat Partol'], index=None, placeholder="Choose...")

    with col1:
        st.write("**Your Details**")
        p1_first = st.text_input("First Name*", key="p1_f")
        p1_last = st.text_input("Surname", key="p1_l")
        p1_known = st.text_input("Known As", key="p1_k")
        # 1. Allegiance Dropdown
        p1_all_df = df_2[df_2['system_name'] == 'Age Of Sigmar']
        p1_all    = st.selectbox("Your Allegiance", p1_all_df['allegiance_name'].unique(), index=None, placeholder="Choose...", key="p1_all_sel")
        # 2. Faction Dropdown (MUST use filtered options)
        if p1_all:
            # We filter the dataframe here
            p1_fac_df = p1_all_df[p1_all_df['allegiance_name'] == p1_all]
            # We use faction_df to get the unique names for the options
            p1_fac = st.selectbox("Your Faction", p1_fac_df['faction_name'].unique(), index=None, placeholder="Choose...", key="p1_fac_sel")
        else:
            p1_fac = st.selectbox("Your Faction", [], disabled=True)
        # 3. Sub-Faction Dropdown (MUST use filtered options)
        if p1_fac:
            p1_sub_df = df_2[df_2['faction_name'] == p1_fac]
            p1_sub = st.selectbox("Your Sub-Faction", p1_sub_df['sub_faction_name'].unique(), index=None, placeholder="Choose...", key="p1_sub_sel")
        else:
            p1_sub = st.selectbox("Your Sub-Faction", [], disabled=True)
        # p1_wf = st.toggle("Went First?*", key="p1_wf_key", on_change=handle_wf_toggle, args=("p1",))

    with col2:
        st.write("**Opponent Details**")
        p2_first = st.text_input("First Name*", key="p2_f")
        p2_last = st.text_input("Surname", key="p2_l")
        p2_known = st.text_input("Known As", key="p2_k")

        # 1. Allegiance Dropdown
        p2_all_df = df_2[df_2['system_name'] == 'Age Of Sigmar']
        p2_all    = st.selectbox("Opponents Allegiance", p2_all_df['allegiance_name'].unique(), index=None, placeholder="Choose...", key="p2_all_sel")
        # 2. Faction Dropdown (MUST use filtered options)
        if p2_all:
            # We filter the dataframe here
            p2_fac_df = p2_all_df[p2_all_df['allegiance_name'] == p2_all]
            # We use faction_df to get the unique names for the options
            p2_fac = st.selectbox("Opponents Faction", p2_fac_df['faction_name'].unique(), index=None, placeholder="Choose...", key="p2_fac_sel")
        else:
            p2_fac = st.selectbox("Opponents Faction", [], disabled=True)
        # 3. Sub-Faction Dropdown (MUST use filtered options)
        if p2_fac:
            p2_sub_df = df_2[df_2['faction_name'] == p2_fac]
            p2_sub = st.selectbox("Opponents Sub-Faction", p2_sub_df['sub_faction_name'].unique(), index=None, placeholder="Choose...", key="p2_sub_sel")
        else:
            p2_sub = st.selectbox("Opponents Sub-Faction", [], disabled=True)
        # p2_wf = st.toggle("Went First?*", key="p2_wf_key", on_change=handle_wf_toggle, args=("p2",))

    if st.button("Proceed to Scoring"):
        # 1. Define your conditions
        names_entered = p1_first and p2_first
        allegiance_selected = p1_all and p2_all
        factions_selected = p1_fac and p2_fac
        sub_factions_selected = p1_sub and p2_sub
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
            p1_row = df_2[df_2['sub_faction_name'] == p1_sub].iloc[0]
            p1_all_id = int(p1_row['allegiance_id'])
            p1_fac_id = int(p1_row['faction_id'])
            p1_sub_id = int(p1_row['sub_faction_id'])

            # --- LOOKUP IDs FOR PLAYER 2 ---
            p2_row = df_2[df_2['sub_faction_name'] == p2_sub].iloc[0]
            p2_all_id = int(p2_row['allegiance_id'])
            p2_fac_id = int(p2_row['faction_id'])
            p2_sub_id = int(p2_row['sub_faction_id'])

            # 3. If all clear, SAVE to session_state and MOVE ON
            st.session_state.game_data = {
                "system_id": 1,
                "game_size": game_size,
                "p1_first": p1_first,
                "p1_last": p1_last,
                "p1_known": p1_known,
                "p1_all_id": p1_all_id,
                "p1_all": p1_all,
                "p1_fac_id": p1_fac_id,
                "p1_fac": p1_fac,
                "p1_sub_id": p1_sub_id,
                "p1_sub": p1_sub,
                # "p1_wf": p1_wf,
                "p2_first": p2_first,
                "p2_last": p2_last,
                "p2_known": p2_known,
                "p2_all_id": p2_all_id,
                "p2_all": p2_all,
                "p2_fac_id": p2_fac_id,
                "p2_fac": p2_fac,
                "p2_sub_id": p2_sub_id,
                "p2_sub": p2_sub
                # "p2_wf": p2_wf
            }
            st.session_state.page = "AoS_scores"
            st.rerun()

    # Pack the backpack before leaving the page!

elif st.session_state.page == "AoS_scores":

    back_home()

    st.subheader("Game Scores")

    game_size = st.session_state.game_data.get("game_size", None)
    p1_first  = st.session_state.game_data.get("p1_first", None)
    p1_last   = st.session_state.game_data.get("p1_last", None)
    p1_known  = st.session_state.game_data.get("p1_known", None)
    p1_all_id = st.session_state.game_data.get("p1_all_id", None)
    p1_all    = st.session_state.game_data.get("p1_all", None)
    p1_fac_id = st.session_state.game_data.get("p1_fac_id", None)
    p1_fac    = st.session_state.game_data.get("p1_fac", None)
    p1_sub_id = st.session_state.game_data.get("p1_sub_id", None)
    p1_sub    = st.session_state.game_data.get("p1_sub", None)
    # p1_wf     = st.session_state.game_data.get("p1_wf", None)

    p2_first  = st.session_state.game_data.get("p2_first", None)
    p2_last   = st.session_state.game_data.get("p2_last", None)
    p2_known  = st.session_state.game_data.get("p2_known", None)
    p2_all_id = st.session_state.game_data.get("p2_all_id", None)
    p2_all    = st.session_state.game_data.get("p2_all", None)
    p2_fac_id = st.session_state.game_data.get("p2_fac_id", None)
    p2_fac    = st.session_state.game_data.get("p2_fac", None)
    p2_sub_id = st.session_state.game_data.get("p2_sub_id", None)
    p2_sub    = st.session_state.game_data.get("p2_sub", None)
    # p2_wf     = st.session_state.game_data.get("p2_wf", None)

    # 1. The Data Entry Form
    if not st.session_state.confirm_submit:
        with st.form("score_submission_form"):
            col3, col4 = st.columns(2)
            with col3:
                st.subheader(f"{p1_first}")
                # st.write(f"{p1_all}")
                st.write(f"**{p1_fac}**")
                st.write(f"{p1_sub}")
                p1_pri = st.number_input("Primary Score*", 0, 45, key="p1_p")
                p1_sec = st.number_input("Secondary Score*", 0, 45, key="p1_s")
                if st.toggle("Battle Ready?*", key="p1_br"):
                    p1_br = 10
                else:
                    p1_br = 0
            with col4:
                st.subheader(f"{p2_first}")
                # st.write(f"{p2_all}")
                st.write(f"**{p2_fac}**")
                st.write(f"{p2_sub}")
                p2_pri = st.number_input("Primary Score*", 0, 45, key="p2_p")
                p2_sec = st.number_input("Secondary Score*", 0, 45, key="p2_s")
                if st.toggle("Battle Ready?*", key="p2_br"):
                    p2_br = 10
                else:
                    p2_br = 0

            # submit_button = st.form_submit_button("Submit Game")

            # # --- 3. Mandatory Field Validation ---
            # if submit_button:
            #     if not p1_br or not p2_br:
            #         st.error("Battle Ready Flag is mandatory for both players!")
            #     else:
            #         st.success(f"Scores for {p1_first} vs {p2_first} are ready for the database.")
            #         # Database logic goes here next

            if st.form_submit_button("Preview Submission"):
                # Save scores to session state
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
            p1_res, p2_res = "Win", "Loss"
            p1_win, p2_win = True, False
        elif p2_total > p1_total:
            p1_res, p2_res = "Loss", "Win"
            p1_win, p2_win = False, True
        else:
            p1_res, p2_res = "Draw", "Draw"
            p1_win, p2_win = False, False

        col_a, col_b = st.columns(2)
        col_a.write(f"Name: **{setup['p1_first']}**"
                    f"\n\nFaction: {setup['p1_fac']}"
                    f"\n\nBattle Formation: {setup['p1_sub']}"
                    f"\n\nPrimary: {scores['p1_pri']}"
                    f"\n\nSecondary: {scores['p1_sec']}"
                    f"\n\nBattle Ready: {scores['p1_br']}")
        col_b.write(f"Name: **{setup['p2_first']}**"
                    f"\n\nFaction: {setup['p2_fac']}"
                    f"\n\nBattle Formation: {setup['p2_sub']}"
                    f"\n\nPrimary: {scores['p2_pri']}"
                    f"\n\nSecondary: {scores['p2_sec']}"
                    f"\n\nBattle Ready: {scores['p2_br']}")

        c1, c2 = st.columns(2)
        if c1.button("✅ Yes, Post Results", type="primary", use_container_width=True):
            # --- DATABASE INSERT LOGIC HERE ---

            game_payload = {
                "system_id": 2,  # Stored from your 40k page lookup
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
                    "game_id": new_game_id,
                    "first_name": p1_first,
                    "surname": p1_last,
                    "known_as": p1_known,
                    "allegiance_id": p1_all_id,
                    "faction_id": p1_fac_id,
                    "sub_faction_id": p1_sub_id,
                    "primary_score": scores['p1_pri'],
                    "secondary_score": scores['p1_sec'],
                    "bonus_score": 10 if scores['p1_br'] else 0,
                    # "went_first": p1_wf,
                    "result": p1_res,
                    "is_winner": p1_win,
                    "score_diff": p1_total - p2_total
                },
                {
                    "game_id": new_game_id,
                    "first_name": p2_first,
                    "surname": p2_last,
                    "known_as": p2_known,
                    "allegiance_id": p2_all_id,
                    "faction_id": p2_fac_id,
                    "sub_faction_id": p2_sub_id,
                    "primary_score": scores['p2_pri'],
                    "secondary_score": scores['p2_sec'],
                    "bonus_score": 10 if scores['p2_br'] else 0,
                    # "went_first": p2_wf,
                    "result": p2_res,
                    "is_winner": p2_win,
                    "score_diff": p2_total - p1_total
                }
            ]

            supabase.table("bgc_game_details").insert(player_entries).execute()

            st.success("Game posted to Supabase!")

            st.session_state.game_data = {}
            st.session_state.temp_scores = {}
            st.session_state.confirm_submit = False
            # st.session_state.page = None  # Go back to home
            # st.rerun()
            st.session_state.selected_system = "AoS"
            st.session_state.page = "bgc_games"
            st.rerun()

        if c2.button("❌ No, Edit Scores", use_container_width=True):
            st.session_state.confirm_submit = False
            st.rerun()

elif st.session_state.page == "bgc_games":

    # Loading Bar - to show that things are happening?
    progress_text = "Operation in progress. Please wait."
    my_bar = st.progress(0, text=progress_text)
    for percent_complete in range(100):
        time.sleep(0.01)
        my_bar.progress(percent_complete + 1, text=progress_text)
    time.sleep(1)
    my_bar.empty()

    back_home()

    df = None
    option = None  # Add this line here

    # Testing connection to custom view
    try:
        response_1 = supabase.table("v_bgc_game_results_light").select("*").execute()
        df = DataFrame(response_1.data)
        # response_2 = supabase.table("v_league_pairing_results").select("*").execute()
        # df_2 = DataFrame(response_2.data)
    except Exception as e:
        st.error(f"Error fetching data: {e}")

    st.title("BGC Game Data")

    # 2. Only show the selectbox if df was successfully created and isn't empty
    if df is not None and not df.empty:
        # Get your unique options
        system_options = df['system_short_name'].unique().tolist()

        # Check if we have a "remembered" system from the submission
        default_index = None
        if 'selected_system' in st.session_state:
            try:
                # Find where our remembered system is in the list
                default_index = system_options.index(st.session_state.selected_system)
            except ValueError:
                default_index = None

        # Pass the index to the selectbox
        option = st.selectbox(
            "Please select a Game System",
            system_options,
            index=default_index,  # This sets the pre-selection
            placeholder="Choose one...",
            key="results_system_select"
        )
        if option:
            st.session_state.selected_system = option
    else:
        st.warning("No data available to display.")

    ### Printing Dataframe - no editing though
    if option:
        st.header("Game Results by System")
        # st.subheader("st.dataframe")

        bgc_tab1, = st.tabs(["Games"])

        with bgc_tab1:

            display_df = df[df['system_short_name'] == option].copy()
            display_df = display_df.sort_values(by='id', ascending=False)

            st.subheader("System Games")
            st.dataframe(
                display_df[['game_size','name_a','faction_a','score_a','result_a','name_b','faction_b','score_b','result_b']],
                hide_index=True,
                column_config={
                    "game_size": "Size",
                    "name_a": "1 - Name",
                    "faction_a": "1 - Faction",
                    "score_a": "1 - Score",
                    "result_a": "1 - Result",
                    "name_b": "2 - Name",
                    "faction_b": "2 - Faction",
                    "score_b": "2 - Score",
                    "result_b": "2 - Result"
                },
                use_container_width=True
            )

elif st.session_state.page == "league_data":

    # Loading Bar - to show that things are happening?
    progress_text = "Operation in progress. Please wait."
    my_bar = st.progress(0, text=progress_text)
    for percent_complete in range(100):
        time.sleep(0.01)
        my_bar.progress(percent_complete + 1, text=progress_text)
    time.sleep(1)
    my_bar.empty()

    back_home()

    df = None
    option = None  # Add this line here

    # Testing connection to custom view
    try:
        response_1 = supabase.table("v_league_data_sum_v1").select("*").execute()
        df = DataFrame(response_1.data)
        response_2 = supabase.table("v_league_pairing_results").select("*").execute()
        df_2 = DataFrame(response_2.data)
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

        tab1, tab2, tab3 = st.tabs(["Placings", "Pairings", "Faction Data"])

        with tab1:

            display_df = df[df['league_name'] == option].copy()
            display_df = display_df.sort_values(by='sorting', ascending=False)
            display_df.insert(0, 'rank', range(1, len(display_df) + 1))
            display_df['record'] = (
                    display_df['win'].astype(str) + "/" +
                    display_df['draw'].astype(str) + "/" +
                    display_df['loss'].astype(str)
            )

            st.subheader("Current Rankings in Event")
            st.dataframe(
                display_df[['rank', 'player_name', 'faction_name', 'sub_faction_name', 'record', 'total_score', 'score_difference']],
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

            display_df_2 = df_2[df_2['league_name'] == option].copy()
            display_df_2 = display_df_2.sort_values(by='round_no', ascending=False)

            st.subheader("Round Pairings")
            st.dataframe(
                display_df_2[['round_no','first_name_a','faction_name_a','score_a','result_a','first_name_b','faction_name_b','score_b','result_b']],
                hide_index=True,
                column_config={
                    "round_no": "Round",
                    "first_name_a": "1 - Name",
                    "faction_name_a": "1 - Faction",
                    "score_a": "1 - Score",
                    "result_a": "1 - Result",
                    "first_name_b": "2 - Name",
                    "faction_name_b": "2 - Faction",
                    "score_b": "2 - Score",
                    "result_b": "2 - Result"
                },
                use_container_width=True
            )
        with tab3:
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
            allegiance_stats['total_games'] = allegiance_stats['win'] + allegiance_stats['loss'] + allegiance_stats['draw']
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

elif st.session_state.page == "event_data":
    st.header("BGC Event Data")
    back_home()
