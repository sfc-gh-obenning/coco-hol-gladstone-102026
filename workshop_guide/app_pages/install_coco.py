import streamlit as st

from components import ctx, render_real_world_examples, render_references
from content import links as L

st.title("Install CoCo Desktop and CLI")
st.markdown("Do this **the day before** the lab. Either CoCo Desktop or the CoCo CLI is enough for every step; the "
            "CLI also needs the Snowflake CLI. Allow 10-15 minutes, more if your laptop needs IT approval to install apps.")

st.warning(
    "CoCo Desktop is available to commercial accounts **with cross-region inference enabled**. Gladstone's account is on "
    "Azure UK South, so the admin should confirm `CORTEX_ENABLED_CROSS_REGION` (questionnaire item 6) before attendees "
    "install. If cross-region inference isn't allowed, check with the admin and the account team before the session.",
    title="Check this first (admin)", icon=":material/public:")

st.markdown("#### :material/checklist: Prerequisites")
st.markdown("""
| You need | Desktop | CLI | How to check |
|---|---|---|---|
| A Snowflake user on `GLADSTONESOFTWARE` that can sign in (SSO or password + MFA) | Yes | Yes | Log in at app.snowflake.com |
| Role with `SNOWFLAKE.CORTEX_USER` or `SNOWFLAKE.CORTEX_AGENT_USER` | Yes | Yes | Granted to `PUBLIC` by default; the lab role `DQ_LAB_ATTENDEE` has it |
| Your **account identifier** (`orgname-accountname`) and **login name** | Yes | Yes | Snowsight » your avatar » *Connect a tool to Snowflake* |
| macOS or Windows | Yes | - | Desktop supports macOS and Windows |
| macOS (Apple Silicon or Intel), Linux (x64/arm64), Windows native (x64) or WSL (x64) | - | Yes | |
| Terminal: zsh / bash / fish, or PowerShell on Windows | - | Yes | |
| **Snowflake CLI** (`snow`) - required by the CoCo CLI and for Bonus B3 (3.17+) | - | Yes | `snow --version` |
| Network access to Snowflake (VPN, proxy, firewall allow it) | Yes | Yes | You can open Snowsight on the same network |
| Permission to install apps on your laptop | Yes | Yes | Windows **User installer** needs no admin rights |
""")

desktop, cli, snowcli, verify, trouble = st.tabs([
    ":material/desktop_windows: CoCo Desktop", ":material/terminal: CoCo CLI", ":material/build: Snowflake CLI",
    ":material/task_alt: Verify for the lab", ":material/help: Troubleshooting",
])

with desktop:
    st.markdown("##### 1. Download and install")
    st.link_button("Open the CoCo downloads page", L.COCO_DOWNLOADS[1], icon=":material/download:", type="primary")
    st.markdown("""
- **macOS:** download the macOS build, open the downloaded file, follow the installer prompts, then launch CoCo.
- **Windows:** choose the **User installer** (recommended - no administrator rights, updates itself). The **System
  installer** installs for all users and needs administrator rights (for IT-managed deployments).
- Updates are automatic after that; you don't need to download a new installer.
""")
    st.markdown("##### 2. First launch: four-step setup")
    st.markdown("""
1. **Welcome** - click **Next**.
2. **Connect to Snowflake** - if you already have `~/.snowflake/connections.toml` (for example from the CLI), your
   connections are listed. Otherwise click **Add connection**:
   - **Account identifier:** `orgname-accountname` for `GLADSTONESOFTWARE` (ask your admin, or copy it from Snowsight)
   - **Connection name:** for example `gladstone`
   - **Username:** your Snowflake login name
   - **Authentication method:** *Local OAuth* (recommended) or *External browser (SSO)* if Gladstone signs in through Entra ID
   - Click **Sign in** and finish in your browser.
3. **Choose a view** - *Agent* or *Editor* (you can switch later).
4. **Choose a theme** - then **Get Started**.
""")
    st.markdown("##### 3. Set the lab role and warehouse")
    st.markdown(f"""
Click the connection name in the top bar: **Change Role** » `{ctx()['ROLE']}` and **Default Warehouse** » `DQ_LAB_WH`.
""")
    st.caption("Setting the default warehouse in CoCo Desktop runs ALTER USER SET DEFAULT_WAREHOUSE on your Snowflake user.")

