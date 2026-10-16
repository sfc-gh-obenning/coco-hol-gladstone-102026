"""Headless smoke test: render every page with AppTest and fail on any exception.
Run: python tools/test_app.py   (from dq-lab/workshop_guide)"""
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
pages = sorted((ROOT / "app_pages").glob("*.py"))
failed = 0
for p in pages:
    at = AppTest.from_file(str(p), default_timeout=30)
    at.session_state["operator_name"] = "NIELS"
    at.run()
    errs = [e.value for e in at.exception]
    code_blocks = "\n".join(c.value for c in at.code)
    leftover = [t for t in ("{SCHEMA}", "{ROLE}", "{FQ_SCHEMA}", "{NAME}") if t in code_blocks]
    md = "\n".join(m.value for m in at.markdown)
    has_refs = "References" in md
    status = "OK " if not errs and not leftover else "ERR"
    if errs or leftover:
        failed += 1
    print(f"{status} {p.name:24s} code={len(at.code):2d} refs={'y' if has_refs else 'n'} "
          f"{'unfilled=' + str(leftover) if leftover else ''} {errs[0][:300] if errs else ''}")
sys.exit(1 if failed else 0)
