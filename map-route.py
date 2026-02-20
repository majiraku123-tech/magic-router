import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import random
import math
from datetime import datetime, timedelta, date

# ==========================================
# 1. 膨大な施設データベース (全エリア網羅・30施設以上)
# ==========================================
AREA_INFO = {
    "ENT": {"name": "エントランス", "color": "#ffffff"},
    "MH": {"name": "メディテレーニアンハーバー", "color": "#06d6a0"},
    "AW": {"name": "アメリカンウォーターフロント", "color": "#ef476f"},
    "MI": {"name": "ミステリアスアイランド", "color": "#118ab2"},
    "LR": {"name": "ロストリバーデルタ", "color": "#073b4c"},
    "PD": {"name": "ポートディスカバリー", "color": "#118ab2"},
    "AC": {"name": "アラビアンコースト", "color": "#ffd166"},
    "ML": {"name": "マーメイドラグーン", "color": "#ee6c4d"},
    "FS": {"name": "ファンタジースプリングス", "color": "#b5179e"},
}

# 座標(pos)はパークマップを模した相対座標。durは所要時間(分)。
# FSエリアはスタンバイ不可（dpaまたはsp必須）として扱う
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
    "アナとエルサのフローズンジャーニー": {"area": "FS", "pos": (52, 98), "dur": 20, "type": "Ride", "indoor": True, "dpa": True},
    "ラプンツェルのランタンフェスティバル": {"area": "FS", "pos": (56, 92), "dur": 10, "type": "Ride", "indoor": False, "dpa": True},
    "ピーターパンのネバーランドアドベンチャー": {"area": "FS", "pos": (62, 105), "dur": 20, "type": "Ride", "indoor": True, "dpa": True},
    "フェアリー・ティンカーベルのビジーバギー": {"area": "FS", "pos": (60, 100), "dur": 10, "type": "Ride", "indoor": False, "dpa": False}, # SP専用
}

# 門限 (22:00 = 0:00から起算して1320分)
PARK_CLOSING_MINUTES = 22 * 60

# ==========================================
# 2. 環境シミュレーション・エンジン
# ==========================================
class EnvironmentAI:
    def __init__(self, selected_date, rain_prob, is_extra_holiday):
        self.selected_date = selected_date
        self.rain_prob = rain_prob
        # 土日か、ユーザーが指定した特別混雑日なら係数を上げる
        self.is_crowded = selected_date.weekday() >= 5 or is_extra_holiday

    def get_wait_curve(self, attr_name, current_min):
        attr = MASTER_DB[attr_name]
        
        # FSエリアの厳密処理: 通常スタンバイは存在しない
        if attr['area'] == "FS":
            return 999  # DPAかSPを持たない場合、物理的に並べないためペナルティ値
            
        base = 80 if attr['dpa'] else 30
        
        # 混雑ピークのモデリング (昼〜夕方にピーク)
        # 1日のうち、開園(約500分)〜22時(1320分)の間で山なりを作る
        time_factor = np.sin(np.pi * max(0, (current_min - 480)) / 840)
        
        weather_mod = 1.3 if self.rain_prob > 50 and attr['indoor'] else 0.7 if self.rain_prob > 50 else 1.0
        crowd_mod = 1.5 if self.is_crowded else 1.0
        
        wait = int(base * (1 + 0.6 * time_factor) * weather_mod * crowd_mod)
        return max(5, wait)

