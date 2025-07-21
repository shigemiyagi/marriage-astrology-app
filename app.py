import streamlit as st
import swisseph as swe
import datetime
from datetime import timezone, timedelta
import pandas as pd
import altair as alt
from collections import defaultdict
import traceback

# --- 初期設定 ---
APP_VERSION = "10.1 (占術ロジック最終版)"
swe.set_ephe_path('ephe')

# --- 定数定義 ---
PLANET_IDS = {
    "太陽": swe.SUN, "月": swe.MOON, "水星": swe.MERCURY, "金星": swe.VENUS, "火星": swe.MARS,
    "木星": swe.JUPITER, "土星": swe.SATURN, "天王星": swe.URANUS, "海王星": swe.NEPTUNE, "冥王星": swe.PLUTO,
}
MAJOR_ASPECTS = { 0: '合', 60: 'セクスタイル', 90: 'スクエア', 120: 'トライン', 180: 'オポジション' }
GOOD_ASPECTS = { 0: '合', 60: 'セクスタイル', 120: 'トライン' }
ORB = 1.2
ZODIAC_SIGNS = ["牡羊座", "牡牛座", "双子座", "蟹座", "獅子座", "乙女座", "天秤座", "蠍座", "射手座", "山羊座", "水瓶座", "魚座"]
RULER_OF_SIGN = {
    "牡羊座": "火星", "牡牛座": "金星", "双子座": "水星", "蟹座": "月", "獅子座": "太陽", "乙女座": "水星",
    "天秤座": "金星", "蠍座": "火星", "射手座": "木星", "山羊座": "土星", "水瓶座": "土星", "魚座": "木星"
}
EVENT_DEFINITIONS = {
    # --- スコア 90以上 (最重要イベント) ---
    "SA_7Ruler_CONJ_ASC_DSC": {"score": 95, "title": "SA 7H支配星がN ASC/DSCに合", "desc": "結婚の運命を司る星が「自分」か「パートナー」の感受点に重なる、極めて重要な時期。"},
    "SA_SUN_VENUS_CONJ": {"score": 92, "title": "SA 太陽/金星が合", "desc": "人生の目的（太陽）と愛と喜び（金星）が重なる、恋愛や結婚において最も幸福な時期の一つです。運命的な出会いやプロポーズの可能性。"},
    "P_NEW_MOON": {"score": 90, "title": "プログレス新月", "desc": "P太陽とP月が重なる、約30年に一度の人生の新しいサイクルの始まり。結婚、出産、転職など、人生の大きな節目となる重要な時期です。"},
    "P_MOON_CONJ_SMMidpoint": {"score": 90, "title": "P月がN太陽/月ミッドポイントに合", "desc": "感情（P月）が、公私の統合を象徴する感受点に到達。結婚など、人生の重要なパートナーシップが具体化する時です。"},
    "T_JUP_7H_INGRESS": {"score": 90, "title": "T木星が第7ハウス入り", "desc": "約12年に一度の結婚幸運期。出会いのチャンスが拡大し、関係がスムーズに進展しやすい1年間。"},
    "T_SAT_7H_INGRESS": {"score": 90, "title": "T土星が第7ハウス入り", "desc": "パートナーシップに対する責任感が生まれ、関係を真剣に考える時期。結婚を固めるタイミング。"},
    "T_JUP_CONJ_DSC": {"score": 90, "title": "T木星とNディセンダントが合", "desc": "素晴らしいパートナーとの出会いや、現在の関係が結婚へと発展する絶好のチャンス。"},
    
    # --- スコア 80台 (重要イベント) ---
    "P_VENUS_CONJ_DSC": {"score": 88, "title": "P金星がNディセンダントに合", "desc": "あなたの愛と喜び（P金星）がパートナーシップの扉（DSC）を開く時。恋愛の成就や結婚の絶好の機会です。"},
    "SA_VENUS_CONJ_ASC": {"score": 88, "title": "SA金星がN ASCに合", "desc": "愛される喜びを実感する時。人生の新しい扉が開き、パートナーシップが始まる。"},
    "SA_ASC_CONJ_VENUS": {"score": 88, "title": "SA ASCがN金星に合", "desc": "自分自身が愛のエネルギーに満ち、魅力が高まる時期。恋愛や結婚の大きなチャンス。"},
    "T_SAT_CONJ_DSC": {"score": 85, "title": "T土星とNディセンダントが合", "desc": "運命的な相手との関係が始まり、長期的な契約を結ぶ時。結婚への決意が固まる。"},
    "SA_MC_CONJ_VENUS": {"score": 85, "title": "SA MCがN金星に合", "desc": "恋愛や結婚が社会的なステータスアップに繋がる可能性。公に認められる喜び。"},
    "SA_JUP_CONJ_ASC": {"score": 85, "title": "SA木星がN ASCに合", "desc": "人生における大きな幸運期。拡大と発展のエネルギーが自分に降り注ぐ。"},
    "SA_MC_CONJ_SUN": {"score": 85, "title": "SA MCがN太陽に合", "desc": "社会的頂点（MC）と人生の目的（太陽）が重なります。結婚が社会的なステータスを向上させるなど、人生の大きな節目となる時期。"},
    "SA_VENUS_CONJ_MOON": {"score": 85, "title": "SA金星がN月に合", "desc": "愛情（金星）と感情（月）が結びつく、結婚に非常に繋がりやすい時期。プライベートな幸福感が高まります。"},
    "T_JUP_ASPECT_VENUS": {"score": 80, "title": "T木星がN金星に吉角", "desc": "恋愛運が最高潮に。人生を楽しむ喜びにあふれ、幸せな恋愛・結婚に繋がりやすい。"},
    "P_VENUS_ASPECT_MARS": {"score": 80, "title": "P金星がN火星にアスペクト", "desc": "愛情と情熱が結びつき、ロマンスが燃え上がる強力な配置。関係が急速に進展しやすい。"},
    "P_MOON_7H_INGRESS": {"score": 80, "title": "P月が第7ハウス入り", "desc": "約2.5年間、結婚やパートナーへの意識が自然と高まる。心がパートナーを求める時期。"},
    "T_JUP_CONJ_SMMidpoint": {"score": 80, "title": "T木星がN太陽/月ミッドポイントに合", "desc": "幸運の星・木星が、あなたにとって最も重要な感受点を祝福。素晴らしい出会いや関係の発展が期待できる幸運期。"},
    "P_MOON_CONJ_DSC": {"score": 80, "title": "P月がNディセンダントに合", "desc": "あなたの感情（月）がパートナーシップの扉（DSC）を通過する約1ヶ月間。結婚や同棲を具体的に意識し、行動に移しやすい時期です。"},

    # --- スコア 70台 (補助的なイベント) ---
    "T_JUP_ASPECT_SUN": {"score": 75, "title": "T木星がN太陽に吉角", "desc": "人生の発展期。自己肯定感が高まり、良きパートナーを引き寄せ、人生のステージが上がる。"},
    "T_URA_ASPECT_VENUS": {"score": 75, "title": "T天王星がN金星にアスペクト", "desc": "突然の出会いや電撃的な恋愛、または現在の関係に大きな変化が訪れる時期。関係が良くも悪くも大きく動く可能性があり、別離を経て新しい出会いに向かう場合も。"},
    "P_MOON_CONJ_VENUS": {"score": 75, "title": "P月がN金星に合", "desc": "恋愛気分が盛り上がり、ときめきを感じやすい。デートや出会いに最適なタイミング。"},
    "T_SAT_ASPECT_VENUS": {"score": 70, "title": "T土星がN金星にアスペクト", "desc": "恋愛関係に試練や責任が伴うが、それを乗り越えることで関係が安定し、真剣なものへと進む。結婚への覚悟を固める時期。"},
    "P_MOON_CONJ_JUP": {"score": 70, "title": "P月がN木星に合", "desc": "精神的に満たされ、幸福感が高まる。楽観的な気持ちが良縁を引き寄せる。"},
}
PREFECTURES = {
    "北海道": (141.35, 43.06), "青森県": (140.74, 40.82), "岩手県": (141.15, 39.70), "宮城県": (140.87, 38.27),
    "秋田県": (140.10, 39.72), "山形県": (140.36, 38.24), "福島県": (140.47, 37.75), "茨城県": (140.45, 36.34),
    "栃木県": (139.88, 36.57), "群馬県": (139.06, 36.39), "埼玉県": (139.65, 35.86), "千葉県": (140.12, 35.60),
    "東京都": (139.69, 35.69), "神奈川県": (139.64, 35.45), "新潟県": (139.02, 37.90), "富山県": (137.21, 36.70),
    "石川県": (136.63, 36.59), "福井県": (136.07, 36.07), "山梨県": (138.57, 35.66), "長野県": (138.18, 36.65),
    "岐阜県": (136.72, 35.39), "静岡県": (138.38, 34.98), "愛知県": (136.91, 35.18), "三重県": (136.51, 34.73),
    "滋賀県": (135.87, 35.00), "京都府": (135.76, 35.02), "大阪府": (135.52, 34.69), "兵庫県": (135.18, 34.69),
    "奈良県": (135.83, 34.69), "和歌山県": (135.17, 34.23), "鳥取県": (134.24, 35.50), "島根県": (133.05, 35.47),
    "岡山県": (133.93, 34.66), "広島県": (132.46, 34.40), "山口県": (131.47, 34.19), "徳島県": (134.55, 34.07),
    "香川県": (134.04, 34.34), "愛媛県": (132.77, 33.84), "高知県": (133.53, 33.56), "福岡県": (130.42, 33.61),
    "佐賀県": (130.30, 33.26), "長崎県": (129.88, 32.75), "熊本県": (130.74, 32.79), "大分県": (131.61, 33.24),
    "宮崎県": (131.42, 31.91), "鹿児島県": (130.56, 31.56), "沖縄県": (127.68, 26.21)
}

