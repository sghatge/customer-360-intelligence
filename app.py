import json
from datetime import datetime, timezone
import pandas as pd
import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from aep_engine import validate_against_contract, detect_identity_collisions, assess_identity_conflicts, evaluate_lab_audience, apply_entry_exit_rule, run_read_only_sql

st.set_page_config(page_title="AEP Customer 360 Lab", page_icon="🧩", layout="wide")
st.title("🧩 Adobe Experience Platform | Customer 360 Lab")
st.caption("Hands-on simulator: XDM, unified profiles, identity stitching, consent-aware audiences and activation readiness")
st.info("Synthetic learning data only. This lab does not connect to an Adobe tenant, ingest production data or activate real audiences.")

with st.sidebar:
    st.header("Learning path")
    st.markdown(
        "1. **Profile foundation** — inspect customer attributes\n"
        "2. **Identity resolution** — review CRM ID, ECID and email\n"
        "3. **Data modelling** — explore XDM and validate events\n"
        "4. **Audience governance** — apply segment and consent rules\n"
        "5. **Activation** — inspect the AJO / Salesforce hand-off"
    )
    st.divider()
    st.caption("Recommended: complete the tabs from left to right, then repeat with a different synthetic customer.")
    st.info("Sandbox boundary: all records and actions are simulated. No Adobe or Salesforce tenant is connected.")

PROFILES = [
    {"crm_id":"C-1001","name":"Aarav Mehta","email":"aarav@example.test","ecid":"ECID-9001","tier":"GOLD","ltv":48200,"email_ok":True,"sms_ok":True,"last_seen":2},
    {"crm_id":"C-1002","name":"Diya Shah","email":"diya@example.test","ecid":"ECID-9002","tier":"SILVER","ltv":12400,"email_ok":False,"sms_ok":True,"last_seen":8},
    {"crm_id":"C-1003","name":"Kabir Rao","email":"kabir@example.test","ecid":"ECID-9003","tier":"PLATINUM","ltv":96500,"email_ok":True,"sms_ok":False,"last_seen":1},
    {"crm_id":"C-1004","name":"Mira Iyer","email":"mira@example.test","ecid":"ECID-9004","tier":"GOLD","ltv":35600,"email_ok":True,"sms_ok":True,"last_seen":42},
    {"crm_id":"C-1005","name":"Neil Kapoor","email":"neil@example.test","ecid":"ECID-9005","tier":"BRONZE","ltv":3900,"email_ok":False,"sms_ok":False,"last_seen":95},
]
BASE_EVENTS = [
    {"event_id":"EV-01","crm_id":"C-1001","ecid":"ECID-9001","event_type":"product_view","product":"Phone X","event_time":"2026-11-24T08:05:00Z"},
    {"event_id":"EV-02","crm_id":"C-1001","ecid":"ECID-9001","event_type":"add_to_cart","product":"Phone X","event_time":"2026-11-24T08:08:00Z"},
    {"event_id":"EV-03","crm_id":"C-1002","ecid":"ECID-9002","event_type":"purchase","product":"Watch Z","event_time":"2026-11-23T12:00:00Z"},
    {"event_id":"EV-04","crm_id":"C-1003","ecid":"ECID-9003","event_type":"support_case_opened","product":"Service","event_time":"2026-11-24T07:40:00Z"},
    {"event_id":"EV-05","crm_id":"C-1004","ecid":"ECID-9004","event_type":"email_click","product":"Care Plan","event_time":"2026-11-20T10:00:00Z"},
]
EVENT_TYPES = ["product_view","add_to_cart","purchase","support_case_opened","email_click"]
XDM_FIELDS = [
    ("_id","string","Record identifier","Required"),
    ("timestamp","dateTime","Event occurrence time","Required for ExperienceEvent"),
    ("eventType","string","Business event classification","Required for this lab contract"),
    ("identityMap","map","Identity namespace and identity values","Identity resolution"),
    ("person.name","string","Customer display name","Profile attribute"),
    ("person.email","string","Email address","Profile attribute; handle as personal data"),
    ("loyalty.tier","string","Loyalty classification","Profile attribute"),
    ("consents.marketing.email","boolean","Email marketing permission","Governance signal"),
    ("consents.marketing.sms","boolean","SMS marketing permission","Governance signal"),
]
if "events" not in st.session_state:
    st.session_state.events = BASE_EVENTS.copy()