# ==========================================
# 3. 最適化エンジン (数学的厳密モデル)
# ==========================================
class OptimizationCore:
    def __init__(self, env):
        self.env = env

    def calc_route_cost(self, route, start_time, dpa_list, fs_passes, auto_rest):
        current_t = start_time
        current_pos = (0, 0)
        current_area = "ENT"
        total_wait = 0
        timeline = []
        has_rested = not auto_rest
        
        for name in route:
            attr = MASTER_DB[name]
            
            # 1. 移動コスト計算 (エリアまたぎのペナルティ係数 1.5倍)
            dist = math.sqrt((current_pos[0]-attr['pos'][0])**2 + (current_pos[1]-attr['pos'][1])**2)
            time_cost = dist * 0.8  # 基本移動係数
            
            if current_area != "ENT" and current_area != attr['area']:
                time_cost *= 1.5  # 異なるエリア間の移動ペナルティ
                
            if time_cost > 2:
                timeline.append({
                    "name": f"🚶 移動 ({AREA_INFO[current_area]['name']} → {AREA_INFO[attr['area']]['name']})", 
                    "start": current_t, "wait": 0, "dur": int(time_cost), "type": "Travel", "area": "NA"
                })
                current_t += int(time_cost)
            
            # 2. 自動休憩挿入 (滞在が長時間になる場合、最も待ち時間が長い昼時 11:30~13:30 に休憩)
            if auto_rest and not has_rested and (current_t >= 11*60+30):
                rest_dur = 60
                timeline.append({"name": "🍽️ ダイニング休憩 (ランチ/ディナー)", "start": current_t, "wait": 0, "dur": rest_dur, "type": "Rest", "area": attr['area']})
                current_t += rest_dur
                has_rested = True

            # 3. FS スタンバイパス / DPAの厳格処理
            w = 0
            if attr['area'] == "FS":
                if name in dpa_list:
                    w = 10 # FS DPAは優先案内
                elif name in fs_passes:
                    pass_start = fs_passes[name]
                    if current_t < pass_start:
                        idle = pass_start - current_t
                        timeline.append({"name": "⏱️ 指定時刻まで待機", "start": current_t, "wait": 0, "dur": int(idle), "type": "Wait", "area": attr['area']})
                        current_t += idle
                    elif current_t > pass_start + 60:
                        current_t += 5000 # 指定時間を過ぎた場合の重篤なペナルティ
                    w = 20 # FS スタンバイパスの目安待ち時間
                else:
                    current_t += 5000 # パスなしでFSに乗ろうとしたペナルティ(解なし)
            else:
                w = 10 if name in dpa_list else self.env.get_wait_curve(name, current_t)
            
            # 4. 待ち時間と体験
            timeline.append({"name": name, "start": int(current_t), "wait": w, "dur": attr['dur'], "type": "Ride", "area": attr['area']})
            current_t += w + attr['dur']
            
            current_pos = attr['pos']
            current_area = attr['area']
            total_wait += w
            
        # 5. 閉園時間 (22:00) 厳守のペナルティ
        if current_t > PARK_CLOSING_MINUTES:
            total_wait += (current_t - PARK_CLOSING_MINUTES) * 1000 # 1分超過ごとに極大ペナルティ

        return total_wait, current_t, timeline

    def anneal(self, selected, dpa_list, fs_passes, auto_rest, start_time):
        best_route = list(selected)
        random.shuffle(best_route)
        _, best_end, _ = self.calc_route_cost(best_route, start_time, dpa_list, fs_passes, auto_rest)
        
        # 初期状態のスコア関数は「総待ち時間 + 終了時刻」の最小化
        best_score, _, _ = self.calc_route_cost(best_route, start_time, dpa_list, fs_passes, auto_rest)
        
        temp = 1000.0
        cooling_rate = 0.98
        
        for _ in range(500): # 反復回数
            if temp < 1.0: break
            new_route = best_route[:]
            i, j = random.sample(range(len(new_route)), 2)
            new_route[i], new_route[j] = new_route[j], new_route[i]
            
            new_score, _, _ = self.calc_route_cost(new_route, start_time, dpa_list, fs_passes, auto_rest)
            
            if new_score < best_score or random.random() < math.exp((best_score - new_score) / temp):
                best_score = new_score
                best_route = new_route
            temp *= cooling_rate
            
        return best_route

