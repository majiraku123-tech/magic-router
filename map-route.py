import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import itertools
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ==========================================
# 1. Data Modeling & Prediction (待ち時間予測)
# ==========================================
class WaitTimePredictor:
    """
    数理的処理:
    ランダムフォレスト回帰を用いた非線形な待ち時間予測モデル。
    """
    def __init__(self, attractions):
        self.models = {}
        self.attractions = attractions
        self._train_dummy_models()

    def _train_dummy_models(self):
        np.random.seed(42)
        
        # アトラクションの特性グループ定義
        super_popular = ['ソアリン', 'アナとエルサのフローズンジャーニー', 'トイ・ストーリー・マニア！', 'ピーターパンのネバーランドアドベンチャー']
        fast_turnover = ['シンドバッド', '海底2万マイル', 'ヴェネツィアン・ゴンドラ', 'キャラバンカルーセル', 'ジャンピン・ジェリーフィッシュ', 'スカットルのスクーター', 'マジックランプシアター']
        fs_area = ['ラプンツェルのランタンフェスティバル', 'フェアリー・ティンカーベルのビジーバギー']
        
        for attr in self.attractions:
            X = pd.DataFrame({
                'weekday': np.random.randint(0, 7, 1000),
                'is_holiday': np.random.randint(0, 2, 1000),
                'rain_prob': np.random.randint(0, 100, 1000),
                'max_temp': np.random.uniform(5, 35, 1000),
                'elapsed_mins': np.random.randint(0, 600, 1000)
            })
            
            # TDS専用の混雑波形アルゴリズム
            if attr in super_popular:
                # 超人気: 開園直後から120分を超え、終日高い
                base_wait = 120 + np.random.rand(1000) * 40
                time_effect = -20 * np.sin(np.pi * X['elapsed_mins'] / 600) # 午後少し落ち着く程度
            elif attr in fast_turnover:
                # 回転の速い施設: 安定して30分以下
                base_wait = 10 + np.random.rand(1000) * 15
                time_effect = 5 * np.sin(np.pi * X['elapsed_mins'] / 600)
            elif attr in fs_area:
                # FSエリア（超人気以外）: 平均待ち時間を底上げ（60〜90分）
                base_wait = 70 + np.random.rand(1000) * 20
                time_effect = 10 * np.sin(np.pi * X['elapsed_mins'] / 600)
            else:
                # その他レギュラーアトラクション
                base_wait = 40 + np.random.rand(1000) * 30
                phase_shift = np.random.randint(-60, 60)
                time_effect = 30 * np.sin(np.pi * (X['elapsed_mins'] + phase_shift) / 600)
            
            y = base_wait + time_effect + (X['is_holiday'] * 20) - (X['rain_prob'] * 0.3)
            y = np.maximum(5, y) # 最低5分
            
            model = RandomForestRegressor(n_estimators=50, max_depth=5, random_state=42)
            model.fit(X, y)
            self.models[attr] = model

    def predict(self, attraction, conditions, elapsed_mins):
        features = pd.DataFrame([{**conditions, 'elapsed_mins': elapsed_mins}])
        return max(5, int(self.models[attraction].predict(features)[0]))
    
    def get_park_average_curve(self, conditions, max_mins):
        """パーク全体の平均的な混雑度推移（背景グラフ用）"""
        times = np.arange(0, max_mins, 15)
        avg_waits = []
        for t in times:
            waits = [self.predict(a, conditions, t) for a in self.attractions]
            avg_waits.append(np.mean(waits))
        return times, avg_waits

