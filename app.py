import streamlit as st
import swisseph as swe
import datetime
from datetime import timezone, timedelta
import math

# --- 初期設定 ---

# 1. 天文暦ファイルのパス
swe.set_ephe_path('ephe')

# 2. 定数定義
PLANET_IDS = {
    "太陽": swe.SUN, "月": swe.MOON, "水星": swe.MERCURY, "金星": swe.VENUS, "火星": swe.MARS,
    "木星": swe.JUPITER, "土星": swe.SATURN, "天王星": swe.URANUS, "海王星": swe.NEPTUNE, "冥王星": swe.PLUTO,
    "ASC": swe.ASC, "MC": swe.MC,
    "ジュノー": swe.AST_OFFSET + 3 # 小惑星番号3番がジュノー
}
PLANET_NAMES = {v: k for k, v in PLANET_IDS.items()}

ASPECTS = { 0: '合', 60: 'セクスタイル', 90: 'スクエア', 120: 'トライン', 180: 'オポジション' }
ORB = 1.2

ZODIAC_SIGNS = [
    "牡羊座", "牡牛座", "双子座", "蟹座", "獅子座", "乙女座",
    "天秤座", "蠍座", "射手座", "山羊座", "水瓶座", "魚座"
]

RULER_OF_SIGN = {
    "牡羊座": "火星", "牡牛座": "金星", "双子座": "水星", "蟹座": "月", "獅子座": "太陽",
    "乙女座": "水星", "天秤座": "金星", "蠍座": "火星", "射手座": "木星", "山羊座": "土星",
    "水瓶座": "土星", "魚座": "木星"
}
RULER_IDS = { "太陽": swe.SUN, "月": swe.MOON, "水星": swe.MERCURY, "金星": swe.VENUS, "火星": swe.MARS, "木星": swe.JUPITER, "土星": swe.SATURN }


# --- イベントのスコアと解説 ---
EVENT_DEFINITIONS = {
    # トランジット (T)
    "T_JUP_7H_INGRESS": {"score": 95, "title": "T木星が第7ハウス入り", "desc": "約12年に一度の最大の結婚幸運期。出会いのチャンスが拡大し、関係がスムーズに進展しやすい1年間。"},
    "T_SAT_7H_INGRESS": {"score": 90, "title": "T土星が第7ハウス入り", "desc": "パートナーシップに対する責任感が生まれ、関係を真剣に考える時期。結婚を固めるタイミング。"},
    "T_JUP_CONJ_DSC": {"score": 90, "title": "T木星とNディセンダントが合", "desc": "素晴らしいパートナーとの出会いや、現在の関係が結婚へと発展する絶好のチャンス。"},
    "T_JUP_ASPECT_VENUS": {"score": 80, "title": "T木星がN金星に吉角", "desc": "恋愛運が最高潮に。人生を楽しむ喜びにあふれ、幸せな恋愛・結婚に繋がりやすい。"},
    "T_JUP_ASPECT_SUN": {"score": 75, "title": "T木星がN太陽に吉角", "desc": "人生の発展期。自己肯定感が高まり、良きパートナーを引き寄せ、人生のステージが上がる。"},
    "T_SAT_CONJ_DSC": {"score": 85, "title": "T土星とNディセンダントが合", "desc": "運命的な相手との関係が始まり、長期的な契約を結ぶ時。結婚への決意が固まる。"},
    "T_SAT_ASPECT_VENUS": {"score": 70, "title": "T土星がN金星に吉角", "desc": "恋愛関係が安定し、誠実なパートナーシップを築く。関係が真剣なものへと進む。"},
    "T_URA_ASPECT_VENUS": {"score": 75, "title": "T天王星がN金星に吉角", "desc": "突然の出会いや電撃的な恋愛の始まり。今までにないタイプの人に強く惹かれるかも。"},
    # ソーラーアーク (SA)
    "SA_ASC_CONJ_VENUS": {"score": 90, "title": "SA ASCがN金星に合", "desc": "自分自身が愛のエネルギーに満ち、魅力が高まる時期。恋愛や結婚の大きなチャンス。"},
    "SA_MC_CONJ_VENUS": {"score": 85, "title": "SA MCがN金星に合", "desc": "恋愛や結婚が社会的なステータスアップに繋がる可能性。公に認められる喜び。"},
    "SA_VENUS_CONJ_ASC": {"score": 88, "title": "SA金星がN ASCに合", "desc": "愛される喜びを実感する時。人生の新しい扉が開き、パートナーシップが始まる。"},
    "SA_JUP_CONJ_ASC": {"score": 85, "title": "SA木星がN ASCに合", "desc": "人生における大きな幸運期。拡大と発展のエネルギーが自分に降り注ぐ。"},
    "SA_7Ruler_CONJ_ASC_DSC": {"score": 95, "title": "SA 7H支配星がN ASC/DSCに合", "desc": "結婚の運命を司る星が「自分」か「パートナー」の感受点に重なる、極めて重要な時期。"},
    # プログレス (P)
    "P_MOON_7H_INGRESS": {"score": 80, "title": "P月が第7ハウス入り", "desc": "約2.5年間、結婚やパートナーへの意識が自然と高まる。心がパートナーを求める時期。"},
    "P_MOON_CONJ_JUP": {"score": 70, "title": "P月がN木星に合", "desc": "精神的に満たされ、幸福感が高まる。楽観的な気持ちが良縁を引き寄せる。"},
    "P_MOON_CONJ_VENUS": {"score": 75, "title": "P月がN金星に合", "desc": "恋愛気分が盛り上がり、ときめきを感じやすい。デートや出会いに最適なタイミング。"},
    "P_VENUS_ASPECT_MARS": {"score": 80, "title": "P金星がN火星にアスペクト", "desc": "愛情と情熱が結びつき、ロマンスが燃え上がる強力な配置。関係が急速に進展しやすい。"}
}


