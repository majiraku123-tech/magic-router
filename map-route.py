import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import random
import math
from datetime import datetime, timedelta, date

# ==========================================
# 1. 施設データベース (最新化)
# ==========================================
AREA_INFO = {
    "ENT": {"name": "エントランス", "color": "#AAAAAA"},
    "MH": {"name": "メディテレーニアンハーバー", "color": "#06d6a0"},
    "AW": {"name": "アメリカンウォーターフロント", "color": "#ef476f"},
    "MI": {"name": "ミステリアスアイランド", "color": "#118ab2"},
    "LR": {"name": "ロストリバーデルタ", "color": "#073b4c"},
    "PD": {"name": "ポートディスカバリー", "color": "#00b4d8"},
    "AC": {"name": "アラビアンコースト", "color": "#ffd166"},
    "ML": {"name": "マーメイドラグーン", "color": "#ee6c4d"},
    "FS": {"name": "ファンタジースプリングス", "color": "#b5179e"},
}

# FSは「DPA」または「通常待ち」のみに変更。SPは廃止。
MASTER_DB = {
    "ソアリン：ファンタスティック・フライト": {"area": "MH", "pos": (12, 12), "dur": 20, "type": "Ride", "indoor": True, "dpa": True},
    "ヴェネツィアン・ゴンドラ": {"area": "MH", "pos": (5, 6), "dur": 15, "type": "Ride", "indoor": False, "dpa": False},
    "トランジットスチーマーライン(MH)": {"area": "MH", "pos": (8, 15), "dur": 15, "type": "Ride", "indoor": False, "dpa": False},
    "フォートレス・エクスプロレーション": {"area": "MH", "pos": (10, 25), "dur": 30, "type": "Walk", "indoor": False, "dpa": False},
    "トイ・ストーリー・マニア！": {"area": "AW", "pos": (5, 28), "dur": 15, "type": "Ride", "indoor": True, "dpa": True},
    "タワー・オブ・テラー": {"area": "AW", "pos": (15, 22), "dur": 15, "type": "Ride", "indoor": True, "dpa": True},
    "タートル・トーク": {"area": "AW", "pos": (18, 25), "dur": 30, "type": "Show", "indoor": True, "dpa": False},
    "エレクトリックレールウェイ(AW)": {"area": "AW", "pos": (12, 28), "dur": 10, "type": "Ride", "indoor": False, "dpa": False},
    "ビッグシティ・ヴィークル": {"area": "AW", "pos": (10, 20), "dur": 10, "type": "Ride", "indoor": False, "dpa": False},
    "ヴィレッジ・グリーティングプレイス": {"area": "AW", "pos": (2, 35), "dur": 15, "type": "Greet", "indoor": True, "dpa": False},
    "センター・オブ・ジ・アース": {"area": "MI", "pos": (8, 42), "dur": 15, "type": "Ride", "indoor": False, "dpa": True},
    "海底2万マイル": {"area": "MI", "pos": (10, 38), "dur": 15, "type": "Ride", "indoor": True, "dpa": False},
    "インディ・ジョーンズ・アドベンチャー": {"area": "LR", "pos": (-25, 68), "dur": 20, "type": "Ride", "indoor": True, "dpa": True},
    "レイジングスピリッツ": {"area": "LR", "pos": (-22, 72), "dur": 12, "type": "Ride", "indoor": False, "dpa": True},
    "トランジットスチーマーライン(LR)": {"area": "LR", "pos": (-20, 65), "dur": 15, "type": "Ride", "indoor": False, "dpa": False},
    "ミッキー＆フレンズ・グリーティングトレイル": {"area": "LR", "pos": (-28, 75), "dur": 15, "type": "Greet", "indoor": False, "dpa": False},
    "ニモ＆フレンズ・シーライダー": {"area": "PD", "pos": (-12, 48), "dur": 15, "type": "Ride", "indoor": True, "dpa": False},
    "アクアトピア": {"area": "PD", "pos": (-15, 52), "dur": 10, "type": "Ride", "indoor": False, "dpa": False},
    "エレクトリックレールウェイ(PD)": {"area": "PD", "pos": (-10, 50), "dur": 10, "type": "Ride", "indoor": False, "dpa": False},
    "シンドバッド・ストーリーブック・ヴォヤッジ": {"area": "AC", "pos": (18, 88), "dur": 15, "type": "Ride", "indoor": True, "dpa": False},
    "マジックランプシアター": {"area": "AC", "pos": (12, 82), "dur": 25, "type": "Show", "indoor": True, "dpa": False},
    "キャラバンカルーセル": {"area": "AC", "pos": (15, 85), "dur": 10, "type": "Ride", "indoor": True, "dpa": False},
    "ジャスミンのフライングカーペット": {"area": "AC", "pos": (20, 80), "dur": 10, "type": "Ride", "indoor": False, "dpa": False},
    "ジャンピン・ジェリーフィッシュ": {"area": "ML", "pos": (35, 58), "dur": 10, "type": "Ride", "indoor": True, "dpa": False},
    "スカットルのスクーター": {"area": "ML", "pos": (30, 52), "dur": 10, "type": "Ride", "indoor": False, "dpa": False},
    "フランダーのフライングフィッシュコースター": {"area": "ML", "pos": (32, 50), "dur": 5, "type": "Ride", "indoor": False, "dpa": False},
    "ブローフィッシュ・バルーンレース": {"area": "ML", "pos": (36, 60), "dur": 5, "type": "Ride", "indoor": True, "dpa": False},
    "ワールプール": {"area": "ML", "pos": (38, 62), "dur": 5, "type": "Ride", "indoor": True, "dpa": False},
    "アリエルのプレイグラウンド": {"area": "ML", "pos": (34, 65), "dur": 20, "type": "Walk", "indoor": True, "dpa": False},
    "アナとエルサのフローズンジャーニー": {"area": "FS", "pos": (52, 120), "dur": 20, "type": "Ride", "indoor": True, "dpa": True},
    "ラプンツェルのランタンフェスティバル": {"area": "FS", "pos": (56, 122), "dur": 10, "type": "Ride", "indoor": False, "dpa": True},
    "ピーターパンのネバーランドアドベンチャー": {"area": "FS", "pos": (62, 125), "dur": 20, "type": "Ride", "indoor": True, "dpa": True},
    "フェアリー・ティンカーベルのビジーバギー": {"area": "FS", "pos": (60, 121), "dur": 10, "type": "Ride", "indoor": False, "dpa": False}, 
}

