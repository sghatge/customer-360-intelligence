import json
from datetime import datetime, timezone
import pandas as pd
import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from aep_engine import validate_against_contract, detect_identity_collisions, apply_entry_exit_rule

st.set_page_config(page_title="AEP Customer 360 Lab", page_icon="🧩", layout="wide")
st.title("🧩 Adobe Experience Platform | Customer 360 Lab")
st.caption("Hands-on simulator: XDM, unified profiles, identity stitching, consent-aware audiences and activation readiness")
st.info("Synthetic learning data only. This lab does not connect to an Adobe tenant, ingest production data or activate real audiences.")

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
events_df = pd.DataFrame(st.session_state.events)
c1,c2,c3,c4 = st.columns(4)
c1.metric("Unified profiles",len(PROFILES))
c2.metric("Experience events",len(st.session_state.events))
c3.metric("Identity namespaces",3)
c4.metric("Lab ingestions",len(st.session_state.ingest_log))

tabs = st.tabs(["Profile explorer","Identity graph","Audience builder","XDM schema explorer","Event ingestion lab","Activation preview","Enterprise rule engine"])
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
      crm [label="CRM ID\\n{person['crm_id']}"];
      ecid [label="ECID\\n{person['ecid']}"];
      email [label="Email\\n{person['email']}"];
      profile [label="Unified Profile\\n{person['name']}",fillcolor="#E2F5E9",color="#4A9B68"];
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

with tabs[2]:
    st.subheader("Build a consent-aware audience")
    a,b,c = st.columns(3)
    with a:
        tiers = st.multiselect("Loyalty tier",["BRONZE","SILVER","GOLD","PLATINUM"],default=["GOLD","PLATINUM"])
    with b:
        min_ltv = st.number_input("Minimum lifetime value (₹)",min_value=0,max_value=200000,value=20000,step=5000)
    with c:
        recency = st.slider("Seen within last N days",1,120,30)
    channel = st.radio("Activation channel",["Email","SMS"],horizontal=True)
    consent_field = "email_ok" if channel=="Email" else "sms_ok"
    candidate = profiles_df[profiles_df.tier.isin(tiers) & (profiles_df.ltv>=min_ltv) & (profiles_df.last_seen<=recency)]
    eligible = candidate[candidate[consent_field] == True]
    excluded = candidate[candidate[consent_field] == False]
    x,y,z = st.columns(3)
    x.metric("Segment matches",len(candidate))
    y.metric("Consent eligible",len(eligible))
    z.metric("Excluded by consent",len(excluded))
    st.markdown("**Eligible profiles**")
    st.dataframe(eligible[["crm_id","name","tier","ltv","last_seen",consent_field]],use_container_width=True,hide_index=True)
    if not excluded.empty:
        with st.expander("View profiles excluded by channel consent"):
            st.dataframe(excluded[["crm_id","name","tier",consent_field]],use_container_width=True,hide_index=True)
    st.caption("Lab rule: consent is evaluated after segment matching. A production policy must also check suppression, jurisdiction, channel eligibility, purpose and current consent source.")
    audience_name = st.text_input("Audience name",value="High-value active customers")
    st.session_state["audience_export"] = {"name":audience_name,"channel":channel,"eligible_ids":eligible.crm_id.tolist()}
    st.download_button("Download eligible audience CSV",eligible.to_csv(index=False).encode("utf-8"),file_name="aep_lab_eligible_audience.csv",mime="text/csv",disabled=eligible.empty)

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

with st.expander("Architecture and learning checkpoints"):
    st.markdown("**XDM:** model schemas and field groups before ingestion. **Datasets:** store records conforming to schemas; Profile-enabled datasets contribute to Real-Time Customer Profile when correctly configured. **Identity:** CRM ID, ECID and email are separate namespace-backed signals. **Consent:** evaluate current purpose and channel permissions before activation. **Activation:** downstream hand-off is simulated here and requires tenant configuration in production.")
st.caption("Source alignment: consolidated Adobe/AEP/AJO/Salesforce learning guide and governed MarTech architecture. Fabricated sample data. This simulator is not a substitute for Adobe product validation.")