if "ingest_log" not in st.session_state:
    st.session_state.ingest_log = []

profiles_df = pd.DataFrame(PROFILES)
c1,c2,c3,c4 = st.columns(4)
c1.metric("Unified profiles",len(PROFILES))
c2.metric("Experience events",len(st.session_state.events))
c3.metric("Identity namespaces",3)
c4.metric("Lab ingestions",len(st.session_state.ingest_log))

tabs = st.tabs(["Profile explorer","Identity graph","Audience builder","XDM schema explorer","Event ingestion lab","Activation preview","Enterprise rule engine","Query Service SQL lab","AJO journey preview","Lifecycle integration hub"])
with tabs[0]:
    selected = st.selectbox("Choose a customer",PROFILES,format_func=lambda p:f"{p['name']} · {p['crm_id']}")
    left,right = st.columns(2)
    with left:
        st.subheader(selected["name"])
        st.write("CRM ID:",selected["crm_id"])
        st.write("Email:",selected["email"])
        st.write("Loyalty tier:",selected["tier"])
        st.metric("Lifetime value",f"₹{selected['ltv']:,}")
    with right:
        st.write("Email consent:", "Opted in" if selected["email_ok"] else "Opted out")
        st.write("SMS consent:", "Opted in" if selected["sms_ok"] else "Opted out")
        st.write("Last seen:",f"{selected['last_seen']} days ago")
        st.write("Profile status: Synthetic / lab record")
    customer_events = pd.DataFrame(st.session_state.events)
    if not customer_events.empty:
        st.subheader("Customer experience events")
        st.dataframe(customer_events[customer_events.crm_id==selected["crm_id"]],use_container_width=True,hide_index=True)
    payload = {"_id":selected["crm_id"],"identityMap":{"CRMID":[selected["crm_id"]],"ECID":[selected["ecid"]],"Email":[selected["email"]]},"person":{"name":selected["name"],"email":selected["email"]},"loyalty":{"tier":selected["tier"],"lifetimeValue":selected["ltv"]},"consents":{"marketing":{"email":selected["email_ok"],"sms":selected["sms_ok"]}}}
    with st.expander("View XDM-inspired profile payload"):
        st.code(json.dumps(payload,indent=2),language="json")

with tabs[1]:
    person = st.selectbox("Select profile identity graph",PROFILES,key="identity_profile",format_func=lambda p:p["name"])
    st.subheader(f"Identity graph · {person['name']}")
    st.graphviz_chart(f'''
    digraph G {{
      rankdir=LR; graph [bgcolor="transparent"]; node [shape=box,style="rounded,filled",fontname="Arial",color="#8CA4C8",fillcolor="#EEF4FF"];
      crm [label="CRM ID\n{person['crm_id']}"];
      ecid [label="ECID\n{person['ecid']}"];
      email [label="Email\n{person['email']}"];
      profile [label="Unified Profile\n{person['name']}",fillcolor="#E2F5E9",color="#4A9B68"];
      crm -> profile; ecid -> profile; email -> profile;
    }}
    ''')
    st.caption("Illustrative identity links. A production identity graph depends on configured namespaces, identity type, graph limits and merge policies.")
    st.warning("Identity design checkpoint: do not automatically merge records solely because an email value matches. Validate provenance, namespace configuration and ownership rules.")
    st.dataframe(pd.DataFrame([
        {"Namespace":"CRMID","Identity value":person["crm_id"],"Illustrative role":"Known customer identifier"},
        {"Namespace":"ECID","Identity value":person["ecid"],"Illustrative role":"Digital experience identifier"},
        {"Namespace":"Email","Identity value":person["email"],"Illustrative role":"Contact identifier"},
    ]),use_container_width=True,hide_index=True)

    st.markdown("#### Identity conflict review simulator")
    scenario = st.selectbox(
        "Choose a synthetic identity scenario",
        ["Clean identifiers", "Shared email across CRM IDs", "Shared ECID across CRM IDs"],
        key="identity_conflict_scenario",
    )
    review_profiles = [dict(p) for p in PROFILES]
    if scenario == "Shared email across CRM IDs":
        review_profiles.append({**person, "crm_id":"C-REVIEW-EMAIL", "email":person["email"].upper(), "ecid":"ECID-REVIEW-EMAIL"})
    elif scenario == "Shared ECID across CRM IDs":
        review_profiles.append({**person, "crm_id":"C-REVIEW-ECID", "email":"review@example.test", "ecid":person["ecid"]})
    conflicts = assess_identity_conflicts(review_profiles)
    if conflicts:
        st.warning("Potential identity conflict detected. The simulator flags it for human/data-steward review and does not merge profiles.")
        st.dataframe(pd.DataFrame(conflicts), use_container_width=True, hide_index=True)
    else:
        st.success("No shared ECID or email across different CRM IDs was detected in this scenario.")
    st.caption("Lab rule only: shared identifiers are review signals, not proof that two customer records represent the same person. Production outcomes depend on namespace identity types, graph configuration, merge policies and data stewardship.")

