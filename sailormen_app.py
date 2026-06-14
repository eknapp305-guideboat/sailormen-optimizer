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

CURE = {1:112177,2:99370,3:173013,4:97227,5:131930,6:89348,7:117839,8:126960,9:170439,10:133248,11:196317,12:125487,17:159200,18:94180,28:77254,29:76408,30:69492,31:59701,54:113242,55:106580,93:123522,95:104683,97:93719,99:83199,100:124433,101:78398,102:68442,103:91026,104:98420,105:85538,106:95726,107:91683,109:107415,112:68667,113:114525,114:113993,115:62004,116:114382,117:75475,118:106408,119:68226,120:108879,121:86384,122:162416,123:92010,124:79796,125:105525,126:66452,127:97064,128:95746,129:68532,130:70964,131:48443,132:119137,139:66677,140:86340,141:82301,142:59125,143:59197,146:65404,148:96427,150:91297,151:106387,152:121825,154:90710,155:109028,156:112571,157:93439,160:87097,162:101951,163:95844,167:112057,170:120110,171:96053,177:141140,178:73890,179:128513,180:84238,181:88107,183:67874,184:79256,185:113359,186:75993,187:80933,190:117119,191:79415,193:79886,194:100117,196:146715,198:121300,199:146277,200:69252,203:71773,207:80572,209:65069,210:72555,211:86245,212:79871,213:97187,214:91442,218:113932,219:64948,220:98194,221:85638,223:64678,224:58498,225:72915,228:59658,229:119806,230:99455,232:57782,238:61629,241:91765,242:92106,246:98869,250:125120,251:103383,901:52500,902:119836}

RUN_RATE = {128:48132,129:24063,130:8113,131:24063,132:48127,146:48127,148:95613,150:16227,151:16227,152:48127,154:16227,155:149063,156:16227,157:8113,160:48127,162:48127,163:48127,183:7866,187:48132,190:16232,196:16232,199:48132,210:13532,213:16232,214:16232,221:16232,229:16232,250:16987,102:24064,103:16227,107:8113,109:8113,112:16227,113:15727,114:8116,115:16227,116:16227,117:48127,118:48127,119:48127,120:16227,121:16227,122:7866,123:48127,124:48132,125:24063,126:224063,127:16227,177:16227,178:48132,179:16232,230:16232,246:16232,1:16227,2:16227,3:132863,4:7863,5:15732,6:15727,7:8116,8:16227,9:15727,10:16227,11:15732,12:8116,17:8113,18:8113,54:48127,55:48127,167:47050,198:48132,218:15732,220:15727,93:120613,95:241227,97:16227,99:8113,100:16227,101:16227,104:8765,105:16227,106:16227,171:120613,194:16232,242:16232,251:16987,901:16227,902:16227,139:48127,140:16227,141:24063,142:124063,143:24064,180:16232,181:48132,185:16232,203:16232,211:16232,228:13532,232:16232,238:17487,241:17487,28:16227,29:48127,30:133116,31:16227,184:48132,186:16232,191:48132,193:16232,207:48132,212:15732,219:16232,170:8116,200:48132,209:16232,223:48132,224:24063,225:24066}

RENO_CAPEX = {128:525000,129:350000,130:750000,131:1000000,132:525000,146:750000,148:525000,150:750000,151:525000,152:750000,154:525000,155:750000,156:750000,157:350000,160:525000,162:750000,163:525000,183:350000,187:350000,190:350000,196:350000,199:350000,210:0,213:350000,214:150000,221:150000,229:350000,250:150000,102:750000,103:750000,107:750000,109:750000,112:750000,113:150000,114:1000000,115:525000,116:750000,117:750000,118:750000,119:525000,120:525000,121:525000,122:750000,123:350000,124:750000,125:750000,126:350000,127:750000,177:350000,178:350000,179:350000,230:350000,246:150000,1:525000,2:750000,3:750000,4:750000,5:350000,6:150000,7:750000,8:750000,9:750000,10:525000,11:525000,12:750000,17:750000,18:750000,54:525000,55:750000,167:750000,198:350000,218:350000,220:150000,93:525000,95:525000,97:525000,99:750000,100:750000,101:525000,104:750000,105:525000,106:750000,171:525000,194:150000,242:150000,251:150000,901:750000,902:750000,139:1000000,140:750000,141:750000,142:150000,143:750000,180:350000,181:350000,185:350000,203:350000,211:150000,228:0,232:150000,238:150000,241:150000,28:750000,29:525000,30:750000,31:525000,184:350000,186:150000,191:350000,193:350000,207:350000,212:150000,219:150000,170:750000,200:350000,209:350000,223:1000000,224:750000,225:1000000}

