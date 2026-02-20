import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import random
import math
from datetime import datetime, timedelta

# ==========================================
# 1. 膨大な施設データベース (35施設・多次元データ)
# ==========================================
MASTER_DB = {
    "ソアリン": {"area": "MH", "pos": (12, 12), "dur": 20, "type": "Ride", "thrill": 2, "indoor": True, "dpa": True},
    "トイ・ストーリー・マニア！": {"area": "AW", "pos": (5, 28), "dur": 15, "type": "Ride", "thrill": 3, "indoor": True, "dpa": True},
    "タワー・オブ・テラー": {"area": "AW", "pos": (15, 22), "dur": 15, "type": "Ride", "thrill": 5, "indoor": True, "dpa": True},
    "センター・オブ・ジ・アース": {"area": "MI", "pos": (8, 42), "dur": 15, "type": "Ride", "thrill": 5, "indoor": False, "dpa": True},
    "インディ・ジョーンズ": {"area": "LR", "pos": (-25, 68), "dur": 20, "type": "Ride", "thrill": 4, "indoor": True, "dpa": True},
    "レイジングスピリッツ": {"area": "LR", "pos": (-22, 72), "dur": 12, "type": "Ride", "thrill": 5, "indoor": False, "dpa": True},
    "ニモ＆フレンズ・シーライダー": {"area": "PD", "pos": (-12, 48), "dur": 15, "type": "Ride", "thrill": 2, "indoor": True, "dpa": False},
    "アクアトピア": {"area": "PD", "pos": (-15, 52), "dur": 10, "type": "Ride", "thrill": 2, "indoor": False, "dpa": False},
    "シンドバッド": {"area": "AC", "pos": (18, 88), "dur": 15, "type": "Ride", "thrill": 1, "indoor": True, "dpa": False},
    "マジックランプシアター": {"area": "AC", "pos": (12, 82), "dur": 25, "type": "Show", "thrill": 1, "indoor": True, "dpa": False},
    "ジャンピン・ジェリーフィッシュ": {"area": "ML", "pos": (35, 58), "dur": 10, "type": "Ride", "thrill": 1, "indoor": True, "dpa": False},
    "海底2万マイル": {"area": "MI", "pos": (10, 38), "dur": 15, "type": "Ride", "thrill": 2, "indoor": True, "dpa": False},
    "ヴェネツィアン・ゴンドラ": {"area": "MH", "pos": (5, 6), "dur": 15, "type": "Ride", "thrill": 1, "indoor": False, "dpa": False},
    "タートル・トーク": {"area": "AW", "pos": (18, 25), "dur": 30, "type": "Show", "thrill": 1, "indoor": True, "dpa": False},
    "アナとエルサのフローズンジャーニー": {"area": "FS", "pos": (52, 98), "dur": 20, "type": "Ride", "thrill": 2, "indoor": True, "dpa": True},
    "ラプンツェルのランタンフェスティバル": {"area": "FS", "pos": (56, 92), "dur": 10, "type": "Ride", "thrill": 1, "indoor": False, "dpa": True},
    "ピーターパンのネバーランド": {"area": "FS", "pos": (62, 105), "dur": 20, "type": "Ride", "thrill": 4, "indoor": True, "dpa": True},
    "スカットルのスクーター": {"area": "ML", "pos": (30, 52), "dur": 10, "type": "Ride", "thrill": 2, "indoor": False, "dpa": False},
}

# ショー・パレードスケジュール
SHOWS = {
    "ビリーヴ！～シー・オブ・ドリームス～": {"time": "19:20", "dur": 30, "pos": (5, 10)},
    "ビッグバンドビート": {"time": "12:30", "dur": 25, "pos": (14, 20)}
}

# ==========================================
# 2. 環境シミュレーション・エンジン
# ==========================================
class EnvironmentAI:
    def __init__(self, holiday_mode, rain_prob):
        self.holiday_mode = holiday_mode
        self.rain_prob = rain_prob

    def get_wait_curve(self, attr_name, current_min):
        attr = MASTER_DB[attr_name]
        # 基本混雑度
        base = 80 if attr['dpa'] else 30
        if attr['area'] == "FS": base = 120 # 新エリア補正
        
        # 時間帯による変動 (昼にピーク、夜に減少)
        time_factor = np.sin(np.pi * (current_min / 720)) 
        
        # 天候補正 (雨なら屋外の待ち時間が減り、屋内が増える)
        weather_mod = 1.3 if self.rain_prob > 50 and attr['indoor'] else 0.7 if self.rain_prob > 50 else 1.0
        
        # 休日補正
        crowd_mod = 1.4 if self.holiday_mode else 1.0
        
        return max(5, int(base * (1 + 0.5 * time_factor) * weather_mod * crowd_mod))