with tabs[2]:
    st.subheader("Real-Time CDP audience builder")
    st.caption("Build an explainable audience from synthetic profile attributes, experience events and channel consent.")
    a,b,c = st.columns(3)
    with a:
        tiers = st.multiselect("Loyalty tier",["BRONZE","SILVER","GOLD","PLATINUM"],default=["GOLD","PLATINUM"],key="rtcdp_tiers")
    with b:
        min_ltv = st.number_input("Minimum lifetime value (₹)",min_value=0,max_value=200000,value=20000,step=5000,key="rtcdp_ltv")
    with c:
        recency = st.slider("Seen within last N days",1,120,30,key="rtcdp_recency")
    d,e = st.columns(2)
    with d:
        channel = st.radio("Activation channel",["Email","SMS"],horizontal=True,key="rtcdp_channel")
    with e:
        required_event = st.selectbox("Required experience event",["Any event"] + EVENT_TYPES,key="rtcdp_event")
    audience_name = st.text_input("Audience name",value="High-value active customers",key="rtcdp_name")
    audience_results = evaluate_lab_audience(
        PROFILES, st.session_state.events, set(tiers), min_ltv, recency, channel, required_event
    )
    results_df = pd.DataFrame(audience_results)
    eligible_df = results_df[results_df.eligible]
    segment_count = int(results_df.segment_match.sum())
    event_count = int((results_df.segment_match & results_df.event_match).sum())
    consent_blocked = int((results_df.segment_match & results_df.event_match & ~results_df.eligible).sum())
    x,y,z,w = st.columns(4)
    x.metric("Profiles in segment",segment_count)
    y.metric("Event qualified",event_count)
    z.metric("Activation eligible",len(eligible_df))
    w.metric("Blocked by consent",consent_blocked)
    st.markdown("**Qualification results — one row per synthetic profile**")
    st.dataframe(results_df,use_container_width=True,hide_index=True)
    st.caption("Decision order: profile segment → required event → channel consent. Consent denial or unknown/false consent blocks activation.")
    st.divider()
    st.markdown("#### Audience membership transitions")
    st.session_state.setdefault("previous_audience_members",set())
    current_members = set(eligible_df.crm_id.tolist())
    transition_rows = []
    for profile in PROFILES:
        was_member = profile["crm_id"] in st.session_state.previous_audience_members
        is_member = profile["crm_id"] in current_members
        transition_rows.append({"crm_id":profile["crm_id"],"name":profile["name"],
                                "previous_member":was_member,"current_member":is_member,
                                "transition":apply_entry_exit_rule(was_member,is_member)})
    transition_df = pd.DataFrame(transition_rows)
    st.dataframe(transition_df,use_container_width=True,hide_index=True)
    if st.button("Save current membership as previous snapshot",key="save_audience_snapshot"):
        st.session_state.previous_audience_members = current_members
        st.success("Membership snapshot saved for this browser session.")
    st.caption("Snapshot is session-local and illustrative. It is not an Adobe segment evaluation schedule or persistent audience store.")
    st.divider()
    st.markdown("#### Activation preview")
    st.write(f"**{audience_name}** · {channel} · {len(eligible_df)} eligible profiles")
    export_columns = ["crm_id","name","tier","ltv","last_seen","consent","reason"]
    export_df = eligible_df[export_columns] if not eligible_df.empty else pd.DataFrame(columns=export_columns)
    st.download_button("Download eligible audience CSV",export_df.to_csv(index=False).encode("utf-8"),
                       file_name="aep_lab_eligible_audience.csv",mime="text/csv",disabled=eligible_df.empty)
    st.caption("CSV is a synthetic activation preview only. A production destination must enforce consent, suppression, jurisdiction, purpose, identity and destination-specific controls.")