RENO_YEAR = {128:2029,129:2027,130:2027,131:2028,132:2029,146:2029,148:2028,150:2029,151:2029,152:2029,154:2031,155:2027,156:2029,157:2028,160:2029,162:2029,163:2030,183:2028,187:2030,190:2030,196:2030,199:2029,210:2031,213:2032,214:2032,221:2032,229:2032,250:2035,102:2027,103:2029,107:2028,109:2027,112:2029,113:2034,114:2028,115:2030,116:2029,117:2026,118:2029,119:2029,120:2029,121:2030,122:2028,123:2029,124:2029,125:2028,126:2027,127:2026,177:2026,178:2029,179:2029,230:2032,246:2034,1:2030,2:2029,3:2028,4:2028,5:2030,6:2033,7:2028,8:2029,9:2029,10:2029,11:2030,12:2028,17:2028,18:2027,54:2031,55:2029,167:2027,198:2031,218:2032,220:2032,93:2027,95:2026,97:2030,99:2028,100:2029,101:2031,104:2027,105:2029,106:2026,171:2027,194:2029,242:2033,251:2035,901:2033,902:2033,139:2029,140:2029,141:2028,142:2028,143:2028,180:2029,181:2029,185:2030,203:2030,211:2031,228:2032,232:2032,238:2033,241:2033,28:2029,29:2030,30:2027,31:2030,184:2030,186:2030,191:2026,193:2030,207:2031,212:2032,219:2032,170:2027,200:2031,209:2031,223:2029,224:2028,225:2027}


CURE_RENT = {1:20304,2:22620,3:62688,4:39757,5:28592,6:12956,7:29607,8:37925,9:13830,10:30226,11:73209,12:23893,17:44498,18:0,28:29462,29:32164,30:19314,31:26146,54:27377,55:27606,93:38531,95:36179,97:26422,99:20345,100:36141,101:13906,102:13746,103:13915,104:36026,105:28619,106:35252,107:24351,109:36165,112:13633,113:26200,114:30675,115:13746,116:33164,117:13830,118:33275,119:13830,120:38785,121:21653,122:25506,123:31675,124:13830,125:32082,126:19805,127:21575,128:24721,129:29739,130:13920,131:13830,132:35012,139:28067,140:29074,141:16218,142:25959,143:22823,146:10833,148:24845,150:15457,151:24771,152:28841,154:36213,155:36887,156:23432,157:16646,160:14333,162:27009,163:26674,167:50354,170:33527,171:22338,177:49156,178:19058,179:30250,180:30195,181:29954,183:36085,184:25379,185:29703,186:24806,187:29055,190:27884,191:28722,193:35337,194:39986,196:43037,198:27014,199:39626,200:27265,203:34939,207:37547,209:26178,210:25385,211:33000,212:20833,213:23625,214:25903,218:35438,219:22306,220:32473,221:24378,223:21404,224:21906,225:21378,228:28750,229:24697,230:24500,232:21167,238:15575,241:30625,242:23625,246:33750,250:30525,251:42263,901:23341,902:32508}

CURE_TAX = {1:41550,2:32714,3:41043,4:13980,5:49331,6:22212,7:14190,8:32603,9:70726,10:41665,11:45120,12:39911,17:36520,18:22977,28:10228,29:19653,30:9305,31:4605,54:47667,55:37325,93:39191,95:29117,97:30113,99:31379,100:27141,101:27837,102:28985,103:38061,104:18738,105:12934,106:16248,107:33877,109:35344,112:17777,113:39429,114:40460,115:15793,116:29404,117:26709,118:30944,119:15720,120:8196,121:27762,122:90251,123:33985,124:27112,125:14765,126:11744,127:17416,128:28189,129:18709,130:21632,131:16814,132:51759,139:5359,140:27761,141:35817,142:3143,143:1032,146:32294,148:36122,150:31562,151:45342,152:48305,154:31558,155:45295,156:60661,157:37406,160:38004,162:40600,163:34877,167:12888,170:47442,171:36003,177:37031,178:27848,179:48725,180:19112,181:39410,183:1701,184:20440,185:34217,186:17016,187:20366,190:52597,191:19655,193:19836,194:21506,196:51606,198:50578,199:56434,200:7918,203:6913,207:21380,209:5728,210:24225,211:30223,212:17003,213:40773,214:36223,218:44150,219:17763,220:30915,221:37650,223:12377,224:4721,225:7573,228:10523,229:59596,230:37529,232:7314,238:25551,241:26688,242:40673,246:35034,250:56572,251:34047,901:19193,902:35045}