PARK_CLOSING_MINUTES = 22 * 60  # 22時門限 (1320分)

# ==========================================
# 2. 環境シミュレーション・エンジン
# ==========================================
class EnvironmentAI:
    def __init__(self, selected_date, rain_prob, is_extra_holiday):
        self.selected_date = selected_date
        self.rain_prob = rain_prob
        self.is_crowded = selected_date.weekday() >= 5 or is_extra_holiday

    def get_wait_curve(self, attr_name, current_min):
        attr = MASTER_DB[attr_name]
        # FSエリアは「通常待ち」も可能という想定（マジックパス相当や解放時を考慮）
        # DPAでなければ長めの待ち時間を設定
        base = 100 if attr['area'] == "FS" else (80 if attr.get('dpa') else 30)
        
        # 開園〜22時での山なり混雑ピーク
        time_factor = np.sin(np.pi * max(0, (current_min - 480)) / 840)
        weather_mod = 1.3 if self.rain_prob > 50 and attr['indoor'] else 0.7 if self.rain_prob > 50 else 1.0
        crowd_mod = 1.5 if self.is_crowded else 1.0
        
        wait = int(base * (1 + 0.6 * time_factor) * weather_mod * crowd_mod)
        return max(5, wait)

# ==========================================
# 3. 最適化エンジン (厳格な時間管理・距離モデル)
# ==========================================
class OptimizationCore:
    def __init__(self, env):
        self.env = env

    def calc_route_cost(self, route, start_time, dpa_list, auto_rest):
        current_t = start_time
        current_pos = (0, 0)
        current_area = "ENT"
        total_wait = 0
        timeline = []
        has_rested = not auto_rest
        
        for name in route:
            attr = MASTER_DB[name]
            
            # 1. 距離計算（FSモデルの適正化）
            if current_area == "FS" and attr['area'] == "FS":
                time_cost = random.randint(3, 5) # FSエリア内移動は一瞬
            elif current_area == "ENT" and attr['area'] == "FS":
                time_cost = 25 # エントランスからFSは非常に遠い
            elif (current_area != "FS" and attr['area'] == "FS") or (current_area == "FS" and attr['area'] != "FS"):
                time_cost = 20 # 他エリアとの行き来も遠い
            else:
                dist = math.sqrt((current_pos[0]-attr['pos'][0])**2 + (current_pos[1]-attr['pos'][1])**2)
                time_cost = dist * 0.8
                if current_area != "ENT" and current_area != attr['area']:
                    time_cost *= 1.5
            
            # 移動の記録
            if time_cost >= 2:
                timeline.append({
                    "name": f"移動 ({AREA_INFO[current_area]['name']} → {AREA_INFO[attr['area']]['name']})", 
                    "arrive": current_t, "start": current_t, "end": current_t + int(time_cost),
                    "wait": 0, "dur": int(time_cost), "type": "Travel", "area": "NA"
                })
                current_t += int(time_cost)
            
            # 2. 自動休憩 (11:30~13:30 または 17:30~19:30)
            if auto_rest and not has_rested:
                if (690 <= current_t <= 810) or (1050 <= current_t <= 1170):
                    rest_dur = 60
                    timeline.append({
                        "name": "ダイニング休憩", 
                        "arrive": current_t, "start": current_t, "end": current_t + rest_dur,
                        "wait": 0, "dur": rest_dur, "type": "Rest", "area": attr['area']
                    })
                    current_t += rest_dur
                    has_rested = True

            # 3. 待ち時間算出 (DPA vs 通常)
            wait = 10 if name in dpa_list else self.env.get_wait_curve(name, current_t)
            
            arrive_t = int(current_t)
            start_t = arrive_t + wait
            end_t = start_t + attr['dur']
            
            # 22時門限を過ぎたら即座にペナルティ（ルート棄却）
            if end_t > PARK_CLOSING_MINUTES:
                return float('inf'), end_t, timeline

            # 4. 体験の記録
            timeline.append({
                "name": name, "arrive": arrive_t, "start": start_t, "end": end_t, 
                "wait": wait, "dur": attr['dur'], "type": "Ride", "area": attr['area']
            })
            
            current_t = end_t
            current_pos = attr['pos']
            current_area = attr['area']
            total_wait += wait

        return total_wait, current_t, timeline

    def anneal(self, selected, dpa_list, auto_rest, start_time):
        best_route = list(selected)
        random.shuffle(best_route)
        best_score, best_end, _ = self.calc_route_cost(best_route, start_time, dpa_list, auto_rest)
        
        temp = 1000.0
        cooling_rate = 0.95
        
        for _ in range(1000):
            if temp < 1.0: break
            new_route = best_route[:]
            i, j = random.sample(range(len(new_route)), 2)
            new_route[i], new_route[j] = new_route[j], new_route[i]
            
            new_score, _, _ = self.calc_route_cost(new_route, start_time, dpa_list, auto_rest)
            
            # inf(門限オーバー)を回避しつつ最適化
            if new_score < best_score or (new_score != float('inf') and random.random() < math.exp((best_score - new_score) / temp)):
                best_score = new_score
                best_route = new_route
            temp *= cooling_rate
            
        return best_route