with tabs[3]:
    st.subheader("XDM schema field explorer")
    st.write("A simplified learning view of profile and ExperienceEvent field design. It is not an Adobe-exported schema.")
    schema_df = pd.DataFrame(XDM_FIELDS,columns=["Field path","Illustrative type","Purpose","Design note"])
    search = st.text_input("Search field path or purpose")
    if search:
        schema_df = schema_df[schema_df.astype(str).apply(lambda col:col.str.contains(search,case=False,na=False)).any(axis=1)]
    st.dataframe(schema_df,use_container_width=True,hide_index=True)
    st.markdown("**Design checkpoints**")
    st.markdown("- Select the appropriate XDM class and standard/custom field groups.\n- Define identity descriptors and namespaces deliberately.\n- Keep profile attributes distinct from event-level behaviour.\n- Document field ownership, consent semantics and retention.\n- Validate schema compatibility before enabling datasets for Profile.")

    st.divider()
    st.markdown("#### ExperienceEvent contract validator")
    sample_event = {
        "eventId":"LAB-EVENT-001",
        "eventType":"addToCart",
        "timestamp":"2026-11-24T08:00:00Z",
        "identity":{"ecid":"ECID-9001"},
        "commerce":{"currency":"INR","value":2499}
    }
    event_json = st.text_area("Paste or edit a sample event JSON", json.dumps(sample_event, indent=2), height=220)
    if st.button("Validate event against lab contract", key="validate_xdm_event"):
        try:
            parsed_event = json.loads(event_json)
            validation_errors = validate_against_contract(parsed_event, "contracts/experience-event.json")
            if validation_errors:
                st.error("Contract validation failed")
                for error in validation_errors:
                    st.write(f"- {error}")
            else:
                st.success("Event passes the repository's ExperienceEvent learning contract.")
        except json.JSONDecodeError as exc:
            st.error(f"Invalid JSON: {exc}")
        except (OSError, RuntimeError, ValueError) as exc:
            st.error(f"Validation could not run: {exc}")
    st.caption("This validates the repository's illustrative JSON Schema contract. It does not validate against an Adobe tenant or guarantee tenant schema compatibility.")

with tabs[4]:
    st.subheader("Simulate an ExperienceEvent")
    st.caption("Accepted events are added to this browser session only; no network ingestion or Adobe API call occurs.")
    with st.form("event_ingestion_form"):
        event_id = st.text_input("Event ID",value=f"EV-LAB-{len(st.session_state.events)+1:03d}")
        event_type = st.selectbox("Event type",EVENT_TYPES)
        identity_choice = st.selectbox("Link to synthetic profile",PROFILES,format_func=lambda p:f"{p['name']} · {p['crm_id']}")
        product = st.text_input("Product or context",value="Phone X")
        event_time = st.text_input("Event timestamp (ISO 8601)",value=datetime.now(timezone.utc).isoformat())
        submitted = st.form_submit_button("Validate and add event",type="primary")
    if submitted:
        errors = []
        if not event_id.strip(): errors.append("Event ID is required.")
        if any(e["event_id"]==event_id.strip() for e in st.session_state.events): errors.append("Event ID already exists.")
        try:
            parsed_time = datetime.fromisoformat(event_time.replace("Z","+00:00"))
            if parsed_time.tzinfo is None: errors.append("Timestamp must include a timezone.")
        except Exception:
            errors.append("Timestamp must be valid ISO 8601 with timezone.")
        if not product.strip(): errors.append("Product/context is required.")
        if errors:
            for err in errors: st.error(err)
        else:
            new_event = {"event_id":event_id.strip(),"crm_id":identity_choice["crm_id"],"ecid":identity_choice["ecid"],"event_type":event_type,"product":product.strip(),"event_time":event_time}
            st.session_state.events.append(new_event)
            st.session_state.ingest_log.append({"event_id":event_id.strip(),"status":"Accepted by lab validator","timestamp":datetime.now(timezone.utc).isoformat()})
            st.success("Event passed lab checks and was added to this session.")
            st.rerun()
    st.markdown("**Session event stream**")
    st.dataframe(pd.DataFrame(st.session_state.events),use_container_width=True,hide_index=True)
    if st.session_state.ingest_log:
        with st.expander("Lab ingestion audit log"):
            st.dataframe(pd.DataFrame(st.session_state.ingest_log),use_container_width=True,hide_index=True)