CURE_RA_PRE = {1:13468,2:11418,3:17701,4:11056,5:13620,6:14161,7:19445,8:14726,9:22452,10:15282,11:18836,12:15969,17:20572,18:18626,28:9850,29:6402,30:10593,31:7568,54:8550,55:10923,93:11289,95:9805,97:8172,99:7811,100:16033,101:8983,102:6726,103:9444,104:11701,105:12237,106:10841,107:8778,109:9380,112:8726,113:13721,114:11606,115:8369,116:13170,117:8971,118:11525,119:10144,120:15790,121:9599,122:12294,123:6597,124:9415,125:14224,126:9157,127:14842,128:11328,129:5626,130:8884,131:6776,132:8489,139:8508,140:7175,141:8450,142:7707,143:9751,146:6119,148:8346,150:11898,151:9766,152:11819,154:6235,155:7436,156:7835,157:8853,160:8102,162:9393,163:9291,167:12960,170:9455,171:9641,177:13087,178:7066,179:12973,180:9730,181:5377,183:6761,184:8344,185:12696,186:9618,187:8432,190:9883,191:8159,193:6384,194:8354,196:13830,198:10597,199:13263,200:7442,203:7169,207:5824,209:8826,210:6354,211:6202,212:10981,213:8690,214:7541,218:8833,219:6700,220:8556,221:6204,223:8332,224:8743,225:9994,228:5618,229:9456,230:9399,232:7886,238:5943,241:9197,242:7614,246:7981,250:10249,251:7017,901:8372,902:14380}

CURE_RA_POST = {1:36856,2:32619,3:51581,4:32434,5:40386,6:40019,7:54597,8:41706,9:63431,10:46074,11:59153,12:45714,17:57609,18:52577,28:27714,29:18188,30:30280,31:21381,54:29648,55:30727,93:34511,95:29581,97:29013,99:23664,100:45118,101:27672,102:18985,103:29604,104:31956,105:31747,106:33385,107:24677,109:26526,112:28531,113:35176,114:31253,115:24097,116:38644,117:25966,118:30664,119:28532,120:46108,121:27371,122:34364,123:19753,124:29439,125:44455,126:25746,127:43231,128:31508,129:14458,130:26527,131:11023,132:23877,139:24743,140:22330,141:21816,142:22316,143:25590,146:16158,148:27115,150:32380,151:26508,152:32861,154:16704,155:19410,156:20642,157:30535,160:26659,162:24950,163:25002,167:35855,170:29686,171:28071,177:41866,178:19920,179:36565,180:25201,181:13367,183:23328,184:25093,185:36743,186:24554,187:23081,190:26755,191:22880,193:18328,194:30271,196:38242,198:33111,199:36954,200:26627,203:22752,207:15821,209:24336,210:16591,211:16820,212:31053,213:24100,214:21775,218:25511,219:18178,220:26250,221:17406,223:22566,224:23128,225:33970,228:14768,229:26057,230:28026,232:21414,238:14560,241:25255,242:20194,246:22104,250:27773,251:20057,901:1594,902:37903}

