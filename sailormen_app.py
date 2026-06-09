"""
Sailormen 363 Sale — Bid Optimization Engine
Streamlit + OR-Tools version · Case 26-10451-RAM · GuideBoat Advisors
"""
import streamlit as st
import pandas as pd
from ortools.sat.python import cp_model
import time, uuid, json

st.set_page_config(
    page_title="Sailormen 363 · Bid Optimizer",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main .block-container { padding-top: 1rem; max-width: 1400px; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { padding: 8px 20px; border-radius: 8px; }
    div[data-testid="metric-container"] { background:#f5f4f0; border-radius:8px; padding:12px; }
    .win-row { background: #eaf3de; border-radius:6px; padding:6px 10px; margin:3px 0; }
    .sh-row  { background: #faeeda; border-radius:6px; padding:6px 10px; margin:3px 0; }
    .fee-row { background: #fcebeb; border-radius:6px; padding:6px 10px; margin:3px 0; }
    h1 { font-size:1.4rem !important; }
    h3 { font-size:1.0rem !important; }
</style>
""", unsafe_allow_html=True)

# ── Case constants ─────────────────────────────────────────────────────────────
CASE = dict(
    bidDeadline="June 11, 2026",
    auction="June 15, 2026",
    auctionVenue="JW Marriott Miami",
    closing="June 30, 2026",
    expReimbPerStore=1000,
)

MARKET_STORES = {
    "Jacksonville": [128,129,130,131,132,146,148,150,151,152,154,155,156,157,
                     160,162,163,183,187,190,196,199,210,213,214,221,229,250],
    "Orlando":      [102,103,107,109,112,113,114,115,116,117,118,119,120,121,
                     122,123,124,125,126,127,177,178,179,230,246],
    "Miami":        [1,2,3,4,5,6,7,8,9,10,11,12,17,18,54,55,167,198,218,220],
    "Tampa":        [93,95,97,99,100,101,104,105,106,171,194,242,251,901,902],
    "Tallahassee":  [139,140,141,142,143,180,181,185,203,211,228,232,238,241],
    "Pensacola":    [28,29,30,31,184,186,191,193,207,212,219],
    "Savannah":     [170,200,209,223,224,225],
}
ALL_STORES = [s for ss in MARKET_STORES.values() for s in ss]
STORE_TO_MKT = {s: m for m, ss in MARKET_STORES.items() for s in ss}

STORE_DATA = {1:{"sales":2357234,"ebitda":418671},2:{"sales":1983880,"ebitda":309413},3:{"sales":2220696,"ebitda":636543},4:{"sales":1553893,"ebitda":200012},5:{"sales":2004655,"ebitda":290832},6:{"sales":2630819,"ebitda":563987},7:{"sales":3156832,"ebitda":791543},8:{"sales":2734591,"ebitda":561234},9:{"sales":3572386,"ebitda":874841},10:{"sales":2567234,"ebitda":535123},11:{"sales":3456789,"ebitda":930234},12:{"sales":2890123,"ebitda":612345},17:{"sales":3234567,"ebitda":940778},18:{"sales":2789012,"ebitda":747120},28:{"sales":1716298,"ebitda":198234},29:{"sales":1208745,"ebitda":-476},30:{"sales":1987125,"ebitda":347985},31:{"sales":1286075,"ebitda":41136},54:{"sales":1923456,"ebitda":134567},55:{"sales":1654321,"ebitda":187654},93:{"sales":1989874,"ebitda":283476},95:{"sales":1765432,"ebitda":156789},97:{"sales":1675949,"ebitda":91367},99:{"sales":1454123,"ebitda":-988},100:{"sales":2759295,"ebitda":548419},101:{"sales":1619968,"ebitda":138552},102:{"sales":1543210,"ebitda":-62345},103:{"sales":2109876,"ebitda":68863},104:{"sales":1751095,"ebitda":133960},105:{"sales":2080670,"ebitda":268451},106:{"sales":2028459,"ebitda":245596},107:{"sales":2345678,"ebitda":108992},109:{"sales":2234567,"ebitda":93572},112:{"sales":2567890,"ebitda":188886},113:{"sales":2465827,"ebitda":448104},114:{"sales":2678901,"ebitda":239199},115:{"sales":1987654,"ebitda":108247},116:{"sales":2876543,"ebitda":371315},117:{"sales":2345678,"ebitda":155331},118:{"sales":2789012,"ebitda":344892},119:{"sales":1876543,"ebitda":70301},120:{"sales":2972945,"ebitda":593384},121:{"sales":2123456,"ebitda":89604},122:{"sales":2456789,"ebitda":239303},123:{"sales":1765432,"ebitda":-21630},124:{"sales":1987654,"ebitda":51346},125:{"sales":2678901,"ebitda":475144},126:{"sales":2123456,"ebitda":111955},127:{"sales":2890123,"ebitda":548724},128:{"sales":1938757,"ebitda":150026},129:{"sales":1006106,"ebitda":-49044},130:{"sales":1589303,"ebitda":25605},131:{"sales":1165611,"ebitda":-52962},132:{"sales":1489331,"ebitda":116967},139:{"sales":1693082,"ebitda":39701},140:{"sales":1450102,"ebitda":-23634},141:{"sales":1513309,"ebitda":140632},142:{"sales":1413903,"ebitda":81190},143:{"sales":1456789,"ebitda":56789},146:{"sales":1268715,"ebitda":-35425},148:{"sales":1358291,"ebitda":18857},150:{"sales":2003935,"ebitda":265175},151:{"sales":1876543,"ebitda":53389},152:{"sales":2234567,"ebitda":191657},154:{"sales":1123456,"ebitda":-74145},155:{"sales":1765432,"ebitda":47483},156:{"sales":1456789,"ebitda":-35756},157:{"sales":2098765,"ebitda":109065},160:{"sales":1987654,"ebitda":47504},162:{"sales":1876543,"ebitda":80991},163:{"sales":2098765,"ebitda":130332},167:{"sales":2234567,"ebitda":313795},170:{"sales":1839113,"ebitda":124263},171:{"sales":1765739,"ebitda":120285},177:{"sales":2567890,"ebitda":398979},178:{"sales":1876543,"ebitda":34107},179:{"sales":2789012,"ebitda":462481},180:{"sales":1987654,"ebitda":83456},181:{"sales":1654321,"ebitda":67890},183:{"sales":1123456,"ebitda":-79521},184:{"sales":1359720,"ebitda":-71826},185:{"sales":1876543,"ebitda":91568},186:{"sales":1659790,"ebitda":112273},187:{"sales":1456789,"ebitda":38955},190:{"sales":2098765,"ebitda":134044},191:{"sales":1500747,"ebitda":97760},193:{"sales":1207701,"ebitda":-46440},194:{"sales":1381563,"ebitda":-37294},196:{"sales":2456789,"ebitda":353486},198:{"sales":2234567,"ebitda":227129},199:{"sales":2678901,"ebitda":270292},200:{"sales":1676256,"ebitda":128528},203:{"sales":1456789,"ebitda":56789},207:{"sales":1132182,"ebitda":-84800},209:{"sales":1630842,"ebitda":77060},210:{"sales":1234567,"ebitda":-84692},211:{"sales":1567890,"ebitda":56789},212:{"sales":1876543,"ebitda":337828},213:{"sales":1987654,"ebitda":109270},214:{"sales":1765432,"ebitda":-27048},218:{"sales":1876543,"ebitda":37568},219:{"sales":1131343,"ebitda":24290},220:{"sales":1654321,"ebitda":160451},221:{"sales":1234567,"ebitda":-94951},223:{"sales":1498867,"ebitda":44843},224:{"sales":1634517,"ebitda":169885},225:{"sales":1836329,"ebitda":165680},228:{"sales":1456789,"ebitda":56789},229:{"sales":1876543,"ebitda":53757},230:{"sales":2098765,"ebitda":130253},232:{"sales":1234567,"ebitda":45678},238:{"sales":1345678,"ebitda":67890},241:{"sales":1678901,"ebitda":77278},242:{"sales":1301740,"ebitda":-60554},246:{"sales":1987654,"ebitda":76143},250:{"sales":2345678,"ebitda":154232},251:{"sales":1272983,"ebitda":-72864},901:{"sales":1292775,"ebitda":-31238},902:{"sales":2474357,"ebitda":396400}}

CURE_COSTS = {1:97558,2:83818,3:100580,4:76508,5:101280,6:115431,7:154791,8:92884,9:130468,10:84258,11:166509,12:88391,17:120490,18:108375,28:55918,29:78260,30:33054,31:51188,54:100778,55:80395,93:90037,95:77061,97:76361,99:86563,100:96007,101:74417,102:64069,103:94405,104:57833,105:51720,106:53785,107:87594,109:83167,112:73230,113:93251,114:101418,115:47706,116:82939,117:75915,118:69506,119:71435,120:55762,121:82007,122:128631,123:86534,124:69104,125:71423,126:63438,127:62384,128:85675,129:50608,130:62283,131:56481,132:100756,139:38753,140:58059,141:89584,142:48954,143:50890,146:62242,148:80662,150:79042,151:76295,152:98118,154:60822,155:85033,156:106485,157:93298,160:93622,162:84572,163:71896,167:85049,170:95752,171:83009,177:83217,178:76789,179:97898,180:89762,181:70287,183:48120,184:69389,185:91569,186:73311,187:64092,190:102751,191:62990,193:63235,194:68221,196:110866,198:110052,199:124129,200:67937,203:50654,207:74112,209:58965,210:75828,211:69400,212:73581,213:81056,214:76238,218:89883,219:68082,220:73381,221:83387,223:56483,224:46303,225:52489,228:51771,229:104607,230:82807,232:45247,238:54818,241:77279,242:80340,246:86505,250:112351,251:92288,901:61281,902:99547}

MKT_AGG = {m: {"count": len(ss), "sales": sum(STORE_DATA.get(s,{}).get("sales",0) for s in ss), "ebitda": sum(STORE_DATA.get(s,{}).get("ebitda",0) for s in ss)} for m, ss in MARKET_STORES.items()}

# ── Sample bids ────────────────────────────────────────────────────────────────
SAMPLE_BIDS = [
    {"id":"sh1","buyer":"Flynn Restaurant Group","amount":87e6,"storeIds":[1,2,3,4,5,6,7,8,9,10,11,12,17,18,54,55,167,198,218,220,102,103,107,109,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,177,178,179,230,246],"isSH":True,"breakupPct":2.5,"include":True,"plkApproval":False,"comment":"MIA + ORL SH bid","optMode":"bundle","storeAmounts":{}},
    {"id":"sh2","buyer":"GPS Hospitality","amount":32e6,"storeIds":[128,129,130,131,132,146,148,150,151,152,154,155,156,157,160,162,163,183,187,190,196,199,210,213,214,221,229,250,93,95,97,99,100,101,104,105,106,171,194,242,251,901,902],"isSH":True,"breakupPct":2.5,"include":True,"plkApproval":False,"comment":"JAX + TPA SH bid","optMode":"bundle","storeAmounts":{}},
    {"id":"sh3","buyer":"Boddie-Noell","amount":18e6,"storeIds":[139,140,141,142,143,180,181,185,203,211,228,232,238,241,28,29,30,31,184,186,191,193,207,212,219,170,200,209,223,224,225],"isSH":True,"breakupPct":2.5,"include":True,"plkApproval":False,"comment":"TAL + PNS + SAV SH bid","optMode":"bundle","storeAmounts":{}},
    {"id":"b1","buyer":"Carrols Restaurant Group","amount":130e6,"storeIds":ALL_STORES,"isSH":False,"breakupPct":2.5,"include":True,"plkApproval":False,"comment":"","optMode":"bundle","storeAmounts":{}},
    {"id":"b2","buyer":"NPC International","amount":58e6,"storeIds":[1,2,3,4,5,6,7,8,9,10,11,12,17,18,54,55,167,198,218,220],"isSH":False,"breakupPct":2.5,"include":True,"plkApproval":False,"comment":"Miami only","optMode":"bundle","storeAmounts":{}},
    {"id":"b3","buyer":"Ambrosia QSR","amount":32e6,"storeIds":[102,103,107,109,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,177,178,179,230,246],"isSH":False,"breakupPct":2.5,"include":True,"plkApproval":False,"comment":"Orlando only","optMode":"bundle","storeAmounts":{}},
    {"id":"b4","buyer":"Sun Holdings","amount":135e6,"storeIds":ALL_STORES,"isSH":False,"breakupPct":2.5,"include":True,"plkApproval":False,"comment":"","optMode":"bundle","storeAmounts":{}},
]

# ── Session state ──────────────────────────────────────────────────────────────
if "bids" not in st.session_state:
    st.session_state.bids = [dict(b) for b in SAMPLE_BIDS]
if "result" not in st.session_state:
    st.session_state.result = None

def fmt_m(n):
    if n is None: return "—"
    if abs(n) >= 1e6: return f"${n/1e6:.1f}M"
    if abs(n) >= 1e3: return f"${n/1e3:.0f}K"
    return f"${n:,.0f}"

def get_fin(store_ids):
    return {"sales": sum(STORE_DATA.get(s,{}).get("sales",0) for s in store_ids),
            "ebitda": sum(STORE_DATA.get(s,{}).get("ebitda",0) for s in store_ids)}

def get_cure(store_ids):
    return sum(CURE_COSTS.get(s,0) for s in store_ids)

def scope_desc(bid):
    mkts = sorted({STORE_TO_MKT.get(s,"?") for s in bid["storeIds"]})
    if set(bid["storeIds"]) == set(ALL_STORES): return "Full portfolio"
    if len(bid["storeIds"]) == 1: return f"Store {bid['storeIds'][0]}"
    mkt_abbr = {"Jacksonville":"JAX","Orlando":"ORL","Miami":"MIA","Tampa":"TPA","Tallahassee":"TAL","Pensacola":"PNS","Savannah":"SAV"}
    return " + ".join(mkt_abbr.get(m,m[:3]) for m in mkts)

# ── OR-Tools optimizer ─────────────────────────────────────────────────────────
def expand_bids(bids):
    items = []
    for bid in bids:
        if not bid.get("include", True): continue
        if bid.get("optMode") == "perStore" and bid.get("storeAmounts"):
            for sid in bid["storeIds"]:
                price = bid["storeAmounts"].get(str(sid)) or bid["storeAmounts"].get(sid)
                if price:
                    items.append({**bid, "id": f"{bid['id']}_{sid}", "storeIds":[sid],
                                  "amount": float(price)*1e6, "_parentId": bid["id"]})
        else:
            items.append({**bid, "_parentId": bid["id"]})
    return items

def optimize(bids):
    if not bids: return [], 0, 0
    model  = cp_model.CpModel()
    solver = cp_model.CpSolver()
    scale  = 100
    amounts = [round(b["amount"] * scale) for b in bids]
    x = [model.NewBoolVar(f"x{i}") for i in range(len(bids))]
    store_map = {}
    for i, bid in enumerate(bids):
        for s in bid["storeIds"]:
            store_map.setdefault(s, []).append(i)
    for s, idxs in store_map.items():
        if len(idxs) > 1:
            model.Add(sum(x[i] for i in idxs) <= 1)
    model.Maximize(sum(amounts[i]*x[i] for i in range(len(bids))))
    solver.parameters.max_time_in_seconds = 60.0
    solver.parameters.num_search_workers  = 8
    t0 = time.time()
    status = solver.Solve(model)
    ms = round((time.time()-t0)*1000)
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        winners = [bids[i] for i in range(len(bids)) if solver.Value(x[i])==1]
        return winners, sum(b["amount"] for b in winners), ms
    return [], 0, ms

# ── Header ─────────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([3,1])
with col_h1:
    st.markdown("## ⚖️ Sailormen 363 Sale — Bid Optimization Engine")
    st.caption(f"Case 26-10451-RAM · Auction: {CASE['auction']} · {CASE['auctionVenue']} · Bid deadline: {CASE['bidDeadline']}")
with col_h2:
    if st.button("🔄 Reset to sample bids", use_container_width=True):
        st.session_state.bids = [dict(b) for b in SAMPLE_BIDS]
        st.session_state.result = None
        st.rerun()

st.divider()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_bids, tab_matrix, tab_opt, tab_ref = st.tabs(["📋 Bids", "🗺️ Buyers Matrix", "⚡ Optimization", "📊 Reference"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: BIDS
# ══════════════════════════════════════════════════════════════════════════════
with tab_bids:
    bids = st.session_state.bids
    result = st.session_state.result

    # ── Add bid form ──────────────────────────────────────────────────────────
    with st.expander("➕ Add / Edit Bid", expanded=len(bids)==0):
        with st.form("add_bid_form", clear_on_submit=True):
            fc1, fc2, fc3 = st.columns([2,1,1])
            with fc1: buyer    = st.text_input("Buyer name", placeholder="e.g. Carrols Corp")
            with fc2: amount   = st.number_input("Bid amount ($M)", min_value=0.0, step=0.5, format="%.1f")
            with fc3: opt_mode = st.selectbox("Optimize as", ["bundle","perStore"])

            scope_type = st.radio("Scope", ["Full portfolio","Markets","Individual stores"], horizontal=True)
            sel_mkts=[]; sel_stores=[]
            if scope_type == "Markets":
                sel_mkts = st.multiselect("Select markets", list(MARKET_STORES.keys()),
                    format_func=lambda m: f"{m} ({MKT_AGG[m]['count']} stores, {fmt_m(MKT_AGG[m]['ebitda'])} EBITDA)")
            elif scope_type == "Individual stores":
                sel_stores = st.multiselect("Select stores", ALL_STORES,
                    format_func=lambda s: f"{s} — {STORE_TO_MKT.get(s,'')} — {fmt_m(STORE_DATA.get(s,{}).get('ebitda',0))} EBITDA")

            fa1, fa2, fa3 = st.columns(3)
            with fa1: is_sh        = st.checkbox("Stalking horse bid")
            with fa2: breakup_pct  = st.number_input("Breakup fee %", 0.0, 5.0, 2.5, 0.25) if is_sh else 2.5
            with fa3: plk_approval = st.checkbox("PLK Approval ✓")
            comment = st.text_input("Comment (optional)", placeholder="e.g. financing not confirmed")

            submitted = st.form_submit_button("Submit bid", use_container_width=True, type="primary")
            if submitted and buyer and amount > 0:
                if scope_type == "Full portfolio":
                    store_ids = ALL_STORES
                elif scope_type == "Markets":
                    store_ids = [s for m in sel_mkts for s in MARKET_STORES[m]]
                else:
                    store_ids = sel_stores
                if store_ids:
                    st.session_state.bids.append({
                        "id": str(uuid.uuid4())[:8],
                        "buyer": buyer.strip(), "amount": amount*1e6,
                        "storeIds": store_ids, "isSH": is_sh,
                        "breakupPct": breakup_pct, "include": True,
                        "plkApproval": plk_approval, "comment": comment,
                        "optMode": opt_mode, "storeAmounts": {},
                    })
                    st.session_state.result = None
                    st.rerun()

    # ── Bids table ────────────────────────────────────────────────────────────
    if not bids:
        st.info("No bids entered yet. Use the form above to add the first bid.")
    else:
        # Summary metrics
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("Total bids", len(bids))
        m2.metric("Stalking horse", sum(1 for b in bids if b.get("isSH")))
        m3.metric("Included", sum(1 for b in bids if b.get("include",True)))
        m4.metric("Gross (if all accepted)", fmt_m(sum(b["amount"] for b in bids)))
        st.caption("⚠️ Gross assumes no conflicts — run optimizer for actual proceeds")

        st.markdown("---")
        for i, bid in enumerate(bids):
            fin = get_fin(bid["storeIds"])
            ev  = bid["amount"]/fin["ebitda"] if fin["ebitda"] > 0 else None
            result_status = ""
            if result:
                sel_ids = [b["id"] for b in result.get("winners",[])]
                result_status = "✅ Selected" if bid["id"] in sel_ids else "❌ Excluded"

            with st.container():
                c1,c2,c3,c4,c5,c6,c7,c8 = st.columns([3,2,1,1,1,1,1,1])
                with c1:
                    tags = []
                    if bid.get("isSH"):      tags.append("⚓ SH")
                    if bid.get("plkApproval"): tags.append("✅ PLK")
                    if not bid.get("include",True): tags.append("👁️ excl")
                    tag_str = " ".join(tags)
                    st.markdown(f"**{bid['buyer']}** {tag_str}")
                    st.caption(scope_desc(bid))
                with c2: st.markdown(f"**{fmt_m(bid['amount'])}**"); st.caption(f"{ev:.1f}x EV/EBITDA" if ev else "neg EBITDA")
                with c3: st.caption(f"{len(bid['storeIds'])} stores")
                with c4:
                    if result_status:
                        st.caption(result_status)
                with c5:
                    if st.button("⚓", key=f"sh_{i}", help="Toggle SH"):
                        st.session_state.bids[i]["isSH"] = not bid.get("isSH")
                        st.rerun()
                with c6:
                    icon = "👁️" if bid.get("include",True) else "🙈"
                    if st.button(icon, key=f"inc_{i}", help="Toggle include"):
                        st.session_state.bids[i]["include"] = not bid.get("include",True)
                        st.rerun()
                with c7:
                    if st.button("📋", key=f"copy_{i}", help="Copy bid"):
                        new_bid = dict(bid); new_bid["id"] = str(uuid.uuid4())[:8]; new_bid["buyer"] += " (copy)"
                        st.session_state.bids.append(new_bid); st.rerun()
                with c8:
                    if st.button("🗑️", key=f"del_{i}", help="Delete"):
                        st.session_state.bids.pop(i); st.session_state.result=None; st.rerun()

                if bid.get("comment"):
                    st.caption(f"💬 {bid['comment']}")
            st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: BUYERS MATRIX
# ══════════════════════════════════════════════════════════════════════════════
with tab_matrix:
    bids = st.session_state.bids
    if not bids:
        st.info("No bids to display.")
    else:
        mkt_abbr = {"Jacksonville":"JAX","Orlando":"ORL","Miami":"MIA",
                    "Tampa":"TPA","Tallahassee":"TAL","Pensacola":"PNS","Savannah":"SAV"}
        cols = ["Buyer","Scope","Amount"] + [mkt_abbr[m] for m in MARKET_STORES]

        rows = []
        for bid in bids:
            bid_set = set(bid["storeIds"])
            row = {"Buyer": bid["buyer"], "Scope": scope_desc(bid),
                   "Amount": fmt_m(bid["amount"])}
            for mkt, stores in MARKET_STORES.items():
                abbr = mkt_abbr[mkt]
                covered = sum(1 for s in stores if s in bid_set)
                total   = len(stores)
                if covered == total:   row[abbr] = "✅ Full"
                elif covered > 0:      row[abbr] = f"⚡ {covered}/{total}"
                else:                  row[abbr] = "—"
            rows.append(row)

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True,
            column_config={
                "Amount": st.column_config.TextColumn("Amount ($)"),
                **{mkt_abbr[m]: st.column_config.TextColumn(mkt_abbr[m]) for m in MARKET_STORES}
            })

        # Market summaries
        st.markdown("---")
        st.markdown("#### Market financials")
        mkt_rows = []
        for mkt, stores in MARKET_STORES.items():
            agg = MKT_AGG[mkt]
            mkt_rows.append({
                "Market": mkt, "Stores": agg["count"],
                "Net Sales": fmt_m(agg["sales"]), "EBITDA": fmt_m(agg["ebitda"]),
                "Margin": f"{agg['ebitda']/agg['sales']*100:.1f}%" if agg["sales"] > 0 else "—",
                "5x": fmt_m(agg["ebitda"]*5), "6x": fmt_m(agg["ebitda"]*6),
                "7x": fmt_m(agg["ebitda"]*7),
            })
        st.dataframe(pd.DataFrame(mkt_rows), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: OPTIMIZATION
# ══════════════════════════════════════════════════════════════════════════════
with tab_opt:
    bids = st.session_state.bids
    included = [b for b in bids if b.get("include", True)]

    if not included:
        st.warning("No bids included. Enable at least one bid in the Bids tab.")
    else:
        if st.button("⚡ Run Optimizer", type="primary", use_container_width=False):
            with st.spinner("Running OR-Tools CP-SAT solver..."):
                expanded   = expand_bids(included)
                sh_exp     = [b for b in expanded if b.get("isSH")]
                winners, gross, ms = optimize(expanded)
                sh_winners, sh_floor, _ = optimize(sh_exp) if sh_exp else ([], 0, 0)

                # Map expanded winners back to parent bids
                parent_winner_ids = {b.get("_parentId", b["id"]) for b in winners}

                sh_winner_ids  = {b.get("_parentId", b["id"]) for b in sh_winners}
                displaced_sh   = [b for b in sh_exp if b.get("_parentId", b["id"]) in sh_winner_ids
                                                    and b.get("_parentId", b["id"]) not in parent_winner_ids]
                breakup_fees   = sum(
                    b["amount"]*b.get("breakupPct",2.5)/100 + len(b["storeIds"])*CASE["expReimbPerStore"]
                    for b in displaced_sh
                )
                winning_stores  = [s for b in winners for s in b["storeIds"]]
                total_cure      = get_cure(winning_stores)
                net_after_sh    = gross - breakup_fees
                net_after_cure  = net_after_sh - total_cure

                st.session_state.result = {
                    "winners": winners, "gross": gross, "ms": ms,
                    "sh_floor": sh_floor, "displaced_sh": displaced_sh,
                    "breakup_fees": breakup_fees, "winning_stores": winning_stores,
                    "total_cure": total_cure, "net_after_sh": net_after_sh,
                    "net_after_cure": net_after_cure,
                    "parent_winner_ids": parent_winner_ids,
                }
            st.rerun()

        result = st.session_state.result
        if result:
            winners        = result["winners"]
            gross          = result["gross"]
            net_after_cure = result["net_after_cure"]
            net_after_sh   = result["net_after_sh"]
            total_cure     = result["total_cure"]
            displaced_sh   = result["displaced_sh"]
            breakup_fees   = result["breakup_fees"]
            winning_stores = result["winning_stores"]
            sh_floor       = result["sh_floor"]
            ms             = result["ms"]

            # KPI metrics
            k1,k2,k3,k4,k5 = st.columns(5)
            k1.metric("Gross proceeds",    fmt_m(gross))
            k2.metric("SH protections",    fmt_m(-breakup_fees) if breakup_fees else "—")
            k3.metric("Net after SH",      fmt_m(net_after_sh))
            k4.metric("Cure costs",        fmt_m(-total_cure))
            k5.metric("Net after cure",    fmt_m(net_after_cure))
            st.caption(f"✅ Solved in {ms}ms using OR-Tools CP-SAT · {len(winners)} winning bids · {len(winning_stores)}/119 stores covered · SH floor: {fmt_m(sh_floor)}")

            st.markdown("---")
            col_alloc, col_wf = st.columns([3,2])

            with col_alloc:
                st.markdown("#### Winning allocation")
                for bid in sorted(winners, key=lambda b: -b["amount"]):
                    fin  = get_fin(bid["storeIds"])
                    ev   = bid["amount"]/fin["ebitda"] if fin["ebitda"] > 0 else None
                    cure = get_cure(bid["storeIds"])
                    tag  = "⚓ " if bid.get("isSH") else ""
                    with st.expander(f"✅ {tag}{bid['buyer']} — {fmt_m(bid['amount'])} — {scope_desc(bid)}"):
                        sc1, sc2, sc3, sc4 = st.columns(4)
                        sc1.metric("Bid amount", fmt_m(bid["amount"]))
                        sc2.metric("EV/EBITDA", f"{ev:.1f}x" if ev else "—")
                        sc3.metric("Net sales", fmt_m(fin["sales"]))
                        sc4.metric("Cure costs", fmt_m(cure))
                        if bid.get("comment"):
                            st.caption(f"💬 {bid['comment']}")

                        # Store-level breakdown
                        store_rows = []
                        for sid in sorted(bid["storeIds"]):
                            sd = STORE_DATA.get(sid, {})
                            cc = CURE_COSTS.get(sid, 0)
                            store_rows.append({
                                "Store": sid,
                                "Market": STORE_TO_MKT.get(sid,""),
                                "Net Sales": fmt_m(sd.get("sales",0)),
                                "EBITDA": fmt_m(sd.get("ebitda",0)),
                                "Margin": f"{sd.get('ebitda',0)/sd.get('sales',1)*100:.1f}%" if sd.get("sales",0) > 0 else "—",
                                "Cure Cost": fmt_m(cc),
                            })
                        st.dataframe(pd.DataFrame(store_rows), use_container_width=True, hide_index=True)

                if displaced_sh:
                    st.markdown("##### Displaced stalking horse bids")
                    for bid in displaced_sh:
                        fee = bid["amount"]*bid.get("breakupPct",2.5)/100 + len(bid["storeIds"])*CASE["expReimbPerStore"]
                        st.markdown(f"<div class='fee-row'>❌ {bid['buyer']} — breakup fee: {fmt_m(fee)}</div>", unsafe_allow_html=True)

            with col_wf:
                st.markdown("#### Proceeds waterfall")
                wf_data = [
                    ("Gross auction proceeds",       gross,           False),
                ]
                if breakup_fees > 0:
                    wf_data.append(("SH bid protections",         -breakup_fees,    True))
                wf_data += [
                    ("Net after SH protections",     net_after_sh,    False),
                    ("Lease cure costs",             -sum(CURE_COSTS.get(s,0)*0.355 for s in winning_stores), True),
                    ("Tax cure costs",               -sum(CURE_COSTS.get(s,0)*0.369 for s in winning_stores), True),
                    ("PLK cure costs",               -sum(CURE_COSTS.get(s,0)*0.275 for s in winning_stores), True),
                    (f"Total cure ({len(winning_stores)} stores)",  -total_cure, False),
                    ("Net after cure costs",         net_after_cure,  False),
                ]
                wf_df = pd.DataFrame([
                    {"Line item": label, "Amount": fmt_m(val), "Indent": indent}
                    for label, val, indent in wf_data
                ])
                for _, row_wf in wf_df.iterrows():
                    prefix = "  └─ " if row_wf["Indent"] else ""
                    color  = "color:#a32d2d" if "-" in str(row_wf["Amount"]) else "color:#3b6d11"
                    bold   = "" if row_wf["Indent"] else "font-weight:600"
                    st.markdown(
                        f"<div style='display:flex;justify-content:space-between;padding:4px 0;border-bottom:0.5px solid #eee;{bold}'>"
                        f"<span>{prefix}{row_wf['Line item']}</span>"
                        f"<span style='{color}'>{row_wf['Amount']}</span></div>",
                        unsafe_allow_html=True
                    )
                st.caption("Cure costs per KIA 05-24-2026")

            # Uncovered stores
            covered_set = set(winning_stores)
            uncovered   = [s for s in ALL_STORES if s not in covered_set]
            if uncovered:
                st.markdown("---")
                st.markdown(f"#### ⚠️ Uncovered stores ({len(uncovered)})")
                unc_by_mkt = {}
                for s in uncovered:
                    m = STORE_TO_MKT.get(s,"?")
                    unc_by_mkt.setdefault(m,[]).append(s)
                cols_unc = st.columns(len(unc_by_mkt))
                for col_u, (mkt, stores) in zip(cols_unc, unc_by_mkt.items()):
                    col_u.markdown(f"**{mkt}**")
                    col_u.write(", ".join(str(s) for s in stores))

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4: REFERENCE
# ══════════════════════════════════════════════════════════════════════════════
with tab_ref:
    st.markdown("#### Store-level reference — all 119 stores")
    ref_rows = []
    for mkt, stores in MARKET_STORES.items():
        for sid in stores:
            sd = STORE_DATA.get(sid,{})
            sales  = sd.get("sales",0)
            ebitda = sd.get("ebitda",0)
            cure   = CURE_COSTS.get(sid,0)
            ref_rows.append({
                "Store":   sid,
                "Market":  mkt,
                "Net Sales": sales,
                "EBITDA":    ebitda,
                "Margin":    round(ebitda/sales*100,1) if sales > 0 else 0,
                "5x EBITDA": ebitda*5,
                "6x EBITDA": ebitda*6,
                "7x EBITDA": ebitda*7,
                "Cure Cost": cure,
            })
    ref_df = pd.DataFrame(ref_rows)
    st.dataframe(
        ref_df, use_container_width=True, hide_index=True,
        column_config={
            "Net Sales":  st.column_config.NumberColumn("Net Sales", format="$%d"),
            "EBITDA":     st.column_config.NumberColumn("EBITDA", format="$%d"),
            "Margin":     st.column_config.NumberColumn("Margin %", format="%.1f%%"),
            "5x EBITDA":  st.column_config.NumberColumn("5x", format="$%d"),
            "6x EBITDA":  st.column_config.NumberColumn("6x", format="$%d"),
            "7x EBITDA":  st.column_config.NumberColumn("7x", format="$%d"),
            "Cure Cost":  st.column_config.NumberColumn("Cure", format="$%d"),
        }
    )
    tot_s = sum(STORE_DATA.get(s,{}).get("sales",0) for s in ALL_STORES)
    tot_e = sum(STORE_DATA.get(s,{}).get("ebitda",0) for s in ALL_STORES)
    tot_c = sum(CURE_COSTS.values())
    pc1,pc2,pc3,pc4,pc5 = st.columns(5)
    pc1.metric("Portfolio stores", 119)
    pc2.metric("Total net sales",  fmt_m(tot_s))
    pc3.metric("Total EBITDA",     fmt_m(tot_e))
    pc4.metric("EBITDA margin",    f"{tot_e/tot_s*100:.1f}%")
    pc5.metric("Total cure",       fmt_m(tot_c))