with tabs[5]:
    st.subheader("AEP → AJO / Salesforce activation hand-off")
    audience = st.session_state.get("audience_export",{"name":"No audience built yet","channel":"—","eligible_ids":[]})
    st.write("Audience:",audience["name"])
    st.write("Proposed channel:",audience["channel"])
    st.metric("Consent-eligible profiles",len(audience["eligible_ids"]))
    st.code(json.dumps({"source":"AEP Customer 360 Lab","audience_name":audience["name"],"channel":audience["channel"],"eligible_profile_ids":audience["eligible_ids"],"activation_status":"SIMULATED_NOT_SENT","downstream_targets":["Adobe Journey Optimizer","Salesforce"]},indent=2),language="json")
    st.warning("This is an activation contract preview only. No audience is exported to AJO or Salesforce and no message is sent.")
    st.markdown("**Production integration checkpoints**")
    st.markdown("1. Confirm audience qualification and identity mapping.\n2. Enforce consent, suppression and destination-specific policies.\n3. Define destination schema, authentication and retry handling.\n4. Reconcile audience counts and activation failures.\n5. Maintain an auditable activation and consent evidence trail.")

with tabs[6]:
    st.subheader("Enterprise validation and identity governance")
    st.markdown("**1. Contract validation**")
    sample_event = {"eventId":"EVT-LAB-9001","eventType":"addToCart","timestamp":datetime.now(timezone.utc).isoformat(),"identity":{"crmId":"C-1001","ecid":"ECID-9001"},"commerce":{"productId":"SKU-DEMO-01","currency":"INR","value":2499}}
    raw_contract = st.text_area("ExperienceEvent JSON", json.dumps(sample_event, indent=2), height=220, key="contract_json")
    if st.button("Validate against versioned JSON Schema", key="validate_contract"):
        try:
            contract_errors = validate_against_contract(json.loads(raw_contract), "contracts/experience-event.json")
            if contract_errors:
                for error in contract_errors: st.error(error)
            else:
                st.success("Passed the repository's synthetic ExperienceEvent JSON Schema contract.")
        except Exception as exc:
            st.error(f"Validation could not run: {exc}")
    st.divider()
    st.markdown("**2. Identity collision review**")
    collision_demo = [
        {"crmId":"C-2001","email":"shared@example.test","source":"CRM"},
        {"crmId":"C-2002","email":"SHARED@example.test","source":"Commerce"}
    ]
    collisions = detect_identity_collisions(collision_demo)
    st.dataframe(pd.DataFrame(collisions), use_container_width=True, hide_index=True)
    st.warning("Shared email across distinct CRM IDs is flagged for review. The lab never auto-merges these records.")
    st.divider()
    st.markdown("**3. Audience membership transitions**")
    was_member = st.toggle("Previously in audience", value=False)
    currently_eligible = st.toggle("Currently meets segment and consent rules", value=True)
    transition = apply_entry_exit_rule(was_member, currently_eligible)
    st.metric("Membership action", transition)
    st.caption("Illustrative deterministic transition: ENTER, EXIT, REMAIN or NOT_IN_AUDIENCE. This is not Adobe's native segment evaluation engine.")