CURE_LANDLORD = {1: 'SVC ABS', 2: 'SVC ABS', 3: 'Realty Income Corp', 4: 'The Promenada Plaza Partnership c/o', 5: 'Los Compadres', 6: 'Realty Income Corp', 7: 'Field Apartments', 8: 'SB SAND LLC', 9: 'Store SPE Chancellor 2021-3', 10: 'SVC ABS', 11: 'F&L Properties', 12: 'SVC ABS', 17: 'SVC ABS', 18: 'Nazih Chamoun c/o Brad Kline with P', 28: 'SVC ABS', 29: 'Realty Income Corp', 30: 'Jean Cornil', 31: 'Nine Mile Plaza Investors c/o Victo', 54: 'SVC ABS', 55: 'First Power Group', 93: 'B-Thap', 95: 'Realty Income Corp', 97: 'Realty Income Corp', 99: 'Anna Smith Barthell (John G. Barthe', 100: 'Realty Income Corp', 101: 'Store SPE Chancellor 2021-3', 102: 'Store SPE Chancellor 2021-3', 103: 'Store SPE Chancellor 2021-3', 104: 'Realty Income Corp', 105: 'Heart of Florida c/o Brookhill Mana', 106: 'Realty Income Corp', 107: 'LEEAGLES', 109: 'Realty Income Corp', 112: 'FREP V', 113: 'LDP Bailey Road LLC', 114: '402 Main', 115: 'Store SPE Chancellor 2021-3', 116: 'HS Land Holdings LTD', 117: 'Store SPE Chancellor 2021-3', 118: 'WDP Enterprises at Melbourne LLC', 119: 'Store SPE Chancellor 2021-3', 120: 'Vast Peak Property LLC', 121: 'HS Land Holdings LTD', 122: 'HS Land Holdings LTD', 123: 'Realty Income Corp', 124: 'Store SPE Chancellor 2021-3', 125: 'HS Land Holdings LTD', 126: 'HS Land Holdings LTD', 127: 'Shepard Banks Investment', 128: 'HS Land Holdings LTD', 129: 'Realty Income Corp', 130: 'Store SPE Chancellor 2021-3', 131: 'Store SPE Chancellor 2021-3', 132: 'J11823 PLANO ROAD LLC', 139: '813 Lake Bradford FL', 140: 'Altocumulus', 141: 'Strickland Brothers', 142: 'Realty Income Corp', 143: 'Realty Income Corp', 146: '50% Brewer Family Trust dated May 2', 148: 'LLD Family Properties II', 150: 'Hart Centers VI LTD', 151: 'Anna Smith Barthell (John G. Barthe', 152: '8007 Normandy', 154: 'Realty Income Corp', 155: '10132 SAN JOSE NS LLC & 10132 SAN J', 156: '524 Atlantic Blvd', 157: 'MQ Series Investments', 160: 'FLI Properties', 162: 'Narita Holdings', 163: '5581 Soutel', 167: 'South Dade Shopping', 170: 'Iris Associates LP', 171: 'Howard N Real Estate Investments', 177: 'Inverinvest Company LLC', 178: 'Spider Group Corporation', 179: 'Mocny Limited Partnership LLLP', 180: 'Rooster 2 Quincy Properties', 181: 'Jengeo Realty', 183: 'The Richard Esnard Living Trust Dat', 184: 'MESA Crestview', 185: 'Freedom Holdings', 186: 'EEMS Kerollos', 187: '2496 Blanding Blvd LLC -Eliaho Wein', 190: 'Sanft and Hollenbach', 191: 'Apple & Apple', 193: 'KGGK Venture LLC', 194: 'TMAMM', 196: 'Golem Duval', 198: '4946 South 25th Street', 199: '320', 200: 'Augusta Road', 203: 'Lawrence Martin', 207: 'Luke Starlight', 209: 'DoubleV Pooler', 210: 'Neimon Group LLC', 211: 'Andrade Associates Limited Partners', 212: 'Anna Smith Barthell (John G. Barthe', 213: 'VDM Longwood Retail', 214: 'Rizzy Investment', 218: 'LR911', 219: 'WACHS Capital LP', 220: 'SO Miami Kal-Si-Stem', 221: 'LBJ Alachua', 223: 'RGS Commerical LLC', 224: '4202 Third Avenue', 225: 'James E. Weilbaecher Jr. Revocable ', 228: 'Blue Dominion', 229: 'Atrium Circle CP', 230: 'The San Marino Group', 232: 'Seven Prings Trust and Vinton & Son', 238: '404 Midland Avenue', 241: 'Art Family Investments Corp', 242: '63rd Terrace', 246: 'Orange Way Properties', 250: 'Navdeep Singh & Rajinder Singh', 251: 'Investments AAB Two', 901: 'JDSI', 902: '820 N Washington'}

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
if "bids"           not in st.session_state: st.session_state.bids           = [dict(b) for b in SAMPLE_BIDS]
if "result"         not in st.session_state: st.session_state.result         = None
if "edit_id"        not in st.session_state: st.session_state.edit_id        = None
if "show_add"       not in st.session_state: st.session_state.show_add       = False
if "scenarios"      not in st.session_state: st.session_state.scenarios      = []
if "cure_overrides" not in st.session_state: st.session_state.cure_overrides = {}

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

def cure(sids):
    overrides = st.session_state.get("cure_overrides", {})
    return sum(overrides.get(s, overrides.get(str(s), CURE.get(s,0))) for s in sids)

def effective_cure(sid):
    overrides = st.session_state.get("cure_overrides", {})
    return overrides.get(sid, overrides.get(str(sid), CURE.get(sid,0)))

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
    # Objective: net of cure OR gross depending on toggle
    opt_mode_flag = st.session_state.get("opt_objective", "Net of cure costs")
    if opt_mode_flag == "Net of cure costs":
        cure_amounts = [round(sum(effective_cure(s) for s in b.get("storeIds",[])) * scale)
                        for b in bids]
        net_amounts  = [amounts[i] - cure_amounts[i] for i in range(len(bids))]
        model.Maximize(sum(net_amounts[i]*x[i] for i in range(len(bids))))
    else:
        # Gross: maximize purchase price only
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
    export_payload = {
        "bids": st.session_state.bids,
        "cure_overrides": {str(k):v for k,v in st.session_state.get("cure_overrides",{}).items()}
    }
    bids_json = json.dumps(export_payload, indent=2)
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
            data = json.loads(raw)
            # Support two formats:
            # 1. Plain list of bids: [{"buyer":...}, ...]
            # 2. Dict with bids + cure overrides: {"bids":[...], "cure_overrides":{store_id: amount}}
            if isinstance(data, list):
                imported = data
                cure_overrides = {}
            elif isinstance(data, dict):
                imported       = data.get("bids", [])
                cure_overrides = {int(k): v for k,v in data.get("cure_overrides", {}).items()}
            else:
                st.session_state._import_error = "Invalid JSON format"
                return
            for b in imported:
                if "id" not in b: b["id"] = str(uuid.uuid4())[:8]
            st.session_state.bids           = imported
            st.session_state.cure_overrides = cure_overrides
            st.session_state.result         = None
            st.session_state.edit_id        = None
            st.session_state._import_error  = None
            if cure_overrides:
                st.session_state._import_msg = f"Imported {len(imported)} bids + cure overrides for {len(cure_overrides)} stores"
            else:
                st.session_state._import_msg = f"Imported {len(imported)} bids"
        except Exception as e:
            st.session_state._import_error = str(e)
    else:
        # X clicked — clear bids and cure overrides
        st.session_state.bids           = []
        st.session_state.cure_overrides = {}
        st.session_state.result         = None
        st.session_state.edit_id        = None
        st.session_state._import_error  = None
        st.session_state._import_msg    = None