# ==========================================
# 2. Route Optimization Algorithm (ルート最適化)
# ==========================================
class RouteOptimizer:
    def __init__(self, predictor, coords):
        self.predictor = predictor
        self.coords = coords
        self.ride_duration = 10 # TDSは体験時間がやや長めの傾向
        self.speed_multipliers = {'ゆっくり': 1.5, '普通': 1.0, '急ぎ': 0.7}

    def get_travel_time(self, attr_from, attr_to, speed_mode):
        x1, y1 = self.coords[attr_from]
        x2, y2 = self.coords[attr_to]
        distance = abs(x1 - x2) + abs(y1 - y2)
        return int(distance * 0.5 * self.speed_multipliers[speed_mode])

    def optimize(self, target_attrs, utilities, use_dpa, max_mins, conditions, speed_mode, fixed_events):
        best_route = None
        best_timeline = []
        best_efficiency = -1.0
        best_total_time = 0

        # Orienteering Problem: 部分集合から探索
        for r in range(len(target_attrs), 0, -1):
            for subset in itertools.combinations(target_attrs, r):
                for route_candidate in itertools.permutations(subset):
                    current_elapsed = 0
                    current_loc = 'エントランス'
                    timeline = []
                    total_utility = sum([utilities[attr] for attr in route_candidate])
                    is_valid = True
                    
                    pending_events = sorted(fixed_events, key=lambda x: x['start'])

                    for attr in route_candidate:
                        travel_t = self.get_travel_time(current_loc, attr, speed_mode)
                        arrival_t = current_elapsed + travel_t
                        
                        # DPA/優先パスの適用判定
                        if use_dpa.get(attr, False):
                            wait_t = 10
                        else:
                            wait_t = self.predictor.predict(attr, conditions, arrival_t)
                            
                        expected_finish = arrival_t + wait_t + self.ride_duration
                        
                        # スケジュール調整機能 (固定イベントの回避)
                        for ev in pending_events:
                            ev_end = ev['start'] + ev['duration']
                            if not (expected_finish <= ev['start'] or arrival_t >= ev_end):
                                idle_time = ev_end - current_elapsed
                                timeline.append({
                                    'attraction': f"✨ {ev['name']} (固定予定)",
                                    'arrival_mins': current_elapsed,
                                    'wait_time': 0,
                                    'duration': idle_time,
                                    'type': 'event',
                                    'dpa_used': False
                                })
                                current_elapsed = ev_end
                                pending_events.remove(ev)
                                
                                # 時刻が変わったので到着と待ち時間を再計算
                                arrival_t = current_elapsed + self.get_travel_time(current_loc, attr, speed_mode)
                                if use_dpa.get(attr, False):
                                    wait_t = 10
                                else:
                                    wait_t = self.predictor.predict(attr, conditions, arrival_t)
                                expected_finish = arrival_t + wait_t + self.ride_duration
                                break
                        
                        if expected_finish > max_mins:
                            is_valid = False
                            break
                            
                        timeline.append({
                            'attraction': attr,
                            'arrival_mins': arrival_t,
                            'wait_time': wait_t,
                            'duration': self.ride_duration,
                            'type': 'ride',
                            'dpa_used': use_dpa.get(attr, False)
                        })
                        
                        current_elapsed = expected_finish
                        current_loc = attr

                    if is_valid:
                        efficiency = total_utility / current_elapsed if current_elapsed > 0 else 0
                        if efficiency > best_efficiency:
                            best_efficiency = efficiency
                            best_route = route_candidate
                            best_timeline = timeline
                            best_total_time = current_elapsed

            if best_route is not None:
                break

        return best_route, best_total_time, best_timeline, best_efficiency