# --- 計算ロジック関数 ---

def calculate_midpoint(p1, p2):
    diff = (p2 - p1 + 360) % 360
    return (p1 + diff / 2) % 360 if diff <= 180 else (p2 + (360 - diff) / 2) % 360

@st.cache_data
def get_natal_chart(birth_dt_jst, lon, lat):
    dt_utc = birth_dt_jst.astimezone(timezone.utc)
    year, month, day, hour, minute, second = dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour, dt_utc.minute, float(dt_utc.second)
    jday = swe.utc_to_jd(year, month, day, hour, minute, second, 1)[1]
    chart_data = {"jday": jday, "lon": lon, "lat": lat}
    try:
        cusps, ascmc = swe.houses(jday, lat, lon, b'P')
    except Exception: return None
    chart_data["ASC_pos"], chart_data["MC_pos"] = float(ascmc[0]), float(ascmc[1])
    temp_planet_ids = PLANET_IDS.copy()
    for name, pid in temp_planet_ids.items():
        chart_data[name] = float(swe.calc_ut(jday, pid)[0][0])
    chart_data["SunMoonMidpoint"] = calculate_midpoint(chart_data["太陽"], chart_data["月"])
    chart_data["DSC_pos"] = (chart_data["ASC_pos"] + 180) % 360
    chart_data["IC_pos"] = (chart_data["MC_pos"] + 180) % 360
    chart_data["cusps"] = cusps
    dsc_sign_index = int(chart_data["DSC_pos"] / 30)
    ruler_name = RULER_OF_SIGN[ZODIAC_SIGNS[dsc_sign_index]]
    chart_data["7H_RulerName"], chart_data["7H_Ruler_pos"] = ruler_name, chart_data.get(ruler_name)
    return chart_data