# --- 都道府県データ ---
PREFECTURES = {
    "北海道": (141.35, 43.06), "青森県": (140.74, 40.82), "岩手県": (141.15, 39.70),
    "宮城県": (140.87, 38.27), "秋田県": (140.10, 39.72), "山形県": (140.36, 38.24),
    "福島県": (140.47, 37.75), "茨城県": (140.45, 36.34), "栃木県": (139.88, 36.57),
    "群馬県": (139.06, 36.39), "埼玉県": (139.65, 35.86), "千葉県": (140.12, 35.60),
    "東京都": (139.69, 35.69), "神奈川県": (139.64, 35.45), "新潟県": (139.02, 37.90),
    "富山県": (137.21, 36.70), "石川県": (136.63, 36.59), "福井県": (136.07, 36.07),
    "山梨県": (138.57, 35.66), "長野県": (138.18, 36.65), "岐阜県": (136.72, 35.39),
    "静岡県": (138.38, 34.98), "愛知県": (136.91, 35.18), "三重県": (136.51, 34.73),
    "滋賀県": (135.87, 35.00), "京都府": (135.76, 35.02), "大阪府": (135.52, 34.69),
    "兵庫県": (135.18, 34.69), "奈良県": (135.83, 34.69), "和歌山県": (135.17, 34.23),
    "鳥取県": (134.24, 35.50), "島根県": (133.05, 35.47), "岡山県": (133.93, 34.66),
    "広島県": (132.46, 34.40), "山口県": (131.47, 34.19), "徳島県": (134.55, 34.07),
    "香川県": (134.04, 34.34), "愛媛県": (132.77, 33.84), "高知県": (133.53, 33.56),
    "福岡県": (130.42, 33.61), "佐賀県": (130.30, 33.26), "長崎県": (129.88, 32.75),
    "熊本県": (130.74, 32.79), "大分県": (131.61, 33.24), "宮崎県": (131.42, 31.91),
    "鹿児島県": (130.56, 31.56), "沖縄県": (127.68, 26.21)
}


# --- 計算ロジック関数 ---
def get_julian_day(dt_utc):
    return swe.utc_to_jd(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour + dt_utc.minute / 60, 1)[1]

def get_planet_longitude(jday, planet_id):
    res, _ = swe.calc_ut(jday, planet_id)
    return res[0]

