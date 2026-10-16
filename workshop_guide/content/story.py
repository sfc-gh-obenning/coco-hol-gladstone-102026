"""The lab's story: cast, chapters, incident tickets and the Home timelines - one source for the live and static guides.
Edit the words here; the pages only decide where each piece appears."""
import streamlit as st

LAB = "full"
ARC = ["Meet the pipeline", "Monitor", "Diagnose", "Contain", "Fleet"]

CAST = [
    {"name": "Sam", "role": "Operations manager at your operator (a leisure chain on Nova)", "icon": ":material/storefront:",
     "says": "Sees Nova every morning. Rings Gladstone when the numbers look wrong."},
    {"name": "Priya", "role": "Customer Success lead, Gladstone", "icon": ":material/support_agent:",
     "says": "Looks after every operator. Gets the calls - several on a bad morning."},
    {"name": "You", "role": "Data engineer, Gladstone - on call for one operator", "icon": ":material/engineering:",
     "says": "Own one operator's Nova pipeline (your schema). Work in CoCo."},
]

CHAPTERS = {
    1: {"previously": "It's Tuesday. Every attendee is on call for a different operator, each in its own database.",
        "who": "Priya", "quote": "Before the phones start - do you actually know how your operator's Nova numbers are built?",
        "scene": "Nothing is wrong yet. You have five minutes to learn the pipeline you're on call for.",
        "mission": "Map Bronze, REPORTING and the semantic view, and note Nova's two KPIs on a good day."},
    2: {"previously": "You know your operator's pipeline and its numbers on a good day.",
        "who": "Priya", "quote": "Last month we heard about three bad syncs from operators, not from our own systems.",
        "scene": "There are hundreds of operator databases and nobody watching them. Put monitors on yours.",
        "mission": "Turn \"what must always be true\" into expectations that pass on clean data."},
    3: {"previously": "Your monitors are on and every expectation passes.",
        "who": "Sam", "quote": "Nova's numbers look wrong this week. Can someone tell me why?",
        "scene": "Minute 11: something broke in every operator's feed - a different thing for each of you. Priya forwards Sam's call.",
        "mission": "Find which check failed, which rows and batch caused it, and say it in one sentence Priya can send to Sam."},
    4: {"previously": "You know what broke and why.",
        "who": "Priya", "quote": "Sam's board report goes out at noon. Can we stop the bad numbers spreading, and hear about it first next time?",
        "scene": "Finding the cause is half the job. Now contain it and make the next failure tell you.",
        "mission": "Add a circuit breaker on REPORTING and an alert on the check that matters."},
    5: {"previously": "Your operator is fixed, contained and alerting.",
        "who": "Priya", "quote": "It's my morning stand-up. Which operators do I call first, and about what?",
        "scene": "Every attendee's operator had a different fault. Priya needs one picture of all of them.",
        "mission": "Read the fleet view, group the failures, and sketch how this reaches every operator database."},
}

TURNS = {
    1: {"changed": "You can name every layer between your operator's database and Nova, and you've seen why Nova has two answers for active members.",
        "next": "Next: put monitors on it before something breaks."},
    2: {"changed": "Your operator's pipeline is checked every 5 minutes, serverless, with a pass/fail answer for each rule.",
        "next": "Next: the facilitator breaks something in every operator's feed."},
    3: {"changed": "Priya has a one-sentence root cause, with the batch and the rows, to send to Sam.",
        "next": "Next: stop it spreading and make the next one alert you."},
    4: {"changed": "REPORTING pauses while Bronze is failing and resumes by itself, and the critical check now emails you.",
        "next": "Next: Priya's stand-up - every operator at once."},
    5: {"changed": "Priya can see every operator's health in one view and knows who to call first.",
        "next": "Epilogue below."},
}

# One ticket per fault (the facilitator assigns faults round-robin; attendees don't know theirs in advance)
FAULT_TICKETS = {
    "BIFROST_REPLAY": ("CS-2101", "\"Nova says we have more active members than our front desk can count.\""),
    "MERGE_TASK_STALLED": ("CS-2102", "\"Nothing in Nova has changed since this morning.\""),
    "REFUND_SIGN_FLIP": ("CS-2103", "\"Today's revenue in Nova is far too low.\""),
    "ORPHAN_ATTENDANCE": ("CS-2104", "\"Some classes show more than 100% attendance.\""),
    "TENANT_LEAK": ("CS-2105", "\"I can see members who aren't ours.\""),
    "STATUS_DRIFT": ("CS-2106", "\"Two of your screens disagree on active members.\""),
}