imp_col, _ = st.columns([2,4])
with imp_col:
    st.file_uploader("Import bids (JSON)", type="json",
                     label_visibility="collapsed",
                     key="bid_uploader",
                     on_change=_handle_upload)
    if st.session_state.get("_import_error"):
        st.error(f"Import failed: {st.session_state._import_error}")
    if st.session_state.get("_import_msg"):
        st.success(st.session_state._import_msg)
    if st.session_state.get("cure_overrides"):
        st.caption(f"🔄 Cure overrides active for {len(st.session_state.cure_overrides)} stores — hardcoded values bypassed")

st.divider()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_bids, tab_matrix, tab_opt, tab_cure, tab_curecosts, tab_scenarios, tab_ref = st.tabs([
    "Bids", "Buyers Matrix", "Optimization", "Cure Analysis", "Cure Costs", "Scenarios", "Reference"
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
                net_to_estate = bid.get("amount",0) - cure(bid.get("storeIds",[]))
                color = "green" if net_to_estate >= 0 else "red"
                st.markdown(fmt(bid.get("amount",0)))
                st.markdown(f":{color}[Net: {fmt(net_to_estate)}]")
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
                bid_stores   = set(bid.get("storeIds",[]))
                mkt_stores   = set(s for m in {STORE_MKT.get(s) for s in bid_stores}
                                   for s in MARKET_STORES.get(m,[]))
                excl_stores  = [s for s in mkt_stores if s not in bid_stores]
                bid_cure_tot = cure(bid.get("storeIds",[]))
                excl_cure_tot= cure(excl_stores)
                net_est      = bid.get("amount",0) - bid_cure_tot

                d1,d2,d3,d4,d5,d6 = st.columns(6)
                d1.metric("Net sales",   fmt(f_data["s"]))
                d2.metric("EBITDA",      fmt(f_data["e"]))
                d3.metric("EV/EBITDA",   f"{ev:.1f}x" if ev else "—")
                d4.metric("Cure (bid)",  fmt(bid_cure_tot))
                net_color = "normal" if net_est >= 0 else "inverse"
                d5.metric("Net to estate", fmt(net_est),
                          delta=fmt(net_est), delta_color=net_color)
                if excl_stores:
                    d6.metric(f"Excl. cure ({len(excl_stores)} stores)",
                              fmt(excl_cure_tot),
                              help="Cure cost on stores in same markets NOT included in this bid")
                else:
                    d6.metric("Maint capex", fmt(capex_total(bid.get("storeIds",[]))))

                # Break-even callout
                break_even = bid_cure_tot
                shortfall  = break_even - bid.get("amount",0)
                if shortfall > 0:
                    st.error(f"⚠️ Bid is **{fmt(shortfall)} below break-even** — cure costs exceed purchase price")
                else:
                    st.success(f"✓ Bid clears cure costs by **{fmt(-shortfall)}**")
                rows = []
                for sid in sorted(bid.get("storeIds",[])):
                    sd = STORE_DATA.get(sid,{}); cc = CURE.get(sid,0)
                    store_bid = None
                    if bid.get("optMode")=="perStore" and bid.get("storeAmounts"):
                        sa = bid["storeAmounts"].get(str(sid)) or bid["storeAmounts"].get(sid)
                        if sa: store_bid = float(sa)*1e6
                    alloc = bid["amount"]/len(bid.get("storeIds",[])) if not store_bid else None
                    store_bid_amt = store_bid if store_bid else alloc
                    store_net = (store_bid_amt - cc) if store_bid_amt else None
                    rows.append({"Store":sid,"Market":STORE_MKT.get(sid,""),
                        "Bid":fmt(store_bid) if store_bid else (fmt(alloc)+" *" if alloc else "—"),
                        "Cure":fmt(cc),
                        "Net":fmt(store_net) if store_net else "—",
                        "Net Sales":fmt(sd.get("s",0)),"EBITDA":fmt(sd.get("e",0)),
                        "Maint Capex":fmt(RUN_RATE.get(sid,0)),"Reno Capex":fmt(RENO_CAPEX.get(sid,0)),
                        "Reno Yr":RENO_YEAR.get(sid,0) or "—"})
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
        run_col, tog_col, save_col = st.columns([2,2,2])
        with run_col:
            run_clicked = st.button("Run Optimizer", type="primary", use_container_width=True)
        with tog_col:
            opt_objective = st.radio("Optimize for",
                                     ["Net of cure costs", "Gross (SH floor only)"],
                                     horizontal=True, key="opt_objective",
                                     help="Net of cure: maximizes bid minus cure obligations. Gross: maximizes purchase price only (SH protection floor applies).")
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
        obj_label = st.session_state.get("opt_objective","Net of cure costs")
        st.caption(f"OR-Tools solved in {ms}ms · {len(winners)} winning bids · "
                   f"{len(set(win_stores))}/119 stores · SH floor: {fmt(sh_floor)} · "
                   f"Objective: {obj_label}")

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
                    net_bid   = bid["amount"] - c
                    break_even= c
                    shortfall = break_even - bid["amount"]
                    s1,s2,s3,s4,s5 = st.columns(5)
                    s1.metric("Bid",           fmt(bid["amount"]))
                    s2.metric("Cure costs",    fmt(c))
                    s3.metric("Net to estate", fmt(net_bid),
                              delta=fmt(net_bid), delta_color="normal" if net_bid>=0 else "inverse")
                    s4.metric("EV/EBITDA",     f"{ev:.1f}x" if ev else "—")
                    s5.metric("Net sales",     fmt(f["s"]))
                    if shortfall > 0:
                        st.error(f"⚠️ **{bid.get('buyer','')}** bid is **{fmt(shortfall)} below break-even** — cure costs exceed purchase price")
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
# CURE ANALYSIS TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_cure:
    st.markdown("#### Cure vs Bid — Market Summary")
    st.caption("Net to Estate = Best bid for that market minus cure costs for stores included in that bid. "
               "Red = bid is below cure (estate pays to sell). Excluded cure = cost of stores in same markets not included in any bid.")

    bids = st.session_state.bids
    included = [b for b in bids if b.get("include", True)]

    # Build best bid per market group
    from collections import defaultdict
    mkt_best = {}  # market -> best bid object
    for bid in included:
        mkts = sorted({STORE_MKT.get(s) for s in bid.get("storeIds",[]) if STORE_MKT.get(s)})
        key  = " + ".join(mkts)
        if key not in mkt_best or bid["amount"] > mkt_best[key]["amount"]:
            mkt_best[key] = bid

    # Market-level summary table
    summary_rows = []
    for mkt, stores in MARKET_STORES.items():
        # Find best single-market bid
        best_bid = None
        for bid in included:
            bid_mkts = {STORE_MKT.get(s) for s in bid.get("storeIds",[])}
            if bid_mkts == {mkt}:
                if best_bid is None or bid["amount"] > best_bid["amount"]:
                    best_bid = bid

        all_cure      = cure(stores)
        if best_bid:
            bid_stores    = best_bid.get("storeIds",[])
            bid_cure      = cure(bid_stores)
            excl_stores   = [s for s in stores if s not in set(bid_stores)]
            excl_cure     = cure(excl_stores)
            net           = best_bid["amount"] - bid_cure
            covered       = len(bid_stores)
        else:
            bid_cure      = 0
            excl_cure     = all_cure
            excl_stores   = stores
            net           = 0
            covered       = 0

        summary_rows.append({
            "Market":          mkt,
            "Stores (total)":  len(stores),
            "Best bid":        best_bid["buyer"][:30] if best_bid else "No bid",
            "Stores (bid)":    covered,
            "Bid amount":      fmt(best_bid["amount"]) if best_bid else "—",
            "Cure (bid stores)": fmt(bid_cure) if best_bid else "—",
            "Net to estate":   fmt(net) if best_bid else "—",
            "Excl. stores":    len(excl_stores),
            "Excl. cure cost": fmt(excl_cure) if excl_stores else "—",
            "All-in cure":     fmt(all_cure),
        })

    df_cure = pd.DataFrame(summary_rows)
    st.dataframe(df_cure, use_container_width=True, hide_index=True)

    # Portfolio totals
    tot_best = sum(b["amount"] for b in included)
    tot_cure_all = sum(CURE.values())
    st.divider()
    pc1,pc2,pc3,pc4 = st.columns(4)
    pc1.metric("Portfolio cure (all 119)", fmt(tot_cure_all))
    pc2.metric("All included bids (gross)", fmt(tot_best))
    pc3.metric("Break-even bid needed", fmt(tot_cure_all))
    pc4.metric("Portfolio cure gap", fmt(tot_best - tot_cure_all),
               delta=fmt(tot_best - tot_cure_all),
               delta_color="normal" if tot_best > tot_cure_all else "inverse")

    st.divider()
    st.markdown("#### Break-even calculator")
    st.caption("Enter any set of stores — shows minimum bid to clear cure costs")
    calc_mkts = st.multiselect("Select markets", list(MARKET_STORES.keys()),
                                key="cure_calc_mkts")
    if calc_mkts:
        calc_stores = [s for m in calc_mkts for s in MARKET_STORES[m]]
        calc_cure   = cure(calc_stores)
        cc1,cc2,cc3 = st.columns(3)
        cc1.metric("Stores selected", len(calc_stores))
        cc2.metric("Total cure", fmt(calc_cure))
        cc3.metric("Break-even bid", fmt(calc_cure))
        st.caption("Any bid below this number results in negative net proceeds to the estate for these stores.")

    st.divider()
    st.markdown("#### Store-level cure detail — all 119 stores")
    cure_store_rows = []
    for mkt, stores in MARKET_STORES.items():
        for sid in stores:
            sd = STORE_DATA.get(sid,{})
            cc = CURE.get(sid,0)
            # Find which bid covers this store
            covering = [b["buyer"] for b in included if sid in b.get("storeIds",[])]
            cure_store_rows.append({
                "Store":    sid,
                "Market":   mkt,
                "EBITDA":   fmt(sd.get("e",0)),
                "Cure":     fmt(cc),
                "Net EBITDA": fmt(sd.get("e",0) - cc),
                "Covered by": covering[0][:25] if covering else "No bid",
            })
    st.dataframe(pd.DataFrame(cure_store_rows), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# CURE COSTS TAB — live editable cure schedule with component breakdown
# ══════════════════════════════════════════════════════════════════════════════
with tab_curecosts:
    st.markdown("#### Cure Cost Schedule — editable")
    st.caption("Estimated Cure Costs = Rent Due + Property Taxes + Pre-Petition R&A + Post-Petition R&A. "
               "Edit the Total column directly for a quick override, or expand a market below to edit "
               "individual components — the total recalculates automatically. Changes apply immediately "
               "across all tabs without needing a file upload.")

    rc1, rc2, rc3 = st.columns([1.5,1.5,5])
    with rc1:
        if st.button("Reset to base schedule", use_container_width=True):
            st.session_state.cure_overrides = {}
            st.session_state.cure_component_overrides = {}
            st.rerun()
    with rc2:
        cure_export = json.dumps({str(k):v for k,v in
                                   {s: effective_cure(s) for s in ALL_STORES}.items()})
        st.download_button("Export cure schedule", data=cure_export,
                           file_name="cure_schedule.json", mime="application/json",
                           use_container_width=True)

    if "cure_component_overrides" not in st.session_state:
        st.session_state.cure_component_overrides = {}

    # ── Quick-edit: Total only, one row per store, filterable by market ──────
    mkt_filter = st.selectbox("Filter by market", ["All markets"] + list(MARKET_STORES.keys()),
                              key="cure_mkt_filter")
    filter_stores = ALL_STORES if mkt_filter == "All markets" else MARKET_STORES[mkt_filter]

    cure_rows = []
    for sid in filter_stores:
        mkt = STORE_MKT.get(sid,"")
        base_val = CURE.get(sid, 0)
        curr_val = effective_cure(sid)
        comp_ov  = st.session_state.cure_component_overrides.get(sid, {})
        cure_rows.append({
            "Store": sid,
            "Market": mkt,
            "Landlord": CURE_LANDLORD.get(sid,""),
            "Rent": comp_ov.get("rent", CURE_RENT.get(sid,0)),
            "Tax": comp_ov.get("tax", CURE_TAX.get(sid,0)),
            "R&A Pre": comp_ov.get("ra_pre", CURE_RA_PRE.get(sid,0)),
            "R&A Post": comp_ov.get("ra_post", CURE_RA_POST.get(sid,0)),
            "Total Cure ($)": curr_val,
            "Override?": curr_val != base_val,
        })

    df_cure_edit = pd.DataFrame(cure_rows)

    edited_cure = st.data_editor(
        df_cure_edit,
        use_container_width=True,
        hide_index=True,
        disabled=["Store","Market","Landlord","Rent","Tax","R&A Pre","R&A Post","Override?"],
        column_config={
            "Store":          st.column_config.NumberColumn(width="small"),
            "Market":         st.column_config.TextColumn(width="small"),
            "Landlord":       st.column_config.TextColumn(width="medium"),
            "Rent":           st.column_config.NumberColumn(format="$%d", width="small"),
            "Tax":            st.column_config.NumberColumn(format="$%d", width="small"),
            "R&A Pre":        st.column_config.NumberColumn(format="$%d", width="small"),
            "R&A Post":       st.column_config.NumberColumn(format="$%d", width="small"),
            "Total Cure ($)": st.column_config.NumberColumn(format="$%d", width="medium",
                                                             help="Edit for a quick total override"),
            "Override?":      st.column_config.CheckboxColumn(width="small"),
        },
        key=f"cure_cost_editor_{mkt_filter}",
        height=500,
    )

    # Detect total-column edits → write to cure_overrides (component breakdown unaffected)
    new_overrides = dict(st.session_state.cure_overrides)
    changed = False
    for _, row in edited_cure.iterrows():
        sid = int(row["Store"])
        new_val = row["Total Cure ($)"]
        base_val = CURE.get(sid, 0)
        comp_total = row["Rent"]+row["Tax"]+row["R&A Pre"]+row["R&A Post"]
        if new_val != comp_total:
            # User edited the total directly — store as override
            if new_val != base_val:
                if new_overrides.get(sid) != new_val:
                    new_overrides[sid] = new_val; changed = True
            elif sid in new_overrides:
                del new_overrides[sid]; changed = True

    if changed:
        st.session_state.cure_overrides = new_overrides
        st.session_state.result = None
        st.rerun()

    # ── Component drill-down editor ───────────────────────────────────────────
    st.divider()
    st.markdown("#### Component drill-down — edit Rent / Tax / R&A by store")
    sel_store = st.selectbox("Select store to edit components", filter_stores,
                              format_func=lambda s: f"{s} — {STORE_MKT.get(s,'')} — {CURE_LANDLORD.get(s,'')}",
                              key="cure_drill_store")

    comp_ov = st.session_state.cure_component_overrides.get(sel_store, {})
    cd1,cd2,cd3,cd4 = st.columns(4)
    with cd1: new_rent = st.number_input("Rent due", value=float(comp_ov.get("rent", CURE_RENT.get(sel_store,0))), step=100.0, key="cd_rent")
    with cd2: new_tax  = st.number_input("Property tax", value=float(comp_ov.get("tax", CURE_TAX.get(sel_store,0))), step=100.0, key="cd_tax")
    with cd3: new_pre  = st.number_input("Pre-petition R&A", value=float(comp_ov.get("ra_pre", CURE_RA_PRE.get(sel_store,0))), step=100.0, key="cd_rapre")
    with cd4: new_post = st.number_input("Post-petition R&A", value=float(comp_ov.get("ra_post", CURE_RA_POST.get(sel_store,0))), step=100.0, key="cd_rapost")

    new_total = new_rent + new_tax + new_pre + new_post
    st.caption(f"New total for store {sel_store}: **{fmt(new_total)}**  (was {fmt(effective_cure(sel_store))})")

    bc1, bc2 = st.columns([1,1])
    with bc1:
        if st.button("Apply component changes", type="primary", use_container_width=True):
            st.session_state.cure_component_overrides[sel_store] = {
                "rent": new_rent, "tax": new_tax, "ra_pre": new_pre, "ra_post": new_post
            }
            st.session_state.cure_overrides[sel_store] = new_total
            st.session_state.result = None
            st.rerun()
    with bc2:
        if st.button("Revert this store to base", use_container_width=True):
            st.session_state.cure_component_overrides.pop(sel_store, None)
            st.session_state.cure_overrides.pop(sel_store, None)
            st.session_state.cure_overrides.pop(str(sel_store), None)
            st.session_state.result = None
            st.rerun()

    # Summary
    st.divider()
    tot_base = sum(CURE.values())
    tot_curr = sum(effective_cure(s) for s in ALL_STORES)
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("Base portfolio cure", fmt(tot_base))
    sc2.metric("Current portfolio cure", fmt(tot_curr))
    sc3.metric("Net change", fmt(tot_curr - tot_base),
               delta=fmt(tot_curr - tot_base),
               delta_color="inverse" if tot_curr > tot_base else "normal")
    sc4.metric("Stores w/ overrides", len(st.session_state.cure_overrides))

    st.caption(f"Base component totals — Rent: {fmt(sum(CURE_RENT.values()))} · "
               f"Tax: {fmt(sum(CURE_TAX.values()))} · "
               f"R&A Pre: {fmt(sum(CURE_RA_PRE.values()))} · "
               f"R&A Post: {fmt(sum(CURE_RA_POST.values()))}")

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