with cli:
    st.markdown("##### 1. Install the Snowflake CLI first")
    st.markdown("The CoCo CLI lists the Snowflake CLI as a prerequisite - see the **Snowflake CLI** tab.")
    st.markdown("##### 2. Install the CoCo CLI")
    st.markdown("**macOS, Linux or WSL** (in a terminal):")
    st.code("curl -LsS https://ai.snowflake.com/static/cc-scripts/install.sh | sh", language="bash")
    st.caption("Installs `cortex` into `~/.local/bin` and adds it to your PATH. Open a new terminal afterwards.")
    st.markdown("**Windows native** (in PowerShell):")
    st.code("irm https://ai.snowflake.com/static/cc-scripts/install.ps1 | iex", language="powershell")
    st.caption("Installs into `%LOCALAPPDATA%\\cortex` and adds it to your PATH.")
    st.markdown("##### 3. Check the install")
    st.code("cortex --version", language="bash")
    st.markdown("##### 4. Connect and start")
    st.code("cortex", language="bash")
    st.markdown("""
The setup wizard asks you to pick a connection from `~/.snowflake/connections.toml` or create one (**More options**).
It's the same file the Snowflake CLI uses, so a `snow` connection works here too. Then start the lab with your connection:
""")
    st.code(f"cortex -c gladstone\n# then, in the session:\n# use role {ctx()['ROLE']} and warehouse DQ_LAB_WH", language="bash")
    st.markdown("##### Optional: add the connection by hand")
    st.code("""mkdir -p ~/.snowflake && touch ~/.snowflake/connections.toml && chmod 600 ~/.snowflake/connections.toml""", language="bash")
    st.code(f"""[gladstone]
account       = "<orgname-accountname>"
user          = "<your login name>"
authenticator = "externalbrowser"     # SSO (e.g. Entra ID); or "oauth_authorization_code"
role          = "{ctx()['ROLE']}"
warehouse     = "DQ_LAB_WH"
database      = "GLADSTONE_DQ_LAB"
schema        = "{ctx()['SCHEMA']}\"""", language="toml")
    st.info("**SSO or password?** Use the way you sign in to Snowflake in the browser. "
            "**SSO** (for example Microsoft Entra ID): `authenticator = \"externalbrowser\"`. "
            "**Password + MFA**: leave `authenticator` out and add `password = \"...\"` - you'll get an MFA prompt; "
            "`oauth_authorization_code` avoids storing a password. Not sure? Try `externalbrowser` first.",
            icon=":material/key:")
    st.markdown("##### Keep it current")
    st.code("cortex update", language="bash")

with snowcli:
    st.markdown("Needed by the CoCo CLI, and by Bonus B3 (`snow dcm`, version **3.17 or later**).")
    mac, win, lin, py = st.tabs(["macOS", "Windows", "Linux", "Python tools"])
    with mac:
        st.markdown("**Homebrew - Snowflake tap (recommended):**")
        st.code("""brew tap snowflakedb/snowflake-cli
brew trust --cask snowflakedb/snowflake-cli/snowflake-cli
brew install --cask snowflake-cli""", language="bash")
        st.markdown("**Or** download the macOS package installer:")
        st.link_button("Snowflake CLI releases", L.SNOW_CLI_RELEASES[1], icon=":material/download:")
    with win:
        st.markdown("Download and run the Windows installer, then open a **new** terminal.")
        st.link_button("Snowflake CLI releases", L.SNOW_CLI_RELEASES[1], icon=":material/download:")
    with lin:
        st.markdown("Download the `.deb` or `.rpm` from the releases page, then:")
        st.code("sudo dpkg -i snowflake-cli-<version>.deb    # Debian / Ubuntu\nsudo rpm -i snowflake-cli-<version>.rpm     # RHEL / Fedora", language="bash")
    with py:
        st.markdown("Python 3.10 or later:")
        st.code("uv tool install snowflake-cli     # or: pipx install snowflake-cli", language="bash")
    st.markdown("**Check it and add the lab connection:**")
    st.code("""snow --version
snow connection add            # follow the prompts (account, user, authenticator)
snow connection test -c gladstone""", language="bash")

