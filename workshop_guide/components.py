import streamlit as st
from pathlib import Path

LAB_DB = "GLADSTONE_DQ_LAB"
SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


@st.cache_data(max_entries=50)
def sql_file(rel_path: str) -> str:
    """Admin scripts are shown straight from dq-lab/sql so the guide never drifts from the tested SQL."""
    p = SQL_DIR / rel_path
    return p.read_text() if p.exists() else f"-- {rel_path} not found next to the app (expected {p})"


def render_sql_file(rel_path: str, label: str | None = None, expanded: bool = False):
    with st.expander(label or f":material/description: `{rel_path}`", expanded=expanded):
        st.code(sql_file(rel_path), language="sql", line_numbers=True)


DOC_DIR = SQL_DIR.parent


@st.cache_data(max_entries=20)
def doc_file(name: str) -> str:
    """Hand-out docs (questionnaire, attendee prep, roster) live in dq-lab/ and are shown as-is."""
    p = DOC_DIR / name
    return p.read_text() if p.exists() else f"{name} not found next to the app (expected {p})"


def render_doc_download(name: str, label: str, mime: str = "text/markdown"):
    st.download_button(label, data=doc_file(name), file_name=name, mime=mime,
                       icon=":material/download:", key=f"dl_{name}")

# Prompt ids per lab section - drive the green tick next to each page title in the sidebar.
SESSION_PROMPTS = {
    1: ["Prompt 1.1", "Prompt 1.2"],
    2: ["Prompt 2.1", "Prompt 2.2"],
    3: ["Prompt 3.1", "Prompt 3.2"],
    4: ["Prompt 4.1", "Prompt 4.2"],
    5: ["Prompt 5.1", "Prompt 5.2"],
    "D2": ["Prompt D2.1", "Prompt D2.2", "Prompt D2.3", "Prompt D2.4", "Prompt D2.5", "Prompt D2.6", "Prompt D2.7"],
    "B1": ["Prompt B1.1", "Prompt B1.2", "Prompt B1.3", "Prompt B1.4"],
    "B2A": ["Prompt B2.1", "Prompt B2.2", "Prompt B2.3", "Prompt B2.4"],
    "B2B": ["Prompt B2.5", "Prompt B2.6", "Prompt B2.7", "Prompt B2.8", "Prompt B2.9"],
    "B3": ["Prompt B3.1", "Prompt B3.2", "Prompt B3.3", "Prompt B3.4"],
}


# ── operator (attendee) context ──────────────────────────────────────────────
def operator_name() -> str:
    raw = st.session_state.get("operator_name") or "OPERATOR01"
    clean = "".join(c for c in raw.upper() if c.isalnum() or c == "_")
    return clean or "OPERATOR01"


def ctx() -> dict:
    name = operator_name()
    return {
        "NAME": name,
        "SCHEMA": f"CUST_{name}",
        "FQ_SCHEMA": f"{LAB_DB}.CUST_{name}",
        "ROLE": f"DQ_LAB_{name}",
        "DB": LAB_DB,
        "WH": "DQ_LAB_WH",
    }


def fill(text: str) -> str:
    """Replace {SCHEMA}, {ROLE}, ... placeholders with the attendee's operator values."""
    out = text
    for k, v in ctx().items():
        out = out.replace("{" + k + "}", v)
    return out


# ── completion tracking ──────────────────────────────────────────────────────
def _done_store() -> dict:
    if "_done" not in st.session_state:
        st.session_state["_done"] = {}
    return st.session_state["_done"]


def _prompt_key(prompt_id: str) -> str:
    return prompt_id.replace(" ", "_").replace(".", "_")


def _on_toggle(prompt_id: str):
    key = _prompt_key(prompt_id)
    _done_store()[key] = st.session_state[f"_cb_{key}"]


def is_session_complete(session_id) -> bool:
    prompts = SESSION_PROMPTS.get(session_id, [])
    store = _done_store()
    return len(prompts) > 0 and all(store.get(_prompt_key(p), False) for p in prompts)


# ── building blocks ──────────────────────────────────────────────────────────
def render_session_header(label: str, title: str, duration: str, building: str):
    st.title(f"{label}: {title}")
    col1, col2 = st.columns(2)
    col1.markdown(f":material/schedule: **{duration}**")
    col2.markdown(f":material/construction: **Building**: {building}")
    st.space("small")


def render_execution_context():
    st.info(
        ":material/terminal: **Primary: CoCo Desktop or CoCo CLI** - paste each prompt into CoCo.  "
        ":material/web: **Also possible in Snowsight** - open *Do it in Snowsight* under any step.",
        icon=None,
    )
    render_role_callout()


