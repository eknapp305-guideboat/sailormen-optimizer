"""
Sailormen 363 Sale — Bid Optimization Engine
Streamlit + OR-Tools · Case 26-10451-RAM · GuideBoat Advisors
"""
import streamlit as st
import pandas as pd
from ortools.sat.python import cp_model
import time, uuid, json, io

st.set_page_config(page_title="Sailormen 363 · Bid Optimizer", page_icon="⚖️",
                   layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
.main .block-container{padding-top:0.8rem;max-width:1500px}
.stTabs [data-baseweb="tab"]{padding:8px 20px;border-radius:6px;font-size:0.85rem}
/* Professional banking style — sharp, minimal */
.stButton button{border-radius:3px !important;font-size:0.78rem}
.stButton button[kind="primary"]{background:#1F3864 !important;border-color:#1F3864 !important;color:#fff !important;border-radius:3px !important}
.stButton button[kind="primary"]:hover{background:#152a4a !important}
div[data-testid="stMarkdownContainer"] p{margin:0}
div[data-testid="stMarkdownContainer"] strong{font-weight:600}
/* Tighten tab styling */
.stTabs [data-baseweb="tab"]{border-radius:2px;font-size:0.82rem}
/* Metric boxes less rounded */
div[data-testid="metric-container"]{background:#f8f8f8;border-radius:3px;border:0.5px solid #e0e0e0}
/* Popover — compact, sharp */
div[data-testid="stPopover"] button{border-radius:3px !important}
div[data-testid="metric-container"]{background:#f5f4f0;border-radius:8px;padding:10px}
.inline-edit{background:#e6f1fb;border:0.5px solid #378add;border-radius:8px;padding:12px;margin:4px 0 8px 0}
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
ALL_STORES = [s for ss in MARKET_STORES.values() for s in ss]
STORE_MKT  = {s:m for m,ss in MARKET_STORES.items() for s in ss}
MKT_ABBR   = {"Jacksonville":"JAX","Orlando":"ORL","Miami":"MIA",
               "Tampa":"TPA","Tallahassee":"TAL","Pensacola":"PNS","Savannah":"SAV"}

STORE_DATA = {1:{"s":2357234,"e":418671},2:{"s":1983880,"e":309413},3:{"s":2220696,"e":636543},4:{"s":1553893,"e":200012},5:{"s":2004655,"e":290832},6:{"s":2630819,"e":563987},7:{"s":3156832,"e":791543},8:{"s":2734591,"e":561234},9:{"s":3572386,"e":874841},10:{"s":2567234,"e":535123},11:{"s":3456789,"e":930234},12:{"s":2890123,"e":612345},17:{"s":3234567,"e":940778},18:{"s":2789012,"e":747120},28:{"s":1716298,"e":198234},29:{"s":1208745,"e":-476},30:{"s":1987125,"e":347985},31:{"s":1286075,"e":41136},54:{"s":1923456,"e":134567},55:{"s":1654321,"e":187654},93:{"s":1989874,"e":283476},95:{"s":1765432,"e":156789},97:{"s":1675949,"e":91367},99:{"s":1454123,"e":-988},100:{"s":2759295,"e":548419},101:{"s":1619968,"e":138552},102:{"s":1543210,"e":-62345},103:{"s":2109876,"e":68863},104:{"s":1751095,"e":133960},105:{"s":2080670,"e":268451},106:{"s":2028459,"e":245596},107:{"s":2345678,"e":108992},109:{"s":2234567,"e":93572},112:{"s":2567890,"e":188886},113:{"s":2465827,"e":448104},114:{"s":2678901,"e":239199},115:{"s":1987654,"e":108247},116:{"s":2876543,"e":371315},117:{"s":2345678,"e":155331},118:{"s":2789012,"e":344892},119:{"s":1876543,"e":70301},120:{"s":2972945,"e":593384},121:{"s":2123456,"e":89604},122:{"s":2456789,"e":239303},123:{"s":1765432,"e":-21630},124:{"s":1987654,"e":51346},125:{"s":2678901,"e":475144},126:{"s":2123456,"e":111955},127:{"s":2890123,"e":548724},128:{"s":1938757,"e":150026},129:{"s":1006106,"e":-49044},130:{"s":1589303,"e":25605},131:{"s":1165611,"e":-52962},132:{"s":1489331,"e":116967},139:{"s":1693082,"e":39701},140:{"s":1450102,"e":-23634},141:{"s":1513309,"e":140632},142:{"s":1413903,"e":81190},143:{"s":1456789,"e":56789},146:{"s":1268715,"e":-35425},148:{"s":1358291,"e":18857},150:{"s":2003935,"e":265175},151:{"s":1876543,"e":53389},152:{"s":2234567,"e":191657},154:{"s":1123456,"e":-74145},155:{"s":1765432,"e":47483},156:{"s":1456789,"e":-35756},157:{"s":2098765,"e":109065},160:{"s":1987654,"e":47504},162:{"s":1876543,"e":80991},163:{"s":2098765,"e":130332},167:{"s":2234567,"e":313795},170:{"s":1839113,"e":124263},171:{"s":1765739,"e":120285},177:{"s":2567890,"e":398979},178:{"s":1876543,"e":34107},179:{"s":2789012,"e":462481},180:{"s":1987654,"e":83456},181:{"s":1654321,"e":67890},183:{"s":1123456,"e":-79521},184:{"s":1359720,"e":-71826},185:{"s":1876543,"e":91568},186:{"s":1659790,"e":112273},187:{"s":1456789,"e":38955},190:{"s":2098765,"e":134044},191:{"s":1500747,"e":97760},193:{"s":1207701,"e":-46440},194:{"s":1381563,"e":-37294},196:{"s":2456789,"e":353486},198:{"s":2234567,"e":227129},199:{"s":2678901,"e":270292},200:{"s":1676256,"e":128528},203:{"s":1456789,"e":56789},207:{"s":1132182,"e":-84800},209:{"s":1630842,"e":77060},210:{"s":1234567,"e":-84692},211:{"s":1567890,"e":56789},212:{"s":1876543,"e":337828},213:{"s":1987654,"e":109270},214:{"s":1765432,"e":-27048},218:{"s":1876543,"e":37568},219:{"s":1131343,"e":24290},220:{"s":1654321,"e":160451},221:{"s":1234567,"e":-94951},223:{"s":1498867,"e":44843},224:{"s":1634517,"e":169885},225:{"s":1836329,"e":165680},228:{"s":1456789,"e":56789},229:{"s":1876543,"e":53757},230:{"s":2098765,"e":130253},232:{"s":1234567,"e":45678},238:{"s":1345678,"e":67890},241:{"s":1678901,"e":77278},242:{"s":1301740,"e":-60554},246:{"s":1987654,"e":76143},250:{"s":2345678,"e":154232},251:{"s":1272983,"e":-72864},901:{"s":1292775,"e":-31238},902:{"s":2474357,"e":396400}}

CURE = {1:97558,2:83818,3:100580,4:76508,5:101280,6:115431,7:154791,8:92884,9:130468,10:84258,11:166509,12:88391,17:120490,18:108375,28:55918,29:78260,30:33054,31:51188,54:100778,55:80395,93:90037,95:77061,97:76361,99:86563,100:96007,101:74417,102:64069,103:94405,104:57833,105:51720,106:53785,107:87594,109:83167,112:73230,113:93251,114:101418,115:47706,116:82939,117:75915,118:69506,119:71435,120:55762,121:82007,122:128631,123:86534,124:69104,125:71423,126:63438,127:62384,128:85675,129:50608,130:62283,131:56481,132:100756,139:38753,140:58059,141:89584,142:48954,143:50890,146:62242,148:80662,150:79042,151:76295,152:98118,154:60822,155:85033,156:106485,157:93298,160:93622,162:84572,163:71896,167:85049,170:95752,171:83009,177:83217,178:76789,179:97898,180:89762,181:70287,183:48120,184:69389,185:91569,186:73311,187:64092,190:102751,191:62990,193:63235,194:68221,196:110866,198:110052,199:124129,200:67937,203:50654,207:74112,209:58965,210:75828,211:69400,212:73581,213:81056,214:76238,218:89883,219:68082,220:73381,221:83387,223:56483,224:46303,225:52489,228:51771,229:104607,230:82807,232:45247,238:54818,241:77279,242:80340,246:86505,250:112351,251:92288,901:61281,902:99547}

RUN_RATE = {128:48132,129:24063,130:8113,131:24063,132:48127,146:48127,148:95613,150:16227,151:16227,152:48127,154:16227,155:149063,156:16227,157:8113,160:48127,162:48127,163:48127,183:7866,187:48132,190:16232,196:16232,199:48132,210:13532,213:16232,214:16232,221:16232,229:16232,250:16987,102:24064,103:16227,107:8113,109:8113,112:16227,113:15727,114:8116,115:16227,116:16227,117:48127,118:48127,119:48127,120:16227,121:16227,122:7866,123:48127,124:48132,125:24063,126:224063,127:16227,177:16227,178:48132,179:16232,230:16232,246:16232,1:16227,2:16227,3:132863,4:7863,5:15732,6:15727,7:8116,8:16227,9:15727,10:16227,11:15732,12:8116,17:8113,18:8113,54:48127,55:48127,167:47050,198:48132,218:15732,220:15727,93:120613,95:241227,97:16227,99:8113,100:16227,101:16227,104:8765,105:16227,106:16227,171:120613,194:16232,242:16232,251:16987,901:16227,902:16227,139:48127,140:16227,141:24063,142:124063,143:24064,180:16232,181:48132,185:16232,203:16232,211:16232,228:13532,232:16232,238:17487,241:17487,28:16227,29:48127,30:133116,31:16227,184:48132,186:16232,191:48132,193:16232,207:48132,212:15732,219:16232,170:8116,200:48132,209:16232,223:48132,224:24063,225:24066}

RENO_CAPEX = {128:525000,129:350000,130:750000,131:1000000,132:525000,146:750000,148:525000,150:750000,151:525000,152:750000,154:525000,155:750000,156:750000,157:350000,160:525000,162:750000,163:525000,183:350000,187:350000,190:350000,196:350000,199:350000,210:0,213:350000,214:150000,221:150000,229:350000,250:150000,102:750000,103:750000,107:750000,109:750000,112:750000,113:150000,114:1000000,115:525000,116:750000,117:750000,118:750000,119:525000,120:525000,121:525000,122:750000,123:350000,124:750000,125:750000,126:350000,127:750000,177:350000,178:350000,179:350000,230:350000,246:150000,1:525000,2:750000,3:750000,4:750000,5:350000,6:150000,7:750000,8:750000,9:750000,10:525000,11:525000,12:750000,17:750000,18:750000,54:525000,55:750000,167:750000,198:350000,218:350000,220:150000,93:525000,95:525000,97:525000,99:750000,100:750000,101:525000,104:750000,105:525000,106:750000,171:525000,194:150000,242:150000,251:150000,901:750000,902:750000,139:1000000,140:750000,141:750000,142:150000,143:750000,180:350000,181:350000,185:350000,203:350000,211:150000,228:0,232:150000,238:150000,241:150000,28:750000,29:525000,30:750000,31:525000,184:350000,186:150000,191:350000,193:350000,207:350000,212:150000,219:150000,170:750000,200:350000,209:350000,223:1000000,224:750000,225:1000000}

RENO_YEAR = {128:2029,129:2027,130:2027,131:2028,132:2029,146:2029,148:2028,150:2029,151:2029,152:2029,154:2031,155:2027,156:2029,157:2028,160:2029,162:2029,163:2030,183:2028,187:2030,190:2030,196:2030,199:2029,210:2031,213:2032,214:2032,221:2032,229:2032,250:2035,102:2027,103:2029,107:2028,109:2027,112:2029,113:2034,114:2028,115:2030,116:2029,117:2026,118:2029,119:2029,120:2029,121:2030,122:2028,123:2029,124:2029,125:2028,126:2027,127:2026,177:2026,178:2029,179:2029,230:2032,246:2034,1:2030,2:2029,3:2028,4:2028,5:2030,6:2033,7:2028,8:2029,9:2029,10:2029,11:2030,12:2028,17:2028,18:2027,54:2031,55:2029,167:2027,198:2031,218:2032,220:2032,93:2027,95:2026,97:2030,99:2028,100:2029,101:2031,104:2027,105:2029,106:2026,171:2027,194:2029,242:2033,251:2035,901:2033,902:2033,139:2029,140:2029,141:2028,142:2028,143:2028,180:2029,181:2029,185:2030,203:2030,211:2031,228:2032,232:2032,238:2033,241:2033,28:2029,29:2030,30:2027,31:2030,184:2030,186:2030,191:2026,193:2030,207:2031,212:2032,219:2032,170:2027,200:2031,209:2031,223:2029,224:2028,225:2027}

MKT_AGG = {m:{"count":len(ss),
              "sales":sum(STORE_DATA.get(s,{}).get("s",0) for s in ss),
              "ebitda":sum(STORE_DATA.get(s,{}).get("e",0) for s in ss),
              "run_rate":sum(RUN_RATE.get(s,0) for s in ss),
              "reno_capex":sum(RENO_CAPEX.get(s,0) for s in ss)}
           for m,ss in MARKET_STORES.items()}

SAMPLE_BIDS = []
for _b in SAMPLE_BIDS:
    if "id" not in _b: _b["id"] = str(uuid.uuid4())[:8]

# ── Session state ──────────────────────────────────────────────────────────────
if "bids"      not in st.session_state: st.session_state.bids      = [dict(b) for b in SAMPLE_BIDS]
if "result"    not in st.session_state: st.session_state.result    = None
if "edit_id"   not in st.session_state: st.session_state.edit_id   = None
if "show_add"  not in st.session_state: st.session_state.show_add  = False
if "scenarios" not in st.session_state: st.session_state.scenarios = []

# ── Helpers ────────────────────────────────────────────────────────────────────
def fmt(n):
    if n is None: return "—"
    if abs(n)>=1e6: return f"${n/1e6:.1f}M"
    if abs(n)>=1e3: return f"${n/1e3:.0f}K"
    return f"${n:,.0f}"

def fin(sids):
    return {"s":sum(STORE_DATA.get(s,{}).get("s",0) for s in sids),
            "e":sum(STORE_DATA.get(s,{}).get("e",0) for s in sids)}

def capex_total(sids):
    return sum(RUN_RATE.get(s,0) for s in sids)

def cure(sids): return sum(CURE.get(s,0) for s in sids)

def scope(bid):
    if set(bid.get("storeIds",[])) == set(ALL_STORES): return "Full portfolio"
    if len(bid.get("storeIds",[])) == 1: return f"Store {bid['storeIds'][0]}"
    mkts = sorted({STORE_MKT.get(s,"?") for s in bid.get("storeIds",[])})
    return " + ".join(MKT_ABBR.get(m,m[:3]) for m in mkts)

def conflicts(bid, all_bids):
    bs = set(bid.get("storeIds",[]))
    return sum(1 for b in all_bids
               if b.get("id") != bid.get("id") and set(b.get("storeIds",[]))&bs)

# ── Optimizer ──────────────────────────────────────────────────────────────────
def expand(bids):
    items = []
    for bid in bids:
        if not bid.get("include", True): continue
        if bid.get("optMode") == "perStore" and bid.get("storeAmounts"):
            for s in bid.get("storeIds",[]):
                price = bid["storeAmounts"].get(str(s)) or bid["storeAmounts"].get(s)
                if price:
                    items.append({**bid, "id":f"{bid.get('id','')}_{s}",
                                  "storeIds":[s], "amount":float(price)*1e6, "_pid":bid.get("id","")})
        else:
            items.append({**bid, "_pid":bid.get("id","")})
    return items

def optimize(bids):
    if not bids: return [], 0, 0
    model = cp_model.CpModel(); solver = cp_model.CpSolver()
    scale = 100
    amounts = [round(b["amount"]*scale) for b in bids]
    x = [model.NewBoolVar(f"x{i}") for i in range(len(bids))]
    sm = {}
    for i,b in enumerate(bids):
        for s in b.get("storeIds",[]): sm.setdefault(s,[]).append(i)
    for s,idxs in sm.items():
        if len(idxs) > 1: model.Add(sum(x[i] for i in idxs) <= 1)
    model.Maximize(sum(amounts[i]*x[i] for i in range(len(bids))))
    solver.parameters.max_time_in_seconds = 60.0
    solver.parameters.num_search_workers  = 8
    t0 = time.time(); status = solver.Solve(model); ms = round((time.time()-t0)*1000)
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        w = [bids[i] for i in range(len(bids)) if solver.Value(x[i])==1]
        return w, sum(b["amount"] for b in w), ms
    return [], 0, ms

# ── Inline bid form ────────────────────────────────────────────────────────────
def bid_form_inline(key_prefix, iv=None, is_edit=False):
    iv = iv or {}

    # ── Row 1: core fields ────────────────────────────────────────────────────
    c1,c2,c3 = st.columns([3,1.5,1.5])
    with c1: buyer    = st.text_input("Buyer name", value=iv.get("buyer",""), key=f"{key_prefix}_buyer")
    with c2: amount   = st.number_input("Amount ($M)", value=iv.get("amount",0)/1e6, min_value=0.0, step=0.5, format="%.1f", key=f"{key_prefix}_amt")
    with c3: opt_mode = st.selectbox("Optimize as", ["bundle","perStore"],
                            index=["bundle","perStore"].index(iv.get("optMode","bundle")),
                            key=f"{key_prefix}_mode")


    # ── Row 2: market checkboxes ──────────────────────────────────────────────
    st.caption("Markets")
    default_sids = set(iv.get("storeIds", []))
    all_portfolio = set(iv.get("storeIds",[])) == set(ALL_STORES) or not iv.get("storeIds")

    # Full portfolio toggle
    full_port = st.checkbox("Full portfolio (all 119 stores)",
                            value=all_portfolio if not is_edit else set(iv.get("storeIds",[])) == set(ALL_STORES),
                            key=f"{key_prefix}_full")

    acquired = []
    if full_port:
        acquired = ALL_STORES
        cols = st.columns(7)
        for j,(mkt,ss) in enumerate(MARKET_STORES.items()):
            cols[j].markdown(f"<span style='font-size:0.72rem;color:#aaa'>✓ {MKT_ABBR[mkt]}<br>{len(ss)} stores</span>", unsafe_allow_html=True)
    else:
        # Market checkboxes in a single row
        mkt_cols = st.columns(7)
        sel_store_ids = []
        for j,(mkt,stores) in enumerate(MARKET_STORES.items()):
            with mkt_cols[j]:
                mkt_default = all(s in default_sids for s in stores) if default_sids else False
                mkt_checked = st.checkbox(
                    f"**{MKT_ABBR[mkt]}** ({len(stores)})",
                    value=mkt_default,
                    key=f"{key_prefix}_mkt_{mkt}"
                )
                if mkt_checked:
                    sel_store_ids.extend(stores)

        # If any market checked, offer individual store refinement
        checked_mkts = [m for m,ss in MARKET_STORES.items()
                        if st.session_state.get(f"{key_prefix}_mkt_{m}", False)]
        if checked_mkts:
            with st.expander("Refine individual stores (optional)"):
                for mkt in checked_mkts:
                    stores = MARKET_STORES[mkt]
                    st.caption(f"{mkt}")
                    scols = st.columns(8)
                    for k,sid in enumerate(stores):
                        with scols[k%8]:
                            in_default = sid in default_sids
                            if st.checkbox(str(sid), value=True, key=f"{key_prefix}_s_{sid}"):
                                pass  # handled below
                # Rebuild acquired from individual checkboxes
                sel_store_ids = [sid for mkt in checked_mkts
                                 for sid in MARKET_STORES[mkt]
                                 if st.session_state.get(f"{key_prefix}_s_{sid}", True)]
        acquired = list(dict.fromkeys(sel_store_ids))

    if acquired and acquired != ALL_STORES:
        f_acq = fin(acquired)
        st.caption(f"{len(acquired)} stores · {fmt(f_acq['s'])} net sales · {fmt(f_acq['e'])} EBITDA")

    # ── Per-store pricing (only if perStore mode) ─────────────────────────────
    store_amounts = dict(iv.get("storeAmounts", {}))
    ps_total = 0.0
    if opt_mode == "perStore" and acquired:
        with st.expander("Per-store bid amounts ($M)", expanded=bool(store_amounts)):
            ps_rows = [{"Store": sid, "Market": STORE_MKT.get(sid,""),
                        "EBITDA ($)": STORE_DATA.get(sid,{}).get("e",0),
                        "Bid ($M)": float(store_amounts.get(str(sid), store_amounts.get(sid, 0.0)))}
                       for sid in acquired]
            edited = st.data_editor(pd.DataFrame(ps_rows), use_container_width=True, hide_index=True,
                        disabled=["Store","Market","EBITDA ($)"],
                        column_config={"Bid ($M)": st.column_config.NumberColumn(min_value=0.0, step=0.1, format="%.2f")},
                        key=f"{key_prefix}_ps")
            for _, row in edited.iterrows():
                if row["Bid ($M)"] > 0:
                    store_amounts[str(int(row["Store"]))] = float(row["Bid ($M)"])
            ps_total = float(edited["Bid ($M)"].sum())
            if ps_total > 0:
                st.caption(f"Total: {fmt(ps_total*1e6)}" +
                           (" ✓" if abs(ps_total-amount)<0.05 else " — overrides overall bid amount"))

    # ── Row 3: flags + comment (compact single row) ───────────────────────────
    fa,fb,fc,fd,fe = st.columns([1,1,1,1,3])
    with fa: is_sh   = st.checkbox("Stalking horse", value=iv.get("isSH",False), key=f"{key_prefix}_sh")
    with fb: bkp_pct = st.number_input("Breakup %", 0.0, 5.0, iv.get("breakupPct",2.5), 0.25, key=f"{key_prefix}_bkp") if is_sh else iv.get("breakupPct",2.5)
    with fc: plk_ok  = st.checkbox("PLK Approval", value=iv.get("plkApproval",False), key=f"{key_prefix}_plk")
    with fd: include = st.checkbox("Include", value=iv.get("include",True), key=f"{key_prefix}_inc")
    with fe: comment = st.text_input("Comment", value=iv.get("comment",""), placeholder="Optional note", key=f"{key_prefix}_comment")

    final_amount = ps_total if (opt_mode=="perStore" and ps_total>0) else amount

    # ── Submit ────────────────────────────────────────────────────────────────
    b1,b2 = st.columns([2,1])
    with b1: submitted = st.button("Save changes" if is_edit else "Submit bid",
                                   type="primary", use_container_width=True, key=f"{key_prefix}_submit")
    with b2: cancelled = st.button("Cancel", use_container_width=True, key=f"{key_prefix}_cancel")

    if cancelled: return "cancel", None

    if submitted:
        if buyer and final_amount > 0 and acquired:
            nb = {"id": iv.get("id", str(uuid.uuid4())[:8]),
                  "buyer": buyer.strip(), "amount": final_amount*1e6,
                  "storeIds": list(dict.fromkeys(acquired)), "closedStores": [],
                  "isSH": is_sh, "breakupPct": bkp_pct if is_sh else 2.5,
                  "include": include, "plkApproval": plk_ok,
                  "comment": comment, "optMode": opt_mode, "storeAmounts": store_amounts}
            return "submit", nb
        else:
            st.warning("Enter buyer name, amount, and at least one market.")

    return None, None

# ── Header ─────────────────────────────────────────────────────────────────────
h1,h2,h3 = st.columns([4,1,1])
with h1:
    st.markdown("## ⚖️ Sailormen 363 Sale — Bid Optimization Engine")
    st.caption(f"Case 26-10451-RAM · Auction: {CASE['auction']} · {CASE['auctionVenue']} · Bid deadline: {CASE['bidDeadline']}")
with h2:
    # Export bids
    bids_json = json.dumps(st.session_state.bids, indent=2)
    st.download_button("Export bids", data=bids_json, file_name="sailormen_bids.json",
                       mime="application/json", use_container_width=True)
with h3:
    if st.button("Reset to samples", use_container_width=True):
        st.session_state.bids   = [dict(b) for b in SAMPLE_BIDS]
        st.session_state.result = None
        st.session_state.edit_id = None
        st.session_state.show_add = False
        st.rerun()

# Import bids — on_change fires instantly on upload AND on X (clear)
def _handle_upload():
    f = st.session_state.get("bid_uploader")
    if f is not None:
        try:
            raw = f.read().decode("utf-8")
            imported = json.loads(raw)
            if not isinstance(imported, list):
                st.session_state._import_error = "JSON must be a list of bids"
                return
            for b in imported:
                if "id" not in b: b["id"] = str(uuid.uuid4())[:8]
            st.session_state.bids     = imported
            st.session_state.result   = None
            st.session_state.edit_id  = None
            st.session_state._import_error = None
        except Exception as e:
            st.session_state._import_error = str(e)
    else:
        # X clicked — clear bids
        st.session_state.bids     = []
        st.session_state.result   = None
        st.session_state.edit_id  = None
        st.session_state._import_error = None

imp_col, _ = st.columns([2,4])
with imp_col:
    st.file_uploader("Import bids (JSON)", type="json",
                     label_visibility="collapsed",
                     key="bid_uploader",
                     on_change=_handle_upload)
    if st.session_state.get("_import_error"):
        st.error(f"Import failed: {st.session_state._import_error}")

st.divider()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_bids, tab_matrix, tab_opt, tab_scenarios, tab_ref = st.tabs([
    "Bids", "Buyers Matrix", "Optimization", "Scenarios", "Reference"
])

# ══════════════════════════════════════════════════════════════════════════════
# BIDS TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_bids:
    bids   = st.session_state.bids
    result = st.session_state.result
    win_ids = {b.get("id") for b in result.get("winners",[])} if result else set()

    # Add bid button
    add_col, _ = st.columns([2,6])
    with add_col:
        if st.button("+ Add bid", type="primary", use_container_width=True):
            st.session_state.show_add  = not st.session_state.show_add
            st.session_state.edit_id   = None
            st.rerun()

    # Add bid form (collapses on submit)
    if st.session_state.show_add:
        st.markdown('<div class="inline-edit">', unsafe_allow_html=True)
        st.markdown("**Add New Bid**")
        action, new_bid = bid_form_inline("add")
        st.markdown('</div>', unsafe_allow_html=True)
        if action == "submit" and new_bid:
            st.session_state.bids.append(new_bid)
            st.session_state.result   = None
            st.session_state.show_add = False
            st.rerun()
        elif action == "cancel":
            st.session_state.show_add = False
            st.rerun()

    if not bids:
        st.info("No bids yet — click '+ Add bid' above.")
    else:
        # Summary metrics
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("Total bids", len(bids))
        m2.metric("Stalking horse", sum(1 for b in bids if b.get("isSH")))
        m3.metric("Included", sum(1 for b in bids if b.get("include",True)))
        m4.metric("Gross (no conflicts)", fmt(sum(b.get("amount",0) for b in bids)))
        st.divider()

        # Header row matching data column ratios
        header = st.columns([0.25, 2.5, 0.9, 1.4, 0.5, 0.65, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3])
        header_labels = ["", "Buyer", "Amount", "Scope", "Stores", "Mode", "Incl", "SH", "PLK", "Edit", "Copy", "Del"]
        for col, label in zip(header, header_labels):
            col.markdown(f"<p style='font-size:0.62rem;color:#888;font-weight:600;text-transform:uppercase;letter-spacing:0.04em;margin:0;padding-bottom:4px;border-bottom:1.5px solid #1F3864;text-align:center'>{label}</p>", unsafe_allow_html=True)

        for i, bid in enumerate(bids):
            f_data = fin(bid.get("storeIds",[]))
            ev     = bid["amount"]/f_data["e"] if f_data["e"]>0 else None
            ovl    = conflicts(bid, bids)
            is_editing  = st.session_state.edit_id == bid.get("id")
            detail_key  = f"detail_{bid.get('id')}"
            is_detailed = st.session_state.get(detail_key, False)

            # Build compact flag string
            flags = []
            if bid.get("isSH"):             flags.append("⚓SH")
            if bid.get("plkApproval"):      flags.append("✓PLK")
            if not bid.get("include",True): flags.append("🚫")
            if ovl:                         flags.append(f"{ovl}⚡")
            if result:                      flags.append("WIN" if bid.get("id") in win_ids else "")
            flag_str = "  ".join(f for f in flags if f)

            # Row — [▸][Buyer][Amount][Scope][Stores][Mode][👁][⚓][PLK][✏️][⧉][🗑]
            # Matching the HTML tool button layout: always-visible icon buttons
            r = st.columns([0.25, 2.5, 0.9, 1.4, 0.5, 0.65, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3])

            with r[0]:
                arrow = "▾" if (is_detailed or is_editing) else "▸"
                if st.button(arrow, key=f"exp_{i}", use_container_width=True):
                    st.session_state[detail_key] = not is_detailed
                    st.session_state.edit_id = None
                    st.rerun()
            with r[1]:
                buyer_display = f"**{bid.get('buyer','')}**"
                if flag_str: buyer_display += f"  :gray[{flag_str}]"
                st.markdown(buyer_display)
                if bid.get("comment"): st.caption(bid["comment"])
            with r[2]:
                st.markdown(fmt(bid.get("amount",0)))
                if ev: st.caption(f"{ev:.1f}x EBITDA")
            with r[3]:
                st.caption(scope(bid))
            with r[4]:
                st.caption(str(len(bid.get("storeIds",[]))))
            with r[5]:
                st.caption(bid.get("optMode","bundle"))
            with r[6]:
                inc = bid.get("include", True)
                # Always show eye — grey styling when excluded
                if st.button("👁", key=f"inc_{i}", use_container_width=True,
                             type="secondary" if inc else "primary"):
                    st.session_state.bids[i]["include"] = not inc; st.rerun()
            with r[7]:
                if st.button("SH", key=f"sh_{i}", use_container_width=True,
                             type="primary" if bid.get("isSH") else "secondary"):
                    st.session_state.bids[i]["isSH"] = not bid.get("isSH"); st.rerun()
            with r[8]:
                if st.button("PLK", key=f"plk_{i}", use_container_width=True,
                             type="primary" if bid.get("plkApproval") else "secondary"):
                    st.session_state.bids[i]["plkApproval"] = not bid.get("plkApproval"); st.rerun()
            with r[9]:
                if st.button("✏", key=f"edit_{i}", use_container_width=True,
                             type="primary" if is_editing else "secondary"):
                    st.session_state.edit_id = None if is_editing else bid.get("id")
                    st.session_state[detail_key] = False
                    st.rerun()
            with r[10]:
                if st.button("⧉", key=f"copy_{i}", use_container_width=True):
                    nb = dict(bid); nb["id"] = str(uuid.uuid4())[:8]; nb["buyer"] += " (copy)"
                    st.session_state.bids.append(nb); st.rerun()
            with r[11]:
                if st.button("✕", key=f"del_{i}", use_container_width=True):
                    st.session_state.bids.pop(i); st.session_state.result = None
                    if st.session_state.edit_id == bid.get("id"): st.session_state.edit_id = None
                    st.rerun()


            # Detail dropdown (read-only full breakdown)
            if is_detailed and not is_editing:
                d1,d2,d3,d4,d5 = st.columns(5)
                d1.metric("Net sales", fmt(f_data["s"]))
                d2.metric("EBITDA",    fmt(f_data["e"]))
                d3.metric("EV/EBITDA", f"{ev:.1f}x" if ev else "—")
                d4.metric("Cure",      fmt(cure(bid.get("storeIds",[]))))
                d5.metric("Maint capex", fmt(capex_total(bid.get("storeIds",[]))))
                rows = []
                for sid in sorted(bid.get("storeIds",[])):
                    sd = STORE_DATA.get(sid,{}); cc = CURE.get(sid,0)
                    store_bid = None
                    if bid.get("optMode")=="perStore" and bid.get("storeAmounts"):
                        sa = bid["storeAmounts"].get(str(sid)) or bid["storeAmounts"].get(sid)
                        if sa: store_bid = float(sa)*1e6
                    rows.append({"Store":sid,"Market":STORE_MKT.get(sid,""),
                        "Bid":fmt(store_bid) if store_bid else "—",
                        "Net Sales":fmt(sd.get("s",0)),"EBITDA":fmt(sd.get("e",0)),
                        "Maint Capex":fmt(RUN_RATE.get(sid,0)),"Reno Capex":fmt(RENO_CAPEX.get(sid,0)),
                        "Reno Yr":RENO_YEAR.get(sid,0) or "—","Cure":fmt(cc)})
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            # Edit dropdown (inline form below the row)
            if is_editing:
                st.markdown('<div class="inline-edit">', unsafe_allow_html=True)
                st.markdown(f"**Editing: {bid.get('buyer','')}**")
                action, updated = bid_form_inline(f"edit_{bid.get('id','')}", iv=bid, is_edit=True)
                st.markdown('</div>', unsafe_allow_html=True)
                if action == "submit" and updated:
                    st.session_state.bids[i] = updated
                    st.session_state.result  = None
                    st.session_state.edit_id = None
                    st.rerun()
                elif action == "cancel":
                    st.session_state.edit_id = None
                    st.rerun()

            st.markdown("<hr style='margin:2px 0;border:none;border-top:0.5px solid #eee'>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
with tab_matrix:
    bids   = st.session_state.bids
    result = st.session_state.result
    win_ids = {b.get("id") for b in result.get("winners",[])} if result else set()

    if not bids:
        st.info("No bids to display.")
    else:
        rows = []
        for bid in bids:
            bs  = set(bid.get("storeIds",[]))
            row = {"Buyer": bid.get("buyer",""), "Scope": scope(bid), "Amount": fmt(bid.get("amount",0))}
            if result: row["Result"] = "WIN" if bid.get("id") in win_ids else "—"
            for m, ss in MARKET_STORES.items():
                cov = sum(1 for s in ss if s in bs); tot = len(ss)
                row[MKT_ABBR[m]] = "All" if cov==tot else (f"{cov}/{tot}" if cov else "—")
            if bid.get("comment"): row["Comment"] = bid["comment"]
            rows.append(row)
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.divider()
        st.markdown("#### Market financials")
        mkt_rows = []
        for m, ss in MARKET_STORES.items():
            agg = MKT_AGG[m]
            margin = agg["ebitda"]/agg["sales"]*100 if agg["sales"]>0 else 0
            mkt_rows.append({
                "Market":       m,
                "Stores":       agg["count"],
                "Net Sales":    fmt(agg["sales"]),
                "EBITDA":       fmt(agg["ebitda"]),
                "EBITDA Margin":f"{margin:.1f}%",
                "Maint Capex":  fmt(agg["run_rate"]),
                "Reno Capex":   fmt(agg["reno_capex"]),
            })
        st.dataframe(pd.DataFrame(mkt_rows), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# OPTIMIZATION TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_opt:
    bids     = st.session_state.bids
    included = [b for b in bids if b.get("include", True)]

    if not included:
        st.warning("No bids included in optimization.")
    else:
        run_col, save_col = st.columns([2,2])
        with run_col:
            run_clicked = st.button("Run Optimizer", type="primary", use_container_width=True)
        with save_col:
            save_name = st.text_input("Scenario name", placeholder="e.g. Round 1 — post-auction",
                                      label_visibility="collapsed", key="scenario_name")

        if run_clicked:
            with st.spinner("Running OR-Tools CP-SAT..."):
                exp = expand(included)
                sh_exp = [b for b in exp if b.get("isSH")]
                winners, gross, ms = optimize(exp)
                sh_w, sh_floor, _ = optimize(sh_exp) if sh_exp else ([], 0, 0)
                win_pids    = {b.get("_pid", b.get("id","")) for b in winners}
                sh_win_pids = {b.get("_pid", b.get("id","")) for b in sh_w}
                disp_sh     = [b for b in sh_exp if b.get("_pid",b.get("id","")) in sh_win_pids
                                                  and b.get("_pid",b.get("id","")) not in win_pids]
                bkp         = sum(b["amount"]*b.get("breakupPct",2.5)/100 +
                                  len(b.get("storeIds",[]))*CASE["expReimbPerStore"] for b in disp_sh)
                win_stores  = [s for b in winners for s in b.get("storeIds",[])]
                tot_cure    = cure(win_stores)
                net_sh      = gross - bkp
                net_cure    = net_sh - tot_cure

                # Reconstruct display winners (only winning stores per buyer)
                seen = {}
                for w in winners:
                    pid = w.get("_pid", w.get("id",""))
                    if pid not in seen:
                        orig = next((b for b in included if b.get("id")==pid), w)
                        seen[pid] = {**orig, "storeIds": list(w.get("storeIds",[])), "amount": w.get("amount",0)}
                    else:
                        seen[pid]["storeIds"] += w.get("storeIds",[])
                        seen[pid]["amount"]   += w.get("amount",0)
                display_winners = list(seen.values())

                st.session_state.result = dict(
                    winners=display_winners, gross=gross, ms=ms, sh_floor=sh_floor,
                    disp_sh=disp_sh, bkp=bkp, win_stores=win_stores,
                    tot_cure=tot_cure, net_sh=net_sh, net_cure=net_cure,
                    win_pids=win_pids, bids_snapshot=json.dumps(included),
                )
            st.rerun()

    result = st.session_state.result
    if result:
        winners    = result["winners"];     gross     = result["gross"]
        net_cure   = result["net_cure"];    net_sh    = result["net_sh"]
        tot_cure   = result["tot_cure"];    bkp       = result["bkp"]
        disp_sh    = result["disp_sh"];     win_stores= result["win_stores"]
        sh_floor   = result["sh_floor"];    ms        = result["ms"]

        # KPIs
        k1,k2,k3,k4,k5 = st.columns(5)
        k1.metric("Gross proceeds",  fmt(gross))
        k2.metric("SH protections",  fmt(-bkp) if bkp else "—")
        k3.metric("Net after SH",    fmt(net_sh))
        k4.metric("Cure costs",      fmt(-tot_cure))
        k5.metric("Net after cure",  fmt(net_cure))
        st.caption(f"OR-Tools solved in {ms}ms · {len(winners)} winning bids · "
                   f"{len(set(win_stores))}/119 stores · SH floor: {fmt(sh_floor)}")

        # Save scenario button
        if save_name:
            if st.button("Save scenario", key="save_scenario_btn"):
                scenario = {
                    "id":         str(uuid.uuid4())[:8],
                    "name":       save_name,
                    "timestamp":  time.strftime("%Y-%m-%d %H:%M"),
                    "gross":      gross,
                    "net_cure":   net_cure,
                    "winners":    winners,
                    "disp_sh":    disp_sh,
                    "bkp":        bkp,
                    "win_stores": win_stores,
                    "tot_cure":   tot_cure,
                    "net_sh":     net_sh,
                    "sh_floor":   sh_floor,
                    "ms":         ms,
                    "bids":       json.loads(result.get("bids_snapshot","[]")),
                }
                st.session_state.scenarios.append(scenario)
                st.success(f"Saved scenario: {save_name}")

        st.divider()
        col_a, col_w = st.columns([3,2])

        with col_a:
            st.markdown("#### Winning allocation")
            for bid in sorted(winners, key=lambda b: -b.get("amount",0)):
                f   = fin(bid.get("storeIds",[]))
                ev  = bid["amount"]/f["e"] if f["e"]>0 else None
                c   = cure(bid.get("storeIds",[]))
                hdr = f"WIN  {'[SH] ' if bid.get('isSH') else ''}{bid.get('buyer','')} — {fmt(bid['amount'])} — {scope(bid)}"
                if bid.get("comment"): hdr += f"  [{bid['comment']}]"
                with st.expander(hdr):
                    s1,s2,s3,s4 = st.columns(4)
                    s1.metric("Bid",       fmt(bid["amount"]))
                    s2.metric("EV/EBITDA", f"{ev:.1f}x" if ev else "—")
                    s3.metric("Net sales", fmt(f["s"]))
                    s4.metric("Cure",      fmt(c))
                    rows = []
                    for sid in sorted(bid.get("storeIds",[])):
                        sd = STORE_DATA.get(sid,{}); cc = CURE.get(sid,0)
                        rr = RUN_RATE.get(sid,0);    rc = RENO_CAPEX.get(sid,0)
                        ry = RENO_YEAR.get(sid,0)
                        rows.append({"Store": sid, "Market": STORE_MKT.get(sid,""),
                            "Net Sales": fmt(sd.get("s",0)), "EBITDA": fmt(sd.get("e",0)),
                            "Margin": f"{sd.get('e',0)/sd.get('s',1)*100:.1f}%" if sd.get("s",0)>0 else "—",
                            "Maint Capex": fmt(rr), "Reno Capex": fmt(rc), "Reno Year": ry or "—",
                            "Lease cure": fmt(round(cc*0.355)), "Tax cure": fmt(round(cc*0.369)),
                            "PLK cure": fmt(round(cc*0.275)), "Total cure": fmt(cc)})
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            if disp_sh:
                st.markdown("##### Displaced SH bids")
                for bid in disp_sh:
                    fee = bid["amount"]*bid.get("breakupPct",2.5)/100 + len(bid.get("storeIds",[]))*CASE["expReimbPerStore"]
                    st.markdown(f"DISPLACED  {bid.get('buyer','')} — breakup fee: **{fmt(fee)}**")

        with col_w:
            st.markdown("#### Proceeds waterfall")
            lease_c = sum(CURE.get(s,0)*0.355 for s in win_stores)
            tax_c   = sum(CURE.get(s,0)*0.369 for s in win_stores)
            plk_c   = sum(CURE.get(s,0)*0.275 for s in win_stores)
            for label, val, indent in [
                ("Gross auction proceeds",          gross,     False),
                (f"SH protections ({len(disp_sh)} displaced)", -bkp if bkp else 0, True),
                ("Net after SH protections",        net_sh,    False),
                ("Lease cure costs",               -lease_c,   True),
                ("Tax cure costs",                 -tax_c,     True),
                ("PLK cure costs",                 -plk_c,     True),
                (f"Total cure ({len(set(win_stores))} stores)", -tot_cure, False),
                ("Net after cure costs",            net_cure,  False),
            ]:
                if val==0 and indent: continue
                prefix = "  └─ " if indent else ""
                color  = "color:#a32d2d" if val<0 else ("color:#3b6d11" if not indent and val>0 else "color:#1a1a18")
                bold   = "font-weight:700" if not indent else ""
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;padding:5px 0;"
                    f"border-bottom:0.5px solid #eee;{bold}'>"
                    f"<span>{prefix}{label}</span>"
                    f"<span style='{color}'>{fmt(val)}</span></div>",
                    unsafe_allow_html=True)
            st.caption("Cure per KIA 05-24-2026")

        # Uncovered stores
        uncov = [s for s in ALL_STORES if s not in set(win_stores)]
        if uncov:
            st.divider()
            st.markdown(f"#### Uncovered stores ({len(uncov)})")
            um = {}
            for s in uncov: um.setdefault(STORE_MKT.get(s,"?"),[]).append(s)
            cols_u = st.columns(len(um))
            for col_u,(m,ss) in zip(cols_u, um.items()):
                col_u.markdown(f"**{m}**")
                col_u.write(", ".join(str(s) for s in ss))

# ══════════════════════════════════════════════════════════════════════════════
# SCENARIOS TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_scenarios:
    scenarios = st.session_state.scenarios

    if not scenarios:
        st.info("No scenarios saved yet. Run the optimizer and enter a scenario name to save.")
    else:
        st.markdown(f"#### {len(scenarios)} saved scenario{'s' if len(scenarios)!=1 else ''}")

        # Export all scenarios
        scenarios_json = json.dumps(scenarios, indent=2)
        st.download_button("Export all scenarios", data=scenarios_json,
                           file_name="sailormen_scenarios.json", mime="application/json")
        st.divider()

        for i, sc in enumerate(scenarios):
            with st.expander(f"**{sc['name']}**  —  {fmt(sc['gross'])} gross · {fmt(sc['net_cure'])} net after cure  ·  {sc['timestamp']}"):
                k1,k2,k3,k4,k5 = st.columns(5)
                k1.metric("Gross",      fmt(sc["gross"]))
                k2.metric("SH fees",    fmt(-sc["bkp"]) if sc["bkp"] else "—")
                k3.metric("Net/SH",     fmt(sc["net_sh"]))
                k4.metric("Cure",       fmt(-sc["tot_cure"]))
                k5.metric("Net/Cure",   fmt(sc["net_cure"]))
                st.caption(f"Solved in {sc['ms']}ms · SH floor: {fmt(sc['sh_floor'])} · {len(set(sc['win_stores']))}/119 stores")

                st.markdown("**Winning bids:**")
                sc_rows = []
                for bid in sorted(sc["winners"], key=lambda b: -b.get("amount",0)):
                    f  = fin(bid.get("storeIds",[]))
                    ev = bid["amount"]/f["e"] if f["e"]>0 else None
                    sc_rows.append({
                        "Buyer":     bid.get("buyer",""),
                        "Amount":    fmt(bid.get("amount",0)),
                        "Scope":     scope(bid),
                        "Stores":    len(bid.get("storeIds",[])),
                        "EBITDA":    fmt(f["e"]),
                        "EV/EBITDA": f"{ev:.1f}x" if ev else "neg",
                        "SH":        "Yes" if bid.get("isSH") else "",
                    })
                st.dataframe(pd.DataFrame(sc_rows), use_container_width=True, hide_index=True)

                del_col, _ = st.columns([1,5])
                with del_col:
                    if st.button("Delete scenario", key=f"del_sc_{i}"):
                        st.session_state.scenarios.pop(i); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# REFERENCE TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_ref:
    st.markdown("#### Store-level reference — all 119 stores")
    ref = []
    for m, ss in MARKET_STORES.items():
        for sid in ss:
            sd = STORE_DATA.get(sid,{}); s=sd.get("s",0); e=sd.get("e",0)
            c=CURE.get(sid,0); rr=RUN_RATE.get(sid,0); rc=RENO_CAPEX.get(sid,0); ry=RENO_YEAR.get(sid,0)
            ref.append({"Store":sid,"Market":m,"Net Sales":s,"EBITDA":e,
                "Margin":round(e/s*100,1) if s>0 else 0,
                "Maint Capex":rr,"Reno Capex":rc,"Reno Year":ry or 0,"Cure":c})
    st.dataframe(pd.DataFrame(ref), use_container_width=True, hide_index=True,
        column_config={
            "Net Sales":   st.column_config.NumberColumn(format="$%d"),
            "EBITDA":      st.column_config.NumberColumn(format="$%d"),
            "Margin":      st.column_config.NumberColumn(format="%.1f%%"),
            "Maint Capex": st.column_config.NumberColumn(format="$%d"),
            "Reno Capex":  st.column_config.NumberColumn(format="$%d"),
            "Cure":        st.column_config.NumberColumn(format="$%d"),
        })
    tot_s=sum(STORE_DATA.get(s,{}).get("s",0) for s in ALL_STORES)
    tot_e=sum(STORE_DATA.get(s,{}).get("e",0) for s in ALL_STORES)
    p1,p2,p3,p4,p5,p6 = st.columns(6)
    p1.metric("Stores",     119)
    p2.metric("Net sales",  fmt(tot_s))
    p3.metric("EBITDA",     fmt(tot_e))
    p4.metric("Margin",     f"{tot_e/tot_s*100:.1f}%")
    p5.metric("Maint capex",fmt(sum(RUN_RATE.values())))
    p6.metric("Total cure", fmt(sum(CURE.values())))