@st.cache_data
def create_composite_chart(chart_a, chart_b):
    composite_chart = {"lon": chart_a["lon"], "lat": chart_a["lat"]}
    for name in PLANET_IDS.keys():
        composite_chart[name] = calculate_midpoint(chart_a[name], chart_b[name])
    composite_chart["ASC_pos"] = calculate_midpoint(chart_a["ASC_pos"], chart_b["ASC_pos"])
    composite_chart["MC_pos"] = calculate_midpoint(chart_a["MC_pos"], chart_b["MC_pos"])
    composite_chart["cusps"] = tuple([(composite_chart["ASC_pos"] + 30 * i) % 360 for i in range(12)])
    composite_chart["DSC_pos"] = (composite_chart["ASC_pos"] + 180) % 360
    composite_chart["jday"], composite_chart["太陽"] = chart_a["jday"], composite_chart.get("太陽")
    composite_chart["7H_RulerName"], composite_chart["7H_Ruler_pos"] = None, None
    composite_chart["SunMoonMidpoint"] = calculate_midpoint(composite_chart["太陽"], composite_chart["月"])
    return composite_chart

@st.cache_data
def find_events(_natal_chart, birth_dt, years=80, is_composite=False):
    events_by_date = {}
    t_planets = ["木星", "土星", "天王星"]
    p_planets = ["太陽", "月", "金星"]
    sa_points = ["太陽", "金星", "ASC_pos", "MC_pos", "木星"] if is_composite else ["太陽", "金星", "ASC_pos", "MC_pos", "木星", "7H_Ruler_pos"]
    base_jday, natal_sun_pos, prev_positions = _natal_chart["jday"], _natal_chart["太陽"], {}
    for day_offset in range(1, int(365.25 * years)):
        current_date = birth_dt + timedelta(days=day_offset)
        current_jday, p_jday = base_jday + day_offset, base_jday + day_offset / 365.25
        t_pos = {p: float(swe.calc_ut(current_jday, PLANET_IDS[p])[0][0]) for p in t_planets}
        p_pos = {p: float(swe.calc_ut(p_jday, PLANET_IDS[p])[0][0]) for p in p_planets}
        sa_arc = p_pos["太陽"] - natal_sun_pos
        sa_pos = {p: (_natal_chart.get(p, 0) + sa_arc) % 360 for p in sa_points if _natal_chart.get(p) is not None}
        if not prev_positions:
            prev_positions = {'t': t_pos, 'p': p_pos, 'sa': sa_pos}; continue
        def check_crossing(curr, prev, target, orb):
            dist_c = (curr - target + 180) % 360 - 180; dist_p = (prev - target + 180) % 360 - 180
            return (abs(dist_c) <= orb and abs(dist_p) > orb) or (dist_p * dist_c < 0)
        def check_ingress(curr, prev, cusp):
            return ((curr - cusp + 360) % 360 < 10) and ((prev - cusp + 360) % 360 > 350)
        
        # --- トランジット ---
        if check_ingress(t_pos["木星"], prev_positions['t']["木星"], _natal_chart["cusps"][6]): events_by_date.setdefault(current_date.date(), []).append("T_JUP_7H_INGRESS")
        if check_ingress(t_pos["土星"], prev_positions['t']["土星"], _natal_chart["cusps"][6]): events_by_date.setdefault(current_date.date(), []).append("T_SAT_7H_INGRESS")
        if check_crossing(t_pos["木星"], prev_positions['t']["木星"], _natal_chart["DSC_pos"], ORB): events_by_date.setdefault(current_date.date(), []).append("T_JUP_CONJ_DSC")
        if check_crossing(t_pos["土星"], prev_positions['t']["土星"], _natal_chart["DSC_pos"], ORB): events_by_date.setdefault(current_date.date(), []).append("T_SAT_CONJ_DSC")
        if "SunMoonMidpoint" in _natal_chart and check_crossing(t_pos["木星"], prev_positions['t']["木星"], _natal_chart["SunMoonMidpoint"], ORB): events_by_date.setdefault(current_date.date(), []).append("T_JUP_CONJ_SMMidpoint")
        for aspect in GOOD_ASPECTS:
            if check_crossing(t_pos["木星"], prev_positions['t']["木星"], (_natal_chart["金星"] + aspect) % 360, ORB): events_by_date.setdefault(current_date.date(), []).append("T_JUP_ASPECT_VENUS")
            if check_crossing(t_pos["木星"], prev_positions['t']["木星"], (_natal_chart["太陽"] + aspect) % 360, ORB): events_by_date.setdefault(current_date.date(), []).append("T_JUP_ASPECT_SUN")
        for aspect in MAJOR_ASPECTS:
            if check_crossing(t_pos["土星"], prev_positions['t']["土星"], (_natal_chart["金星"] + aspect) % 360, ORB): events_by_date.setdefault(current_date.date(), []).append("T_SAT_ASPECT_VENUS")
            if check_crossing(t_pos["天王星"], prev_positions['t']["天王星"], (_natal_chart["金星"] + aspect) % 360, ORB): events_by_date.setdefault(current_date.date(), []).append("T_URA_ASPECT_VENUS")
        
        # --- ソーラーアーク ---
        if "ASC_pos" in sa_pos and check_crossing(sa_pos["ASC_pos"], prev_positions['sa']["ASC_pos"], _natal_chart["金星"], ORB): events_by_date.setdefault(current_date.date(), []).append("SA_ASC_CONJ_VENUS")
        if "MC_pos" in sa_pos and check_crossing(sa_pos["MC_pos"], prev_positions['sa']["MC_pos"], _natal_chart["金星"], ORB): events_by_date.setdefault(current_date.date(), []).append("SA_MC_CONJ_VENUS")
        if "金星" in sa_pos and check_crossing(sa_pos["金星"], prev_positions['sa']["金星"], _natal_chart["ASC_pos"], ORB): events_by_date.setdefault(current_date.date(), []).append("SA_VENUS_CONJ_ASC")
        if "木星" in sa_pos and "ASC_pos" in _natal_chart and check_crossing(sa_pos["木星"], prev_positions['sa']["木星"], _natal_chart["ASC_pos"], ORB): events_by_date.setdefault(current_date.date(), []).append("SA_JUP_CONJ_ASC")
        if "太陽" in sa_pos and "金星" in _natal_chart and check_crossing(sa_pos["太陽"], prev_positions['sa']["太陽"], _natal_chart["金星"], ORB): events_by_date.setdefault(current_date.date(), []).append("SA_SUN_VENUS_CONJ")
        if "金星" in sa_pos and "太陽" in _natal_chart and check_crossing(sa_pos["金星"], prev_positions['sa']["金星"], _natal_chart["太陽"], ORB): events_by_date.setdefault(current_date.date(), []).append("SA_SUN_VENUS_CONJ")
        if "金星" in sa_pos and "月" in _natal_chart and check_crossing(sa_pos["金星"], prev_positions['sa']["金星"], _natal_chart["月"], ORB): events_by_date.setdefault(current_date.date(), []).append("SA_VENUS_CONJ_MOON")
        if "MC_pos" in sa_pos and "太陽" in _natal_chart and check_crossing(sa_pos["MC_pos"], prev_positions['sa']["MC_pos"], _natal_chart["太陽"], ORB): events_by_date.setdefault(current_date.date(), []).append("SA_MC_CONJ_SUN")
        if not is_composite and "7H_Ruler_pos" in sa_pos:
            if check_crossing(sa_pos["7H_Ruler_pos"], prev_positions['sa'].get("7H_Ruler_pos",0), _natal_chart["ASC_pos"], ORB): events_by_date.setdefault(current_date.date(),[]).append("SA_7Ruler_CONJ_ASC_DSC")
            if check_crossing(sa_pos["7H_Ruler_pos"], prev_positions['sa'].get("7H_Ruler_pos",0), _natal_chart["DSC_pos"], ORB): events_by_date.setdefault(current_date.date(),[]).append("SA_7Ruler_CONJ_ASC_DSC")
        
        # --- プログレス ---
        if check_ingress(p_pos["月"], prev_positions['p']["月"], _natal_chart["cusps"][6]): events_by_date.setdefault(current_date.date(), []).append("P_MOON_7H_INGRESS")
        if "木星" in _natal_chart and check_crossing(p_pos["月"], prev_positions['p']["月"], _natal_chart["木星"], ORB): events_by_date.setdefault(current_date.date(), []).append("P_MOON_CONJ_JUP")
        if "金星" in _natal_chart and check_crossing(p_pos["月"], prev_positions['p']["月"], _natal_chart["金星"], ORB): events_by_date.setdefault(current_date.date(), []).append("P_MOON_CONJ_VENUS")
        if "SunMoonMidpoint" in _natal_chart and check_crossing(p_pos["月"], prev_positions['p']["月"], _natal_chart["SunMoonMidpoint"], ORB): events_by_date.setdefault(current_date.date(), []).append("P_MOON_CONJ_SMMidpoint")
        if "金星" in p_pos and "DSC_pos" in _natal_chart and check_crossing(p_pos["金星"], prev_positions['p']["金星"], _natal_chart["DSC_pos"], ORB): events_by_date.setdefault(current_date.date(), []).append("P_VENUS_CONJ_DSC")
        if "DSC_pos" in _natal_chart and check_crossing(p_pos["月"], prev_positions['p']["月"], _natal_chart["DSC_pos"], ORB): events_by_date.setdefault(current_date.date(), []).append("P_MOON_CONJ_DSC") #【修正箇所】
        if "太陽" in p_pos and "月" in p_pos and check_crossing(p_pos["月"], prev_positions['p']["月"], p_pos["太陽"], ORB): events_by_date.setdefault(current_date.date(), []).append("P_NEW_MOON")
        if "火星" in _natal_chart and "金星" in p_pos:
            for aspect in MAJOR_ASPECTS:
                if check_crossing(p_pos["金星"], prev_positions['p']["金星"], (_natal_chart["火星"] + aspect) % 360, ORB): events_by_date.setdefault(current_date.date(), []).append("P_VENUS_ASPECT_MARS")
        
        prev_positions = {'t': t_pos, 'p': p_pos, 'sa': sa_pos}
        
    scored_events = []
    for date, event_keys in events_by_date.items():
        unique_keys = list(set(event_keys))
        total_score = sum(EVENT_DEFINITIONS[key]["score"] for key in unique_keys if key in EVENT_DEFINITIONS)
        scored_events.append({"date": date, "score": total_score, "keys": unique_keys})
    if not scored_events: return []
    max_score = max(event["score"] for event in scored_events) if scored_events else 1
    for event in scored_events:
        event["normalized_score"] = (event["score"] / max_score) * 100 if max_score > 0 else 0
    return sorted(scored_events, key=lambda x: x["score"], reverse=True)