def render_role_callout(when: str = "Before you paste any prompt on this page"):
    """The lab never changes users' DEFAULT_ROLE, so every page reminds attendees to switch role themselves."""
    c = ctx()
    with st.container(border=True):
        st.warning(f"**Set your role.** {when}, check CoCo (or your worksheet) is using role "
                   f"**`{c['ROLE']}`** and warehouse **`DQ_LAB_WH`**. Unless your admin set it as your default, "
                   "a new CoCo session, reconnect or new worksheet starts in your usual role.",
                   icon=":material/badge:")
        st.code(f"USE ROLE {c['ROLE']};\nUSE SECONDARY ROLES NONE;\nUSE WAREHOUSE DQ_LAB_WH;\n"
                "SELECT CURRENT_ROLE(), CURRENT_WAREHOUSE();", language="sql")
        st.caption(f"In CoCo you can also just ask: *\"use role {c['ROLE']} and warehouse DQ_LAB_WH\"*.")


def render_what_why(what: str, why: str):
    c1, c2 = st.columns(2)
    with c1.container(border=True, height="stretch"):
        st.markdown("##### :material/flag: What")
        st.markdown(what)
    with c2.container(border=True, height="stretch"):
        st.markdown("##### :material/lightbulb: Why it matters for Gladstone")
        st.markdown(why)


def render_prompt(prompt_id: str, title: str, prompt_text: str):
    key = _prompt_key(prompt_id)
    cb_key = f"_cb_{key}"
    store = _done_store()
    if cb_key not in st.session_state:
        st.session_state[cb_key] = store.get(key, False)
    with st.container(border=True):
        header_col, check_col = st.columns([5, 1], vertical_alignment="center")
        with header_col:
            st.markdown(f"#### :material/terminal: {prompt_id} - {title}")
        with check_col:
            st.checkbox("Done", key=cb_key, on_change=_on_toggle, args=(prompt_id,))
        st.caption("Copy this prompt into CoCo Desktop or the CoCo CLI")
        st.code(fill(prompt_text), language="text", wrap_lines=True)


def render_explanation(title: str, body: str):
    with st.expander(f":material/school: {title}", expanded=False):
        st.markdown(fill(body))


def render_snowsight_route(steps: list[str], sql: str | None = None):
    """The same step done in the Snowsight UI (and/or a worksheet)."""
    with st.expander(":material/web: Do it in Snowsight", expanded=False):
        for i, s in enumerate(steps, 1):
            st.markdown(f"{i}. {fill(s)}")
        if sql:
            st.caption("Or paste into a Snowsight worksheet:")
            st.code(fill(sql), language="sql")


def render_checkpoint(text: str, sql: str | None = None):
    with st.container(border=True):
        st.markdown(f":material/task_alt: **Checkpoint** - {fill(text)}")
        if sql:
            st.code(fill(sql), language="sql")


def render_fallback(sql: str):
    with st.expander(":material/sos: Behind? Run this to catch up", expanded=False):
        st.caption("Exactly what CoCo should have produced. Run it as your operator role.")
        st.code(fill(sql), language="sql")


def render_technologies_used(technologies: list[dict]):
    st.markdown("##### :material/build: Snowflake capabilities in this section")
    cols = st.columns(min(len(technologies), 3))
    for i, tech in enumerate(technologies):
        with cols[i % len(cols)].container(border=True, height="stretch"):
            st.markdown(f":material/{tech.get('icon', 'widgets')}: **{tech['name']}**")
            st.caption(tech["description"])


def render_key_concepts(concepts: list[dict]):
    st.markdown("##### :material/lightbulb: Key concepts")
    for concept in concepts:
        with st.expander(f"**{concept['term']}**"):
            st.markdown(concept["definition"])


def render_what_you_built(items: list[str]):
    st.markdown("##### :material/check_circle: What you built")
    for item in items:
        st.markdown(f"- :green-badge[Done] {fill(item)}")


# ── page footers (required on every lab page) ────────────────────────────────
def render_real_world_examples(items: list[dict]):
    st.divider()
    st.markdown("##### :material/apartment: Where Gladstone would use this")
    cols = st.columns(2)
    for i, it in enumerate(items):
        with cols[i % 2].container(border=True, height="stretch"):
            st.markdown(f"**{it['title']}**")
            st.markdown(it["body"])


def render_references(links: dict):
    """links = {"Quickstarts": [(title, url, note)], "Docs": [...], "Blogs and guidance": [...]}"""
    from content.links import VERIFIED_ON

    st.markdown("##### :material/menu_book: References")
    for group, items in links.items():
        if not items:
            continue
        st.markdown(f"**{group}**")
        for title, url, note in items:
            suffix = f" - {note}" if note else ""
            st.markdown(f"- [{title}]({url}){suffix}")
    st.caption(f"Links verified {VERIFIED_ON}.")
