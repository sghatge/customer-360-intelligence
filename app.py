import json
from datetime import datetime, timezone
import pandas as pd
import streamlit as st
st.set_page_config(page_title="AEP Customer 360 Lab",page_icon="🧩",layout="wide")
st.title("🧩 Adobe Experience Platform | Customer 360 Lab")
st.caption("Hands-on simulator: XDM profile foundation, identity stitching and consent-aware audiences")
st.info("Synthetic learning data only. This app does not connect to an Adobe tenant or ingest data.")
profiles=[
{"crm_id":"C-1001","name":"Aarav Mehta","email":"aarav@example.test","ecid":"ECID-9001","tier":"GOLD","ltv":48200,"email_ok":True,"sms_ok":True,"last_seen":2},
{"crm_id":"C-1002","name":"Diya Shah","email":"diya@example.test","ecid":"ECID-9002","tier":"SILVER","ltv":12400,"email_ok":False,"sms_ok":True,"last_seen":8},
{"crm_id":"C-1003","name":"Kabir Rao","email":"kabir@example.test","ecid":"ECID-9003","tier":"PLATINUM","ltv":96500,"email_ok":True,"sms_ok":False,"last_seen":1},
{"crm_id":"C-1004","name":"Mira Iyer","email":"mira@example.test","ecid":"ECID-9004","tier":"GOLD","ltv":35600,"email_ok":True,"sms_ok":True,"last_seen":42},
{"crm_id":"C-1005","name":"Neil Kapoor","email":"neil@example.test","ecid":"ECID-9005","tier":"BRONZE","ltv":3900,"email_ok":False,"sms_ok":False,"last_seen":95}]
events=[
{"event_id":"EV-01","crm_id":"C-1001","ecid":"ECID-9001","event_type":"product_view","product":"Phone X","event_time":"2026-11-24T08:05:00Z"},
{"event_id":"EV-02","crm_id":"C-1001","ecid":"ECID-9001","event_type":"add_to_cart","product":"Phone X","event_time":"2026-11-24T08:08:00Z"},
{"event_id":"EV-03","crm_id":"C-1002","ecid":"ECID-9002","event_type":"purchase","product":"Watch Z","event_time":"2026-11-23T12:00:00Z"},
{"event_id":"EV-04","crm_id":"C-1003","ecid":"ECID-9003","event_type":"support_case_opened","product":"Service","event_time":"2026-11-24T07:40:00Z"},
{"event_id":"EV-05","crm_id":"C-1004","ecid":"ECID-9004","event_type":"email_click","product":"Care Plan","event_time":"2026-11-20T10:00:00Z"}]
df=pd.DataFrame(profiles); ev=pd.DataFrame(events)
x,y,z=st.columns(3); x.metric("Profiles",len(df)); y.metric("Events",len(ev)); z.metric("Identity namespaces",3)
t1,t2,t3,t4=st.tabs(["Profile explorer","Identity graph","Audience builder","Event validator"])
with t1:
 p=st.selectbox("Choose a customer",profiles,format_func=lambda x:f"{x['name']} · {x['crm_id']}")
 l,r=st.columns(2)
 with l:
  st.subheader(p["name"]); st.write("CRM ID:",p["crm_id"]); st.write("Email:",p["email"]); st.write("Tier:",p["tier"]); st.metric("Lifetime value",f"₹{p['ltv']:,}")
 with r:
  st.write("Email consent:", "Opted in" if p["email_ok"] else "Opted out"); st.write("SMS consent:","Opted in" if p["sms_ok"] else "Not opted in"); st.write("Last seen:",f"{p['last_seen']} days ago")
 st.dataframe(ev[ev.crm_id==p["crm_id"]],use_container_width=True,hide_index=True)
 with st.expander("XDM-inspired profile payload"):
  st.code(json.dumps({"_id":p["crm_id"],"identityMap":{"CRMID":[p["crm_id"]],"ECID":[p["ecid"]],"Email":[p["email"]]},"person":{"name":p["name"],"email":p["email"]},"loyalty":{"tier":p["tier"],"lifetimeValue":p["ltv"]},"consents":{"email":p["email_ok"],"sms":p["sms_ok"]}},indent=2),language="json")
with t2:
 p=st.selectbox("Profile identity graph",profiles,key="graph",format_func=lambda x:x["name"])
 st.markdown(f"**CRM ID:** {p['crm_id']}  →  **ECID:** {p['ecid']}  →  **Email:** {p['email']}")
 st.success("Three identifiers are linked in this synthetic profile.")
 st.warning("Do not merge people solely because they share an email. Validate namespace configuration, provenance and merge policy.")
with t3:
 tiers=st.multiselect("Loyalty tier",["BRONZE","SILVER","GOLD","PLATINUM"],default=["GOLD","PLATINUM"])
 floor=st.slider("Minimum lifetime value (₹)",0,100000,20000,5000)
 days=st.slider("Seen within last N days",1,120,30)
 channel=st.selectbox("Activation channel",["Email","SMS"])
 consent="email_ok" if channel=="Email" else "sms_ok"
 aud=df[df.tier.isin(tiers)&(df.ltv>=floor)&(df.last_seen<=days)&df[consent]]
 st.metric("Eligible profiles after consent",len(aud))
 st.dataframe(aud[["crm_id","name","tier","ltv","last_seen",consent]],use_container_width=True,hide_index=True)
 st.caption("Production activation also evaluates suppression, channel availability, jurisdiction and policy.")
with t4:
 sample={"event_id":"EV-TEST","event_type":"add_to_cart","crm_id":"C-1001","ecid":"ECID-9001","event_time":datetime.now(timezone.utc).isoformat(),"product_id":"SKU-100"}
 raw=st.text_area("Incoming event JSON",json.dumps(sample,indent=2),height=220)
 if st.button("Validate event",type="primary"):
  errors=[]
  try:
   o=json.loads(raw)
   for k in ["event_id","event_type","event_time"]:
    if not o.get(k): errors.append("Missing required field: "+k)
   if not any(o.get(k) for k in ["crm_id","ecid","email"]): errors.append("At least one identity is required.")
   if o.get("event_type") not in ["product_view","add_to_cart","purchase","support_case_opened","email_click"]: errors.append("Unsupported event type.")
   if o.get("event_time"): datetime.fromisoformat(o["event_time"].replace("Z","+00:00"))
  except Exception as e: errors.append("Invalid JSON or timestamp: "+str(e))
  if errors:
   for e in errors: st.error(e)
  else: st.success("Passed lab structural checks; not full Adobe XDM schema validation."); st.json(o)
with st.expander("Architecture and checkpoints"):
 st.markdown("**XDM first:** define schemas, field groups, identities and event semantics before ingestion.\n\n**Datasets:** hold records conforming to schemas; profile-enabled datasets contribute to Real-Time Customer Profile.\n\n**Identity:** connect CRM ID, ECID and email using explicit namespaces.\n\n**Consent:** synchronize the configured source of truth and enforce it before activation.\n\n**Query Service:** use bounded time windows and cost controls; avoid unbounded scans.")
st.caption("Source alignment: Consolidated Adobe/AEP/AJO/Salesforce Guide and MarTech 2030 Governed AI Agent Architecture. Fabricated sample data.")