# ==========================================
# 3. UI & Simulation (Streamlit)
# ==========================================
def main():
    st.set_page_config(page_title="TDS Route Optimizer", layout="wide")
    
    # 4. デザインの「シー化」 (CSS)
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #e0f7fa 0%, #80deea 50%, #4dd0e1 100%);
    }
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown {
        color: #001529 !important;
    }
    .stButton>button {
        background-color: #001529 !important;
        color: #D4AF37 !important;
        border: 2px solid #D4AF37 !important;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #D4AF37 !important;
        color: #001529 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("🌋 TDS 次世代ルート最適化 & 混雑回避シミュレーター")
    st.markdown("時間枠制約付きオリエンテーリング問題 (OPTW) を応用し、**東京ディズニーシー**の地形とアトラクション特性に合わせた最適ルートを算出します。")

    # 1. アトラクションと座標の完全網羅
    coords = {
        'エントランス': (0, 0),
        # メディテレーニアンハーバー
        'ソアリン': (10, 10),
        'ヴェネツィアン・ゴンドラ': (5, 5),
        # アメリカンウォーターフロント
        'トイ・ストーリー・マニア！': (5, 20),
        'タワー・オブ・テラー': (10, 15),
        'タートル・トーク': (15, 15),
        # ポートディスカバリー
        'ニモ＆フレンズ・シーライダー': (-10, 30),
        'アクアトピア': (-15, 30),
        # ロストリバーデルタ
        'インディ・ジョーンズ': (-20, 45),
        'レイジングスピリッツ': (-15, 45),
        # アラビアンコースト
        'マジックランプシアター': (5, 50),
        'キャラバンカルーセル': (10, 50),
        'シンドバッド': (15, 55),
        # マーメイドラグーン
        'ジャンピン・ジェリーフィッシュ': (25, 40),
        'スカットルのスクーター': (20, 35),
        # ミステリアスアイランド
        'センター・オブ・ジ・アース': (0, 30),
        '海底2万マイル': (5, 25),
        # ファンタジースプリングス
        'アナとエルサのフローズンジャーニー': (30, 65),
        'ラプンツェルのランタンフェスティバル': (35, 60),
        'ピーターパンのネバーランドアドベンチャー': (40, 65),
        'フェアリー・ティンカーベルのビジーバギー': (45, 60)
    }
    attractions_list = [a for a in coords.keys() if a != 'エントランス']

    if 'predictor' not in st.session_state:
        st.session_state.predictor = WaitTimePredictor(attractions_list)
        st.session_state.optimizer = RouteOptimizer(st.session_state.predictor, coords)

    predictor = st.session_state.predictor
    optimizer = st.session_state.optimizer

    # --- サイドバー ---
    st.sidebar.header("1. アトラクション & 満足度設定")
    default_attrs = ['ソアリン', 'センター・オブ・ジ・アース', 'トイ・ストーリー・マニア！', 'アナとエルサのフローズンジャーニー']
    selected_attrs = st.sidebar.multiselect("候補を選択 (計算負荷のため4〜6個推奨)", attractions_list, default=default_attrs)
    
    utilities = {}
    use_dpa = {}
    if selected_attrs:
        st.sidebar.markdown("---")
        for attr in selected_attrs:
            st.sidebar.markdown(f"**{attr}**")
            col_u, col_d = st.sidebar.columns([3, 2])
            with col_u:
                utilities[attr] = st.slider("乗りたい度", 1, 5, 3, key=f"u_{attr}")
            with col_d:
                # 2. DPA / プライオリティパス機能の実装
                use_dpa[attr] = st.checkbox("DPA/優先パス", key=f"dpa_{attr}")

    st.sidebar.header("2. 移動 & 時間設定")
    speed_mode = st.sidebar.radio("歩行速度", ['ゆっくり', '普通', '急ぎ'], index=1)
    max_stay_hours = st.sidebar.slider("滞在予定時間 (時間)", 2, 14, 10)
    
    st.sidebar.header("3. 固定イベント (ショー等)")
    has_event = st.sidebar.checkbox("固定の予定を追加する")
    fixed_events = []
    if has_event:
        ev_name = st.sidebar.text_input("予定名", "ビリーヴ！～シー・オブ・ドリームス～")
        ev_start = st.sidebar.slider("開始時間 (開園からの経過分)", 0, max_stay_hours*60, 600)
        ev_dur = st.sidebar.slider("所要時間 (分)", 15, 90, 30)
        fixed_events.append({'name': ev_name, 'start': ev_start, 'duration': ev_dur})

    st.sidebar.header("4. 環境データ")
    conditions = {
        'weekday': st.sidebar.selectbox("曜日", [0, 1, 2, 3, 4, 5, 6], format_func=lambda x: ['月','火','水','木','金','土','日'][x]),
        'is_holiday': int(st.sidebar.checkbox("休祝日フラグ", value=True)),
        'rain_prob': st.sidebar.slider("降雨確率 (%)", 0, 100, 10),
        'max_temp': st.sidebar.slider("最高気温 (℃)", 0, 40, 25)
    }

    # --- メイン画面 ---
    if st.button("🚢 最適ルート（満足度最大化）を計算", type="primary"):
        if not selected_attrs:
            st.warning("アトラクションを選択してください。")
            return
        if len(selected_attrs) > 8:
            st.warning("選択数が多すぎると計算に時間がかかる場合があります（順列全探索アルゴリズムのため）。")

        with st.spinner('TDSの複雑な地形と予測混雑波形を計算中...'):
            max_mins = max_stay_hours * 60
            route, total_time, timeline, efficiency = optimizer.optimize(
                selected_attrs, utilities, use_dpa, max_mins, conditions, speed_mode, fixed_events
            )

        if not route:
            st.error("指定された条件では、どのアトラクションも体験できません。滞在時間を延ばすか、予定を変更してください。")
            return

        st.subheader("✅ 最適化された航海スケジュール")
        col1, col2, col3 = st.columns(3)
        col1.metric("体験アトラクション数", f"{len(route)} / {len(selected_attrs)} 個")
        col2.metric("総所要時間", f"{total_time} 分")
        col3.metric("ルート効率スコア", f"{efficiency:.4f}")

        # タイムラインのデータフレーム化
        df_timeline = pd.DataFrame(timeline)
        df_timeline['時刻目安 (開園9:00想定)'] = df_timeline['arrival_mins'].apply(
            lambda x: (datetime.strptime("09:00", "%H:%M") + timedelta(minutes=int(x))).strftime("%H:%M")
        )
        
        # DPAバッジの追加
        df_timeline['アトラクション'] = df_timeline.apply(
            lambda row: f"{row['attraction']} 🎟️(DPA/優先)" if row.get('dpa_used', False) else row['attraction'], axis=1
        )
        
        display_df = df_timeline[['時刻目安 (開園9:00想定)', 'アトラクション', 'arrival_mins', 'wait_time']].rename(
            columns={'arrival_mins': '経過(分)', 'wait_time': '予測待ち時間(分)'}
        )
        st.table(display_df)

        # 4. 統計的な「混雑平準化」の可視化 (Plotly)
        st.subheader("📊 混雑回避の分析 (Peak Avoidance Analysis)")
        st.markdown("背景の曲線はパーク全体の平均待ち時間を示しています。AIが**ピークを避けて（谷を縫うように）**あなたを案内したのか、DPAの強力な時短効果（10分への短縮）がどう発揮されたかを確認できます。")

        bg_times, bg_waits = predictor.get_park_average_curve(conditions, max_mins)
        fig = go.Figure()

        # パーク平均混雑度（面グラフ）
        fig.add_trace(go.Scatter(
            x=bg_times, y=bg_waits, 
            fill='tozeroy', 
            mode='none', 
            name='パーク平均混雑度',
            fillcolor='rgba(0, 21, 41, 0.2)' # シーの色に合わせる
        ))

        # ユーザーの到着タイミング（散布図・バー）
        ride_events = df_timeline[df_timeline['type'] == 'ride']
        
        # 通常利用のマーカー
        normal_rides = ride_events[~ride_events['dpa_used']]
        if not normal_rides.empty:
            fig.add_trace(go.Scatter(
                x=normal_rides['arrival_mins'], 
                y=normal_rides['wait_time'],
                mode='markers+text',
                name='通常ラインの到着',
                text=normal_rides['attraction'],
                textposition="top center",
                marker=dict(size=12, color='#001529', line=dict(width=2, color='#D4AF37'))
            ))

        # DPA利用のマーカー
        dpa_rides = ride_events[ride_events['dpa_used']]
        if not dpa_rides.empty:
            fig.add_trace(go.Scatter(
                x=dpa_rides['arrival_mins'], 
                y=dpa_rides['wait_time'],
                mode='markers+text',
                name='🎟️ DPA/優先パス利用',
                text=dpa_rides['attraction'],
                textposition="bottom center",
                marker=dict(size=14, symbol='star', color='#D4AF37', line=dict(width=1, color='#001529'))
            ))

        # 固定イベントの帯を描画
        for ev in fixed_events:
            fig.add_vrect(
                x0=ev['start'], x1=ev['start']+ev['duration'], 
                fillcolor="#4dd0e1", opacity=0.3, 
                layer="below", line_width=0,
                annotation_text=ev['name'], annotation_position="top left"
            )

        fig.update_layout(
            xaxis_title="開園からの経過時間 (分)",
            yaxis_title="待ち時間 (分)",
            hovermode="x unified",
            height=500,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()