import streamlit as st
from supabase import create_client, Client, ClientOptions
from streamlit_js_eval import streamlit_js_eval
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px
import time
import os
import requests

def post_to_discord_webhook(message_text):
    """Sends a quick message alert to a specific Discord channel."""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return False
        
    payload = {"content": message_text}
    try:
        response = requests.post(webhook_url, json=payload)
        return response.status_code == 204
    except Exception:
        return False

# from supabase import create_client, ClientOptions

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



def check_admin_access(supabase):
    """Returns True if the logged-in user is an admin, False otherwise."""
    if "user" not in st.session_state or st.session_state.user is None:
        return False
        
    user_id = st.session_state.user.id
    res = supabase.table("profiles").select("role").eq("id", user_id).maybe_single().execute()
    
    if res.data and res.data.get("role") in ["system_admin", "event_admin"]:
        return True
    return False



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

# # scottpaisey 03/04/2026
# # DEBUG: comment this out if the sign in has issues !!!
# 3. PERSISTENT USER SYNC (Uncommented and improved)
if "user" in st.session_state and "user_role" not in st.session_state:
    try:
        user_id = st.session_state.user.id
        # Fetch the role from the profile table where ID matches the authenticated user
        profile_res = supabase.table("profiles").select("role").eq("id", user_id).execute()
        
        if profile_res.data:
            st.session_state.user_role = profile_res.data[0].get('role', 'member')
        else:
            st.session_state.user_role = "member" # Fallback if no profile exists
    except Exception as e:
        st.session_state.user_role = "member"

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
    st.sidebar.header("Account")
    if st.sidebar.button("Personal Stats"):
        st.session_state.page = "Personal Stats"
        collapse_sidebar()
        st.rerun()
    if st.sidebar.button("Log Out"):
        supabase.auth.sign_out()
        # Clear session state completely to be safe
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.sidebar.header("BGC App")
    if st.sidebar.button("Home"):
        st.session_state.page = None
        collapse_sidebar()
        st.rerun()
    if st.sidebar.button("Log Games"):
        st.session_state.page = "Log Games"
        collapse_sidebar()
        st.rerun()
    if st.session_state.get("user_role") == "system_admin":
        if st.sidebar.button("BGC League"):
            st.session_state.page = "BGC_League"
            collapse_sidebar()
            st.rerun()
        if st.sidebar.button("BGC Ladder"):
            st.session_state.page = "BGC_Ladder"
            collapse_sidebar()
            st.rerun()
    if st.sidebar.button("Event Results"):
        st.session_state.page = "Event_Results"
        collapse_sidebar()
        st.rerun()
    if st.sidebar.button("Club Stats"): # was Graphs
        st.session_state.page = "Club Stats"
        collapse_sidebar()
        st.rerun()
    if st.session_state.get("user_role") != "member":
        st.sidebar.header("Admin Pages")
    if st.session_state.get("user_role") == "system_admin":
        if st.sidebar.button("Graphs_2"):
            st.session_state.page = "Graphs_2"
            collapse_sidebar()
            st.rerun()
        if st.sidebar.button("Current Events"):
            st.session_state.page = "Current_Events"
            collapse_sidebar()
            st.rerun()

    if st.session_state.get("user_role") in ("system_admin", "event_admin"):
        if st.sidebar.button("Event Manager"):
            st.session_state.page = "Event_Manager"
            collapse_sidebar()
            st.rerun()        

    if st.session_state.page is None:
        st.header("BGC Club App")
        st.write(f"Welcome back, {st.session_state.user.user_metadata.get('full_name')}!")
        st.divider()

        # -------------------------------------------------------------
        # 1. FETCH & PREPARE ALL LOGGED DATA
        # -------------------------------------------------------------
        res = (
            supabase.table("match_results")
            .select("*")
            .eq("status", "Logged")
            .order("game_date_ord", desc=True)
            .limit(1000)
            .execute()
        )
        
        if res.data:
            all_df = pd.DataFrame(res.data)
            
            # Layout: Left for metrics/chart, Right for recent raw feed
            col_chart, col_recent = st.columns([3, 2])
            
            # -------------------------------------------------------------
            # 1. VISUAL ANALYTICS (FULL WIDTH)
            # -------------------------------------------------------------
            st.subheader("Games per System")
            system_counts = all_df["system_name"].value_counts().reset_index()
            system_counts.columns = ["System", "Games Played"]
            
            # Draw the Pie Chart across the full container width
            fig = px.pie(
                system_counts, 
                values="Games Played", 
                names="System", 
                hole=0.3,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_layout(
                margin=dict(t=10, b=10, l=10, r=10), 
                height=300,
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig, use_container_width=True)

            # --- RECENT MATCHES TABLE (PLACED UNDER CHART) ---
            st.write("")
            st.subheader("⚔️ Recent Faction Matchups")
            
            # Grab the 5 most recent matches
            recent_table_df = all_df.head(5).copy()
            
            st.dataframe(
                recent_table_df,
                column_order=(
                    "game_date",
                    "system_name",
                    "p1_faction",
                    "p1_score_total",
                    "p2_score_total",
                    "p2_faction"
                ),
                column_config={
                    "game_date": "Date",
                    "system_name": "System",
                    "p1_faction": "Player 1 Faction",
                    "p1_score_total": st.column_config.NumberColumn("P1 Score", format="%d"),
                    "p2_score_total": st.column_config.NumberColumn("P2 Score", format="%d"),
                    "p2_faction": "Player 2 Faction"
                },
                use_container_width=True,
                hide_index=True
            )

            # -------------------------------------------------------------
            # 2. DYNAMIC WIN RATE RANKINGS ENGINE
            # -------------------------------------------------------------
            st.divider()
            st.header("🏆 Club Leaderboards")

            def calculate_leaderboard(df_subset):
                """Processes any slice of the data frame to compile individual records."""
                player_stats = {}
                
                for _, row in df_subset.iterrows():
                    p1 = row["display_p1_name"]
                    p2 = row["display_p2_name"]
                    winner = row["winner_name"]
                    is_draw = row["is_draw"]
                    
                    # Process Player 1
                    if p1 not in player_stats:
                        player_stats[p1] = {"Played": 0, "Wins": 0, "Draws": 0}
                    player_stats[p1]["Played"] += 1
                    if is_draw:
                        player_stats[p1]["Draws"] += 1
                    elif winner == p1:
                        player_stats[p1]["Wins"] += 1
                        
                    # Process Player 2 (Ignore if it is empty or a Guest string)
                    if pd.notna(p2) and str(p2).strip() != "":
                        if p2 not in player_stats:
                            player_stats[p2] = {"Played": 0, "Wins": 0, "Draws": 0}
                        player_stats[p2]["Played"] += 1
                        if is_draw:
                            player_stats[p2]["Draws"] += 1
                        elif winner == p2:
                            player_stats[p2]["Wins"] += 1

                # Structural conversions
                leaderboard_rows = []
                for player, stats in player_stats.items():
                    # Set minimum threshold to 2 matches to prevent unearned 100% win rates
                    if stats["Played"] >= 2: 
                        win_rate = (stats["Wins"] / stats["Played"]) * 100
                        leaderboard_rows.append({
                            "Player": player,
                            "Played": stats["Played"],
                            "Wins": stats["Wins"],
                            "Draws": stats["Draws"],
                            "Win Rate": round(win_rate, 1)
                        })
                
                if not leaderboard_rows:
                    return pd.DataFrame()
                    
                lb_df = pd.DataFrame(leaderboard_rows)
                # Primary sorting on Win Rate, Secondary sorting on Experience (Played)
                lb_df = lb_df.sort_values(by=["Win Rate", "Played"], ascending=[False, False]).reset_index(drop=True)
                lb_df.index += 1  # Standard 1-based ranking index
                return lb_df

            # --- DISPLAY: ALL SYSTEMS GLOBAL BOARD ---
            st.subheader("Top 25 Players (Overall - All Systems)")
            overall_lb = calculate_leaderboard(all_df)
            
            if not overall_lb.empty:
                st.dataframe(
                    overall_lb.head(25),
                    column_config={
                        "Win Rate": st.column_config.NumberColumn("Win Rate", format="%.1f%%"),
                    },
                    use_container_width=True
                )
            else:
                st.info("Play more matches to populate the overall leaderboard.")

            # --- DISPLAY: SYSTEM SPECIFIC BOARDS ---
            st.write("")
            st.subheader("Top 5 Players by Game System")
            
            # Dynamically pull whatever unique systems are represented in the dataset
            unique_systems = all_df["system_name"].unique()
            system_tabs = st.tabs(list(unique_systems))
            
            for tab, system_name in zip(system_tabs, unique_systems):
                with tab:
                    system_matches = all_df[all_df["system_name"] == system_name]
                    system_lb = calculate_leaderboard(system_matches)
                    
                    if not system_lb.empty:
                        st.dataframe(
                            system_lb.head(5),
                            column_config={
                                "Win Rate": st.column_config.NumberColumn("Win Rate", format="%.1f%%"),
                            },
                            use_container_width=True
                        )
                    else:
                        st.info(f"Not enough data to calculate top players for {system_name}.")
        else:
            st.info("No match history found yet. Go log some games!")

    elif st.session_state.page == "Log Games":
        st.header("Log Games")
        st.divider()
        st.subheader("Step 1: Please Choose the System you are logging")
        if st.session_state.get("user_role") == "system_admin":
            if st.button("Warhammer 40,000 (11th Edition)"):
                st.session_state.page = "40k11th"
                st.rerun()
        if st.button("Warhammer 40,000"):
            st.session_state.page = "40k"
            st.rerun()        
        if st.button("Age of Sigmar (3rd Edition)"):
            st.session_state.page = "AOS"
            st.rerun()
        if st.button("Kill Team"):
            st.session_state.page = "KT"
            st.rerun()
        if st.session_state.get("user_role") == "system_admin":
            if st.button("Middle Earth: SBG"):
                st.session_state.page = "MESBG"
                st.rerun()
        if st.session_state.get("user_role") == "system_admin":
            if st.button("Old World"):
                st.session_state.page = "OW"
                st.rerun()


    # WARHAMMER 11TH EDITION GAME LOGGING
    # # / DIFFERENCE FROM 10TH TO 11TH IS HOW DETATCHMENTS ARE CHOSEN, BEING ABLE TO SELECT UP TO 3 DETATCHMENT POINTS AND HAVING
    # # / NO SHARED KEYWORDS BETWEEN THEM.

    elif st.session_state.page == "40k11th":
        st.header("Warhammer 40,000 Game (11th Edition)")
        st.divider()
        try:
            # System ID for your new 11th Edition 40K system row
            SYSTEM_11TH_ID = 'ccc3b65d-a53c-4528-9b6e-d0313e71c790' 
            
            p1_response_system_factions = supabase.table("system_factions").select("*").execute()
            p1_df_system_factions = pd.DataFrame(p1_response_system_factions.data)
            p2_response_system_factions = supabase.table("system_factions").select("*").execute()
            p2_df_system_factions = pd.DataFrame(p2_response_system_factions.data)
            p2_response_account = supabase.table("profiles").select("*").execute()
            p2_df_account = pd.DataFrame(p2_response_account.data)
        except Exception as e:
            st.error(f"Error loading system data: {e}")
            
        st.subheader("Game Details")
        game_size = st.selectbox('Game Size', ['Strike Force', 'Incursion', 'Other'], index=None,
                                 placeholder="Choose...", key="game_s")
        
        # -------------------------------------------------------------
        # PLAYER 1 DETAILS
        # -------------------------------------------------------------
        st.write("**Your Details**")
        p1_name = st.text_input("Your Discord Name*", value=discord_name, key="p1_username", disabled=True)
        
        p1_all_df = p1_df_system_factions[p1_df_system_factions['system_id'] == SYSTEM_11TH_ID]
        p1_all = st.selectbox("Your Allegiance", p1_all_df['allegiance'].unique(), index=None,
                              placeholder="Choose...", key="p1_all_sel")
        
        p1_fac_id = None
        p1_selected_dets = []
        
        if p1_all:
            p1_fac_df = p1_all_df[p1_all_df['allegiance'] == p1_all]
            p1_fac = st.selectbox("Your Faction", p1_fac_df['faction'].unique(), index=None,
                                  placeholder="Choose...", key="p1_fac_sel")
            
            if p1_fac:
                # 1. Locate rows matching your faction selection
                matched_rows = p1_fac_df[p1_fac_df['faction'] == p1_fac]
                
                if not matched_rows.empty:
                    # 2. Extract the clean string text UUID using .at or .iloc[0] position safely
                    p1_fac_id = str(matched_rows.iloc[0]['faction_id'])
                    
                    # 3. Pull your newly created 11th edition detachments from Supabase
                    p1_det_resp = supabase.table("detachments_11th").select("*").eq("faction_id", p1_fac_id).execute()

                    if p1_det_resp.data:
                        p1_det_df = pd.DataFrame(p1_det_resp.data)
                        p1_det_df['display_label'] = p1_det_df['name'] + " (" + p1_det_df['dp_cost'].astype(str) + " DP)"
                        
                        p1_chosen_labels = st.multiselect("Your Detachments (Max 3, Max 3 DP Total)", p1_det_df['display_label'].unique(), max_selections=3, key="p1_dets")
                        p1_selected_dets = p1_det_df[p1_det_df['display_label'].isin(p1_chosen_labels)].to_dict(orient="records")
                    else:
                        st.info(f"ℹ️ No multi-detachments found in DB matching faction_id: `{p1_fac_id}`")
                else:
                    st.error("❌ Could not map faction selections to view data rows.")

        else:
            p1_fac = st.selectbox("Your Faction", [], disabled=True)

        # -------------------------------------------------------------
        # PLAYER 2 DETAILS
        # -------------------------------------------------------------
        st.write("**Opponent Details**")
        p2_input = st.text_input("Opponent Name*", key="p2_username",
                                 help="Type their Discord User Name to link their profile")
        p2_id = None
        p2_name = None

        if p2_input:
            search_term = p2_input.strip().lower()
            mask = (p2_df_account['username'].fillna('').str.lower() == search_term) | \
                   (p2_df_account['full_name'].fillna('').str.lower() == search_term)
            matched_rows = p2_df_account[mask]

            if not matched_rows.empty:
                user_row = matched_rows.iloc[0]
                p2_id = user_row['id']
                p2_name = user_row['full_name'] if user_row['full_name'] else user_row['username']
                st.success(f"✅ User found! Linked to **{p2_name}**.")
            else:
                p2_name = p2_input
                st.warning("⚠️ User not found. Recording as 'Guest'.")

        p2_all_df = p2_df_system_factions[p2_df_system_factions['system_id'] == SYSTEM_11TH_ID]
        p2_all = st.selectbox("Opponents Allegiance", p2_all_df['allegiance'].unique(), index=None,
                              placeholder="Choose...", key="p2_all_sel")
        
        p2_fac_id = None
        p2_selected_dets = []
        
        if p2_all:
            p2_fac_df = p2_all_df[p2_all_df['allegiance'] == p2_all]
            p2_fac = st.selectbox("Opponents Faction", p2_fac_df['faction'].unique(), index=None,
                                  placeholder="Choose...", key="p2_fac_sel")
            
            if p2_fac:
                p2_fac_id = p2_fac_df[p2_fac_df['faction'] == p2_fac].iloc[0]['faction_id']
                
                # Fetch valid 11th edition detachments for Opponent
                p2_det_resp = supabase.table("detachments_11th").select("*").eq("faction_id", p2_fac_id).execute()
                if p2_det_resp.data:
                    p2_det_df = pd.DataFrame(p2_det_resp.data)
                    p2_det_df['display_label'] = p2_det_df['name'] + " (" + p2_det_df['dp_cost'].astype(str) + " DP)"
                    
                    p2_chosen_labels = st.multiselect("Opponents Detachments (Max 3, Max 3 DP Total)", p2_det_df['display_label'].unique(), max_selections=3, key="p2_dets")
                    p2_selected_dets = p2_det_df[p2_det_df['display_label'].isin(p2_chosen_labels)].to_dict(orient="records")
                else:
                    st.info("ℹ️ No multi-detachments found for this faction yet.")
        else:
            p2_fac = st.selectbox("Opponents Faction", [], disabled=True)

        # -------------------------------------------------------------
        # TURN ORDER & ROLES
        # -------------------------------------------------------------
        options = ["You", "Opponent"]
        went_first = st.segmented_control("Who went first?", options, selection_mode="single", key="went_first")
        attacking_player = st.segmented_control("Who is the attacker?", options, selection_mode="single", key="attacking_player")

        if st.button("Proceed to Scoring"):
            # Validation Step: 11th Edition Rule Constraints Check
            def validate_list(detachments, player_label):
                total_dp = sum(d['dp_cost'] for d in detachments)
                if total_dp > 3:
                    return f"❌ {player_label} list exceeds detachment points limit ({total_dp}/3 DP selected)."
                
                # Keyword overlapping check
                seen_keywords = []
                for d in detachments:
                    if d.get('keywords'):
                        duplicates = set(seen_keywords).intersection(set(d['keywords']))
                        if duplicates:
                            return f"❌ {player_label} list has duplicate detachment keywords: {list(duplicates)}"
                        seen_keywords.extend(d['keywords'])
                return None

            p1_error = validate_list(p1_selected_dets, "Your")
            p2_error = validate_list(p2_selected_dets, "Opponent's")

            if not (p1_name and p2_name):
                st.error("❌ Both player names are mandatory.")
            elif not (p1_fac and p2_fac):
                st.error("❌ Both players must select a Faction.")
            elif p1_error:
                st.error(p1_error)
            elif p2_error:
                st.error(p2_error)
            else:
                # Map actual IDs safely
                actual_p2_id = p2_id if (p2_id and p2_id != p2_name) else None
                attacker_id = st.session_state.user.id if attacking_player == "You" else actual_p2_id
                defender_id = actual_p2_id if attacking_player == "You" else st.session_state.user.id
                went_first_id = st.session_state.user.id if went_first == "You" else actual_p2_id

                # Bundle values up for the scoring layout step
                st.session_state.game_data = {
                    "system_id": SYSTEM_11TH_ID,
                    "p1_id": st.session_state.user.id,
                    "p1_name": p1_name,
                    "p1_all": p1_all,
                    "p1_fac": p1_fac,
                    "p2_id": actual_p2_id,
                    "p2_name": p2_name,
                    "p2_all": p2_all,
                    "p2_fac": p2_fac,
                    "p1_fac_id": str(p1_fac_id),
                    "p2_fac_id": str(p2_fac_id),
                    "attacker_id": attacker_id,
                    "defender_id": defender_id,
                    "went_first_id": went_first_id,
                    "game_size": game_size,
                    # Carry the full dictionary records forward to insert into match_detachments_11th later
                    "p1_detachments": p1_selected_dets, 
                    "p2_detachments": p2_selected_dets
                }

                st.session_state.page = "40k11th_scores"
                st.rerun()

    elif st.session_state.page == "40k11th_scores":
        st.subheader("Game Scores")
        st.divider()
        setup = st.session_state.game_data
        
        system_id = setup.get("system_id", None)
        game_size = setup.get("game_size", None)

        attacker_id = setup.get("attacker_id", None)
        defender_id = setup.get("defender_id", None)
        went_first_id = setup.get("went_first_id", None)

        p1_id = setup.get("p1_id", None)
        p1_name = setup.get("p1_name", None)
        p1_fac_id = setup.get("p1_fac_id", None)
        p1_all = setup.get("p1_all", None)
        p1_fac = setup.get("p1_fac", None)
        p1_detachments = setup.get("p1_detachments", [])  # List of chosen detachment records

        p2_id = setup.get("p2_id", None)
        p2_name = setup.get("p2_name", None)
        p2_fac_id = setup.get("p2_fac_id", None)
        p2_all = setup.get("p2_all", None)
        p2_fac = setup.get("p2_fac", None)
        p2_detachments = setup.get("p2_detachments", [])  # List of chosen detachment records

        if not st.session_state.confirm_submit:
            with st.form("score_submission_form"):
                col3, col4 = st.columns(2)
                with col3:
                    st.subheader(f"{p1_name}")
                    st.write(f"**Faction:** {p1_fac}")
                    p1_det_string = ", ".join([d['name'] for d in p1_detachments]) if p1_detachments else "None Chosen"
                    st.caption(f"**Formations:** {p1_det_string}")
                    
                    p1_pri = st.number_input("Primary Score*", 0, 45, key="p1_p")
                    p1_sec = st.number_input("Secondary Score*", 0, 45, key="p1_s")
                    p1_br = 10 if st.toggle("Battle Ready?*", key="p1_br") else 0
                    p1_killed_warlord = True if st.toggle("Slain Enemy Warlord?*", key="p1_killed_warlord") else False
                    p1_tabled_opponent = True if st.toggle("Tabled Opponent?*", key="p1_tabled_opponent") else False
                    
                with col4:
                    st.subheader(f"{p2_name}")
                    st.write(f"**Faction:** {p2_fac}")
                    p2_det_string = ", ".join([d['name'] for d in p2_detachments]) if p2_detachments else "None Chosen"
                    st.caption(f"**Formations:** {p2_det_string}")
                    
                    p2_pri = st.number_input("Primary Score*", 0, 45, key="p2_p")
                    p2_sec = st.number_input("Secondary Score*", 0, 45, key="p2_s")
                    p2_br = 10 if st.toggle("Battle Ready?*", key="p2_br") else 0
                    p2_killed_warlord = True if st.toggle("Slain Enemy Warlord?*", key="p2_killed_warlord") else False
                    p2_tabled_opponent = True if st.toggle("Tabled Opponent?*", key="p2_tabled_opponent") else False
                    
                submit_scores = st.form_submit_button("Review Results")

                if submit_scores:
                    st.session_state.temp_scores = {
                        "p1_pri": p1_pri, "p1_sec": p1_sec, "p1_br": p1_br, "p1_killed_warlord": p1_killed_warlord, "p1_tabled_opponent": p1_tabled_opponent,
                        "p2_pri": p2_pri, "p2_sec": p2_sec, "p2_br": p2_br, "p2_killed_warlord": p2_killed_warlord, "p2_tabled_opponent": p2_tabled_opponent
                    }
                    st.session_state.confirm_submit = True
                    st.rerun()

        else:
            st.warning("⚠️ **Confirm Game Results**")
            st.write("Please review the details below. **These cannot currently be changed after posting.**")
            scores = st.session_state.temp_scores
            
            p1_total = scores['p1_pri'] + scores['p1_sec'] + scores['p1_br']
            p2_total = scores['p2_pri'] + scores['p2_sec'] + scores['p2_br']

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
            p1_det_string = ", ".join([d['name'] for d in p1_detachments]) if p1_detachments else "None"
            col_a.write(f"Name: **{setup['p1_name']}**"
                        f"\n\nFaction: {setup['p1_fac']}"
                        f"\n\nDetachments: {p1_det_string}"
                        f"\n\nPrimary: {scores['p1_pri']}"
                        f"\n\nSecondary: {scores['p1_sec']}"
                        f"\n\nBattle Ready: {scores['p1_br']}")
                        
            p2_det_string = ", ".join([d['name'] for d in p2_detachments]) if p2_detachments else "None"
            col_b.write(f"Name: **{setup['p2_name']}**"
                        f"\n\nFaction: {setup['p2_fac']}"
                        f"\n\nDetachments: {p2_det_string}"
                        f"\n\nPrimary: {scores['p2_pri']}"
                        f"\n\nSecondary: {scores['p2_sec']}"
                        f"\n\nBattle Ready: {scores['p2_br']}")

            c1, c2 = st.columns(2)

            def clean_id(val):
                if isinstance(val, str) and len(val) < 30:
                    return None
                return val

            if c1.button("✅ Yes, Post Results", type="primary", use_container_width=True):
                try:
                    match_details = {
                        "game_system_id": setup['system_id'],
                        "event_id": setup.get('event_id', None),  # Dynamically assigns ladder/league ID if present
                        "round_id": setup.get('round_id', None),
                        "mission_id": None,
                        "game_size": setup['game_size'],
                        "player_1_id": setup['p1_id'],
                        "p1_faction_id": setup['p1_fac_id'],
                        "p1_score_01": scores['p1_pri'],
                        "p1_score_02": scores['p1_sec'],
                        "p1_score_03": scores['p1_br'],
                        "p1_score_total": p1_total,
                        "p1_score_mar": p1_total - p2_total,
                        "player_2_id": clean_id(setup['p2_id']),
                        "player_2_name": setup['p2_name'],
                        "p2_faction_id": setup['p2_fac_id'],
                        "p2_score_01": scores['p2_pri'],
                        "p2_score_02": scores['p2_sec'],
                        "p2_score_03": scores['p2_br'],
                        "p2_score_total": p2_total,
                        "p2_score_mar": p2_total - p1_total,
                        "went_first_id": clean_id(setup['went_first_id']),
                        "winner_id": clean_id(winner_id),
                        "loser_id": clean_id(loser_id),
                        "attacker_id": clean_id(setup['attacker_id']),
                        "defender_id": clean_id(setup['defender_id']),
                        "is_draw": is_draw,
                        "recorded_by": setup['p1_id'],
                        # "club_id": "ac85d0d1-24df-4b85-a4bd-0e5e944acd99", # BGC
                        "club_id": "e0435ab2-d5e4-438f-8442-90cc27365cb5", # Test Club
                        "p1_killed_warlord": scores['p1_killed_warlord'],
                        "p2_killed_warlord": scores['p2_killed_warlord'],
                        "p1_tabled_opponent": scores['p1_tabled_opponent'],
                        "p2_tabled_opponent": scores['p2_tabled_opponent'],
                    }

                    # 1. Post to primary match log table
                    match_insert_res = supabase.table("matches").insert(match_details).execute()
                    
                    if match_insert_res.data:
                        # Extract the freshly generated uuid match id
                        new_match_id = match_insert_res.data[0]['id']
                        
                        # 2. Iterate and write Player 1's Multi-Detachments
                        p1_det_payloads = [
                            {"match_id": new_match_id, "player_id": setup['p1_id'], "detachment_id": det['id']}
                            for det in p1_detachments
                        ]
                        if p1_det_payloads:
                            supabase.table("match_detachments_11th").insert(p1_det_payloads).execute()
                            
                        # 3. Iterate and write Player 2's Multi-Detachments
                        if clean_id(setup['p2_id']):
                            p2_det_payloads = [
                                {"match_id": new_match_id, "player_id": setup['p2_id'], "detachment_id": det['id']}
                                for det in p2_detachments
                            ]
                            if p2_det_payloads:
                                supabase.table("match_detachments_11th").insert(p2_det_payloads).execute()
                        
                        # Trigger Discord Notification Feed
                        post_to_discord_webhook(f"⚔️ **Match Logged!** {setup['p1_name']} vs {setup['p2_name']}. Result: {p1_total} - {p2_total}")
                        
                        st.success("Game posted to Supabase!")

                        # 4. State Reset Routine
                        st.session_state.game_data = {}
                        st.session_state.temp_scores = {}
                        st.session_state.confirm_submit = False
                        st.session_state.selected_system = "40K"
                        st.session_state.page = None
                        st.rerun()
                        
                except Exception as db_err:
                    st.error(f"Failed to record match. Database error: {db_err}")
                    
            if c2.button("❌ Cancel / Make Changes", use_container_width=True):
                st.session_state.confirm_submit = False
                st.rerun()


    # WARHAMMER 10TH EDITION GAME LOGGING

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
        p1_name = st.text_input("Your Discord Name*", value=discord_name, key="p1_username", disabled=True)
        # 1. Allegiance Dropdown
        p1_all_df = p1_df_system_factions[p1_df_system_factions['system_id'] == 'b24b1f7a-152f-49f5-b273-29ba5c00bfb8']
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
                    if st.toggle("Slain Enemy Warlord?*", key="p1_killed_warlord"):
                        p1_killed_warlord = True
                    else:
                        p1_killed_warlord = False
                    if st.toggle("Tabled Opponent?*", key="p1_tabled_opponent"):
                        p1_tabled_opponent = True
                    else:
                        p1_tabled_opponent = False
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
                    if st.toggle("Slain Enemy Warlord?*", key="p2_killed_warlord"):
                        p2_killed_warlord = True
                    else:
                        p2_killed_warlord = False
                    if st.toggle("Tabled Opponent?*", key="p2_tabled_opponent"):
                        p2_tabled_opponent = True
                    else:
                        p2_tabled_opponent = False
                    

                # Use the form submit button to move to confirmation
                submit_scores = st.form_submit_button("Review Results")

                if submit_scores:
                    st.session_state.temp_scores = {
                        "p1_pri": p1_pri, "p1_sec": p1_sec, "p1_br": p1_br, "p1_killed_warlord": p1_killed_warlord, "p1_tabled_opponent": p1_tabled_opponent,
                        "p2_pri": p2_pri, "p2_sec": p2_sec, "p2_br": p2_br, "p2_killed_warlord": p2_killed_warlord, "p2_tabled_opponent": p2_tabled_opponent
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
                        "recorded_by":  setup['p1_id'],
                        "club_id": "ac85d0d1-24df-4b85-a4bd-0e5e944acd99",
                        "p1_killed_warlord": scores['p1_killed_warlord'],
                        "p2_killed_warlord": scores['p2_killed_warlord'],
                        "p1_tabled_opponent": scores['p1_tabled_opponent'],
                        "p2_tabled_opponent": scores['p2_tabled_opponent'],
                    }

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

    elif st.session_state.page == "AOS":
        st.header("Age of Sigmar Game")
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
        game_size = st.selectbox('Game Size', ['2000pts', '1000pts', 'Other'], index=None,
                                 placeholder="Choose...", key="game_s")
        # mission_pack = st.selectbox(st.selectbox('Mission Pack',['Strike Force (2k)', 'Incursion (1k)', 'Combat Partol'], index=None, placeholder="Choose...")
        st.write("**Your Details**")
        # Extract the name from Discord metadata
        p1_name = st.text_input("Your Discord Name*", value=discord_name, key="p1_username", disabled=True)
        # 1. Allegiance Dropdown
        p1_all_df = p1_df_system_factions[p1_df_system_factions['short_name'] == 'AOS']
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
        p2_all_df = p2_df_system_factions[p2_df_system_factions['short_name'] == 'AOS']
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
                st.session_state.page = "AOS_scores"
                st.rerun()

    elif st.session_state.page == "AOS_scores":

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
                    p1_pri = st.number_input("Primary Score*", 0, 50, key="p1_p")
                    p1_sec = st.number_input("Battle Tactics Score*", 0, 30, key="p1_s")
                    #if st.toggle("Battle Ready?*", key="p1_br"):
                        #p1_br = 10
                    #else:
                        #p1_br = 0
                    if st.toggle("Slain Enemy General?*", key="p1_killed_warlord"):
                        p1_killed_warlord = True
                    else:
                        p1_killed_warlord = False
                    if st.toggle("Tabled Opponent?*", key="p1_tabled_opponent"):
                        p1_tabled_opponent = True
                    else:
                        p1_tabled_opponent = False
                with col4:
                    st.subheader(f"{p2_name}")
                    st.write(f"**{p2_fac}**")
                    st.write(f"{p2_sub}")
                    p2_pri = st.number_input("Primary Score*", 0, 50, key="p2_p")
                    p2_sec = st.number_input("Battle Tactics Score*", 0, 30, key="p2_s")
                    #if st.toggle("Battle Ready?*", key="p2_br"):
                        #p2_br = 10
                    #else:
                        #p2_br = 0
                    if st.toggle("Slain Enemy General?*", key="p2_killed_warlord"):
                        p2_killed_warlord = True
                    else:
                        p2_killed_warlord = False
                    if st.toggle("Tabled Opponent?*", key="p2_tabled_opponent"):
                        p2_tabled_opponent = True
                    else:
                        p2_tabled_opponent = False
                    

                # Use the form submit button to move to confirmation
                submit_scores = st.form_submit_button("Review Results")

                if submit_scores:
                    st.session_state.temp_scores = {
                        "p1_pri": p1_pri, "p1_sec": p1_sec, "p1_killed_warlord": p1_killed_warlord, "p1_tabled_opponent": p1_tabled_opponent,
                        "p2_pri": p2_pri, "p2_sec": p2_sec, "p2_killed_warlord": p2_killed_warlord, "p2_tabled_opponent": p2_tabled_opponent
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
            p1_total = scores['p1_pri'] + scores['p1_sec']
            p2_total = scores['p2_pri'] + scores['p2_sec']

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
                        f"\n\nBattle Formation: {setup['p1_sub']}"
                        f"\n\nPrimary: {scores['p1_pri']}"
                        f"\n\nSecondary: {scores['p1_sec']}")
            col_b.write(f"Name: **{setup['p2_name']}**"
                        f"\n\nFaction: {setup['p2_fac']}"
                        f"\n\nBattle Formation: {setup['p2_sub']}"
                        f"\n\nPrimary: {scores['p2_pri']}"
                        f"\n\nSecondary: {scores['p2_sec']}")

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
                        "p1_score_03": 0,
                        "p1_score_04": 0,
                        "p1_score_05": 0,
                        "p1_score_total": scores['p1_pri'] + scores['p1_sec'],
                        "p1_score_mar": p1_total - p2_total,
                        "player_2_id": clean_id(setup['p2_id']),
                        "player_2_name": setup['p2_name'],
                        "p2_faction_id": setup['p2_fac_id'],
                        "p2_score_01": scores['p2_pri'],
                        "p2_score_02": scores['p2_sec'],
                        "p2_score_03": 0,
                        "p2_score_04": 0,
                        "p2_score_05": 0,
                        "p2_score_total": scores['p2_pri'] + scores['p2_sec'],
                        "p2_score_mar": p2_total - p1_total,
                        "went_first_id": clean_id(setup['went_first_id']),
                        "winner_id": clean_id(winner_id),
                        "loser_id": clean_id(loser_id),
                        "attacker_id": clean_id(setup['attacker_id']),
                        "defender_id": clean_id(setup['defender_id']),
                        "is_draw": is_draw,
                        # "played_at": ,
                        "recorded_by":  setup['p1_id'],
                        "club_id": "ac85d0d1-24df-4b85-a4bd-0e5e944acd99",
                        "p1_killed_warlord": scores['p1_killed_warlord'],
                        "p2_killed_warlord": scores['p2_killed_warlord'],
                        "p1_tabled_opponent": scores['p1_tabled_opponent'],
                        "p2_tabled_opponent": scores['p2_tabled_opponent'],
                    }

                supabase.table("matches").insert(match_details).execute()

                st.success("Game posted to Supabase!")

                st.session_state.game_data = {}
                st.session_state.temp_scores = {}
                st.session_state.confirm_submit = False
                st.session_state.page = None  # Go back to home
                st.rerun()
                #st.session_state.selected_system = "AOS"
                #st.session_state.page = None
                #st.rerun()

            if c2.button("❌ No, Edit Scores", use_container_width=True):
                st.session_state.confirm_submit = False
                st.rerun()

    elif st.session_state.page == "KT":
        st.header("Kill Team Game")
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
        #game_size = st.selectbox('Game Size', ['Strike Force', 'Incursion', 'Other'], index=None,
                                 #placeholder="Choose...", key="game_s")
        # mission_pack = st.selectbox(st.selectbox('Mission Pack',['Strike Force (2k)', 'Incursion (1k)', 'Combat Partol'], index=None, placeholder="Choose...")
        st.write("**Your Details**")
        # Extract the name from Discord metadata
        p1_name = st.text_input("Your Discord Name*", value=discord_name, key="p1_username", disabled=True)
        # 1. Allegiance Dropdown
        p1_all_df = p1_df_system_factions[p1_df_system_factions['short_name'] == 'KT']
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
        # 3. Sub-Faction Dropdown
        if p1_fac:
            p1_sub_df = p1_fac_df[p1_fac_df['faction'] == p1_fac]
            p1_sub = st.selectbox("Your Kill Team", p1_sub_df['subfaction'].unique(), index=None,
                                  placeholder="Choose...", key="p1_sub_sel")
            
            # Logic for dynamic min/max
            if p1_sub:
                # Get the specific data for the selected subfaction
                selected_sub = p1_sub_df[p1_sub_df['subfaction'] == p1_sub].iloc[0]
                min_val = int(selected_sub['kt_min_op'])
                max_val = int(selected_sub['kt_max_op'])
                
                # Disable if min and max are the same
                is_disabled = (min_val == max_val)
                
                p1_op_count = st.number_input(
                    "Number of Operatives?*", 
                    min_value=min_val, 
                    max_value=max_val, 
                    value=min_val, # Default to min
                    disabled=is_disabled,
                    key="p1_op_count"
                )
            else:
                st.number_input("Number of Operatives?*", disabled=True, key="p1_op_count_placeholder")
        else:
            p1_sub = st.selectbox("Your Kill Team", [], disabled=True)
            st.number_input("Number of Operatives?*", disabled=True, key="p1_op_count_init")

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
        p2_all_df = p2_df_system_factions[p2_df_system_factions['short_name'] == 'KT']
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
        # 3. Sub-Faction Dropdown
        if p2_fac:
            p2_sub_df = p2_fac_df[p2_fac_df['faction'] == p2_fac]
            p2_sub = st.selectbox("Opponents Kill Team", p2_sub_df['subfaction'].unique(), index=None,
                                  placeholder="Choose...", key="p2_sub_sel")
            
            # Logic for dynamic min/max
            if p2_sub:
                # Get the specific data for the selected subfaction
                selected_sub = p2_sub_df[p2_sub_df['subfaction'] == p2_sub].iloc[0]
                min_val = int(selected_sub['kt_min_op'])
                max_val = int(selected_sub['kt_max_op'])
                
                # Disable if min and max are the same
                is_disabled = (min_val == max_val)
                
                p2_op_count = st.number_input(
                    "Number of Operatives?*", 
                    min_value=min_val, 
                    max_value=max_val, 
                    value=min_val, # Default to min
                    disabled=is_disabled,
                    key="p2_op_count"
                )
            else:
                st.number_input("Number of Operatives?*", disabled=True, key="p2_op_count_placeholder")
        else:
            p2_sub = st.selectbox("Opponents Kill Team", [], disabled=True)
            st.number_input("Number of Operatives?*", disabled=True, key="p2_op_count_init")

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
                    "p1_op_count": p1_op_count,
                    "p2_op_count": p2_op_count,
                    "attacker_id": attacker_id,
                    "defender_id": defender_id,
                    "went_first_id": went_first_id,
                    "game_size": "Kill Team"
                }

                # FIX 2: Switch the page and rerun
                st.session_state.page = "KT_scores"
                st.rerun()

    elif st.session_state.page == "KT_scores":

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
        p1_op_count = st.session_state.game_data.get("p1_op_count", None)

        p2_id = st.session_state.game_data.get("p2_id", None)
        p2_name = st.session_state.game_data.get("p2_name", None)
        p2_fac_id = st.session_state.game_data.get("p2_fac_id", None)
        p2_all = st.session_state.game_data.get("p2_all", None)
        p2_fac = st.session_state.game_data.get("p2_fac", None)
        p2_sub = st.session_state.game_data.get("p2_sub", None)
        p2_op_count = st.session_state.game_data.get("p2_op_count", None)
        
        # 1. The Data Entry Form
        if not st.session_state.confirm_submit:
            
            # The lookup table based on your image
            # Format: {starting_count: [Grade 1 threshold, Grade 2, Grade 3, Grade 4, Grade 5]}
            KILL_GRADE_MAPPING = {
                5:  [1, 2, 3, 4, 5],
                6:  [1, 2, 4, 5, 6],
                7:  [1, 3, 4, 6, 7],
                8:  [2, 3, 5, 6, 8],
                9:  [2, 4, 5, 7, 9],
                10: [2, 4, 6, 8, 10],
                11: [2, 4, 7, 9, 11],
                12: [2, 5, 7, 10, 12],
                13: [3, 5, 8, 10, 13],
                14: [3, 6, 8, 11, 14]
            }
            
            def calculate_kill_grade(kills, enemy_starting_count):
                """Returns the Kill Grade (0-5) based on kills and enemy starting size."""
                if enemy_starting_count not in KILL_GRADE_MAPPING or kills == 0:
                    return 0
                
                thresholds = KILL_GRADE_MAPPING[enemy_starting_count]
                grade = 0
                # Iterate through thresholds; index + 1 is the grade
                for i, threshold in enumerate(thresholds):
                    if kills >= threshold:
                        grade = i + 1
                return grade
            
            with st.form("score_submission_form"):
                col3, col4 = st.columns(2)
                with col3:
                    st.subheader(f"{p1_name}")
                    st.write(f"**{p1_fac}**")
                    st.write(f"{p1_sub}")
                    p1_pri = st.number_input("Crit Op Score*", 0, 6, key="p1_p")
                    p1_sec = st.number_input("Tac Op Score*", 0, 6, key="p1_s")
                    p1_kills = st.number_input("Operatives Killed*", 0, p2_op_count, key="p1_kills")
                    #if st.toggle("Battle Ready?*", key="p1_br"):
                        #p1_br = 2
                    #else:
                        #p1_br = 0
                    if st.toggle("Slain Enemy Leader?*", key="p1_killed_warlord"):
                        p1_killed_warlord = True
                    else:
                        p1_killed_warlord = False
                    if st.toggle("Tabled Opponent?*", key="p1_tabled_opponent"):
                        p1_tabled_opponent = True
                    else:
                        p1_tabled_opponent = False
                with col4:
                    st.subheader(f"{p2_name}")
                    st.write(f"**{p2_fac}**")
                    st.write(f"{p2_sub}")
                    p2_pri = st.number_input("Crit Op Score*", 0, 6, key="p2_p")
                    p2_sec = st.number_input("Tac Op Score*", 0, 6, key="p2_s")
                    p2_kills = st.number_input("Operatives Killed?*", 0, p1_op_count, key="p2_kills")
                    #if st.toggle("Battle Ready?*", key="p2_br"):
                        #p2_br = 2
                    #else:
                        #p2_br = 0
                    if st.toggle("Slain Enemy Leader?*", key="p2_killed_warlord"):
                        p2_killed_warlord = True
                    else:
                        p2_killed_warlord = False
                    if st.toggle("Tabled Opponent?*", key="p2_tabled_opponent"):
                        p2_tabled_opponent = True
                    else:
                        p2_tabled_opponent = False
                    

                # Use the form submit button to move to confirmation
                submit_scores = st.form_submit_button("Review Results")

                if submit_scores:
                    
                    p1_kill_grade = calculate_kill_grade(p1_kills, p2_op_count)
                    p2_kill_grade = calculate_kill_grade(p2_kills, p1_op_count)
                    
                    st.session_state.temp_scores = {
                        "p1_pri": p1_pri, "p1_sec": p1_sec, "p1_kills": p1_kills, "p1_kill_grade": p1_kill_grade, "p1_killed_warlord": p1_killed_warlord, "p1_tabled_opponent": p1_tabled_opponent,
                         "p2_pri": p2_pri, "p2_sec": p2_sec, "p2_kills": p2_kills, "p2_kill_grade": p2_kill_grade, "p2_killed_warlord": p2_killed_warlord, "p2_tabled_opponent": p2_tabled_opponent
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
            p1_total = scores['p1_pri'] + scores['p1_sec'] + scores['p1_kill_grade']
            p2_total = scores['p2_pri'] + scores['p2_sec'] + scores['p2_kill_grade']

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
                        f"\n\nKill Team: {setup['p1_sub']}"
                        f"\n\nCrit Op: {scores['p1_pri']}"
                        f"\n\nTac Op: {scores['p1_sec']}"
                        f"\n\nKill Op: {scores['p1_kill_grade']}")
                        
            col_b.write(f"Name: **{setup['p2_name']}**"
                        f"\n\nFaction: {setup['p2_fac']}"
                        f"\n\nKill Team: {setup['p2_sub']}"
                        f"\n\nCrit Op: {scores['p2_pri']}"
                        f"\n\nTac Op: {scores['p2_sec']}"
                        f"\n\nKill Op: {scores['p2_kill_grade']}")

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
                        "p1_score_03": 0,
                        "p1_score_04": scores['p1_kill_grade'],
                        "p1_score_05": scores['p1_kills'],
                        "p1_score_total": scores['p1_pri'] + scores['p1_sec'] + scores['p1_kill_grade'],
                        "p1_score_mar": p1_total - p2_total,
                        "player_2_id": clean_id(setup['p2_id']),
                        "player_2_name": setup['p2_name'],
                        "p2_faction_id": setup['p2_fac_id'],
                        "p2_score_01": scores['p2_pri'],
                        "p2_score_02": scores['p2_sec'],
                        "p2_score_03": 0,
                        "p2_score_04": scores['p2_kill_grade'],
                        "p2_score_05": scores['p2_kills'],
                        "p2_score_total": scores['p2_pri'] + scores['p2_sec'] + scores['p2_kill_grade'],
                        "p2_score_mar": p2_total - p1_total,
                        "went_first_id": clean_id(setup['went_first_id']),
                        "winner_id": clean_id(winner_id),
                        "loser_id": clean_id(loser_id),
                        "attacker_id": clean_id(setup['attacker_id']),
                        "defender_id": clean_id(setup['defender_id']),
                        "is_draw": is_draw,
                        # "played_at": ,
                        "recorded_by":  setup['p1_id'],
                        "club_id": "ac85d0d1-24df-4b85-a4bd-0e5e944acd99",
                        "p1_killed_warlord": scores['p1_killed_warlord'],
                        "p2_killed_warlord": scores['p2_killed_warlord'],
                        "p1_tabled_opponent": scores['p1_tabled_opponent'],
                        "p2_tabled_opponent": scores['p2_tabled_opponent'],
                    }

                supabase.table("matches").insert(match_details).execute()

                st.success("Game posted to Supabase!")

                st.session_state.game_data = {}
                st.session_state.temp_scores = {}
                st.session_state.confirm_submit = False
                st.session_state.page = None  # Go back to home
                st.rerun()
                #st.session_state.selected_system = "40K"
                #st.session_state.page = None
                #st.rerun()

            if c2.button("❌ No, Edit Scores", use_container_width=True):
                st.session_state.confirm_submit = False
                st.rerun()

    elif st.session_state.page == "MESBG":
        st.header("Middle Earth: Strategy Battle Game")
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
        #game_size = st.selectbox('Game Size', ['1000', '800', 'Other'], index=None,
                                 #placeholder="Choose...", key="game_s")
                                
        game_size = st.number_input("Game Size", 0, 1500, key="game_s")
        # mission_pack = st.selectbox(st.selectbox('Mission Pack',['Strike Force (2k)', 'Incursion (1k)', 'Combat Partol'], index=None, placeholder="Choose...")
        st.write("**Your Details**")
        # Extract the name from Discord metadata
        p1_name = st.text_input("Your Discord Name*", value=discord_name, key="p1_username", disabled=True)
        # 1. Allegiance Dropdown
        p1_all_df = p1_df_system_factions[p1_df_system_factions['short_name'] == 'MESBG']
        p1_all = st.selectbox("Your Allegiance", p1_all_df['allegiance'].unique(), index=None,
                              placeholder="Choose...", key="p1_all_sel")
        # 2. Faction Dropdown (MUST use filtered options)
        if p1_all:
            # We filter the dataframe here
            p1_sub_df = p1_all_df[p1_all_df['allegiance'] == p1_all]
            # We use faction_df to get the unique names for the options
            p1_sub = st.selectbox("Your Army List", p1_sub_df['subfaction'].unique(), index=None,
                                  placeholder="Choose...", key="p1_sub_sel")
        else:
            p1_sub = st.selectbox("Your Army List", [], disabled=True)

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
        p2_all_df = p2_df_system_factions[p2_df_system_factions['short_name'] == 'MESBG']
        p2_all = st.selectbox("Opponents Allegiance", p2_all_df['allegiance'].unique(), index=None,
                              placeholder="Choose...", key="p2_all_sel")
        # 2. Faction Dropdown (MUST use filtered options)
        if p2_all:
            # We filter the dataframe here
            p2_sub_df = p2_all_df[p2_all_df['allegiance'] == p2_all]
            # We use faction_df to get the unique names for the options
            p2_sub = st.selectbox("Opponents Army List", p2_sub_df['subfaction'].unique(), index=None,
                                  placeholder="Choose...", key="p2_sub_sel")
        else:
            p2_sub = st.selectbox("Opponents Army List", [], disabled=True)

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
            #factions_selected = p1_fac and p2_fac
            sub_factions_selected = p1_sub and p2_sub
            actual_p2_id = p2_id if (p2_id and p2_id != p2_name) else None

            if not names_entered:
                st.error("❌ Both player names are mandatory.")
            elif not sub_factions_selected:
                st.error("❌ Both players must select an Allegiance and Army List.")
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
                    #"p1_fac": p1_fac,
                    "p1_sub": p1_sub,
                    "p2_id": actual_p2_id,
                    "p2_name": p2_name,
                    "p1_all": p1_all,
                    #"p2_fac": p2_fac,
                    "p2_sub": p2_sub,
                    "p1_fac_id": p1_row['faction_id'],
                    "p2_fac_id": p2_row['faction_id'],
                    "attacker_id": attacker_id,
                    "defender_id": defender_id,
                    "went_first_id": went_first_id,
                    "game_size": game_size
                }

                # FIX 2: Switch the page and rerun
                st.session_state.page = "MESBG_scores"
                st.rerun()

    elif st.session_state.page == "MESBG_scores":

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
        #p1_fac = st.session_state.game_data.get("p1_fac", None)
        p1_sub = st.session_state.game_data.get("p1_sub", None)

        p2_id = st.session_state.game_data.get("p2_id", None)
        p2_name = st.session_state.game_data.get("p2_name", None)
        p2_fac_id = st.session_state.game_data.get("p2_fac_id", None)
        p2_all = st.session_state.game_data.get("p2_all", None)
        #p2_fac = st.session_state.game_data.get("p2_fac", None)
        p2_sub = st.session_state.game_data.get("p2_sub", None)

        # 1. The Data Entry Form
        if not st.session_state.confirm_submit:
            with st.form("score_submission_form"):
                col3, col4 = st.columns(2)
                with col3:
                    st.subheader(f"{p1_name}")
                    #st.write(f"**{p1_fac}**")
                    st.write(f"{p1_sub}")
                    p1_pri = st.number_input("Total Score*", 0, 20, key="p1_p")
                    #p1_sec = st.number_input("Secondary Score*", 0, 45, key="p1_s")
                    #if st.toggle("Battle Ready?*", key="p1_br"):
                        #p1_br = 10
                    #else:
                        #p1_br = 0
                    if st.toggle("Slain Enemy Warlord?*", key="p1_killed_warlord"):
                        p1_killed_warlord = True
                    else:
                        p1_killed_warlord = False
                    if st.toggle("Tabled Opponent?*", key="p1_tabled_opponent"):
                        p1_tabled_opponent = True
                    else:
                        p1_tabled_opponent = False
                with col4:
                    st.subheader(f"{p2_name}")
                    #st.write(f"**{p2_fac}**")
                    st.write(f"{p2_sub}")
                    p2_pri = st.number_input("Total Score*", 0, 20, key="p2_p")
                    #p2_sec = st.number_input("Secondary Score*", 0, 45, key="p2_s")
                    #if st.toggle("Battle Ready?*", key="p2_br"):
                        #p2_br = 10
                    #else:
                        #p2_br = 0
                    if st.toggle("Slain Enemy Warlord?*", key="p2_killed_warlord"):
                        p2_killed_warlord = True
                    else:
                        p2_killed_warlord = False
                    if st.toggle("Tabled Opponent?*", key="p2_tabled_opponent"):
                        p2_tabled_opponent = True
                    else:
                        p2_tabled_opponent = False
                    

                # Use the form submit button to move to confirmation
                submit_scores = st.form_submit_button("Review Results")

                if submit_scores:
                    st.session_state.temp_scores = {
                        "p1_pri": p1_pri, "p1_killed_warlord": p1_killed_warlord, "p1_tabled_opponent": p1_tabled_opponent,
                        "p2_pri": p2_pri, "p2_killed_warlord": p2_killed_warlord, "p2_tabled_opponent": p2_tabled_opponent
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
            p1_total = scores['p1_pri']
            p2_total = scores['p2_pri']

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
                        #f"\n\nFaction: {setup['p1_fac']}"
                        f"\n\nTotal Score: {setup['p1_sub']}"
                        f"\n\nTotal Score: {scores['p1_pri']}")
                        #f"\n\nSecondary: {scores['p1_sec']}"
                        #f"\n\nBattle Ready: {scores['p1_br']}")
            col_b.write(f"Name: **{setup['p2_name']}**"
                        #f"\n\nFaction: {setup['p2_fac']}"
                        f"\n\nArmy List: {setup['p2_sub']}"
                        f"\n\nTotal Score: {scores['p2_pri']}")
                        #f"\n\nSecondary: {scores['p2_sec']}"
                        #f"\n\nBattle Ready: {scores['p2_br']}")

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
                        "p1_score_02": 0,
                        "p1_score_03": 0,
                        "p1_score_04": 0,
                        "p1_score_05": 0,
                        "p1_score_total": scores['p1_pri'],
                        "p1_score_mar": p1_total - p2_total,
                        "player_2_id": clean_id(setup['p2_id']),
                        "player_2_name": setup['p2_name'],
                        "p2_faction_id": setup['p2_fac_id'],
                        "p2_score_01": scores['p2_pri'],
                        "p2_score_02": 0,
                        "p2_score_03": 0,
                        "p2_score_04": 0,
                        "p2_score_05": 0,
                        "p2_score_total": scores['p2_pri'],
                        "p2_score_mar": p2_total - p1_total,
                        "went_first_id": clean_id(setup['went_first_id']),
                        "winner_id": clean_id(winner_id),
                        "loser_id": clean_id(loser_id),
                        "attacker_id": clean_id(setup['attacker_id']),
                        "defender_id": clean_id(setup['defender_id']),
                        "is_draw": is_draw,
                        # "played_at": ,
                        "recorded_by":  setup['p1_id'],
                        "club_id": "ac85d0d1-24df-4b85-a4bd-0e5e944acd99",
                        "p1_killed_warlord": scores['p1_killed_warlord'],
                        "p2_killed_warlord": scores['p2_killed_warlord'],
                        "p1_tabled_opponent": scores['p1_tabled_opponent'],
                        "p2_tabled_opponent": scores['p2_tabled_opponent'],
                    }

                supabase.table("matches").insert(match_details).execute()

                st.success("Game posted to Supabase!")

                st.session_state.game_data = {}
                st.session_state.temp_scores = {}
                st.session_state.confirm_submit = False
                # st.session_state.page = None  # Go back to home
                # st.rerun()
                st.session_state.selected_system = "MESBG"
                st.session_state.page = None
                st.rerun()

            if c2.button("❌ No, Edit Scores", use_container_width=True):
                st.session_state.confirm_submit = False
                st.rerun()

    elif st.session_state.page == "BGC_League":
        st.header("BGC League")
        st.divider()

    elif st.session_state.page == "BGC_Ladder":
        st.header("BGC Ladder")
        st.divider()    

    elif st.session_state.page == "Event_Results":
        st.header("Event Results")
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

            st.write("### 🛡️ Sector Commanders")
            
            # 1. Unpivot/Melt to standardise columns (Now including Factions)
            p1 = df[['display_p1_name', 'p1_allegiance', 'p1_faction', 'p1_score_total']].rename(
                columns={'display_p1_name': 'player', 'p1_allegiance': 'allg', 'p1_faction': 'faction', 'p1_score_total': 'score'}
            )
            p2 = df[['display_p2_name', 'p2_allegiance', 'p2_faction', 'p2_score_total']].rename(
                columns={'display_p2_name': 'player', 'p2_allegiance': 'allg', 'p2_faction': 'faction', 'p2_score_total': 'score'}
            )
            all_perf = pd.concat([p1, p2])
            
            # 2. Aggregate stats
            # We group by player and allegiance, but take the 'first' faction found 
            # (or use .mode() if they played multiple, but 'first' is usually safe for an event)
            commander_stats = all_perf.groupby(['allg', 'player']).agg(
                Total_VP=('score', 'sum'),
                Faction=('faction', 'first') 
            ).reset_index()
            
            # 3. Create columns for each Allegiance
            # allg_list = sorted(all_perf['allg'].unique())
            # This removes any None values before trying to sort them
            allg_list = sorted([a for a in all_perf['allg'].unique() if a is not None])

            cols = st.columns(len(allg_list))
            
            medals = ["🥇 Gold", "🥈 Silver", "🥉 Bronze"]
            
            for i, current_allg in enumerate(allg_list):
                with cols[i]:
                    st.subheader(f"🚩 {current_allg}")
                    
                    # Get top 3 for this specific allegiance
                    top_3 = commander_stats[commander_stats['allg'] == current_allg].sort_values('Total_VP', ascending=False).head(3)
                    
                    # Loop through top 3 and display metrics
                    for rank, (_, row) in enumerate(top_3.iterrows()):
                        # We put the Faction in the Label to make it look professional
                        st.metric(
                            label=f"{medals[rank]} | {row['Faction']}", 
                            value=row['player'], 
                            delta=f"{int(row['Total_VP'])} VP",
                            delta_color="off"
                        )
            
            st.divider()


        
            # --- NARRATIVE AWARDS ---
            st.write("### 🕵️ Intelligence Reports")
            n1, n2, n3 = st.columns(3)
        
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

        def show_faction_win_rates(df):
            st.subheader(f"📊 {selected_event} Faction Meta")
            p1_data = df[['p1_faction', 'p1_score_total', 'p2_score_total']].copy()
            p1_data.columns = ['faction', 'score', 'opp_score']
            p2_data = df[['p2_faction', 'p2_score_total', 'p1_score_total']].copy()
            p2_data.columns = ['faction', 'score', 'opp_score']
            combined = pd.concat([p1_data, p2_data])
            combined['is_win'] = combined['score'] > combined['opp_score']
            stats = combined.groupby('faction').agg(Total=('faction', 'count'), Wins=('is_win', 'sum')).reset_index()
            stats['Win_Rate'] = (stats['Wins'] / stats['Total'] * 100).round(1)
            stats = stats.sort_values(by='Win_Rate', ascending=False)
            fig = px.bar(stats, x='faction', y='Win_Rate', text='Win_Rate', color='Win_Rate', color_continuous_scale='RdYlGn', height=400)
            fig.update_layout(yaxis_range=[0, 110])
            st.plotly_chart(fig, use_container_width=True)

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
        event_res = supabase.table("match_results").select("event_name").eq("event_status", "Finished").execute()
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
                    show_faction_win_rates(event_df)
                    st.divider()
                    show_faction_turnout(event_df)
                    st.divider()
                    show_allegiance_points_pie(event_df)
        
                else:
                    st.warning("No valid match data found after filtering out Dropped/Unplayed results.")
        else:
            st.info("No events found in the database.")

    elif st.session_state.page == "Event_Manager":
        st.header("Event Manager")
        st.divider()
        
        def render_event_manager_page(supabase):
            st.title("🏆 Events Manager Dashboard")
        
            # 1. Fetch Core Setup Lists for Dropdowns
            try:
                game_systems = supabase.table("game_systems").select("id, name, edition").eq("is_active", True).execute().data
                events_list = supabase.table("events").select("*").execute().data
                all_profiles = supabase.table("profiles").select("id, username, full_name").execute().data
                event_types_data = supabase.table("event_type").select("*").execute().data
            except Exception as e:
                st.error(f"Initialization error fetching lookup data: {e}")
                return
        
            # 2. Main Layout Split: Active Event Context Selection at the Top
            st.markdown("### 🎯 Active Event Context")
            if events_list:
                event_map = {f"{e['name']} ({e['status']})": e for e in events_list}
                
                # Keep track of active event index across form submissions
                if "active_event_index" not in st.session_state:
                    st.session_state.active_event_index = 0
                    
                selected_event_name = st.selectbox(
                    "Choose Event to Manage:", 
                    list(event_map.keys()),
                    index=st.session_state.active_event_index
                )
                active_event = event_map[selected_event_name]
                
                # Sync the chosen list index back to state
                st.session_state.active_event_index = list(event_map.keys()).index(selected_event_name)
            else:
                active_event = None
                st.warning("No events found. Please use 'Create Event' below to add one first.")
        
            # 3. Horizontal Management Tabs (Keeps sidebar clean for your app navigation buttons)
            tab1, tab2, tab3, tab4 = st.tabs([
                "1️⃣ Create Event", 
                "2️⃣ Manage Event", 
                "3️⃣ Manage Players", 
                "4️⃣ Manage Pairings"
            ])
        
            # =========================================================================
            # TAB 1: CREATE EVENT
            # =========================================================================
            with tab1:
                st.subheader("Create New Event")
                with st.form("create_event_form", clear_on_submit=True):
                    # Strip trailing spaces to prevent sneaky duplicate variations
                    name = st.text_input("Event Name*").strip()
                    
                    if event_types_data:
                        type_options = [row["event_type"] for row in event_types_data]
                        event_type = st.selectbox("Event Type*", type_options)
                    else:
                        event_type = st.text_input("Event Type* (Fallback - No types found in DB)", value="Swiss")
                        
                    status = st.selectbox("Initial Status", ["upcoming", "ongoing"])
        
                    col1, col2 = st.columns(2)
                    with col1:
                        start_date = st.date_input("Start Date", value=pd.Timestamp.now().date())
                    with col2:
                        end_date = st.date_input("End Date", value=pd.Timestamp.now().date())
                        
                    col3, col4, col5 = st.columns(3)
                    with col3:
                        min_players = st.number_input("Min Players", min_value=0, value=4)
                    with col4:
                        max_players = st.number_input("Max Players", min_value=2, value=128)
                    with col5:
                        # Ladders default to 1 open round, Swiss defaults to 3 rounds
                        default_rounds = 1 if str(event_type).lower() == "ladder" else 3
                        rounds = st.number_input("Rounds", min_value=1, value=default_rounds)
                        
                    gs_map = {f"{gs['name']} ({gs['edition']})": gs['id'] for gs in game_systems}
                    selected_gs = st.selectbox("Game System", list(gs_map.keys())) if gs_map else None
                    
                    submitted = st.form_submit_button("Create Event")
                    if submitted:
                        # 🛡️ PROTECTION: Compile existing names in lower-case
                        existing_names = [e["name"].lower().strip() for e in events_list] if events_list else []
                        
                        if not name or not event_type:
                            st.error("Event Name and Event Type are required.")
                        elif name.lower() in existing_names:
                            # ❌ BLOCK DUPLICATE
                            st.error(f"🚫 An event named '{name}' already exists. Please choose a unique name.")
                        else:
                            new_event = {
                                "name": name,
                                "event_type": event_type,
                                "status": status,
                                "start_date": start_date.isoformat(),
                                "end_date": end_date.isoformat(),
                                "min_players": min_players,
                                "max_players": max_players,
                                "rounds": rounds,
                                "created_by": st.session_state.user.id,
                                "game_system_id": gs_map[selected_gs] if selected_gs else None
                            }
                            try:
                                # 1. Insert Event Meta Entry
                                event_res = supabase.table("events").insert(new_event).execute()
                                
                                if event_res.data:
                                    created_event_id = event_res.data[0]['id']
                                    
                                    # 2. Automated Initialization for Ladder Events
                                    if str(event_type).lower() == "ladder":
                                        ladder_round_payload = {
                                            "event_id": created_event_id,
                                            "round_number": 1,
                                            "is_active": True,
                                            "deployment_type": "Open Challenge Map"
                                        }
                                        supabase.table("event_rounds").insert(ladder_round_payload).execute()
                                
                                announcement = f"🎮 **New Event Created!** 🎮\n**{name}** ({event_type}) has been added! Sign ups are now open."
                                post_to_discord_webhook(announcement)
                                st.success(f"🎉 Event '{name}' created successfully!")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error saving event: {e}")
        
            # =========================================================================
            # TAB 2: MANAGE EVENT
            # =========================================================================
            with tab2:
                if not active_event:
                    st.info("Please create an event first.")
                else:
                    st.subheader(f"Editing: {active_event['name']}")
                    with st.form("update_event_form"):
                        u_name = st.text_input("Event Name", value=active_event["name"]).strip()
                        
                        if event_types_data:
                            type_options = [row["event_type"] for row in event_types_data]
                            current_type_idx = type_options.index(active_event["event_type"]) if active_event["event_type"] in type_options else 0
                            u_type = st.selectbox("Event Type", type_options, index=current_type_idx)
                        else:
                            u_type = st.text_input("Event Type", value=active_event["event_type"])
                            
                        status_list = ["upcoming", "ongoing", "completed", "cancelled"]
                        u_status = st.selectbox("Status", status_list, index=status_list.index(active_event["status"]) if active_event["status"] in status_list else 0)
                        
                        s_date = pd.to_datetime(active_event["start_date"]).date() if active_event["start_date"] else pd.Timestamp.now().date()
                        e_date = pd.to_datetime(active_event["end_date"]).date() if active_event["end_date"] else pd.Timestamp.now().date()
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            u_start_date = st.date_input("Start Date", value=s_date)
                        with col2:
                            u_end_date = st.date_input("End Date", value=e_date)
                            
                        col3, col4, col5 = st.columns(3)
                        with col3:
                            u_min_players = st.number_input("Min Players", min_value=0, value=int(active_event["min_players"] or 0))
                        with col4:
                            u_max_players = st.number_input("Max Players", min_value=1, value=int(active_event["max_players"] or 9999))
                        with col5:
                            # 🎯 LADDER RULE FORCE: Ladders always operate out of 1 single continuous round
                            if str(u_type).lower() == "ladder":
                                u_rounds = st.number_input("Rounds", min_value=1, value=1, disabled=True, help="Ladders use a single persistent round for open tracking.")
                            else:
                                u_rounds = st.number_input("Rounds", min_value=0, value=int(active_event["rounds"] or 0))
                            
                        update_submitted = st.form_submit_button("Save Changes")
                        if update_submitted:
                            # 🛡️ PROTECTION: Verify name isn't clashing with a separate event name
                            other_events_names = [
                                e["name"].lower().strip() for e in events_list 
                                if e["id"] != active_event["id"]
                            ] if events_list else []
                            
                            if not u_name:
                                st.error("Event Name cannot be empty.")
                            elif u_name.lower() in other_events_names:
                                st.error(f"🚫 Another event is already using the name '{u_name}'.")
                            else:
                                updated_data = {
                                    "name": u_name, "event_type": u_type, "status": u_status,
                                    "start_date": u_start_date.isoformat(), "end_date": u_end_date.isoformat(),
                                    "min_players": u_min_players, "max_players": u_max_players, "rounds": u_rounds
                                }
                                try:
                                    supabase.table("events").update(updated_data).eq("id", active_event["id"]).execute()
                                    
                                    # Safe-catch deployment validation for event migrations
                                    if str(u_type).lower() == "ladder":
                                        # Check if a round entry already exists to avoid duplicate primary key crashes
                                        round_check = supabase.table("event_rounds").select("id").eq("event_id", active_event["id"]).eq("round_number", 1).execute()
                                        if not round_check.data:
                                            supabase.table("event_rounds").insert({
                                                "event_id": active_event["id"],
                                                "round_number": 1,
                                                "is_active": True,
                                                "deployment_type": "Open Challenge Map"
                                            }).execute()
                                            
                                    st.success("💾 Changes saved successfully!")
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating event: {e}")

            # =========================================================================
            # TAB 3: MANAGE PLAYERS
            # =========================================================================
            with tab3:
                if not active_event:
                    st.info("Select or create an event context first.")
                else:
                    is_ladder = str(active_event.get("event_type", "")).lower() == "ladder"
                    st.subheader(f"Roster for {active_event['name']}")
                    
                    # Fetch participants, sorted by rank for ladders, or by name for swiss
                    if is_ladder:
                        parts = supabase.table("event_participants").select("*").eq("event_id", active_event["id"]).order("current_rank", nullsfirst=False).execute().data
                    else:
                        parts = supabase.table("event_participants").select("*").eq("event_id", active_event["id"]).order("player_name").execute().data
                    
                    if parts:
                        # 🎯 LADDER VISUAL ANCHORS: Split out players into categories
                        if is_ladder:
                            st.caption("🏆 **Active Sector Ladder**")
                        
                        for p in parts:
                            col_name, col_status, col_del = st.columns([3, 2, 1])
                            
                            # Customise name display based on the active event mechanics
                            if is_ladder:
                                rank_val = f"Rank {p['current_rank']}" if p.get('current_rank') else "Entry Pool (Unranked)"
                                streak_val = f"🔥 {p.get('current_win_streak', 0)}" if p.get('current_win_streak', 0) > 0 else ""
                                col_name.write(f"👤 **{p['player_name'] or 'Unknown'}**  \n`{rank_val}` {streak_val}")
                            else:
                                col_name.write(f"👤 **{p['player_name'] or 'Unknown'}** (Score: {p['current_points']})")
                            
                            status_options = ["Checked In", "Registered", "Dropped"]
                            current_idx = status_options.index(p["status"]) if p["status"] in status_options else 0
                            new_status = col_status.selectbox(
                                "Status Setup", status_options, index=current_idx, key=f"status_widget_{p['id']}", label_visibility="collapsed"
                            )
                            
                            if new_status != p["status"]:
                                supabase.table("event_participants").update({"status": new_status}).eq("id", p["id"]).execute()
                                st.rerun()
                                
                            if col_del.button("❌", key=f"del_player_{p['id']}"):
                                supabase.table("event_participants").delete().eq("id", p["id"]).execute()
                                st.rerun()
                    else:
                        st.info("No players registered for this event yet.")
                        
                    st.markdown("---")
                    st.write("➕ **Register Profile to Event**")
                    profile_map = {f"{p['full_name']} (@{p['username']})" : p for p in all_profiles if p.get('full_name')}
                    
                    if profile_map:
                        with st.form("add_player_form"):
                            target_profile_str = st.selectbox("Select Profile System User", list(profile_map.keys()))
                            custom_name = st.text_input("Override Player Display Name (Optional)")
                            
                            add_submitted = st.form_submit_button("Add Player to Roster")
                            if add_submitted and target_profile_str:
                                chosen_p = profile_map[target_profile_str]
                                
                                # Build entry payload explicitly matching your rules
                                new_part = {
                                    "event_id": active_event["id"],
                                    "player_id": chosen_p["id"],
                                    "player_name": custom_name if custom_name else chosen_p["full_name"],
                                    "status": "Checked In",
                                    "current_rank": None,        # Explicitly forces open entry starting pool status
                                    "current_win_streak": 0,
                                    "days_at_rank": 1
                                }
                                try:
                                    supabase.table("event_participants").insert(new_part).execute()
                                    st.success(f"Added {new_part['player_name']} to the Entry Pool!")
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error("Unable to add player. Check if they are already registered.")
                    else:
                        st.warning("No global system profiles found with complete full names.")

        
        #     # =========================================================================
        #     # TAB 4: MANAGE PAIRINGS
        #     # =========================================================================
        #     with tab4:
        #         if not active_event:
        #             st.info("Select or create an event context first.")
        #         else:
        #             st.subheader("Pairings & Match Slip Entry")
        #             rounds_data = supabase.table("event_rounds").select("*").eq("event_id", active_event["id"]).order("round_number").execute().data
                    
        #             if not rounds_data:
        #                 if st.button("🏁 Initialize Round 1 Setup"):
        #                     try:
        #                         supabase.table("event_rounds").insert({"event_id": active_event["id"], "round_number": 1, "is_active": True}).execute()
        #                         st.success("Round 1 Initialised!")
        #                         st.rerun()
        #                     except Exception as e:
        #                         st.error(f"Error initiating rounds: {e}")
        #             else:
        #                 round_map = {f"Round {r['round_number']} {'(Active)' if r['is_active'] else ''}": r for r in rounds_data}
        #                 selected_round_str = st.selectbox("Select Round Matrix:", list(round_map.keys()))
        #                 active_round = round_map[selected_round_str]
                        
        #                 pairings = supabase.table("event_pairings").select("*").eq("round_id", active_round["id"]).order("table_number").execute().data
                        
        #                 if pairings:
        #                     st.write("### Active Match Slips")
        #                     prof_names = {p["id"]: (p["full_name"] or p["username"]) for p in all_profiles}
                            
        #                     for pair in pairings:
        #                         p1_name = prof_names.get(pair["player_1_id"], "Unknown Player 1")
        #                         p2_name = prof_names.get(pair["player_2_id"], "Bye / Ghost Player")
                                
        #                         with st.expander(f"🎲 Table {pair['table_number']}: {p1_name} vs {p2_name} {'✅ Logged' if pair['is_completed'] else '⏳ Pending'}"):
        #                             with st.form(f"match_slip_form_{pair['id']}"):
        #                                 col_p1, col_p2 = st.columns(2)
        #                                 p1_score = col_p1.number_input(f"{p1_name} Score", min_value=0, value=0, key=f"p1_s_{pair['id']}")
        #                                 p2_score = col_p2.number_input(f"{p2_name} Score", min_value=0, value=0, key=f"p2_s_{pair['id']}")
                                        
        #                                 is_draw = p1_score == p2_score
        #                                 w_id = pair["player_1_id"] if p1_score > p2_score else (pair["player_2_id"] if p2_score > p1_score else None)
        #                                 l_id = pair["player_2_id"] if p1_score > p2_score else (pair["player_1_id"] if p2_score > p1_score else None)
                                        
        #                                 # FIX: Changed from st.form_submit_with_button to st.form_submit_button
        #                                 if st.form_submit_button("Verify & Lock Match Scores"):
        #                                     try:
        #                                         supabase.table("event_pairings").update({"is_completed": True}).eq("id", pair["id"]).execute()
                                                
        #                                         match_payload = {
        #                                             "event_id": active_event["id"], "round_id": active_round["id"],
        #                                             "game_system_id": active_event.get("game_system_id"),
        #                                             "player_1_id": pair["player_1_id"], "p1_score_total": p1_score,
        #                                             "player_2_id": pair["player_2_id"], "p2_score_total": p2_score,
        #                                             "winner_id": w_id, "loser_id": l_id, "is_draw": is_draw, "status": "Logged"
        #                                         }
        #                                         supabase.table("matches").insert(match_payload).execute()
        #                                         st.success("Match historical records logged accurately!")
        #                                         time.sleep(1)
        #                                         st.rerun()
        #                                     except Exception as e:
        #                                         st.error(f"Error logging match outputs: {e}")
        #                 else:
        #                     st.info("No pairings have been generated for this round matrix yet.")
        #                     checked_in = supabase.table("event_participants").select("player_id, player_name").eq("event_id", active_event["id"]).eq("status", "Checked In").execute().data
                            
        #                     if len(checked_in) >= 2:
        #                         st.write("### Manual Table Match Generator")
        #                         p_map = {p["player_name"]: p["player_id"] for p in checked_in}
                                
        #                         p1_sel = st.selectbox("Player 1 Assignment", list(p_map.keys()), key="p1_quick_assign")
        #                         p2_sel = st.selectbox("Player 2 Assignment", [k for k in p_map.keys() if k != p1_sel], key="p2_quick_assign")
        #                         table_num = st.number_input("Table Number Assignment", min_value=1, value=1)
                                
        #                         if st.button("Generate Pairing Row"):
        #                             new_pair_payload = {
        #                                 "event_id": active_event["id"], "round_id": active_round["id"],
        #                                 "player_1_id": p_map[p1_sel], "player_2_id": p_map[p2_sel],
        #                                 "table_number": table_num, "is_completed": False
        #                             }
        #                             try:
        #                                 supabase.table("event_pairings").insert(new_pair_payload).execute()
        #                                 st.success("Manual pairing registered successfully!")
        #                                 time.sleep(1)
        #                                 st.rerun()
        #                             except Exception as e:
        #                                 st.error(f"Failed to generate custom pairing: {e}")
        #                     else:
        #                         st.warning("You must have a minimum of 2 users with 'Checked In' status on your roster to build pairings.")

        # render_event_manager_page(supabase)
    
            # =========================================================================
            # TAB 4: MANAGE PAIRINGS / CHALLENGES
            # =========================================================================
            with tab4:
                if not active_event:
                    st.info("Select or create an event context first.")
                else:
                    is_ladder = str(active_event.get("event_type", "")).lower() == "ladder"
                    
                    # =========================================================================
                    # LADDER TRACKING MODE: OPEN CHALLENGE LOG & OVERRULES
                    # =========================================================================
                    if is_ladder:
                        st.subheader("🛡️ Ladder Challenge Log & Overrules")
                        st.caption("Track open challenges and enforce the 2-week deadline rule.")
                        
                        # Fetch open matches for this ladder event
                        open_challenges = supabase.table("matches").select("*").eq("event_id", active_event["id"]).eq("status", "Logged").order("played_at", desc=True).execute().data
                        
                        if open_challenges:
                            prof_names = {p["id"]: (p["full_name"] or p["username"]) for p in all_profiles}
                            
                            for chal in open_challenges:
                                challenger_name = prof_names.get(chal["attacker_id"], "Unknown Challenger")
                                defender_name = prof_names.get(chal["defender_id"], "Unknown Defender")
                                logged_date = pd.to_datetime(chal["played_at"])
                                days_elapsed = (pd.Timestamp.now(tz='UTC') - logged_date).days
                                days_remaining = max(14 - days_elapsed, 0)
                                
                                label = f"⚔️ {challenger_name} vs {defender_name} ({days_remaining} Days Remaining)"
                                with st.expander(label):
                                    st.write(f"**Challenge Issued On:** {logged_date.strftime('%d/%m/%Y')}")
                                    st.write(f"**Days Active:** {days_elapsed} / 14 days maximum deadline.")
                                    
                                    st.markdown("---")
                                    st.write("⚖️ **Organiser Resolution Overrule**")
                                    st.info("If a player is unresponsive within the 2-week window, assign a default win below.")
                                    
                                    col_c, col_d = st.columns(2)
                                    if col_c.button("🏆 Default Win: Challenger", key=f"def_c_{chal['id']}", use_container_width=True):
                                        try:
                                            # Update the game row data directly to trigger the database ladder shift
                                            supabase.table("matches").update({
                                                "winner_id": chal["attacker_id"],
                                                "loser_id": chal["defender_id"],
                                                "p1_score_total": 10,  # Nominal score for tracking records
                                                "p2_score_total": 0,
                                                "status": "Logged"
                                            }).eq("id", chal["id"]).execute()
                                            
                                            post_to_discord_webhook(f"⚖️ **Organiser Resolution:** {challenger_name} awarded default win against {defender_name} due to deadline expiration.")
                                            st.success("Ladder recalculated via challenger default victory.")
                                            time.sleep(1)
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error executing update trigger: {e}")
                                            
                                    if col_d.button("🏆 Default Win: Defender", key=f"def_d_{chal['id']}", use_container_width=True):
                                        try:
                                            supabase.table("matches").update({
                                                "winner_id": chal["defender_id"],
                                                "loser_id": chal["attacker_id"],
                                                "p1_score_total": 0,
                                                "p2_score_total": 10,
                                                "status": "Logged"
                                            }).eq("id", chal["id"]).execute()
                                            
                                            post_to_discord_webhook(f"⚖️ **Organiser Resolution:** {defender_name} awarded default win defense against {challenger_name} due to deadline expiration.")
                                            st.success("Ladder recalculated via defender default defense.")
                                            time.sleep(1)
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error executing update trigger: {e}")
                        else:
                            st.info("No open challenges are currently logged in the sector field.")
    
                    # =========================================================================
                    # STANDARD MODE: SWISS PAIRINGS MATRIX GENERATION
                    # =========================================================================
                    else:
                        st.subheader("Pairings & Match Slip Entry")
                        rounds_data = supabase.table("event_rounds").select("*").eq("event_id", active_event["id"]).order("round_number").execute().data
                        
                        if not rounds_data:
                            if st.button("🏁 Initialize Round 1 Setup"):
                                try:
                                    supabase.table("event_rounds").insert({"event_id": active_event["id"], "round_number": 1, "is_active": True}).execute()
                                    st.success("Round 1 Initialised!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error initiating rounds: {e}")
                        else:
                            round_map = {f"Round {r['round_number']} {'(Active)' if r['is_active'] else ''}": r for r in rounds_data}
                            selected_round_str = st.selectbox("Select Round Matrix:", list(round_map.keys()))
                            active_round = round_map[selected_round_str]
                            
                            pairings = supabase.table("event_pairings").select("*").eq("round_id", active_round["id"]).order("table_number").execute().data
                            
                            if pairings:
                                st.write("### Active Match Slips")
                                prof_names = {p["id"]: (p["full_name"] or p["username"]) for p in all_profiles}
                                
                                for pair in pairings:
                                    p1_name = prof_names.get(pair["player_1_id"], "Unknown Player 1")
                                    p2_name = prof_names.get(pair["player_2_id"], "Bye / Ghost Player")
                                    
                                    with st.expander(f"🎲 Table {pair['table_number']}: {p1_name} vs {p2_name} {'✅ Logged' if pair['is_completed'] else '⏳ Pending'}"):
                                        with st.form(f"match_slip_form_{pair['id']}"):
                                            col_p1, col_p2 = st.columns(2)
                                            p1_score = col_p1.number_input(f"{p1_name} Score", min_value=0, value=0, key=f"p1_s_{pair['id']}")
                                            p2_score = col_p2.number_input(f"{p2_name} Score", min_value=0, value=0, key=f"p2_s_{pair['id']}")
                                            
                                            is_draw = p1_score == p2_score
                                            w_id = pair["player_1_id"] if p1_score > p2_score else (pair["player_2_id"] if p2_score > p1_score else None)
                                            l_id = pair["player_2_id"] if p1_score > p2_score else (pair["player_1_id"] if p2_score > p1_score else None)
                                            
                                            if st.form_submit_button("Verify & Lock Match Scores"):
                                                try:
                                                    supabase.table("event_pairings").update({"is_completed": True}).eq("id", pair["id"]).execute()
                                                    
                                                    match_payload = {
                                                        "event_id": active_event["id"], "round_id": active_round["id"],
                                                        "game_system_id": active_event.get("game_system_id"),
                                                        "player_1_id": pair["player_1_id"], "p1_score_total": p1_score,
                                                        "player_2_id": pair["player_2_id"], "p2_score_total": p2_score,
                                                        "winner_id": w_id,
                                                        "loser_id": l_id,
                                                        "is_draw": is_draw,
                                                        "status": "Logged"}
                                                    supabase.table("matches").insert(match_payload).execute()
                                                    st.success("Match historical records logged accurately!")
                                                    time.sleep(1)
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"Error logging match outputs: {e}")
                                                else:
                                                    st.info("No pairings have been generated for this round matrix yet.")
                                                    checked_in = supabase.table("event_participants").select("player_id, player_name").eq("event_id", active_event["id"]).eq("status", "Checked In").execute().data
                                                    if len(checked_in) >= 2:
                                                        st.write("### Manual Table Match Generator")
                                                        p_map = {p["player_name"]:
                                                                 p["player_id"] for p in checked_in}
                                                        p1_sel = st.selectbox("Player 1 Assignment", list(p_map.keys()), key="p1_quick_assign")
                                                        p2_sel = st.selectbox("Player 2 Assignment", [k for k in p_map.keys() if k != p1_sel], key="p2_quick_assign")
                                                        table_num = st.number_input("Table Number Assignment", min_value=1, value=1)
                                                        if st.button("Generate Pairing Row"):
                                                            new_pair_payload = {"event_id": active_event["id"], "round_id": active_round["id"],"player_1_id": p_map[p1_sel], "player_2_id": p_map[p2_sel],"table_number": table_num, "is_completed": False}
                                                            try:
                                                                supabase.table("event_pairings").insert(new_pair_payload).execute()
                                                                st.success("Manual pairing registered successfully!")
                                                                time.sleep(1)
                                                                st.rerun()
                                                            except Exception as e:
                                                                st.error(f"Failed to generate custom pairing: {e}")
                                                            else:
                                                                st.warning("You must have a minimum of 2 users with 'Checked In' status on your roster to build pairings.")
        render_event_manager_page(supabase)


    
  
    elif st.session_state.page == "Club Stats":
        st.header("Club Stats")
        st.divider()

        # --- STEP 1: INITIAL DATA FETCH & SYSTEM SELECTION ---
        system_res = supabase.table("match_results").select("system_name").execute()

        if system_res.data:
            # Get unique systems for the dropdown
            system_options = sorted(list(set([row['system_name'] for row in system_res.data if row['system_name']])))
            selected_system = st.selectbox("Select System to View Reports", system_options)

            # --- STEP 2: SETUP DYNAMIC LABELS & COLUMN MAPPING ---
            is_kt = selected_system in ("KT", "MESBG")
            label = "Subfaction" if is_kt else "Faction"
            f_col = "p1_subfaction" if is_kt else "p1_faction"
            opp_f_col = "p2_subfaction" if is_kt else "p2_faction"

            # --- STEP 3: DEFINE REPORT FUNCTIONS ---
            
            def show_faction_win_rates(df, label, f_col, opp_f_col):
                st.subheader(f"📊 {selected_system} {label} Meta")
        
                p1_data = df[[f_col, 'p1_score_total', 'p2_score_total']].copy()
                p1_data.columns = ['unit', 'score', 'opp_score']
                p2_data = df[[opp_f_col, 'p2_score_total', 'p1_score_total']].copy()
                p2_data.columns = ['unit', 'score', 'opp_score']
                
                combined = pd.concat([p1_data, p2_data])
                combined['is_win'] = (combined['score'] > combined['opp_score']).astype(int)
                
                stats = combined.groupby('unit').agg(Total=('unit', 'count'), Wins=('is_win', 'sum')).reset_index()
                stats['Win_Rate'] = (stats['Wins'] / stats['Total'] * 100).round(1)
                stats = stats.sort_values(by='Win_Rate', ascending=True)
            
                # Smart Logic: If winrate is small (<15%), show text outside. 
                # We use 15 here because % bars are often wider.
                positions = ["inside" if val > 15 else "outside" for val in stats['Win_Rate']]

                fig = px.bar(
                    stats, 
                    x='Win_Rate', 
                    y='unit', 
                    text='Win_Rate', 
                    color='Win_Rate', 
                    color_continuous_scale='RdYlGn', 
                    orientation='h'
                )
            
                fig.add_vline(x=50, line_dash="dash", line_color="white", annotation_text="50%")
                
                fig.update_layout(
                    height=max(500, len(stats) * 30), # Dynamic scrolling height
                    xaxis=dict(range=[0, 115], title="Win Rate (%)"), # 115 to give buffer for outside text
                    yaxis=dict(title=""),
                    coloraxis_showscale=False,
                    margin=dict(l=0, r=10, t=30, b=30)
                )
                
                fig.update_traces(
                    texttemplate='%{text}%', 
                    textposition=positions,
                    insidetextanchor='end',
                    cliponaxis=False
                )
                st.plotly_chart(fig, use_container_width=True)
            
            def show_faction_turnout(df, label, f_col, opp_f_col):
                st.subheader(f"👥 {selected_system} {label} Turnout")
                
                combined = pd.concat([
                    df[[f_col]].rename(columns={f_col:'f'}), 
                    df[[opp_f_col]].rename(columns={opp_f_col:'f'})
                ])
                stats = combined['f'].value_counts().reset_index()
                stats.columns = [label, 'Players']
                stats = stats.sort_values('Players', ascending=True) 

                # Smart Logic: Threshold is 10% of the highest turnout
                max_val = stats['Players'].max()
                positions = ["inside" if val > (max_val * 0.1) else "outside" for val in stats['Players']]

                fig = px.bar(
                    stats, 
                    x='Players', 
                    y=label, 
                    orientation='h',
                    text='Players',
                    color_discrete_sequence=['#636EFA'] 
                )
                
                fig.update_layout(
                    height=max(400, len(stats) * 30),
                    xaxis=dict(range=[0, max_val * 1.15], title="Player Count"),
                    yaxis=dict(title=""),
                    margin=dict(l=0, r=10, t=30, b=30)
                )
                
                fig.update_traces(
                    textposition=positions, 
                    insidetextanchor='end',
                    cliponaxis=False
                )
                st.plotly_chart(fig, use_container_width=True)
            
            def show_allegiance_points(df):
                st.subheader(f"⚔️ {selected_system} Points by Allegiance")
                
                p1 = df[['p1_allegiance', 'p1_score_total']].rename(columns={'p1_allegiance':'a', 'p1_score_total':'s'})
                p2 = df[['p2_allegiance', 'p2_score_total']].rename(columns={'p2_allegiance':'a', 'p2_score_total':'s'})
                combined = pd.concat([p1, p2])
                
                agg = combined.groupby('a')['s'].sum().reset_index().sort_values('s', ascending=True)
                
                # Smart Logic: Threshold is 10% of the highest score
                max_val = agg['s'].max()
                positions = ["inside" if val > (max_val * 0.1) else "outside" for val in agg['s']]

                fig = px.bar(
                    agg, 
                    x='s', 
                    y='a', 
                    orientation='h',
                    labels={'s': 'Total Points', 'a': 'Allegiance'},
                    text='s',
                    color='s',
                    color_continuous_scale='Viridis'
                )
                
                fig.update_layout(
                    height=300, # Fixed height since allegiances are few
                    xaxis=dict(range=[0, max_val * 1.15], title="Total Points"),
                    yaxis=dict(title=""),
                    coloraxis_showscale=False,
                    margin=dict(l=0, r=10, t=30, b=30)
                )
                
                fig.update_traces(
                    textposition=positions, 
                    insidetextanchor='end',
                    cliponaxis=False
                )
                st.plotly_chart(fig, use_container_width=True)

            # --- STEP 4: EXECUTE ---
            # Only fetch data for the selected system
            res = supabase.table("match_results").select("*").eq("system_name", selected_system).execute()
            
            if res.data:
                system_df = pd.DataFrame(res.data)
                
                if not system_df.empty:
                    show_faction_win_rates(system_df, label, f_col, opp_f_col)
                    st.divider()
                    show_faction_turnout(system_df, label, f_col, opp_f_col)
                    st.divider()
                    show_allegiance_points(system_df)
                else:
                    st.warning(f"No valid match data found for {selected_system}.")
        else:
            st.info("No games found in the database.")

    elif st.session_state.page == "Graphs_2":
        st.header("Graphs_2")
        st.divider()

        # --- STEP 1: INITIAL DATA FETCH & SYSTEM SELECTION ---
        system_res = supabase.table("match_results").select("system_name").execute()

        if system_res.data:
            system_options = sorted(list(set([row['system_name'] for row in system_res.data if row['system_name']])))
            selected_system = st.selectbox("Select System to View Reports", system_options)

            # --- STEP 2: SETUP DYNAMIC LABELS & COLUMN MAPPING ---
            is_kt = selected_system in ("KT", "MESBG")
            label = "Subfaction" if is_kt else "Faction"
            f_col = "p1_subfaction" if is_kt else "p1_faction"
            opp_f_col = "p2_subfaction" if is_kt else "p2_faction"

            # --- NEW: UI TOGGLE FOR METRIC ---
            view_mode = st.radio(
                "Select Metric to Visualize:",
                ["Win Rate", "Player Count", "Games Played"],
                horizontal=True
            )

            # --- STEP 3: CONSOLIDATED DYNAMIC REPORT FUNCTION ---
            def show_faction_meta(df, label, f_col, opp_f_col, mode):
                st.subheader(f"📊 {selected_system} {label}: {mode}")
        
                # Combine P1 and P2 data including player names for "Player Count"
                p1 = df[[f_col, 'display_p1_name', 'p1_score_total', 'p2_score_total']].copy()
                p1.columns = ['unit', 'player', 'score', 'opp_score']
                
                p2 = df[[opp_f_col, 'display_p2_name', 'p2_score_total', 'p1_score_total']].copy()
                p2.columns = ['unit', 'player', 'score', 'opp_score']
                
                combined = pd.concat([p1, p2])
                combined['is_win'] = (combined['score'] > combined['opp_score']).astype(int)
                
                # Aggregate all stats at once
                stats = combined.groupby('unit').agg(
                    Games=('unit', 'count'),
                    Wins=('is_win', 'sum'),
                    Players=('player', 'nunique')
                ).reset_index()
                
                stats['Win_Rate'] = (stats['Wins'] / stats['Games'] * 100).round(1)

                # Map UI selection to Data columns & Styling
                if mode == "Win Rate":
                    target_col = 'Win_Rate'
                    chart_color = 'Win_Rate'
                    color_scale = 'RdYlGn'
                    suffix = "%"
                elif mode == "Player Count":
                    target_col = 'Players'
                    chart_color = None # Static color
                    color_scale = None
                    suffix = ""
                else: # Games Played
                    target_col = 'Games'
                    chart_color = None
                    color_scale = None
                    suffix = ""

                stats = stats.sort_values(by=target_col, ascending=True)
            
                # Logic for text positioning
                max_val = stats[target_col].max()
                threshold = 15 if mode == "Win Rate" else (max_val * 0.2)
                positions = ["inside" if val > threshold else "outside" for val in stats[target_col]]

                fig = px.bar(
                    stats, 
                    x=target_col, 
                    y='unit', 
                    text=target_col, 
                    color=chart_color, 
                    color_continuous_scale=color_scale, 
                    orientation='h',
                    color_discrete_sequence=['#636EFA'] # Default blue if Win Rate isn't selected
                )
            
                # Only add 50% line for Win Rate
                if mode == "Win Rate":
                    fig.add_vline(x=50, line_dash="dash", line_color="white", annotation_text="50%")
                
                fig.update_layout(
                    height=max(500, len(stats) * 35),
                    xaxis=dict(range=[0, max_val * 1.15], title=mode),
                    yaxis=dict(title=""),
                    coloraxis_showscale=False,
                    margin=dict(l=0, r=10, t=30, b=30)
                )
                
                fig.update_traces(
                    texttemplate=f'%{{text}}{suffix}', 
                    textposition=positions,
                    insidetextanchor='end',
                    cliponaxis=False
                )
                st.plotly_chart(fig, use_container_width=True)

            # --- STEP 4: EXECUTE ---
            res = supabase.table("match_results").select("*").eq("system_name", selected_system).execute()
            
            if res.data:
                system_df = pd.DataFrame(res.data)
                
                if not system_df.empty:
                    # Call the dynamic function based on radio button
                    show_faction_meta(system_df, label, f_col, opp_f_col, view_mode)
                else:
                    st.warning(f"No valid match data found for {selected_system}.")
        else:
            st.info("No games found in the database.")

    elif st.session_state.page == "Personal Stats":
        st.header("👤 Your Career Dashboard")
        st.divider()
        
        current_user = discord_name

        # 1. Fetch ALL matches for this player (no limit)
        res = supabase.table("match_results") \
            .select("*") \
            .or_(f"display_p1_name.eq.{current_user},display_p2_name.eq.{current_user}") \
            .execute()

        if res.data:
            full_df = pd.DataFrame(res.data)

            # 2. Standardise: 'User' is always you, 'Opp' is always the other person
            p1_mask = full_df['display_p1_name'] == current_user
            
            p1_side = full_df[p1_mask].copy()
            p1_side.columns = [c.replace('p1_', 'user_').replace('p2_', 'opp_') for c in p1_side.columns]
            
            p2_side = full_df[~p1_mask].copy()
            # Rename p1 columns to opp and p2 to user
            p2_side.columns = [c.replace('p1_', 'opp_').replace('p2_', 'user_') for c in p2_side.columns]

            user_df = pd.concat([p1_side, p2_side])
            user_df['is_win'] = user_df['user_score_total'] > user_df['opp_score_total']
            user_df['went_first_flag'] = user_df['went_first'] == current_user

            # 3. THREE DROPDOWNS (Cascading)
            st.write("### 🔍 Filter Your History")
            c1, c2, c3 = st.columns(3)

            # Dropdown 1: System
            sys_options = sorted(user_df['system_name'].unique().tolist())
            sel_sys = c1.selectbox("Select System", ["All Systems"] + sys_options)
            
            df_filtered = user_df.copy()
            if sel_sys != "All Systems":
                df_filtered = df_filtered[df_filtered['system_name'] == sel_sys]

            # Dropdown 2: Allegiance (Filtered by System)
            allg_options = sorted(df_filtered['user_allegiance'].unique().tolist())
            sel_allg = c2.selectbox("Select Allegiance", ["All Allegiances"] + allg_options)
            
            if sel_allg != "All Allegiances":
                df_filtered = df_filtered[df_filtered['user_allegiance'] == sel_allg]

            # Dropdown 3: Faction (Filtered by Allegiance)
            fac_options = sorted(df_filtered['user_faction'].unique().tolist())
            sel_fac = c3.selectbox("Select Faction", ["All Factions"] + fac_options)
            
            if sel_fac != "All Factions":
                df_filtered = df_filtered[df_filtered['user_faction'] == sel_fac]

            # 4. Calculate Stats for the final filtered selection
            total_games = len(df_filtered)
            wins = df_filtered['is_win'].sum()
            win_rate = (wins / total_games * 100) if total_games > 0 else 0
            avg_score = df_filtered['user_score_total'].mean() if total_games > 0 else 0
            
            first_df = df_filtered[df_filtered['went_first_flag'] == True]
            first_win_rate = (first_df['is_win'].sum() / len(first_df) * 100) if len(first_df) > 0 else 0

            # 5. Display Metrics
            st.subheader(f"📊 Stats for: {sel_fac if sel_fac != 'All Factions' else sel_allg if sel_allg != 'All Allegiances' else sel_sys}")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Games Played", total_games)
            m2.metric("Win Rate", f"{win_rate:.1f}%")
            m3.metric("Avg Score", f"{avg_score:.1f}")
            m4.metric("Win% (Went First)", f"{first_win_rate:.1f}%")

            st.divider()

            # 6. History Table
            st.write("### 📜 Match History")
            st.dataframe(
                df_filtered.sort_values('game_date', ascending=False),
                column_order=("game_date", "user_faction", "user_score_total", "opp_score_total", "opp_faction", "display_opp_name", "event_name"),
                column_config={
                    "game_date": "Date",
                    "user_faction": "Your Faction",
                    "user_score_total": "Your Score",
                    "opp_score_total": "Opp Score",
                    "opp_faction": "Opp Faction",
                    "display_opp_name": "Opponent",
                    "event_name": "Event"
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No match history found. Time to roll some dice!")