# ==========================================
# 3. 焼きなまし法による最適化エンジン
# ==========================================
class OptimizationCore:
    def __init__(self, env):
        self.env = env

    def calc_route_cost(self, route, start_time, dpa_list, ps_time=None):
        current_t = start_time
        current_pos = (0, 0)
        total_wait = 0
        timeline = []
        
        for name in route:
            attr = MASTER_DB[name]
            # 移動
            dist = abs(current_pos[0]-attr['pos'][0]) + abs(current_pos[1]-attr['pos'][1])
            current_t += dist * 1.0 # 徒歩速度
            
            # レストランPSチェック (予約時間に間に合うか)
            if ps_time and current_t > ps_time:
                current_t += 999 # ペナルティ

            # 待ち
            w = 10 if name in dpa_list else self.env.get_wait_curve(name, current_t)
            timeline.append({"name": name, "start": current_t, "wait": w, "dur": attr['dur']})
            
            current_t += w + attr['dur']
            current_pos = attr['pos']
            total_wait += w
            
        return total_wait, current_t, timeline

    def anneal(self, selected, dpa_list, ps_time):
        best_route = list(selected)
        random.shuffle(best_route)
        _, best_score, _ = self.calc_route_cost(best_route, 0, dpa_list, ps_time)
        
        temp = 100.0
        while temp > 1.0:
            new_route = best_route[:]
            i, j = random.sample(range(len(new_route)), 2)
            new_route[i], new_route[j] = new_route[j], new_route[i]
            
            _, new_score, _ = self.calc_route_cost(new_route, 0, dpa_list, ps_time)
            
            if new_score < best_score or random.random() < math.exp((best_score - new_score) / temp):
                best_score = new_score
                best_route = new_route
            temp *= 0.98
        return best_route

# ==========================================
# 4. アドバンスド・ダッシュボード UI
# ==========================================
def main():
    st.set_page_config(page_title="TDS Aegis Command", layout="wide")
    
    # カスタムCSS: サイバーパンク・ネイビー
    st.markdown("""
        <style>
        .main { background-color: #000b1a; color: #00d4ff; }
        .stButton>button { width: 100%; border-radius: 20px; background: linear-gradient(90deg, #0052cc, #00d4ff); color: white; border: none; font-weight: bold; }
        .metric-box { border: 1px solid #00d4ff; padding: 15px; border-radius: 10px; background: rgba(0, 212, 255, 0.05); }
        .timeline-card { border-left: 4px solid #00d4ff; margin: 10px 0; padding-left: 15px; background: rgba(255,255,255,0.02); }
        </style>
    """, unsafe_allow_html=True)

    st.title("🛡️ TDS STRATEGIC AEGIS COMMAND")
    st.caption("Version 2.0.4 - 2026 High-Performance Fleet Management")

    # --- Sidebar: Control Panel ---
    with st.sidebar:
        st.header("🎮 MISSION CONTROL")
        holiday = st.toggle("Holiday/Crowded Day", True)
        rain = st.slider("Rain Probability (%)", 0, 100, 20)
        
        st.divider()
        st.subheader("📍 TARGET SELECTION")
        selected = [name for name in MASTER_DB.keys() if st.checkbox(name)]
        
        st.divider()
        st.subheader("🎫 ADVANCED OPTIONS")
        dpa_list = [s for s in selected if MASTER_DB[s]['dpa'] and st.toggle(f"Use DPA: {s[:5]}")]
        ps_hour = st.number_input("Restaurant PS (Hour)", 10, 20, 13)
        
    if not selected:
        st.info("ターゲットを選択してミッションを開始してください。")
        return

    # --- Execution ---
    env = EnvironmentAI(holiday, rain)
    core = OptimizationCore(env)
    
    if st.button("⚡ EXECUTE STRATEGIC OPTIMIZATION"):
        with st.spinner("Calculating optimal trajectory using Simulated Annealing..."):
            best_route = core.anneal(selected, dpa_list, ps_hour * 60 - 540)
            total_w, end_t, timeline = core.calc_route_cost(best_route, 0, dpa_list, ps_hour * 60 - 540)

        # --- Dashboard ---
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='metric-box'>総待ち時間<br><h3>{total_w} min</h3></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='metric-box'>最終帰還時刻<br><h3>{(datetime.strptime('09:00','%H:%M')+timedelta(minutes=end_t)).strftime('%H:%M')}</h3></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='metric-box'>ミッション完遂率<br><h3>{len(timeline)/len(selected)*100:.0f}%</h3></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='metric-box'>DPAコスト<br><h3>¥{len(dpa_list)*2000}</h3></div>", unsafe_allow_html=True)

        # Visualizations
        t_tab, m_tab, d_tab = st.tabs(["🕒 ITINERARY", "🗺️ TACTICAL MAP", "📊 ANALYTICS"])
        
        with t_tab:
            for item in timeline:
                time_str = (datetime.strptime("09:00", "%H:%M") + timedelta(minutes=item['start'])).strftime("%H:%M")
                st.markdown(f"""
                <div class='timeline-card'>
                    <span style='color:#00d4ff; font-weight:bold;'>{time_str}</span> | <b>{item['name']}</b><br>
                    <small>Wait: {item['wait']}m | Duration: {item['dur']}m</small>
                </div>
                """, unsafe_allow_html=True)

        with m_tab:
            df_map = pd.DataFrame([{"x": 0, "y": 0, "name": "Entrance"}] + 
                                 [{"x": MASTER_DB[i['name']]['pos'][0], "y": MASTER_DB[i['name']]['pos'][1], "name": i['name']} for i in timeline])
            fig_map = px.line(df_map, x='x', y='y', text='name', markers=True, template="plotly_dark")
            fig_map.update_traces(line_color='#00d4ff', marker=dict(size=12))
            st.plotly_chart(fig_map, use_container_width=True)

        with d_tab:
            # 混雑トレンド予測
            trend_data = []
            for m in range(0, 720, 30):
                for attr in selected[:3]:
                    trend_data.append({"Time": m, "Wait": env.get_wait_curve(attr, m), "Attr": attr})
            fig_trend = px.line(pd.DataFrame(trend_data), x="Time", y="Wait", color="Attr", template="plotly_dark", title="Expected Wait Trends")
            st.plotly_chart(fig_trend, use_container_width=True)

if __name__ == "__main__":
    main()