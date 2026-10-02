# Save rebuild source audit

Run `python portable/tests/save/rebuild/audit_source.py`. It verifies pinned function names, exact source-order anchors, nested helper edges, and relevant SaveRec row identities against checked-in source and the retained V3 binding map. The JSON output is an audit artifact, not a behavioral differential.