def get_natal_chart(birth_dt_jst, lon, lat):
    dt_utc = birth_dt_jst.astimezone(timezone.utc)
    jday = get_julian_day(dt_utc)
    chart_data = {"jday": jday, "lon": lon, "lat": lat}
    
    # 惑星・感受点の位置を計算
    for name, pid in PLANET_IDS.items():
        chart_data[name] = get_planet_longitude(jday, pid)

    # ハウスと主要な軸を計算
    cusps, ascmc = swe.houses(jday, lat, lon, b'P')
    chart_data["ASC"] = ascmc[0]
    chart_data["MC"] = ascmc[1]
    chart_data["DSC"] = cusps[6] # DSCは7ハウスの開始点
    chart_data["cusps"] = cusps

    # 7ハウスの支配星を特定
    dsc_sign = ZODIAC_SIGNS[int(chart_data["DSC"] / 30)]
    ruler_name = RULER_OF_SIGN[dsc_sign]
    chart_data["7H_RulerName"] = ruler_name
    chart_data["7H_Ruler"] = chart_data.get(ruler_name) # 計算済みの惑星位置から取得
    return chart_data

def find_events(natal_chart, birth_dt, years=80):
    events_by_date = {}
    
    # 3日間隔でチェックし、処理を高速化
    for day_offset in range(0, int(365.25 * years), 3):
        current_date = birth_dt + timedelta(days=day_offset)
        age_in_days = (current_date - birth_dt).days
        current_jday = natal_chart["jday"] + age_in_days

        # --- 計算対象の位置を取得 ---
        # T (Transit)
        t_pos = {p: get_planet_longitude(current_jday, pid) for p, pid in PLANET_IDS.items() if p in ["木星", "土星", "天王星"]}
        # P (Progressed) - 1日1年法
        p_jday = natal_chart["jday"] + age_in_days / 365.25
        p_pos = {p: get_planet_longitude(p_jday, pid) for p, pid in PLANET_IDS.items() if p in ["月", "金星"]}
        # SA (Solar Arc)
        sa_arc = get_planet_longitude(p_jday, swe.SUN) - natal_chart["太陽"]
        sa_pos = {p: (natal_chart[p] + sa_arc) % 360 for p in ["ASC", "MC", "金星", "木星", "7H_Ruler"] if p in natal_chart and natal_chart[p] is not None}
        
        # --- イベントチェック (簡略版) ---
        # オーブ内に入ったらヒットと判定
        
        # T木星
        if abs((t_pos["木星"] - natal_chart["DSC"])%360) < ORB or abs((t_pos["木星"] - natal_chart["DSC"])%360-360) < ORB: events_by_date.setdefault(current_date.date(), []).append("T_JUP_CONJ_DSC")
        if abs((t_pos["木星"] - natal_chart["金星"])%360) < ORB or abs(abs((t_pos["木星"] - natal_chart["金星"])%360)-120) < ORB : events_by_date.setdefault(current_date.date(), []).append("T_JUP_ASPECT_VENUS")

        # SA
        if "ASC" in sa_pos and abs((sa_pos["ASC"] - natal_chart["金星"])%360) < ORB : events_by_date.setdefault(current_date.date(), []).append("SA_ASC_CONJ_VENUS")
        if "MC" in sa_pos and abs((sa_pos["MC"] - natal_chart["金星"])%360) < ORB : events_by_date.setdefault(current_date.date(), []).append("SA_MC_CONJ_VENUS")
        if "金星" in sa_pos and abs((sa_pos["金星"] - natal_chart["ASC"])%360) < ORB : events_by_date.setdefault(current_date.date(), []).append("SA_VENUS_CONJ_ASC")
        if "7H_Ruler" in sa_pos and natal_chart.get("7H_Ruler") is not None and (abs((sa_pos["7H_Ruler"] - natal_chart["ASC"])%360) < ORB or abs((sa_pos["7H_Ruler"] - natal_chart["DSC"])%360) < ORB) : events_by_date.setdefault(current_date.date(), []).append("SA_7Ruler_CONJ_ASC_DSC")

        # P
        if "月" in p_pos and abs((p_pos["月"] - natal_chart["金星"])%360) < ORB : events_by_date.setdefault(current_date.date(), []).append("P_MOON_CONJ_VENUS")
        if "金星" in p_pos and natal_chart.get("火星") and (abs((p_pos["金星"]-natal_chart["火星"])%360) < ORB or abs(abs((p_pos["金星"]-natal_chart["火星"])%360)-120) < ORB): events_by_date.setdefault(current_date.date(), []).append("P_VENUS_ASPECT_MARS")

    # スコア計算
    scored_events = []
    for date, event_keys in events_by_date.items():
        unique_keys = list(set(event_keys))
        total_score = sum(EVENT_DEFINITIONS[key]["score"] for key in unique_keys)
        scored_events.append({"date": date, "score": total_score, "keys": unique_keys})
        
    if not scored_events: return []
    
    # スコアを正規化 (0-100%)
    max_score = max(event["score"] for event in scored_events) if scored_events else 0
    if max_score > 0:
        for event in scored_events:
            event["normalized_score"] = (event["score"] / max_score) * 100
    
    return sorted(scored_events, key=lambda x: x["score"], reverse=True)