with verify:
    st.markdown("Run this in CoCo (Desktop chat or `cortex`). The guide uses your operator name from the sidebar.")
    st.code(f"Run select current_user(), current_role(), current_warehouse() and confirm I can see schema "
            f"{ctx()['FQ_SCHEMA']}.", language="text", wrap_lines=True)
    st.markdown(f"""
You're ready when you see:
- your user, role **`{ctx()['ROLE']}`** and warehouse **`DQ_LAB_WH`**
- the schema `{ctx()['FQ_SCHEMA']}` with its tables (only after the admin has run setup)

If the role or warehouse is different, ask CoCo: *"use role {ctx()['ROLE']} and warehouse DQ_LAB_WH"*.
""")

with trouble:
    issues = [
        ("`cortex: command not found`",
         "The install folder isn't on your PATH yet. Open a new terminal, or add it (bash example):",
         'export PATH="$HOME/.local/bin:$PATH"\necho \'export PATH="$HOME/.local/bin:$PATH"\' >> ~/.bashrc   # zsh: ~/.zshrc'),
        ("The curl install script fails",
         "Custom options in `~/.curlrc` can break it. Re-run with `-q` so curl ignores that file:",
         "curl -qLsS https://ai.snowflake.com/static/cc-scripts/install.sh | sh"),
        ("`Permission denied` running cortex", "Give the binary execute permission:", "chmod +x ~/.local/bin/cortex"),
        ("Connection errors in the CLI",
         "Check the connection file exists and is valid, then name the connection explicitly:",
         "cat ~/.snowflake/connections.toml\ncortex -c gladstone"),
        ("Desktop: *Account not found*",
         "The account identifier is wrong. Copy it from Snowsight » avatar » *Connect a tool to Snowflake* "
         "(format `orgname-accountname`).", None),
        ("Desktop: *Authentication failed*",
         "Wrong password, expired token, or an SSO mismatch. Sign in again; for Entra ID use *External browser (SSO)*.", None),
        ("Desktop: *Connection failed*",
         "Network or firewall. Check VPN/proxy - if Snowsight doesn't load on this network, CoCo won't connect either.", None),
        ("The browser doesn't open for OAuth/SSO",
         "Set a default browser, or use the **Browser didn't open?** link in the app to copy the sign-in URL.", None),
        ("CoCo can't use Cortex / no models available",
         "Your role needs `SNOWFLAKE.CORTEX_USER` or `CORTEX_AGENT_USER`, and models not hosted in UK South need "
         "cross-region inference. List what your role can use:", "SHOW CORTEX BASE MODELS IN SCHEMA SNOWFLAKE.MODELS;"),
        ("MFA prompt on every `snow` command",
         "Expected with MFA. Use SSO (`externalbrowser`) or MFA caching - see the Snowflake CLI docs.", None),
        ("Can't install on a managed laptop",
         "On Windows use the **User installer** (no admin rights). Otherwise ask IT - or use Snowsight for the lab: "
         "every step has a *Do it in Snowsight* route.", None),
        ("Need logs for support",
         "Desktop writes `main.log` here - search it for `[error]`:",
         "macOS:   ~/Library/Application Support/Cortex Code/logs/<timestamp>/main.log\n"
         "Windows: %APPDATA%\\Cortex Code\\logs\\<timestamp>\\main.log"),
        ("Start Desktop setup again", "Command palette » **Reset Onboarding**, then restart the app.", None),
    ]
    for title, body, code in issues:
        with st.expander(f":material/help: {title}"):
            st.markdown(body)
            if code:
                st.code(code, language="bash")

render_real_world_examples([
    {"title": "Rolling CoCo out to the data team", "body": "The same checklist - access role, account identifier, SSO connection, a test prompt - works for every Gladstone engineer, not just the lab."},
    {"title": "IT-managed laptops", "body": "The Windows System installer and CoCo Desktop managed settings let IT deploy and configure CoCo centrally."},
])
render_references({
    "Downloads": [L.COCO_DOWNLOADS, L.SNOW_CLI_RELEASES],
    "Quickstarts": [L.QS_COCO_DESKTOP, L.QS_COCO_CLI],
    "Docs": [L.COCO_DESKTOP, L.COCO_DESKTOP_SETUP, L.COCO_DESKTOP_FAQ, L.COCO_CLI, L.COCO_CLI_REF, L.SNOW_CLI_INSTALL,
             L.CROSS_REGION, L.ACCOUNT_ID],
})