@st.cache_data
def synthesize_couple_events(events_a, events_b, events_comp):
    monthly_scores = defaultdict(lambda: {'score': 0, 'events': defaultdict(list)})
    all_event_lists = {'Aさん': events_a, 'Bさん': events_b, 'お二人の関係性': events_comp}
    for person, event_list in all_event_lists.items():
        for event in event_list:
            month_key = event['date'].strftime('%Y-%m')
            monthly_scores[month_key]['score'] += event.get('normalized_score', 0)
            monthly_scores[month_key]['events'][person].extend(event['keys'])
    if not monthly_scores: return []
    max_combined_score = max(data['score'] for data in monthly_scores.values()) if monthly_scores else 1
    final_events = []
    for month_str, data in monthly_scores.items():
        if data['score'] > 0:
            final_events.append({
                "month": month_str, "score": data['score'],
                "normalized_score": (data['score'] / max_combined_score) * 100 if max_combined_score > 0 else 0,
                "events_detail": data['events']
            })
    return sorted(final_events, key=lambda x: x['score'], reverse=True)

# --- Streamlit UI ---
st.set_page_config(page_title="結婚タイミング占い【PRO】", page_icon="💖")
st.title("💖 結婚タイミング占い【PRO版】")
st.info(f"アプリバージョン: {APP_VERSION}")