# --- Streamlit UI ---
st.set_page_config(page_title="結婚タイミング占い【PRO】", page_icon="💖")
st.title("💖 結婚タイミング占い【PRO版】")
st.write("トランジット、プログレス、ソーラーアークの3技法を統合し、あなたの結婚運がピークに達する時期をスコア化して予測します。")

with st.expander("使い方と注意点"):
    st.markdown("""
    1.  **生年月日、出生時刻、出生地**を入力してください。
    2.  出生時刻が正確であるほど、プログレスやソーラーアークの精度が上がります。
    3.  「鑑定開始」ボタンを押すと、複数の技法を横断的に計算するため、**10〜30秒ほど時間がかかります。**
    ---
    **【重要】**
    * 表示される**重要度(%)**は、鑑定期間内で最も可能性の高い時期を100%とした相対的なものです。
    * スコアが高い日付は、複数の幸運な星回りが重なっていることを示します。その日付自体だけでなく、**その周辺の数ヶ月**がチャンスの期間となります。
    * これはあくまで占星術的な可能性の指標であり、未来を保証するものではありません。
    """)

col1, col2 = st.columns(2)
with col1:
    birth_date = st.date_input("① 生年月日", min_value=datetime.date(1940, 1, 1), max_value=datetime.date.today(), value=datetime.date(1990, 1, 1))
with col2:
    pref = st.selectbox("③ 出生地（都道府県）", options=list(PREFECTURES.keys()), index=12)

time_options = ["不明"] + [f"{h:02d}:00" for h in range(24)]
selected_time = st.selectbox("② 出生時刻（24時間表記）", options=time_options, index=13)
custom_time_str = st.text_input("または、詳細な時刻を入力 (例: 16:27)")

if st.button("鑑定開始", type="primary"):
    try:
        if custom_time_str:
            hour, minute = map(int, custom_time_str.split(':'))
        elif selected_time == "不明": hour, minute = 12, 0
        else: hour, minute = map(int, selected_time.split(':'))

        jst_tz = timezone(timedelta(hours=9))
        birth_dt_jst = datetime.datetime(birth_date.year, birth_date.month, birth_date.day, hour, minute, tzinfo=jst_tz)
        lon, lat = PREFECTURES[pref]
        
        with st.spinner("高度な計算を実行中... (30秒ほどお待ちください)"):
            natal_chart = get_natal_chart(birth_dt_jst, lon, lat)
            all_events = find_events(natal_chart, birth_dt_jst, years=80)

        st.success("計算が完了しました！")
        
        st.header("🌟 あなたの人生における結婚運のピーク TOP15", divider="rainbow")
        if not all_events:
            st.warning("指定された重要な天体の配置は見つかりませんでした。")
        else:
            for event in all_events[:15]:
                date_str = event["date"].strftime('%Y年%m月%d日')
                score = event["normalized_score"]
                st.subheader(f"{date_str}頃")
                st.markdown(f"**重要度: {score:.0f}%**")
                st.progress(int(score))
                
                with st.expander("この時期に何が起こる？ 詳細を見る"):
                    for key in event["keys"]:
                        info = EVENT_DEFINITIONS.get(key)
                        if info:
                            st.markdown(f"**▶ {info['title']}**")
                            st.write(info['desc'])
                st.write("---")

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
        st.error("入力値が正しいか、または天文暦ファイル(`ephe`フォルダ)が正しく配置されているか確認してください。")