TICKETS = {
    "s3": {"id": "CS-2100", "time": "09:12", "from": "Sam, your operator (phone)", "operator": "Your operator",
           "severity": "High", "status": "Open - assigned to you",
           "summary": "\"Nova's numbers look wrong this week. Can someone tell me why?\"",
           "note": "Your operator received one of six faults. The checks you added in Session 2 will tell you which."},
}

TIMELINES = {
    "without": [("08:55", "A bad merge batch lands in six operator databases"),
                ("09:01", "Nova refreshes with the wrong numbers for all six"),
                ("09:12", "The first operator rings Customer Success"),
                ("11:00", "Priya has four tickets open; engineering checks each database by hand"),
                ("Next day", "Last root cause found; two operators sent wrong numbers to their boards")],
    "with": [("08:55", "Same bad batches arrive"),
             ("09:00", "Scheduled checks fail in each affected operator database"),
             ("09:01", "Circuit breakers pause REPORTING; critical checks email on-call"),
             ("09:05", "Fleet view shows six operators, six signatures"),
             ("09:15", "Priya calls the operators first, with the cause and the fix")],
}

EPILOGUE = ("**Epilogue.** By Priya's stand-up every operator in the room is green again, and she called the affected "
            "operators before they called her. Next: the same checks, deployed to every operator database by DCM - "
            "see *Scaling to every operator* and Bonus B3.")

SAY_THIS = {
    0: "It's Tuesday at Gladstone. Each of you is on call for one operator on Nova. In 30 minutes, something will break in every one of them - and you'll find out before the operator does.",
    1: "First, learn the pipeline you're on call for, and what its numbers say on a good day.",
    2: "Nothing is broken yet. Put monitors on your operator now.",
    3: "I've just broken something in every operator - a different thing for each of you. Your operator is on the phone. Find out what happened.",
    4: "Now stop it spreading, and make sure the next one emails you instead of the operator calling.",
    5: "Priya's stand-up: which operators do we call first? Let's look at all of you at once.",
}


# ── renderers (native Streamlit, shared by the live and static guides) ──────────
def story_arc(current: int):
    labels = []
    for i, name in enumerate(ARC, 1):
        if i < current:
            labels.append(f":green-badge[:material/check: {name}]")
        elif i == current:
            labels.append(f":blue-badge[**{i}. {name}**]")
        else:
            labels.append(f":gray-badge[{i}. {name}]")
    st.markdown(" &nbsp;:material/arrow_forward:&nbsp; ".join(labels))


def chapter(n: int):
    c = CHAPTERS[n]
    with st.container(border=True):
        story_arc(n)
        st.caption(f":material/history: **Previously:** {c['previously']}")
        avatar = next(p["icon"] for p in CAST if p["name"] == c["who"])
        with st.chat_message(c["who"], avatar=avatar):
            st.markdown(f"**{c['who']}:** *\"{c['quote']}\"*")
        st.markdown(c["scene"])
        st.markdown(f":material/flag: **Your mission:** {c['mission']}")


def ticket(key: str, fault_code: str | None = None, operator: str | None = None):
    t = dict(TICKETS.get(key, TICKETS["s3"]))
    if fault_code in FAULT_TICKETS:
        t["id"], t["summary"] = FAULT_TICKETS[fault_code]
    if operator:
        t["operator"] = operator
    with st.container(border=True):
        h1, h2 = st.columns([3, 1], vertical_alignment="center")
        h1.markdown(f"#### :material/confirmation_number: {t['id']} - {t['operator']}")
        h2.markdown(f":red-badge[{t['severity']}]")
        st.markdown(f"**{t['summary']}**")
        st.caption(f"Opened {t['time']} by {t['from']} | {t['status']}")
        st.caption(f":material/lightbulb: {t['note']}")


def turn(n: int):
    t = TURNS[n]
    with st.container(border=True):
        st.markdown(f":material/auto_stories: **What changed:** {t['changed']}")
        st.caption(t["next"])


def cast():
    cols = st.columns(len(CAST))
    for col, p in zip(cols, CAST):
        with col.container(border=True, height="stretch"):
            st.markdown(f"##### {p['icon']} {p['name']}")
            st.caption(p["role"])
            st.markdown(p["says"])


def timelines():
    left, right = st.columns(2)
    for col, key, title, icon in [(left, "without", "A Tuesday without monitors", ":material/sentiment_dissatisfied:"),
                                  (right, "with", "The same Tuesday with monitors", ":material/verified_user:")]:
        with col.container(border=True, height="stretch"):
            st.markdown(f"##### {icon} {title}")
            for when, what in TIMELINES[key]:
                st.markdown(f"`{when}` {what}")


def epilogue():
    st.success(EPILOGUE, icon=":material/celebration:")