with tabs[7]:
    st.subheader("Query Service practice workbench")
    st.caption("A local, read-only SQL simulation over synthetic profiles and events. It is not Adobe Experience Platform Query Service.")
    samples = {
        "High-value opted-in profiles": "SELECT crm_id, name, tier, ltv FROM profiles WHERE ltv >= 30000 AND email_ok = 1 ORDER BY ltv DESC",
        "Cart events with customer details": "SELECT e.event_id, e.product, p.name, p.email FROM events e JOIN profiles p ON p.crm_id = e.crm_id WHERE e.event_type = 'add_to_cart'",
        "Event volume by type": "SELECT event_type, COUNT(*) AS event_count FROM events GROUP BY event_type ORDER BY event_count DESC",
        "Profiles without recent activity": "SELECT crm_id, name, last_seen FROM profiles WHERE last_seen >= 30 ORDER BY last_seen DESC"
    }
    sample_name = st.selectbox("Load a practice query", list(samples.keys()))
    sql_text = st.text_area("SQL statement", value=samples[sample_name], height=160, key="sql_workbench")
    if st.button("Run read-only query", type="primary", key="run_sql"):
        try:
            result = run_read_only_sql(sql_text, PROFILES, st.session_state.events)
            st.success(f"Query completed · {result['row_count']} rows returned" + (" · display capped at 100 rows" if result["truncated"] else ""))
            st.dataframe(pd.DataFrame(result["rows"], columns=result["columns"]), use_container_width=True, hide_index=True)
        except ValueError as exc:
            st.error(str(exc))
    st.markdown("**Query design controls**")
    st.markdown("- Use explicit time windows and selective predicates in production.\n- Select only required columns; avoid unnecessary wide scans.\n- Validate joins against identity and cardinality assumptions.\n- This simulator uses SQLite in memory; SQL syntax and performance are not identical to Adobe Query Service.")

with tabs[8]:
    st.subheader("AEP audience → AJO journey hand-off")
    audience = st.session_state.get("audience_export", {"name":"Build an audience first","channel":"Email","eligible_ids":[]})
    st.write("Source audience:", audience["name"])
    st.write("Channel:", audience["channel"])
    st.metric("Consent-eligible synthetic profiles", len(audience["eligible_ids"]))
    journey_type = st.selectbox("Journey pattern", ["Abandoned cart recovery","Post-purchase cross-sell","VIP engagement"])
    if journey_type == "Abandoned cart recovery":
        steps = ["Audience qualification: add_to_cart","Wait: illustrative 60 minutes","Re-check purchase event","Re-check channel consent and suppression","Prepare recovery message action"]
        trigger = "add_to_cart"
    elif journey_type == "Post-purchase cross-sell":
        steps = ["Audience qualification: purchase","Wait: illustrative 24 hours","Check product eligibility and recent purchases","Re-check channel consent and suppression","Prepare cross-sell message action"]
        trigger = "purchase"
    else:
        steps = ["Audience qualification: GOLD or PLATINUM","Check recent engagement","Re-check channel consent and suppression","Prepare VIP engagement action"]
        trigger = "profile_qualification"
    for index, step in enumerate(steps, 1):
        st.write(f"{index}. {step}")
    handoff = {"source":"AEP Customer 360 Lab","destination":"Adobe Journey Optimizer","journey_pattern":journey_type,"entry_trigger":trigger,"channel":audience["channel"],"eligible_synthetic_profile_ids":audience["eligible_ids"],"steps":steps,"activation_status":"SIMULATED_NOT_SENT"}
    st.code(json.dumps(handoff, indent=2), language="json")
    st.warning("This is a conceptual journey hand-off only. No AJO journey, profile, message or campaign is created or activated.")


