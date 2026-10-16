from pathlib import Path

import streamlit as st

from components import ctx, is_session_complete

_DIR = Path(__file__).parent


def _title(session_id, label: str) -> str:
    check = " :green[:material/check_circle:]" if is_session_complete(session_id) else ""
    return f"{label}{check}"


st.set_page_config(
    page_title="Gladstone MRM | Data quality hands-on lab",
    page_icon=":material/fact_check:",
    layout="wide",
)

st.logo(
    str(_DIR / "static" / "snowflake_full_logo.png"),
    icon_image=str(_DIR / "static" / "snowflake_logo.png"),
)

st.session_state.setdefault("operator_name", "NIELS")

with st.sidebar:
    st.text_input(
        "Your operator name",
        key="operator_name",
        help="The NAME your admin used in SETUP_ALL. Every prompt and SQL block updates to CUST_<NAME>.",
        max_chars=30,
    )
    st.caption(f"Your schema: `{ctx()['FQ_SCHEMA']}`  \nYour role: `{ctx()['ROLE']}`")

page = st.navigation(
    {
        "": [
            st.Page("app_pages/home.py", title="Home", icon=":material/home:"),
            st.Page("app_pages/before_you_start.py", title="Before you start", icon=":material/event_available:"),
            st.Page("app_pages/install_coco.py", title="Install CoCo Desktop and CLI", icon=":material/download:"),
            st.Page("app_pages/getting_started.py", title="Getting started", icon=":material/rocket_launch:"),
            st.Page("app_pages/agenda.py", title="Agenda", icon=":material/calendar_today:"),
        ],
        "30-minute lab": [
            st.Page("app_pages/session_01.py", title=_title(1, "1. Meet your operator pipeline"), icon=":material/account_tree:"),
            st.Page("app_pages/session_02.py", title=_title(2, "2. Put monitors on it"), icon=":material/monitoring:"),
            st.Page("app_pages/session_03.py", title=_title(3, "3. Diagnose a broken answer"), icon=":material/troubleshoot:"),
            st.Page("app_pages/session_04.py", title=_title(4, "4. Contain and alert"), icon=":material/shield:"),
            st.Page("app_pages/session_05.py", title=_title(5, "5. Fleet view across operators"), icon=":material/grid_view:"),
        ],
        "Stretch": [
            st.Page("app_pages/stretch.py", title=_title("S", "Agents, automation, migration"), icon=":material/rocket:"),
        ],
        "Bonus labs (after the session)": [
            st.Page("app_pages/bonus_b1.py", title=_title("B1", "B1. Budgets and resource monitors"), icon=":material/savings:"),
            st.Page("app_pages/bonus_b2.py", title="B2. Data governance and GDPR", icon=":material/policy:"),
            st.Page("app_pages/bonus_b3.py", title=_title("B3", "B3. DevOps with DCM Projects"), icon=":material/deployed_code:"),
        ],
        "Reference": [
            st.Page("app_pages/scaling.py", title="Scaling to every operator", icon=":material/hub:"),
            st.Page("app_pages/availability.py", title="Azure UK South availability", icon=":material/public:"),
            st.Page("app_pages/reference_coco.py", title="CoCo prompt cheat sheet", icon=":material/chat:"),
            st.Page("app_pages/snowsight_map.py", title="Snowsight navigation map", icon=":material/map:"),
            st.Page("app_pages/troubleshooting.py", title="Troubleshooting", icon=":material/build:"),
            st.Page("app_pages/admin_setup.py", title="Lab setup (admin)", icon=":material/admin_panel_settings:"),
            st.Page("app_pages/admin_teardown.py", title="Lab teardown (admin)", icon=":material/delete_sweep:"),
        ],
    },
    position="sidebar",
)

page.run()
