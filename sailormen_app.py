"""
Sailormen 363 Sale — Bid Optimization Engine
Streamlit + OR-Tools · Case 26-10451-RAM · GuideBoat Advisors
"""
import streamlit as st
import pandas as pd
from ortools.sat.python import cp_model
import time, uuid

st.set_page_config(page_title="Sailormen 363 · Bid Optimizer", page_icon="⚖️",
                   layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
.main .block-container{padding-top:0.8rem;max-width:1400px}
.stTabs [data-baseweb="tab"]{padding:8px 20px;border-radius:8px}
div[data-testid="metric-container"]{background:#f5f4f0;border-radius:8px;padding:10px}
.bid-card{border:0.5px solid #ddd;border-radius:8px;padding:12px;margin-bottom:8px}
.bid-card-sh{background:#faeeda}
.bid-card-win{background:#eaf3de}
.bid-card-excl{opacity:0.5}
.wf-row{display:flex;justify-content:space-between;padding:5px 0;
        border-bottom:0.5px solid #eee;font-size:0.9rem}
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
CASE = dict(bidDeadline="June 11, 2026", auction="June 15, 2026",
            auctionVenue="JW Marriott Miami", closing="June 30, 2026",
            expReimbPerStore=1000)

MARKET_STORES = {
    "Jacksonville":[128,129,130,131,132,146,148,150,151,152,154,155,156,157,
                    160,162,163,183,187,190,196,199,210,213,214,221,229,250],
    "Orlando":     [102,103,107,109,112,113,114,115,116,117,118,119,120,121,
                    122,123,124,125,126,127,177,178,179,230,246],
    "Miami":       [1,2,3,4,5,6,7,8,9,10,11,12,17,18,54,55,167,198,218,220],
    "Tampa":       [93,95,97,99,100,101,104,105,106,171,194,242,251,901,902],
    "Tallahassee": [139,140,141,142,143,180,181,185,203,211,228,232,238,241],
    "Pensacola":   [28,29,30,31,184,186,191,193,207,212,219],
    "Savannah":    [170,200,209,223,224,225],
}
ALL_STORES  = [s for ss in MARKET_STORES.values() for s in ss]
STORE_MKT   = {s:m for m,ss in MARKET_STORES.items() for s in ss}
MKT_ABBR    = {"Jacksonville":"JAX","Orlando":"ORL","Miami":"MIA",
               "Tampa":"TPA","Tallahassee":"TAL","Pensacola":"PNS","Savannah":"SAV"}

STORE_DATA = {1:{"s":2357234,"e":418671},2:{"s":1983880,"e":309413},3:{"s":2220696,"e":636543},4:{"s":1553893,"e":200012},5:{"s":2004655,"e":290832},6:{"s":2630819,"e":563987},7:{"s":3156832,"e":791543},8:{"s":2734591,"e":561234},9:{"s":3572386,"e":874841},10:{"s":2567234,"e":535123},11:{"s":3456789,"e":930234},12:{"s":2890123,"e":612345},17:{"s":3234567,"e":940778},18:{"s":2789012,"e":747120},28:{"s":1716298,"e":198234},29:{"s":1208745,"e":-476},30:{"s":1987125,"e":347985},31:{"s":1286075,"e":41136},54:{"s":1923456,"e":134567},55:{"s":1654321,"e":187654},93:{"s":1989874,"e":283476},95:{"s":1765432,"e":156789},97:{"s":1675949,"e":91367},99:{"s":1454123,"e":-988},100:{"s":2759295,"e":548419},101:{"s":1619968,"e":138552},102:{"s":1543210,"e":-62345},103:{"s":2109876,"e":68863},104:{"s":1751095,"e":133960},105:{"s":2080670,"e":268451},106:{"s":2028459,"e":245596},107:{"s":2345678,"e":108992},109:{"s":2234567,"e":93572},112:{"s":2567890,"e":188886},113:{"s":2465827,"e":448104},114:{"s":2678901,"e":239199},115:{"s":1987654,"e":108247},116:{"s":2876543,"e":371315},117:{"s":2345678,"e":155331},118:{"s":2789012,"e":344892},119:{"s":1876543,"e":70301},120:{"s":2972945,"e":593384},121:{"s":2123456,"e":89604},122:{"s":2456789,"e":239303},123:{"s":1765432,"e":-21630},124:{"s":1987654,"e":51346},125:{"s":2678901,"e":475144},126:{"s":2123456,"e":111955},127:{"s":2890123,"e":548724},128:{"s":1938757,"e":150026},129:{"s":1006106,"e":-49044},130:{"s":1589303,"e":25605},131:{"s":1165611,"e":-52962},132:{"s":1489331,"e":116967},139:{"s":1693082,"e":39701},140:{"s":1450102,"e":-23634},141:{"s":1513309,"e":140632},142:{"s":1413903,"e":81190},143:{"s":1456789,"e":56789},146:{"s":1268715,"e":-35425},148:{"s":1358291,"e":18857},150:{"s":2003935,"e":265175},151:{"s":1876543,"e":53389},152:{"s":2234567,"e":191657},154:{"s":1123456,"e":-74145},155:{"s":1765432,"e":47483},156:{"s":1456789,"e":-35756},157:{"s":2098765,"e":109065},160:{"s":1987654,"e":47504},162:{"s":1876543,"e":80991},163:{"s":2098765,"e":130332},167:{"s":2234567,"e":313795},170:{"s":1839113,"e":124263},171:{"s":1765739,"e":120285},177:{"s":2567890,"e":398979},178:{"s":1876543,"e":34107},179:{"s":2789012,"e":462481},180:{"s":1987654,"e":83456},181:{"s":1654321,"e":67890},183:{"s":1123456,"e":-79521},184:{"s":1359720,"e":-71826},185:{"s":1876543,"e":91568},186:{"s":1659790,"e":112273},187:{"s":1456789,"e":38955},190:{"s":2098765,"e":134044},191:{"s":1500747,"e":97760},193:{"s":1207701,"e":-46440},194:{"s":1381563,"e":-37294},196:{"s":2456789,"e":353486},198:{"s":2234567,"e":227129},199:{"s":2678901,"e":270292},200:{"s":1676256,"e":128528},203:{"s":1456789,"e":56789},207:{"s":1132182,"e":-84800},209:{"s":1630842,"e":77060},210:{"s":1234567,"e":-84692},211:{"s":1567890,"e":56789},212:{"s":1876543,"e":337828},213:{"s":1987654,"e":109270},214:{"s":1765432,"e":-27048},218:{"s":1876543,"e":37568},219:{"s":1131343,"e":24290},220:{"s":1654321,"e":160451},221:{"s":1234567,"e":-94951},223:{"s":1498867,"e":44843},224:{"s":1634517,"e":169885},225:{"s":1836329,"e":165680},228:{"s":1456789,"e":56789},229:{"s":1876543,"e":53757},230:{"s":2098765,"e":130253},232:{"s":1234567,"e":45678},238:{"s":1345678,"e":67890},241:{"s":1678901,"e":77278},242:{"s":1301740,"e":-60554},246:{"s":1987654,"e":76143},250:{"s":2345678,"e":154232},251:{"s":1272983,"e":-72864},901:{"s":1292775,"e":-31238},902:{"s":2474357,"e":396400}}

CURE = {1:97558,2:83818,3:100580,4:76508,5:101280,6:115431,7:154791,8:92884,9:130468,10:84258,11:166509,12:88391,17:120490,18:108375,28:55918,29:78260,30:33054,31:51188,54:100778,55:80395,93:90037,95:77061,97:76361,99:86563,100:96007,101:74417,102:64069,103:94405,104:57833,105:51720,106:53785,107:87594,109:83167,112:73230,113:93251,114:101418,115:47706,116:82939,117:75915,118:69506,119:71435,120:55762,121:82007,122:128631,123:86534,124:69104,125:71423,126:63438,127:62384,128:85675,129:50608,130:62283,131:56481,132:100756,139:38753,140:58059,141:89584,142:48954,143:50890,146:62242,148:80662,150:79042,151:76295,152:98118,154:60822,155:85033,156:106485,157:93298,160:93622,162:84572,163:71896,167:85049,170:95752,171:83009,177:83217,178:76789,179:97898,180:89762,181:70287,183:48120,184:69389,185:91569,186:73311,187:64092,190:102751,191:62990,193:63235,194:68221,196:110866,198:110052,199:124129,200:67937,203:50654,207:74112,209:58965,210:75828,211:69400,212:73581,213:81056,214:76238,218:89883,219:68082,220:73381,221:83387,223:56483,224:46303,225:52489,228:51771,229:104607,230:82807,232:45247,238:54818,241:77279,242:80340,246:86505,250:112351,251:92288,901:61281,902:99547}

MKT_AGG = {m:{"count":len(ss),"sales":sum(STORE_DATA.get(s,{}).get("s",0) for s in ss),"ebitda":sum(STORE_DATA.get(s,{}).get("e",0) for s in ss)} for m,ss in MARKET_STORES.items()}

SAMPLE_BIDS = [
    
]

# ── Session state ──────────────────────────────────────────────────────────────
# Ensure every bid has an id
for _b in SAMPLE_BIDS:
    if "id" not in _b: _b["id"] = str(uuid.uuid4())[:8]
if "bids"        not in st.session_state: st.session_state.bids = [dict(b) for b in SAMPLE_BIDS]
if "result"      not in st.session_state: st.session_state.result = None
if "edit_bid_id" not in st.session_state: st.session_state.edit_bid_id = None

def fmt(n):
    if n is None: return "—"
    if abs(n)>=1e6: return f"${n/1e6:.1f}M"
    if abs(n)>=1e3: return f"${n/1e3:.0f}K"
    return f"${n:,.0f}"

def fin(sids): return {"s":sum(STORE_DATA.get(s,{}).get("s",0) for s in sids),"e":sum(STORE_DATA.get(s,{}).get("e",0) for s in sids)}
def cure(sids): return sum(CURE.get(s,0) for s in sids)
def scope(bid):
    if set(bid["storeIds"])==set(ALL_STORES): return "Full portfolio"
    if len(bid["storeIds"])==1: return f"Store {bid['storeIds'][0]}"
    mkts=sorted({STORE_MKT.get(s,"?") for s in bid["storeIds"]})
    return " + ".join(MKT_ABBR.get(m,m[:3]) for m in mkts)
def conflicts(bid, all_bids):
    bs=set(bid["storeIds"])
    return sum(1 for b in all_bids if b.get("id")!=bid.get("id") and set(b.get("storeIds",[]))&bs)

# ── Optimizer ──────────────────────────────────────────────────────────────────
def expand(bids):
    items=[]
    for bid in bids:
        if not bid.get("include",True): continue
        if bid.get("optMode")=="perStore" and bid.get("storeAmounts"):
            for s in bid["storeIds"]:
                price=bid["storeAmounts"].get(str(s)) or bid["storeAmounts"].get(s)
                if price: items.append({**bid,"id":f"{bid['id']}_{s}","storeIds":[s],"amount":float(price)*1e6,"_pid":bid["id"]})
        else:
            items.append({**bid,"_pid":bid["id"]})
    return items

def optimize(bids):
    if not bids: return [],0,0
    model=cp_model.CpModel(); solver=cp_model.CpSolver()
    scale=100; amounts=[round(b["amount"]*scale) for b in bids]
    x=[model.NewBoolVar(f"x{i}") for i in range(len(bids))]
    sm={}
    for i,b in enumerate(bids):
        for s in b["storeIds"]: sm.setdefault(s,[]).append(i)
    for s,idxs in sm.items():
        if len(idxs)>1: model.Add(sum(x[i] for i in idxs)<=1)
    model.Maximize(sum(amounts[i]*x[i] for i in range(len(bids))))
    solver.parameters.max_time_in_seconds=60.0
    solver.parameters.num_search_workers=8
    t0=time.time(); status=solver.Solve(model); ms=round((time.time()-t0)*1000)
    if status in(cp_model.OPTIMAL,cp_model.FEASIBLE):
        w=[bids[i] for i in range(len(bids)) if solver.Value(x[i])==1]
        return w,sum(b["amount"] for b in w),ms
    return [],0,ms

# ── Bid form (shared for add + edit) ──────────────────────────────────────────
def bid_form(edit_bid=None):
    is_edit = edit_bid is not None
    iv = edit_bid or {}
    lbl = f"\u270f\ufe0f Editing \u2014 {iv.get('buyer','')}" if is_edit else "\u2795 Add New Bid"
    st.markdown(f"**{lbl}**")

    c1,c2,c3 = st.columns([3,1.5,1.5])
    with c1: buyer    = st.text_input("Buyer name", value=iv.get("buyer",""), key="f_buyer")
    with c2: amount   = st.number_input("Amount ($M)", value=iv.get("amount",0)/1e6, min_value=0.0, step=0.5, format="%.1f", key="f_amt")
    with c3: opt_mode = st.selectbox("Optimize as", ["bundle","perStore"],
                            index=["bundle","perStore"].index(iv.get("optMode","bundle")), key="f_mode")

    scope_opts = ["Full portfolio","Markets","Individual stores"]
    if not iv.get("storeIds"):
        default_scope = "Full portfolio"
    elif set(iv["storeIds"]) == set(ALL_STORES):
        default_scope = "Full portfolio"
    else:
        sids_set = set(iv["storeIds"])
        whole_mkts = [m for m,ss in MARKET_STORES.items() if set(ss) <= sids_set]
        leftover   = [s for s in iv["storeIds"] if STORE_MKT.get(s) not in set(whole_mkts)]
        default_scope = "Individual stores" if leftover else "Markets"

    scope_type = st.radio("Scope", scope_opts,
                          index=scope_opts.index(default_scope), horizontal=True, key="f_scope")

    sel_mkts=[]; sel_stores=[]
    if scope_type == "Markets":
        default_mkts = sorted({STORE_MKT.get(s,"") for s in iv.get("storeIds",[]) if STORE_MKT.get(s)}) if is_edit else []
        sel_mkts = st.multiselect("Select markets", list(MARKET_STORES.keys()),
                        default=default_mkts, key="f_mkts",
                        format_func=lambda m: f"{m}  \u00b7  {MKT_AGG[m]['count']} stores  \u00b7  {fmt(MKT_AGG[m]['ebitda'])} EBITDA")
    elif scope_type == "Individual stores":
        sel_stores = st.multiselect("Select stores", ALL_STORES,
                        default=iv.get("storeIds",[]) if is_edit else [], key="f_stores",
                        format_func=lambda s: f"{s} \u2014 {STORE_MKT.get(s,'')} \u2014 {fmt(STORE_DATA.get(s,{}).get('e',0))} EBITDA")

    if scope_type == "Full portfolio":   acquired = ALL_STORES
    elif scope_type == "Markets":        acquired = [s for m in sel_mkts for s in MARKET_STORES[m]]
    else:                                acquired = list(sel_stores)

    # Per-store pricing via st.data_editor (smooth table, no per-keystroke reruns)
    store_amounts = dict(iv.get("storeAmounts", {}))
    ps_total = 0.0
    if opt_mode == "perStore" and acquired:
        st.markdown("**Per-store bid amounts ($M)** \u2014 total auto-calculates")
        ps_rows = [{"Store": sid, "Market": STORE_MKT.get(sid,""),
                    "EBITDA": STORE_DATA.get(sid,{}).get("e",0),
                    "Bid ($M)": float(store_amounts.get(str(sid), store_amounts.get(sid, 0.0)))}
                   for sid in acquired]
        edited = st.data_editor(pd.DataFrame(ps_rows), use_container_width=True, hide_index=True,
                    disabled=["Store","Market","EBITDA"],
                    column_config={"Bid ($M)": st.column_config.NumberColumn(min_value=0.0, step=0.1, format="%.2f")},
                    key="f_ps")
        for _, row in edited.iterrows():
            if row["Bid ($M)"] > 0:
                store_amounts[str(int(row["Store"]))] = float(row["Bid ($M)"])
        ps_total = float(edited["Bid ($M)"].sum())
        if ps_total > 0:
            delta = abs(ps_total - amount)
            st.info(f"Per-store total: **{fmt(ps_total*1e6)}**" +
                    (" \u2705 matches overall bid" if delta < 0.05 else f" \u2014 will override overall bid"))

    closed_stores = list(iv.get("closedStores",[]))
    with st.expander("\U0001f6aa Store closures (optional)"):
        st.caption("Acquired but closed \u2014 excluded from EBITDA, included in conflict detection")
        if acquired:
            closed_stores = st.multiselect("Mark stores for closure", acquired,
                default=[s for s in closed_stores if s in acquired], key="f_closed",
                format_func=lambda s: f"{s} \u2014 {STORE_MKT.get(s,'')}")

    fa,fb,fc,fd = st.columns(4)
    with fa: is_sh   = st.checkbox("Stalking horse", value=iv.get("isSH",False), key="f_sh")
    with fb: bkp_pct = st.number_input("Breakup %", 0.0, 5.0, iv.get("breakupPct",2.5), 0.25, key="f_bkp") if is_sh else iv.get("breakupPct",2.5)
    with fc: plk_ok  = st.checkbox("PLK Approval", value=iv.get("plkApproval",False), key="f_plk")
    with fd: include = st.checkbox("Include in opt", value=iv.get("include",True), key="f_inc")
    comment = st.text_input("Comment", value=iv.get("comment",""),
                            placeholder="e.g. financing not confirmed", key="f_comment")

    final_amount = ps_total if (opt_mode == "perStore" and ps_total > 0) else amount

    cols = st.columns([3,1]) if is_edit else [st.container()]
    with cols[0]:
        if st.button("Save changes" if is_edit else "Submit bid",
                     type="primary", use_container_width=True, key="f_submit"):
            if buyer and final_amount > 0 and acquired:
                nb = {"id": iv.get("id", str(uuid.uuid4())[:8]),
                      "buyer": buyer.strip(), "amount": final_amount*1e6,
                      "storeIds": list(acquired), "closedStores": closed_stores,
                      "isSH": is_sh, "breakupPct": bkp_pct if is_sh else 2.5,
                      "include": include, "plkApproval": plk_ok,
                      "comment": comment, "optMode": opt_mode, "storeAmounts": store_amounts}
                if is_edit:
                    idx = next((i for i,b in enumerate(st.session_state.bids) if b["id"]==iv["id"]), None)
                    if idx is not None: st.session_state.bids[idx] = nb
                    st.session_state.edit_bid_id = None
                else:
                    st.session_state.bids.append(nb)
                st.session_state.result = None; st.rerun()
            else:
                st.warning("Enter buyer name and amount (or per-store prices).")
    if is_edit and len(cols) > 1:
        with cols[1]:
            if st.button("Cancel", use_container_width=True, key="f_cancel"):
                st.session_state.edit_bid_id = None; st.rerun()


# ── Header ─────────────────────────────────────────────────────────────────────
h1,h2=st.columns([4,1])
with h1:
    st.markdown("## ⚖️ Sailormen 363 Sale — Bid Optimization Engine")
    st.caption(f"Case 26-10451-RAM · Auction: {CASE['auction']} · {CASE['auctionVenue']} · Bid deadline: {CASE['bidDeadline']}")
with h2:
    if st.button("🔄 Reset to samples", use_container_width=True):
        st.session_state.bids=[dict(b) for b in SAMPLE_BIDS]
        st.session_state.result=None; st.session_state.edit_bid_id=None; st.rerun()
st.divider()

tab_bids,tab_matrix,tab_opt,tab_ref=st.tabs(["📋 Bids","🗺️ Buyers Matrix","⚡ Optimization","📊 Reference"])

# ══════════════════════════════════════════════════════════════════════════════
# BIDS TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_bids:
    bids=st.session_state.bids; result=st.session_state.result
    edit_id=st.session_state.edit_bid_id
    if edit_id:
        edit_bid=next((b for b in bids if b["id"]==edit_id),None)
        if edit_bid: bid_form(edit_bid)
        st.divider()
    else:
        with st.expander("➕ Add New Bid", expanded=len(bids)==0):
            bid_form()
    if not bids:
        st.info("No bids yet.")
    else:
        m1,m2,m3,m4=st.columns(4)
        m1.metric("Total bids",len(bids)); m2.metric("Stalking horse",sum(1 for b in bids if b.get("isSH")))
        m3.metric("Included",sum(1 for b in bids if b.get("include",True)))
        m4.metric("Gross all-in",fmt(sum(b["amount"] for b in bids)))
        st.caption("⚠️ Gross assumes no conflicts — run optimizer for actual proceeds")
        st.markdown("---")
        win_ids={b["id"] for b in result.get("winners",[])} if result else set()
        for i,bid in enumerate(bids):
            f=fin(bid["storeIds"]); ev=bid["amount"]/f["e"] if f["e"]>0 else None
            pct=bid["amount"]/f["s"]*100 if f["s"]>0 else None
            ovl=conflicts(bid,bids)
            tags=[]
            if bid.get("isSH"):            tags.append("⚓ SH")
            if bid.get("plkApproval"):     tags.append("✅ PLK")
            if not bid.get("include",True):tags.append("🙈 excl")
            if bid.get("closedStores"):    tags.append(f"🚪 closes {len(bid['closedStores'])}")
            if ovl:                        tags.append(f"⚠️ {ovl} conflicts")
            if result:                     tags.append("✅ Selected" if bid["id"] in win_ids else "❌ Excluded")
            c1,c2,c3,c4,c5,c6,c7,c8,c9=st.columns([3,1.5,1,1,0.7,0.7,0.7,0.7,0.7])
            with c1:
                st.markdown(f"**{bid['buyer']}**  "+"  ".join(f"`{t}`" for t in tags))
                st.caption(scope(bid))
            with c2:
                st.markdown(f"**{fmt(bid['amount'])}**")
                st.caption(f"{ev:.1f}x EV/EBITDA" if ev else "neg EBITDA")
            with c3:
                st.caption(f"{len(bid['storeIds'])} stores")
                if pct: st.caption(f"{pct:.1f}% of sales")
            with c4:
                if bid.get("isSH"):
                    new_pct=st.number_input("Breakup %",0.0,5.0,bid.get("breakupPct",2.5),0.25,key=f"bkp_{i}",label_visibility="collapsed")
                    if new_pct!=bid.get("breakupPct",2.5):
                        st.session_state.bids[i]["breakupPct"]=new_pct; st.rerun()
            with c5:
                if st.button("⚓",key=f"sh_{i}",help="Toggle SH"):
                    st.session_state.bids[i]["isSH"]=not bid.get("isSH"); st.rerun()
            with c6:
                if st.button("✅" if bid.get("plkApproval") else "🏪",key=f"plk_{i}",help="Toggle PLK"):
                    st.session_state.bids[i]["plkApproval"]=not bid.get("plkApproval"); st.rerun()
            with c7:
                if st.button("👁️" if bid.get("include",True) else "🙈",key=f"inc_{i}",help="Toggle include"):
                    st.session_state.bids[i]["include"]=not bid.get("include",True); st.rerun()
            with c8:
                if st.button("✏️",key=f"edit_{i}",help="Edit bid"):
                    st.session_state.edit_bid_id=bid["id"]; st.rerun()
            with c9:
                if st.button("🗑️",key=f"del_{i}",help="Delete"):
                    st.session_state.bids.pop(i); st.session_state.result=None; st.rerun()
            if bid.get("comment"): st.caption(f"  💬 {bid['comment']}")
            st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# MATRIX TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_matrix:
    bids=st.session_state.bids; result=st.session_state.result
    win_ids={b["id"] for b in result.get("winners",[])} if result else set()
    if not bids:
        st.info("No bids to display.")
    else:
        rows=[]
        for bid in bids:
            bs=set(bid["storeIds"])
            row={"Buyer":bid["buyer"],"Scope":scope(bid),"Amount":fmt(bid["amount"])}
            if result: row["Status"]="✅" if bid["id"] in win_ids else "❌"
            for m,ss in MARKET_STORES.items():
                cov=sum(1 for s in ss if s in bs); tot=len(ss)
                row[MKT_ABBR[m]]="✅" if cov==tot else (f"⚡{cov}/{tot}" if cov else "—")
            if bid.get("comment"): row["Comment"]=bid["comment"]
            rows.append(row)
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
        st.markdown("---")
        st.markdown("#### Market financials")
        mkt_rows=[{"Market":m,"Stores":MKT_AGG[m]["count"],"Net Sales":fmt(MKT_AGG[m]["sales"]),"EBITDA":fmt(MKT_AGG[m]["ebitda"]),"Margin":f"{MKT_AGG[m]['ebitda']/MKT_AGG[m]['sales']*100:.1f}%","5x":fmt(MKT_AGG[m]["ebitda"]*5),"6x":fmt(MKT_AGG[m]["ebitda"]*6),"7x":fmt(MKT_AGG[m]["ebitda"]*7)} for m in MARKET_STORES]
        st.dataframe(pd.DataFrame(mkt_rows),use_container_width=True,hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# OPTIMIZATION TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_opt:
    bids=st.session_state.bids
    included=[b for b in bids if b.get("include",True)]
    if not included:
        st.warning("No bids included.")
    else:
        if st.button("⚡ Run Optimizer",type="primary"):
            with st.spinner("Running OR-Tools CP-SAT solver..."):
                exp=expand(included)
                sh_exp=[b for b in exp if b.get("isSH")]
                winners,gross,ms=optimize(exp)
                sh_w,sh_floor,_=optimize(sh_exp) if sh_exp else ([],0,0)
                win_pids={b.get("_pid",b["id"]) for b in winners}
                sh_win_pids={b.get("_pid",b["id"]) for b in sh_w}
                disp_sh=[b for b in sh_exp if b.get("_pid",b["id"]) in sh_win_pids and b.get("_pid",b["id"]) not in win_pids]
                bkp=sum(b["amount"]*b.get("breakupPct",2.5)/100+len(b["storeIds"])*CASE["expReimbPerStore"] for b in disp_sh)
                win_stores=[s for b in winners for s in b["storeIds"]]
                tot_cure=cure(win_stores); net_sh=gross-bkp; net_cure=net_sh-tot_cure
                # Build display bids: for per-store expanded wins, reconstruct
                # a bid showing only the stores that actually won per buyer
                display_winners = []
                seen_pids = {}
                for w in winners:
                    pid = w.get("_pid", w["id"])
                    if pid not in seen_pids:
                        # Find the original bid for metadata
                        orig = next((b for b in included if b["id"]==pid), w)
                        seen_pids[pid] = {**orig, "storeIds": list(w["storeIds"]), "amount": w["amount"]}
                    else:
                        seen_pids[pid]["storeIds"] += w["storeIds"]
                        seen_pids[pid]["amount"]   += w["amount"]
                display_winners = list(seen_pids.values())
                st.session_state.result=dict(winners=display_winners,gross=gross,ms=ms,sh_floor=sh_floor,
                    disp_sh=disp_sh,bkp=bkp,win_stores=win_stores,tot_cure=tot_cure,
                    net_sh=net_sh,net_cure=net_cure,win_pids=win_pids)
            st.rerun()
    result=st.session_state.result
    if result:
        winners=result["winners"]; gross=result["gross"]
        net_cure=result["net_cure"]; net_sh=result["net_sh"]
        tot_cure=result["tot_cure"]; bkp=result["bkp"]
        disp_sh=result["disp_sh"]; win_stores=result["win_stores"]
        sh_floor=result["sh_floor"]; ms=result["ms"]
        k1,k2,k3,k4,k5=st.columns(5)
        k1.metric("Gross proceeds",fmt(gross)); k2.metric("SH protections",fmt(-bkp) if bkp else "—")
        k3.metric("Net after SH",fmt(net_sh)); k4.metric("Cure costs",fmt(-tot_cure))
        k5.metric("Net after cure",fmt(net_cure))
        st.caption(f"✅ OR-Tools solved in {ms}ms · {len(winners)} winning bids · {len(set(win_stores))}/119 stores · SH floor: {fmt(sh_floor)}")
        st.markdown("---")
        col_a,col_w=st.columns([3,2])
        with col_a:
            st.markdown("#### Winning allocation")
            for bid in sorted(winners,key=lambda b:-b["amount"]):
                f=fin(bid["storeIds"]); ev=bid["amount"]/f["e"] if f["e"]>0 else None
                c=cure(bid["storeIds"])
                hdr=f"✅ {'⚓ ' if bid.get('isSH') else ''}{bid['buyer']} — {fmt(bid['amount'])} — {scope(bid)}"
                if bid.get("comment"): hdr+=f"  💬 {bid['comment']}"
                with st.expander(hdr):
                    s1,s2,s3,s4=st.columns(4)
                    s1.metric("Bid",fmt(bid["amount"])); s2.metric("EV/EBITDA",f"{ev:.1f}x" if ev else "—")
                    s3.metric("Net sales",fmt(f["s"])); s4.metric("Cure",fmt(c))
                    rows=[]
                    for sid in sorted(bid["storeIds"]):
                        sd=STORE_DATA.get(sid,{}); cc=CURE.get(sid,0)
                        rows.append({"Store":sid,"Market":STORE_MKT.get(sid,""),
                            "Net Sales":fmt(sd.get("s",0)),"EBITDA":fmt(sd.get("e",0)),
                            "Margin":f"{sd.get('e',0)/sd.get('s',1)*100:.1f}%" if sd.get("s",0)>0 else "—",
                            "Lease cure":fmt(round(cc*0.355)),"Tax cure":fmt(round(cc*0.369)),
                            "PLK cure":fmt(round(cc*0.275)),"Total cure":fmt(cc)})
                    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
            if disp_sh:
                st.markdown("##### Displaced SH bids")
                for bid in disp_sh:
                    fee=bid["amount"]*bid.get("breakupPct",2.5)/100+len(bid["storeIds"])*CASE["expReimbPerStore"]
                    st.markdown(f"❌ **{bid['buyer']}** — breakup fee: **{fmt(fee)}**")
                    if bid.get("comment"): st.caption(f"💬 {bid['comment']}")
        with col_w:
            st.markdown("#### Proceeds waterfall")
            lease_c=sum(CURE.get(s,0)*0.355 for s in win_stores)
            tax_c  =sum(CURE.get(s,0)*0.369 for s in win_stores)
            plk_c  =sum(CURE.get(s,0)*0.275 for s in win_stores)
            wf=[("Gross auction proceeds",gross,False),
                (f"SH bid protections ({len(disp_sh)} displaced)",-bkp if bkp else 0,True),
                ("Net after SH protections",net_sh,False),
                ("Lease cure costs",-lease_c,True),("Tax cure costs",-tax_c,True),
                ("PLK cure costs",-plk_c,True),
                (f"Total cure ({len(set(win_stores))} stores)",-tot_cure,False),
                ("Net after cure costs",net_cure,False)]
            for label,val,indent in wf:
                if val==0 and indent: continue
                prefix="  └─ " if indent else ""
                color="color:#a32d2d" if val<0 else ("color:#3b6d11" if not indent and val>0 else "color:#1a1a18")
                bold="font-weight:700" if not indent else ""
                st.markdown(f"<div style='display:flex;justify-content:space-between;padding:5px 0;border-bottom:0.5px solid #eee;{bold}'><span>{prefix}{label}</span><span style='{color}'>{fmt(val)}</span></div>",unsafe_allow_html=True)
            st.caption("Cure costs per KIA 05-24-2026")
        uncov=[s for s in ALL_STORES if s not in set(win_stores)]
        if uncov:
            st.markdown("---"); st.markdown(f"#### ⚠️ Uncovered stores ({len(uncov)})")
            um={}
            for s in uncov: um.setdefault(STORE_MKT.get(s,"?"),[]).append(s)
            cols_u=st.columns(len(um))
            for col_u,(m,ss) in zip(cols_u,um.items()):
                col_u.markdown(f"**{m}**"); col_u.write(", ".join(str(s) for s in ss))

# ══════════════════════════════════════════════════════════════════════════════
# REFERENCE TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_ref:
    st.markdown("#### Store-level reference — all 119 stores")
    ref=[]
    for m,ss in MARKET_STORES.items():
        for sid in ss:
            sd=STORE_DATA.get(sid,{}); s=sd.get("s",0); e=sd.get("e",0); c=CURE.get(sid,0)
            ref.append({"Store":sid,"Market":m,"Net Sales":s,"EBITDA":e,
                "Margin":round(e/s*100,1) if s>0 else 0,"5x":e*5,"6x":e*6,"7x":e*7,"Cure":c})
    st.dataframe(pd.DataFrame(ref),use_container_width=True,hide_index=True,
        column_config={"Net Sales":st.column_config.NumberColumn(format="$%d"),
            "EBITDA":st.column_config.NumberColumn(format="$%d"),
            "Margin":st.column_config.NumberColumn(format="%.1f%%"),
            "5x":st.column_config.NumberColumn(format="$%d"),
            "6x":st.column_config.NumberColumn(format="$%d"),
            "7x":st.column_config.NumberColumn(format="$%d"),
            "Cure":st.column_config.NumberColumn(format="$%d")})
    tot_s=sum(STORE_DATA.get(s,{}).get("s",0) for s in ALL_STORES)
    tot_e=sum(STORE_DATA.get(s,{}).get("e",0) for s in ALL_STORES)
    p1,p2,p3,p4,p5=st.columns(5)
    p1.metric("Stores",119); p2.metric("Net sales",fmt(tot_s)); p3.metric("EBITDA",fmt(tot_e))
    p4.metric("Margin",f"{tot_e/tot_s*100:.1f}%"); p5.metric("Total cure",fmt(sum(CURE.values())))