with tabs[9]:
    st.subheader("Cross-platform customer lifecycle")
    st.caption("A synthetic customer journey across AEP → AJO → Salesforce → AEP. Contract-driven simulation only.")
    person = st.selectbox("Lifecycle customer", PROFILES, key="lifecycle_customer", format_func=lambda p:f"{p['name']} · {p['crm_id']}")
    journey = st.selectbox("Lifecycle scenario", ["Abandoned cart recovery","Post-purchase follow-up","VIP service follow-up"])
    preferred = st.selectbox("Proposed channel", ["EMAIL","SMS","NONE"])
    email_consent = "GRANTED" if person["email_ok"] else "DENIED"
    sms_consent = "GRANTED" if person["sms_ok"] else "DENIED"
    channel_ok = (preferred=="EMAIL" and email_consent=="GRANTED") or (preferred=="SMS" and sms_consent=="GRANTED") or preferred=="NONE"
    correlation_id = f"CORR-{person['crm_id']}-{journey.split()[0].upper()}-001"
    lifecycle_steps = [
        {"step":"AEP audience qualification","source":"AEP","eventType":"audience_qualified","status":"ELIGIBLE","reason":"Synthetic profile selected"},
        {"step":"AJO journey entry","source":"AJO","eventType":"journey_entered","status":"SIMULATED","reason":journey+" entry condition met"},
        {"step":"AJO channel decision","source":"AJO","eventType":"message_eligible" if channel_ok else "message_blocked","status":"ELIGIBLE" if channel_ok else "BLOCKED","reason":"Consent granted" if channel_ok else "Selected channel consent is not granted"},
        {"step":"Journey exit checkpoint","source":"AJO","eventType":"journey_exited","status":"EXITED","reason":"Simulated completion checkpoint"},
        {"step":"Salesforce follow-up proposal","source":"SALESFORCE","eventType":"crm_followup_requested","status":"PENDING_REVIEW","reason":"Human approval required before CRM write"}
    ]
    st.dataframe(pd.DataFrame(lifecycle_steps),use_container_width=True,hide_index=True)
    event_payload = {"eventId":"LCE-"+correlation_id,"correlationId":correlation_id,"occurredAt":datetime.now(timezone.utc).isoformat(),"source":"INTEGRATION_SIMULATOR","eventType":"message_eligible" if channel_ok else "message_blocked","customer":{"crmId":person["crm_id"],"ecid":person["ecid"],"email":person["email"]},"journey":{"journeyId":"JRN-LAB-001","journeyName":journey,"step":"channel_decision","channel":preferred},"consent":{"email":email_consent,"sms":sms_consent},"status":"ELIGIBLE" if channel_ok else "BLOCKED","reason":"Consent granted" if channel_ok else "Selected channel consent is not granted","metrics":{"cartValue":0,"currency":"INR"}}
    action_payload = {"requestId":"SF-"+correlation_id,"correlationId":correlation_id,"customer":{"crmId":person["crm_id"],"recordType":"Contact"},"actionType":"CREATE_TASK","subject":"Follow up: "+journey,"description":"Review journey outcome and contact customer through an approved channel.","priority":"Normal","status":"PENDING_HUMAN_APPROVAL","requiresHumanApproval":True,"sourceJourney":"JRN-LAB-001"}
    st.markdown("**Shared lifecycle event contract**")
    try:
        errors = validate_against_contract(event_payload,"contracts/customer-lifecycle-event.json")
        if errors:
            for error in errors: st.error(error)
        else: st.success("Lifecycle event passes the shared JSON Schema contract.")
    except Exception as exc:
        st.error(f"Contract validation unavailable: {exc}")
    st.json(event_payload)
    st.markdown("**Salesforce follow-up request**")
    st.json(action_payload)
    st.warning("No AJO message is sent and no Salesforce record is created. The CRM action remains PENDING_HUMAN_APPROVAL.")
    st.download_button("Download lifecycle event JSON",json.dumps(event_payload,indent=2).encode("utf-8"),file_name="customer_lifecycle_event.json",mime="application/json")

with st.expander("Architecture and learning checkpoints"):
    st.markdown("**XDM:** model schemas and field groups before ingestion. **Datasets:** store records conforming to schemas; Profile-enabled datasets contribute to Real-Time Customer Profile when correctly configured. **Identity:** CRM ID, ECID and email are separate namespace-backed signals. **Consent:** evaluate current purpose and channel permissions before activation. **Activation:** downstream hand-off is simulated here and requires tenant configuration in production.")
st.caption("Source alignment: consolidated Adobe/AEP/AJO/Salesforce learning guide and governed MarTech architecture. Fabricated sample data. This simulator is not a substitute for Adobe product validation.")