# ==========================================
# 4. 公式アプリ風 UI/UX
# ==========================================
def main():
    st.set_page_config(page_title="TDS コンシェルジュ", layout="wide")
    
    # 清潔感のある白基調・柔らかいフォントのCSS
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=M+PLUS+1p:wght@400;700&family=Rounded+Mplus+1c:wght@400;700&display=swap');
        
        .stApp {
            background-color: #F8F9FA;
            color: #333333;
            font-family: 'M PLUS 1p', 'Rounded Mplus 1c', sans-serif;
        }
        .header-title {
            color: #1F3C88;
            font-weight: 700;
            margin-bottom: 0px;
        }
        .header-subtitle {
            color: #666666;
            font-size: 1em;
            margin-bottom: 30px;
        }
        .app-card {
            background: #FFFFFF;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            margin-bottom: 16px;
            border-left: 6px solid #1F3C88;
            transition: 0.2s;
        }
        .app-card:hover {
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
        }
        .time-text {
            color: #1F3C88;
            font-weight: 700;
            font-size: 1.2em;
            margin-right: 15px;
        }
        .area-badge {
            display: inline-block;
            color: #FFFFFF;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75em;
            font-weight: 700;
            margin-right: 12px;
            margin-bottom: 8px;
        }
        .wait-time {
            color: #D32F2F;
            font-weight: bold;
        }
        .stButton>button {
            border-radius: 24px;
            background-color: #1F3C88;
            color: #FFFFFF;
            border: none;
            font-weight: 700;
            height: 50px;
            transition: 0.3s;
        }
        .stButton>button:hover {
            background-color: #152B65;
            color: #FFFFFF;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 class='header-title'>TDS コンシェルジュ</h1>", unsafe_allow_html=True)
    st.markdown("<p class='header-subtitle'>あなただけの最適なパーク体験プランをご提案します</p>", unsafe_allow_html=True)

    # --- サイドバー (条件設定) ---
    with st.sidebar:
        st.markdown("### 📅 本日の設定")
        col1, col2 = st.columns(2)
        target_date = col1.date_input("入園予定日", date.today())
        entry_time = col2.time_input("入園時刻", datetime.strptime("08:30", "%H:%M").time())
        
        is_holiday = st.checkbox("祝日・長期休暇", value=False)
        rain_prob = st.slider("降水確率 (%)", 0, 100, 10)
        auto_rest = st.toggle("🍽️ 食事休憩を自動で組み込む", value=True)

        st.divider()
        st.markdown("### 📍 目的地を選択")
        
        selected_attrs = []
        dpa_list = []
        grouped = {}
        for name, data in MASTER_DB.items():
            grouped.setdefault(data['area'], []).append(name)
            
        for area_code, attrs in grouped.items():
            if area_code == "ENT": continue
            with st.expander(f"{AREA_INFO[area_code]['name']}"):
                for attr in attrs:
                    if st.checkbox(attr, key=f"sel_{attr}"):
                        selected_attrs.append(attr)
                        # DPAの選択 (FS含む)
                        if MASTER_DB[attr].get('dpa'):
                            if st.checkbox("┗ 💎 DPAを利用する", key=f"dpa_{attr}"):
                                dpa_list.append(attr)

    if not selected_attrs:
        st.info("👈 左のメニューから、今日体験したいアトラクションを選んでください。")
        return

    start_offset = entry_time.hour * 60 + entry_time.minute

    # --- 実行 ---
    env = EnvironmentAI(target_date, rain_prob, is_holiday)
    core = OptimizationCore(env)
    
    if st.button("✨ プランを作成する", use_container_width=True):
        with st.spinner("最適なルートを計算しています..."):
            best_route = core.anneal(selected_attrs, dpa_list, auto_rest, start_offset)
            total_w, end_t, timeline = core.calc_route_cost(best_route, start_offset, dpa_list, auto_rest)

        if end_t > PARK_CLOSING_MINUTES or total_w == float('inf'):
            st.error("⚠️ 22:00までにすべての施設を回りきれません。選択数を減らすか、DPAのご利用をご検討ください。")
            return
        
        # 概要
        col1, col2, col3 = st.columns(3)
        end_time_str = f"{end_t // 60:02d}:{end_t % 60:02d}"
        col1.metric("体験施設数", f"{len(selected_attrs)} 個")
        col2.metric("総待ち時間（目安）", f"{total_w} 分")
        col3.metric("全日程終了予定", end_time_str)

        st.divider()
        t_tab, m_tab = st.tabs(["📋 本日のプラン", "🗺️ マップで確認"])
        
        with t_tab:
            for item in timeline:
                # 時間フォーマット
                a_h, a_m = item['arrive'] // 60, item['arrive'] % 60
                s_h, s_m = item['start'] // 60, item['start'] % 60
                e_h, e_m = item['end'] // 60, item['end'] % 60
                
                badge = ""
                border_color = "#AAAAAA"
                if item['area'] in AREA_INFO and item['area'] != "NA":
                    bg_color = AREA_INFO[item['area']]['color']
                    border_color = bg_color
                    badge = f"<span class='area-badge' style='background:{bg_color};'>{AREA_INFO[item['area']]['name']}</span><br>"
                
                icon = "🎪"
                if item['type'] == 'Travel': icon = "🚶"
                elif item['type'] == 'Rest': icon = "🍽️"
                
                wait_text = f"<span class='wait-time'>待ち時間: {item['wait']}分</span> | " if item['wait'] > 0 else ""
                
                st.markdown(f"""
                <div class='app-card' style='border-left-color: {border_color};'>
                    {badge}
                    <span class='time-text'>{a_h:02d}:{a_m:02d}</span>
                    <span style='font-size:1.1em; font-weight:700;'>{icon} {item['name']}</span>
                    <div style='color:#666666; font-size:0.9em; margin-top:8px; padding-left:70px;'>
                        {wait_text}体験開始: {s_h:02d}:{s_m:02d} ～ 終了: {e_h:02d}:{e_m:02d} ({item['dur']}分)
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with m_tab:
            st.image("https://upload.wikimedia.org/wikipedia/commons/a/a2/Tokyo_DisneySea_overview.jpg", caption="パーク全体マップ（参考）")
            
            map_pts = [{"x": 0, "y": 0, "name": "エントランス", "area": "エントランス", "color": "#AAAAAA"}]
            for i in timeline:
                if i['type'] == 'Ride' and i['name'] in MASTER_DB:
                    data = MASTER_DB[i['name']]
                    map_pts.append({"x": data['pos'][0], "y": data['pos'][1], "name": i['name'], 
                                    "area": AREA_INFO[data['area']]['name'], "color": AREA_INFO[data['area']]['color']})
            
            df_map = pd.DataFrame(map_pts)
            fig_map = px.scatter(df_map, x='x', y='y', text='name', color='area',
                                color_discrete_map={row['area']: row['color'] for _, row in df_map.iterrows()})
            
            fig_map.add_trace(go.Scatter(x=df_map['x'], y=df_map['y'], mode='lines', 
                                         line=dict(color='#1F3C88', width=2, dash='dot'), showlegend=False))
            fig_map.update_traces(marker=dict(size=14, line=dict(width=1, color='#FFFFFF')), textposition='top center')
            fig_map.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#F8F9FA', font_color='#333333',
                xaxis=dict(visible=False), yaxis=dict(visible=False), 
                title=dict(text="本日の移動ルート", font=dict(color="#1F3C88", size=18, family="M PLUS 1p")),
                height=600, margin=dict(l=0, r=0, t=50, b=0)
            )
            st.plotly_chart(fig_map, use_container_width=True)

if __name__ == "__main__":
    main()