st.sidebar.title("モード選択")
mode = st.sidebar.radio("鑑定する人数を選んでください", ("1人用", "2人用"))

if mode == "1人用":
    st.header("1人用鑑定")
    st.write("あなたの結婚運がピークに達する時期をスコア化して予測します。")
    with st.expander("使い方と注意点"):
        st.markdown("""
        1.  **生年月日、出生時刻、出生地**を入力してください。
        2.  **鑑定したい年齢の範囲**を選択してください。
        3.  **※ ASC/MCやハウスが関わる占術は、正確な出生時刻が非常に重要です。** 不明な場合は「12:00」で計算しますが、結果の信頼度が低下する可能性があります。
        4.  「鑑定開始」ボタンを押すと計算が始まります。
        """)
    col1, col2 = st.columns(2)
    with col1:
        birth_date = st.date_input("① 生年月日", value=datetime.date(1982, 10, 6))
    with col2:
        pref = st.selectbox("③ 出生地", options=list(PREFECTURES.keys()), index=12)
    custom_time_str = st.text_input("② 詳細な時刻を入力 (例: 16:27)", "02:30")
    try: hour, minute = map(int, custom_time_str.split(':'))
    except ValueError:
        st.warning("時刻は「時:分」の形式で入力してください。例: 16:27"); hour, minute = 2, 30
    st.markdown("---"); st.markdown("#### ④ 鑑定範囲（年齢）")
    age_col1, age_col2 = st.columns(2)
    with age_col1:
        age_options = list(range(18, 81)); start_age = st.selectbox("開始年齢", options=age_options, index=2)
    with age_col2:
        end_age_options = list(range(start_age, 81)); end_age = st.selectbox("終了年齢", options=end_age_options, index=20)
    if st.button("鑑定開始", type="primary"):
        jst_tz = timezone(timedelta(hours=9))
        birth_dt_jst = datetime.datetime(birth_date.year, birth_date.month, birth_date.day, hour, minute, tzinfo=jst_tz)
        lon, lat = PREFECTURES[pref]
        with st.spinner("運勢を計算中..."):
            natal_chart = get_natal_chart(birth_dt_jst, lon, lat)
            if natal_chart:
                all_events = find_events(natal_chart, birth_dt_jst)
                filtered_events = []
                for event in all_events:
                    age = event["date"].year - birth_date.year - ((event["date"].month, event["date"].day) < (birth_date.month, birth_date.day))
                    if start_age <= age <= end_age:
                        event['age'] = age
                        filtered_events.append(event)
                st.success("計算が完了しました！")
                if filtered_events:
                    st.header(f"📊 結婚運勢グラフ（{start_age}歳～{end_age}歳）", divider="rainbow")
                    df_chart = pd.DataFrame(filtered_events).groupby('age')['normalized_score'].max().reset_index()
                    chart = alt.Chart(df_chart).mark_line(point=alt.OverlayMarkDef(color="#F63366", size=40)).encode(
                        x=alt.X('age:Q', title='年齢', scale=alt.Scale(zero=False, domain=[start_age, end_age])),
                        y=alt.Y('normalized_score:Q', title='重要度 (%)', scale=alt.Scale(domain=[0, 105])),
                        tooltip=[alt.Tooltip('age', title='年齢'), alt.Tooltip('normalized_score', title='重要度 (%)', format='.1f')]
                    ).properties(title=alt.TitleParams(text='年齢別・結婚運のピーク', anchor='middle')).interactive()
                    st.altair_chart(chart, use_container_width=True)
                st.header(f"🌟 あなたの結婚運のピーク TOP15（{start_age}歳～{end_age}歳）", divider="rainbow")
                if not filtered_events:
                    st.warning(f"選択された年齢範囲（{start_age}歳～{end_age}歳）に、指定された重要な天体の配置は見つかりませんでした。")
                else:
                    for event in sorted(filtered_events, key=lambda x: x['normalized_score'], reverse=True)[:15]:
                        st.subheader(f"{event['date'].strftime('%Y年%m月%d日')}頃 ({event['age']}歳)")
                        st.markdown(f"**重要度: {event['normalized_score']:.0f}%**"); st.progress(int(event['normalized_score']))
                        with st.expander("この時期に何が起こる？ 詳細を見る"):
                            for key in event["keys"]:
                                if info := EVENT_DEFINITIONS.get(key):
                                    st.markdown(f"**▶ {info['title']}**: {info['desc']}")
                        st.write("---")
            else: st.error("チャートの作成に失敗しました。入力情報を確認してください。")