# ==========================================
# 4. UI: 高級日本のWebデザイン (Glassmorphism)
# ==========================================
def main():
    st.set_page_config(page_title="TDS Tactical Aegis", layout="wide", initial_sidebar_state="expanded")
    
    # 高級感のあるネイビーと真鍮色のCSS
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #001529 0%, #002244 100%);
            color: #E8E2D2;
            font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', Meiryo, sans-serif;
        }
        .glass-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(184, 134, 11, 0.3); /* 真鍮色ボーダー */
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
            margin-bottom: 20px;
            transition: all 0.3s ease;
        }
        .glass-card:hover { 
            border: 1px solid rgba(184, 134, 11, 0.8); 
            box-shadow: 0 8px 32px rgba(184, 134, 11, 0.2); 
        }
        .area-badge {
            color: #001529; padding: 4px 10px; border-radius: 4px; font-size: 0.75em; font-weight: 600; margin-right: 12px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        }
        .metric-title { font-size: 0.9em; color: #A0AAB5; margin-bottom: 4px;}
        .metric-value { font-size: 2.2em; font-weight: bold; color: #B8860B; margin: 0;}
        .stButton>button { 
            border-radius: 8px; 
            background: linear-gradient(135deg, #B8860B 0%, #8B6508 100%); 
            color: #fff;
            border: none; 
            font-weight: bold; 
            height: 56px;
            letter-spacing: 2px;
            transition: 0.3s;
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(184, 134, 11, 0.4);
        }
        h1, h2, h3 { color: #B8860B; font-weight: 300; letter-spacing: 1px;}
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1>⚜️ TDS Tactical Aegis</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#A0AAB5; font-size:1.1em; letter-spacing:1px;'>東京ディズニーシー 究極の戦略シミュレーター</p>", unsafe_allow_html=True)

    # --- サイドバー (条件設定) ---
    with st.sidebar:
        st.markdown("<h2 style='font-size:1.2em;'>⚙️ 作戦条件 (CONDITIONS)</h2>", unsafe_allow_html=True)
        
        # 時間・日付管理の徹底改修
        col1, col2 = st.columns(2)
        target_date = col1.date_input("入園予定日", date.today())
        entry_time = col2.time_input("入園時刻", datetime.strptime("08:15", "%H:%M").time())
        
        is_holiday = st.checkbox("祝日・長期休暇（混雑補正）", value=False)
        rain_prob = st.slider("降水確率 (%)", 0, 100, 10)
        auto_rest = st.toggle("🍽️ レストラン休憩を自動挿入", value=True)

        st.divider()
        st.markdown("<h2 style='font-size:1.2em;'>📍 攻略目標 (TARGETS)</h2>", unsafe_allow_html=True)
        
        selected_attrs = []
        fs_passes = {}
        grouped = {}
        for name, data in MASTER_DB.items():
            grouped.setdefault(data['area'], []).append(name)
            
        for area_code, attrs in grouped.items():
            if area_code == "ENT": continue
            area_color = AREA_INFO[area_code]["color"]
            with st.expander(f"{AREA_INFO[area_code]['name']} ({len(attrs)})"):
                for attr in attrs:
                    if st.checkbox(attr, key=f"sel_{attr}"):
                        selected_attrs.append(attr)
                        # FSエリアの場合、SP時間またはDPA指定を必須化
                        if area_code == "FS":
                            is_dpa = False
                            if MASTER_DB[attr]['dpa']:
                                is_dpa = st.checkbox(f"┗ 💎 DPA(有料)を購入", key=f"fs_dpa_{attr}")
                            
                            if not is_dpa:
                                pass_time = st.time_input(f"┗ 🎫 SP(無料) 取得時刻", datetime.strptime("12:00", "%H:%M").time(), key=f"fs_sp_{attr}")
                                fs_passes[attr] = pass_time.hour * 60 + pass_time.minute

        st.divider()
        st.markdown("<h2 style='font-size:1.2em;'>💎 有料戦略 (DPA)</h2>", unsafe_allow_html=True)
        dpa_list = []
        for s in selected_attrs:
            if MASTER_DB[s]['dpa'] and MASTER_DB[s]['area'] != "FS": # FSのDPAは上で処理
                if st.checkbox(f"DPA利用: {s}", key=f"dpa_{s}"):
                    dpa_list.append(s)
            elif MASTER_DB[s]['area'] == "FS" and st.session_state.get(f"fs_dpa_{s}"):
                dpa_list.append(s)

    if not selected_attrs:
        st.info("👈 左のコンシェルジュメニューから、体験したいアトラクションを選択してください。")
        return

    # 計算用時刻のセットアップ (分換算)
    start_offset = entry_time.hour * 60 + entry_time.minute

    # --- 実行 ---
    env = EnvironmentAI(target_date, rain_prob, is_holiday)
    core = OptimizationCore(env)
    
    if st.button("⚜️ 究極の戦略を生成 (AI最適化)", use_container_width=True):
        with st.spinner("数学的アルゴリズムに基づく最適経路を解析中..."):
            best_route = core.anneal(selected_attrs, dpa_list, fs_passes, auto_rest, start_offset)
            total_w, end_t, timeline = core.calc_route_cost(best_route, start_offset, dpa_list, fs_passes, auto_rest)

        # 閉園時間超過チェック
        if end_t > PARK_CLOSING_MINUTES:
            st.error(f"⚠️ 警告: 選択された施設をすべて体験することは不可能です（完了予定時刻が22:00を超過します）。施設数を減らすか、DPAの活用を検討してください。")
        
        # 1. 概要メトリクス
        st.markdown("<h3 style='margin-top:20px;'>戦略概要 (TACTICAL SUMMARY)</h3>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='glass-card'><div class='metric-title'>予測総待ち時間</div><div class='metric-value'>{total_w} <span style='font-size:0.5em;'>min</span></div></div>", unsafe_allow_html=True)
        
        end_time_str = f"{end_t // 60:02d}:{end_t % 60:02d}" if end_t <= 24*60 else "OVER"
        c2.markdown(f"<div class='glass-card'><div class='metric-title'>全工程完了時刻</div><div class='metric-value'>{end_time_str}</div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='glass-card'><div class='metric-title'>体験施設数</div><div class='metric-value'>{len(selected_attrs)} <span style='font-size:0.5em;'>施設</span></div></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='glass-card'><div class='metric-title'>DPA必要予算</div><div class='metric-value'>¥{len(dpa_list)*2000:,}</div></div>", unsafe_allow_html=True)

        # 2. メインダッシュボード（タブ機能）
        t_tab, g_tab, m_tab = st.tabs(["📜 行動工程表 (TIMELINE)", "📊 進行チャート (GANTT)", "🗺️ 展開戦術マップ (TACTICAL MAP)"])
        
        share_text = f"⚜️ {target_date.strftime('%Y/%m/%d')} TDS戦略プロット\n"

        with t_tab:
            for item in timeline:
                h, m = item['start'] // 60, item['start'] % 60
                t_str = f"{h:02d}:{m:02d}"
                
                badge = ""
                if item['area'] in AREA_INFO and item['area'] != "NA":
                    bg_color = AREA_INFO[item['area']]['color']
                    badge = f"<span class='area-badge' style='background:{bg_color};'>{AREA_INFO[item['area']]['name']}</span>"
                
                icon = "✨"
                if item['type'] == 'Travel': icon, badge = "🚶", ""
                elif item['type'] == 'Rest': icon = "🍽️"
                elif item['type'] == 'Wait': icon = "⏱️"
                
                if item['type'] == 'Ride':
                    share_text += f"[{t_str}] {item['name']} (待{item['wait']}分)\n"
                
                st.markdown(f"""
                <div class='glass-card' style='padding: 16px 24px; margin-bottom: 12px;'>
                    <span style='color:#B8860B; font-family:monospace; font-size:1.3em; margin-right: 15px;'>{t_str}</span> 
                    {badge} <span style='font-size:1.1em;'>{icon} <b>{item['name']}</b></span>
                    <br><span style='color:#A0AAB5; font-size:0.85em; margin-left:75px;'>所要時間: {item['dur']}分 {f'｜ 推定待ち時間: <b>{item["wait"]}分</b>' if item['wait'] > 0 else ''}</span>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("<h4 style='color:#B8860B; margin-top:20px;'>📱 共有用テキスト</h4>", unsafe_allow_html=True)
            st.code(share_text, language="text")

        with g_tab:
            gantt_data = []
            base_dt = datetime(2023, 1, 1) # ガント描画用ダミー日付
            for item in timeline:
                s_dt = base_dt + timedelta(minutes=item['start'])
                if item['type'] == 'Ride':
                    w_dt = s_dt + timedelta(minutes=item['wait'])
                    e_dt = w_dt + timedelta(minutes=item['dur'])
                    if item['wait'] > 0:
                        gantt_data.append(dict(Task="行動推移", Start=s_dt, Finish=w_dt, Action="待機", Name=item['name']))
                    gantt_data.append(dict(Task="行動推移", Start=w_dt, Finish=e_dt, Action="体験", Name=item['name']))
                else:
                    e_dt = s_dt + timedelta(minutes=item['dur'])
                    action = "移動" if item['type'] == 'Travel' else "休憩・待機"
                    gantt_data.append(dict(Task="行動推移", Start=s_dt, Finish=e_dt, Action=action, Name=item['name']))
                    
            if gantt_data:
                df_gantt = pd.DataFrame(gantt_data)
                fig_gantt = px.timeline(df_gantt, x_start="Start", x_end="Finish", y="Task", color="Action", text="Name",
                                       color_discrete_map={"待機": "#8B2252", "体験": "#B8860B", "移動": "#1C3953", "休憩・待機": "#4F94CD"})
                fig_gantt.update_yaxes(autorange="reversed", visible=False)
                fig_gantt.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#E8E2D2',
                    xaxis_tickformat='%H:%M', height=300, margin=dict(l=0, r=0, t=30, b=0)
                )
                st.plotly_chart(fig_gantt, use_container_width=True)

        with m_tab:
            map_pts = [{"x": 0, "y": 0, "name": "エントランス", "area": "エントランス", "color": "#ffffff"}]
            for i in timeline:
                if i['type'] == 'Ride' and i['name'] in MASTER_DB:
                    data = MASTER_DB[i['name']]
                    map_pts.append({"x": data['pos'][0], "y": data['pos'][1], "name": i['name'], 
                                    "area": AREA_INFO[data['area']]['name'], "color": AREA_INFO[data['area']]['color']})
            
            df_map = pd.DataFrame(map_pts)
            fig_map = px.scatter(df_map, x='x', y='y', text='name', color='area',
                                color_discrete_map={row['area']: row['color'] for _, row in df_map.iterrows()})
            
            # 移動線(ルート)を描画
            fig_map.add_trace(go.Scatter(x=df_map['x'], y=df_map['y'], mode='lines', 
                                         line=dict(color='rgba(184, 134, 11, 0.6)', width=3, dash='dot'), showlegend=False))
            fig_map.update_traces(marker=dict(size=18, line=dict(width=2, color='#001529')), textposition='top center', textfont=dict(color='#E8E2D2', size=11))
            fig_map.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,21,41,0.5)', font_color='#E8E2D2',
                xaxis=dict(visible=False), yaxis=dict(visible=False), 
                title=dict(text="戦術展開ルートマップ", font=dict(color="#B8860B")),
                height=600, margin=dict(l=0, r=0, t=50, b=0)
            )
            st.plotly_chart(fig_map, use_container_width=True)

if __name__ == "__main__":
    main()