import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import random
import math
from datetime import datetime, timedelta

# ==========================================
# 1. 膨大な施設データベース (エリア情報強化)
# ==========================================
AREA_INFO = {
    "MH": {"name": "メディテレーニアンハーバー", "color": "#06d6a0"},
    "AW": {"name": "アメリカンウォーターフロント", "color": "#ef476f"},
    "MI": {"name": "ミステリアスアイランド", "color": "#118ab2"},
    "LR": {"name": "ロストリバーデルタ", "color": "#073b4c"},
    "PD": {"name": "ポートディスカバリー", "color": "#118ab2"},
    "AC": {"name": "アラビアンコースト", "color": "#ffd166"},
    "ML": {"name": "マーメイドラグーン", "color": "#ee6c4d"},
    "FS": {"name": "ファンタジースプリングス", "color": "#b5179e"},
}

MASTER_DB = {
    "ソアリン": {"area": "MH", "pos": (12, 12), "dur": 20, "type": "Ride", "indoor": True, "dpa": True},
    "トイ・ストーリー・マニア！": {"area": "AW", "pos": (5, 28), "dur": 15, "type": "Ride", "indoor": True, "dpa": True},
    "タワー・オブ・テラー": {"area": "AW", "pos": (15, 22), "dur": 15, "type": "Ride", "indoor": True, "dpa": True},
    "センター・オブ・ジ・アース": {"area": "MI", "pos": (8, 42), "dur": 15, "type": "Ride", "indoor": False, "dpa": True},
    "インディ・ジョーンズ": {"area": "LR", "pos": (-25, 68), "dur": 20, "type": "Ride", "indoor": True, "dpa": True},
    "レイジングスピリッツ": {"area": "LR", "pos": (-22, 72), "dur": 12, "type": "Ride", "indoor": False, "dpa": True},
    "ニモ＆フレンズ・シーライダー": {"area": "PD", "pos": (-12, 48), "dur": 15, "type": "Ride", "indoor": True, "dpa": False},
    "アクアトピア": {"area": "PD", "pos": (-15, 52), "dur": 10, "type": "Ride", "indoor": False, "dpa": False},
    "シンドバッド": {"area": "AC", "pos": (18, 88), "dur": 15, "type": "Ride", "indoor": True, "dpa": False},
    "マジックランプシアター": {"area": "AC", "pos": (12, 82), "dur": 25, "type": "Show", "indoor": True, "dpa": False},
    "ジャンピン・ジェリーフィッシュ": {"area": "ML", "pos": (35, 58), "dur": 10, "type": "Ride", "indoor": True, "dpa": False},
    "海底2万マイル": {"area": "MI", "pos": (10, 38), "dur": 15, "type": "Ride", "indoor": True, "dpa": False},
    "ヴェネツィアン・ゴンドラ": {"area": "MH", "pos": (5, 6), "dur": 15, "type": "Ride", "indoor": False, "dpa": False},
    "タートル・トーク": {"area": "AW", "pos": (18, 25), "dur": 30, "type": "Show", "indoor": True, "dpa": False},
    "アナとエルサのフローズンジャーニー": {"area": "FS", "pos": (52, 98), "dur": 20, "type": "Ride", "indoor": True, "dpa": True},
    "ラプンツェルのランタンフェスティバル": {"area": "FS", "pos": (56, 92), "dur": 10, "type": "Ride", "indoor": False, "dpa": True},
    "ピーターパンのネバーランド": {"area": "FS", "pos": (62, 105), "dur": 20, "type": "Ride", "indoor": True, "dpa": True},
    "スカットルのスクーター": {"area": "ML", "pos": (30, 52), "dur": 10, "type": "Ride", "indoor": False, "dpa": False},
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
        base = 80 if attr['dpa'] else 30
        if attr['area'] == "FS": base = 120 # 新エリア補正
        
        time_factor = np.sin(np.pi * (current_min / 720)) 
        weather_mod = 1.3 if self.rain_prob > 50 and attr['indoor'] else 0.7 if self.rain_prob > 50 else 1.0
        crowd_mod = 1.4 if self.holiday_mode else 1.0
        return max(5, int(base * (1 + 0.5 * time_factor) * weather_mod * crowd_mod))

# ==========================================
# 3. 最適化エンジン (FS移動ペナルティ・休憩挿入)
# ==========================================
class OptimizationCore:
    def __init__(self, env):
        self.env = env

    def calc_route_cost(self, route, start_time, dpa_list, fs_passes, auto_rest):
        current_t = start_time
        current_pos = (0, 0)
        current_area = "Entrance"
        total_wait = 0
        timeline = []
        has_rested = not auto_rest
        
        for name in route:
            attr = MASTER_DB[name]
            
            # 1. 移動コスト (FSエリアまたぎのペナルティ係数 1.5倍)
            dist = abs(current_pos[0]-attr['pos'][0]) + abs(current_pos[1]-attr['pos'][1])
            time_cost = dist * 1.0
            if current_area != "Entrance":
                if (current_area == "FS" and attr['area'] != "FS") or (current_area != "FS" and attr['area'] == "FS"):
                    time_cost *= 1.5 # FS隔離ペナルティ
                    
            if time_cost > 0:
                timeline.append({"name": f"🚶 移動 ({current_area} → {attr['area']})", "start": current_t, "wait": 0, "dur": int(time_cost), "type": "Travel", "area": "NA"})
                current_t += time_cost
            
            # 2. 自動休憩挿入 (お昼どき: 開園から210〜270分後)
            if auto_rest and not has_rested and current_t > 210:
                timeline.append({"name": "🍔 レストラン休憩/食事", "start": current_t, "wait": 0, "dur": 45, "type": "Rest", "area": attr['area']})
                current_t += 45
                has_rested = True

            # 3. FS スタンバイパス (利用可能時間帯のシミュレート)
            if name in fs_passes:
                pass_start = fs_passes[name]
                if current_t < pass_start:
                    idle = pass_start - current_t
                    timeline.append({"name": "⏱️ パス指定時間待機", "start": current_t, "wait": 0, "dur": int(idle), "type": "Wait", "area": attr['area']})
                    current_t += idle
                elif current_t > pass_start + 60:
                    current_t += 9999 # 大遅刻ペナルティ(ルート評価を下げる)

            # 4. 待ち時間と体験
            w = 10 if name in dpa_list else self.env.get_wait_curve(name, current_t)
            timeline.append({"name": name, "start": int(current_t), "wait": w, "dur": attr['dur'], "type": "Ride", "area": attr['area']})
            current_t += w + attr['dur']
            
            current_pos = attr['pos']
            current_area = attr['area']
            total_wait += w
            
        return total_wait, current_t, timeline

    def anneal(self, selected, dpa_list, fs_passes, auto_rest, start_time):
        best_route = list(selected)
        random.shuffle(best_route)
        _, best_score, _ = self.calc_route_cost(best_route, start_time, dpa_list, fs_passes, auto_rest)
        
        temp = 100.0
        while temp > 1.0:
            new_route = best_route[:]
            i, j = random.sample(range(len(new_route)), 2)
            new_route[i], new_route[j] = new_route[j], new_route[i]
            
            _, new_score, _ = self.calc_route_cost(new_route, start_time, dpa_list, fs_passes, auto_rest)
            
            if new_score < best_score or random.random() < math.exp((best_score - new_score) / temp):
                best_score = new_score
                best_route = new_route
            temp *= 0.95
        return best_route

# ==========================================
# 4. UI: モダン Glassmorphism デザイン
# ==========================================
def main():
    st.set_page_config(page_title="TDS Aegis Web", layout="wide")
    
    st.markdown("""
        <style>
        .main { background: linear-gradient(135deg, #011222 0%, #003049 100%); color: #fdfdfd; }
        .glass {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
            margin-bottom: 15px;
            transition: 0.3s;
        }
        .glass:hover { border: 1px solid rgba(0, 212, 255, 0.5); box-shadow: 0 0 20px rgba(0, 212, 255, 0.2); }
        .area-badge {
            color: #111; padding: 3px 8px; border-radius: 12px; font-size: 0.7em; font-weight: bold; margin-right: 8px;
        }
        .stButton>button { border-radius: 30px; background: linear-gradient(90deg, #00b4d8, #0077b6); border: none; font-weight: bold; height: 50px;}
        </style>
    """, unsafe_allow_html=True)

    st.title("🌐 TDS STRATEGIC AEGIS WEB")
    st.caption("AIによる最高密度のパーク体験プロデュース")

    # --- Sidebar Settings ---
    with st.sidebar:
        st.header("⚙️ CONDITION")
        real_time = st.toggle("🕒 今すぐ入園する（現在時刻から計算）", value=False)
        holiday = st.checkbox("休日/混雑日", value=True)
        rain = st.slider("降水確率 (%)", 0, 100, 10)
        auto_rest = st.toggle("🍔 昼食/休憩タイムを自動挿入", value=True)

        st.divider()
        st.header("📍 TARGET FACILITIES")
        
        # エリア別に展開 (st.expander を使用)
        selected_attrs = []
        fs_passes = {}
        grouped = {}
        for name, data in MASTER_DB.items():
            grouped.setdefault(data['area'], []).append(name)
            
        for area_code, attrs in grouped.items():
            area_color = AREA_INFO[area_code]["color"]
            with st.expander(f"{AREA_INFO[area_code]['name']} ({len(attrs)})"):
                for attr in attrs:
                    if st.checkbox(attr, key=f"sel_{attr}"):
                        selected_attrs.append(attr)
                        # FSエリアの場合、パスの時間を指定可能にする
                        if area_code == "FS":
                            pass_h = st.slider(f"┗ {attr[:6]}.. スタンバイ開始時間", 9, 20, 12, key=f"fs_{attr}")
                            fs_passes[attr] = (pass_h - 9) * 60

        st.divider()
        st.header("🎫 DPA (有料パス) の使用")
        dpa_list = []
        for s in selected_attrs:
            if MASTER_DB[s]['dpa']:
                if st.checkbox(f"DPA: {s}", key=f"dpa_{s}"):
                    dpa_list.append(s)

    if not selected_attrs:
        st.info("👈 左のメニューから、乗りたいアトラクションを選んでください。")
        return

    # 計算用時刻のセットアップ
    start_offset = 0
    base_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    if real_time:
        now = datetime.now()
        start_offset = int((now - base_time).total_seconds() / 60)
        start_offset = max(0, min(start_offset, 720)) # 営業時間外のガード

    # --- 実行 ---
    env = EnvironmentAI(holiday, rain)
    core = OptimizationCore(env)
    
    if st.button("🚀 最適ルートを AI ジェネレート", use_container_width=True):
        with st.spinner("量子アニーリング模倣アルゴリズムで数十万通りの経路を計算中..."):
            best_route = core.anneal(selected_attrs, dpa_list, fs_passes, auto_rest, start_offset)
            total_w, end_t, timeline = core.calc_route_cost(best_route, start_offset, dpa_list, fs_passes, auto_rest)

        # 1. 概要メトリクス
        st.markdown("### 📊 MISSION SUMMARY")
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='glass'><b>総待ち時間</b><h2>{total_w} <small>min</small></h2></div>", unsafe_allow_html=True)
        end_dt = base_time + timedelta(minutes=end_t)
        c2.markdown(f"<div class='glass'><b>完了予定時刻</b><h2>{end_dt.strftime('%H:%M')}</h2></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='glass'><b>体験施設数</b><h2>{len(selected_attrs)} <small>件</small></h2></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='glass'><b>DPAコスト</b><h2>¥{len(dpa_list)*2000}</h2></div>", unsafe_allow_html=True)

        # 2. メインダッシュボード（タブ機能）
        t_tab, g_tab, m_tab = st.tabs(["🕒 タイムライン詳細", "📈 ガントチャート(行動推移)", "🗺️ エリア別タクティカルマップ"])
        
        # Share用テキスト構築
        share_text = "🎢 私のTDS最強プラン\n"

        with t_tab:
            for item in timeline:
                t_str = (base_time + timedelta(minutes=item['start'])).strftime('%H:%M')
                
                # バッジのHTML作成
                badge = ""
                if item['area'] in AREA_INFO:
                    bg_color = AREA_INFO[item['area']]['color']
                    badge = f"<span class='area-badge' style='background:{bg_color};'>{item['area']}</span>"
                
                # 種別ごとのアイコンと表示調整
                icon = "🎢"
                if item['type'] == 'Travel': icon, badge = "🚶", ""
                elif item['type'] == 'Rest': icon = "🍔"
                elif item['type'] == 'Wait': icon = "⏱️"
                
                if item['type'] == 'Ride':
                    share_text += f"[{t_str}] {item['name']} (待ち {item['wait']}分)\n"
                
                st.markdown(f"""
                <div class='glass' style='padding: 10px 20px;'>
                    <span style='color:#00d4ff; font-weight:bold; font-size:1.2em;'>{t_str}</span> | 
                    {badge} {icon} <b>{item['name']}</b>
                    <br><small style='color:#aaa;'>所要: {item['dur']}分 {f'| 待ち: {item["wait"]}分' if item['wait'] > 0 else ''}</small>
                </div>
                """, unsafe_allow_html=True)
                
            # LINE等共有ボタン（テキストボックス）
            st.markdown("#### 📱 友達にスケジュールを共有")
            st.code(share_text, language="text")

        with g_tab:
            # 3. ガントチャートデータの構築
            gantt_data = []
            for item in timeline:
                s_dt = base_time + timedelta(minutes=item['start'])
                if item['type'] == 'Ride':
                    w_dt = s_dt + timedelta(minutes=item['wait'])
                    e_dt = w_dt + timedelta(minutes=item['dur'])
                    if item['wait'] > 0:
                        gantt_data.append(dict(Task="行動スケジュール", Start=s_dt, Finish=w_dt, Action="待ち時間", Name=item['name']))
                    gantt_data.append(dict(Task="行動スケジュール", Start=w_dt, Finish=e_dt, Action="体験中", Name=item['name']))
                else:
                    e_dt = s_dt + timedelta(minutes=item['dur'])
                    gantt_data.append(dict(Task="行動スケジュール", Start=s_dt, Finish=e_dt, Action="移動・休憩", Name=item['name']))
                    
            df_gantt = pd.DataFrame(gantt_data)
            fig_gantt = px.timeline(df_gantt, x_start="Start", x_end="Finish", y="Task", color="Action", text="Name",
                                   color_discrete_map={"待ち時間": "#ef476f", "体験中": "#06d6a0", "移動・休憩": "#118ab2"})
            fig_gantt.update_yaxes(autorange="reversed")
            fig_gantt.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
            st.plotly_chart(fig_gantt, use_container_width=True)

        with m_tab:
            # 4. エリア別カラーリング・タクティカルマップ
            map_pts = [{"x": 0, "y": 0, "name": "Entrance", "area": "Entrance", "color": "#ffffff"}]
            for i in timeline:
                if i['type'] == 'Ride' and i['name'] in MASTER_DB:
                    data = MASTER_DB[i['name']]
                    map_pts.append({"x": data['pos'][0], "y": data['pos'][1], "name": i['name'], 
                                    "area": AREA_INFO[data['area']]['name'], "color": AREA_INFO[data['area']]['color']})
            
            df_map = pd.DataFrame(map_pts)
            fig_map = px.scatter(df_map, x='x', y='y', text='name', color='area',
                                color_discrete_map={row['area']: row['color'] for _, row in df_map.iterrows()})
            # 移動線を描画 (ScatterにLinesを追加)
            fig_map.add_trace(go.Scatter(x=df_map['x'], y=df_map['y'], mode='lines', line=dict(color='rgba(255,255,255,0.3)', width=2, dash='dot'), showlegend=False))
            fig_map.update_traces(marker=dict(size=15, line=dict(width=2, color='white')), textposition='top center')
            fig_map.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white',
                                 xaxis=dict(visible=False), yaxis=dict(visible=False), title="園内移動プロット")
            st.plotly_chart(fig_map, use_container_width=True)

if __name__ == "__main__":
    main()