elif mode == "2人用":
    st.header("2人用鑑定 💖")
    st.write("お二人の個人の運勢と、関係性自体の運勢を統合し、結婚に最適な時期を予測します。")
    with st.expander("使い方と注意点（2人用）", expanded=True):
        st.markdown("""
        1.  **お二人それぞれ**の生年月日、出生時刻、出生地を入力してください。
        2.  **鑑定したい期間**を選択してください。
        3.  **※ ASC/MCやハウスが関わる占術は、正確な出生時刻が非常に重要です。** 不明な場合は「12:00」で計算しますが、結果の信頼度が低下する可能性があります。
        4.  計算には複数のチャートを分析するため、**1分〜2分ほど時間がかかります。**
        """)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Aさんの情報")
        a_birth_date = st.date_input("① 生年月日", value=datetime.date(1982, 10, 6), key="a_date")
        a_custom_time_str = st.text_input("② 出生時刻 (例: 16:27)", "02:30", key="a_time")
        a_pref = st.selectbox("③ 出生地", options=list(PREFECTURES.keys()), index=12, key="a_pref")
    with col2:
        st.subheader("Bさんの情報")
        b_birth_date = st.date_input("① 生年月日", value=datetime.date(1976, 12, 25), key="b_date")
        b_custom_time_str = st.text_input("② 出生時刻 (例: 16:27)", "16:25", key="b_time")
        b_pref = st.selectbox("③ 出生地", options=list(PREFECTURES.keys()), index=46, key="b_pref")
    st.markdown("---"); st.markdown("#### ④ 鑑定期間（年）")
    year_col1, year_col2 = st.columns(2)
    with year_col1:
        year_options = list(range(1900, datetime.date.today().year + 51))
        start_year = st.selectbox("開始年", options=year_options, index=year_options.index(2010), key="start_year_2p")
    with year_col2:
        end_year_options = list(range(start_year, datetime.date.today().year + 51))
        end_year = st.selectbox("終了年", options=end_year_options, index=end_year_options.index(2020), key="end_year_2p")
    if st.button("お二人の結婚タイミングを鑑定する", type="primary"):
        try:
            a_hour, a_minute = map(int, a_custom_time_str.split(':'))
            b_hour, b_minute = map(int, b_custom_time_str.split(':'))
            jst_tz = timezone(timedelta(hours=9))
            a_birth_dt_jst = datetime.datetime(a_birth_date.year, a_birth_date.month, a_birth_date.day, a_hour, a_minute, tzinfo=jst_tz)
            a_lon, a_lat = PREFECTURES[a_pref]
            b_birth_dt_jst = datetime.datetime(b_birth_date.year, b_birth_date.month, b_birth_date.day, b_hour, b_minute, tzinfo=jst_tz)
            b_lon, b_lat = PREFECTURES[b_pref]
            with st.spinner("お二人の膨大な運勢データを解析中... (最大2分ほどかかります)"):
                chart_a, chart_b = get_natal_chart(a_birth_dt_jst, a_lon, a_lat), get_natal_chart(b_birth_dt_jst, b_lon, b_lat)
                if not (chart_a and chart_b):
                    st.error("チャートの作成に失敗しました。入力情報を確認してください。")
                else:
                    composite_chart = create_composite_chart(chart_a, chart_b)
                    events_a, events_b, events_comp = find_events(chart_a, a_birth_dt_jst), find_events(chart_b, b_birth_dt_jst), find_events(composite_chart, a_birth_dt_jst, is_composite=True)
                    couple_events = synthesize_couple_events(events_a, events_b, events_comp)
                    st.success("解析が完了しました！")
                    filtered_couple_events = [e for e in couple_events if start_year <= int(e['month'][:4]) <= end_year]
                    if filtered_couple_events:
                        st.header(f"📊 お二人の結婚運勢グラフ（{start_year}年～{end_year}年）", divider="rainbow")
                        df_chart = pd.DataFrame(filtered_couple_events)
                        df_chart['year'] = pd.to_datetime(df_chart['month']).dt.year
                        chart_data = df_chart.groupby('year')['normalized_score'].max().reset_index()
                        chart = alt.Chart(chart_data).mark_line(point=alt.OverlayMarkDef(color="#F63366", size=40)).encode(
                            x=alt.X('year:O', title='年', axis=alt.Axis(labelAngle=0)),
                            y=alt.Y('normalized_score:Q', title='総合重要度 (%)', scale=alt.Scale(domain=[0, 105])),
                            tooltip=[alt.Tooltip('year', title='年'), alt.Tooltip('normalized_score', title='総合重要度 (%)', format='.1f')]
                        ).properties(title=alt.TitleParams(text='年別・お二人の結婚運のピーク', anchor='middle')).interactive()
                        st.altair_chart(chart, use_container_width=True)
                    st.header(f"🌟 お二人の結婚運が最高潮に達する時期 TOP15（{start_year}年～{end_year}年）", divider="rainbow")
                    if not filtered_couple_events:
                        st.warning(f"選択された期間（{start_year}年～{end_year}年）に、お二人にとって重要な星の配置は見つかりませんでした。")
                    else:
                        for event in sorted(filtered_couple_events, key=lambda x: x['normalized_score'], reverse=True)[:15]:
                            month_dt = datetime.datetime.strptime(event["month"], "%Y-%m")
                            age_a = month_dt.year - a_birth_date.year - ((month_dt.month, 1) < (a_birth_date.month, a_birth_date.day))
                            age_b = month_dt.year - b_birth_date.year - ((month_dt.month, 1) < (b_birth_date.month, b_birth_date.day))
                            st.subheader(f"{month_dt.strftime('%Y年%m月')}頃 (Aさん: {age_a}歳 / Bさん: {age_b}歳)")
                            st.markdown(f"**総合重要度: {event['normalized_score']:.0f}%**"); st.progress(int(event['normalized_score']))
                            with st.expander("この時期の運勢の内訳を見る"):
                                for person, event_keys in event['events_detail'].items():
                                    st.markdown(f"**--- {person}の運勢 ---**")
                                    if not (unique_keys := list(set(event_keys))):
                                        st.write("特に大きな動きはありませんでした。")
                                    else:
                                        for key in unique_keys:
                                            if info := EVENT_DEFINITIONS.get(key):
                                                st.markdown(f"**▶ {info['title']}**: {info['desc']}")
                            st.write("---")
        except ValueError:
            st.error("時刻の入力形式が正しくありません。お二人の時刻を「時:分」（例: 16:27）の形式で入力してください。")
        except Exception as e:
            st.error(f"予期せぬエラーが発生しました: {e}")
            traceback.print_exc()
