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
    時刻 $t$ におけるアトラクション $i$ の待ち時間を $w(i, t) = f_i(x_t)$ として定式化。
    $x_t$ は曜日、天候、および開園からの経過時間を含む特徴量ベクトル。
    """
    def __init__(self):
        self.models = {}
        self.attractions = ['スプラッシュ・マウンテン', 'スペース・マウンテン', 'ビッグサンダー・マウンテン', '美女と野獣', 'プーさんのハニーハント']
        self._train_dummy_models()

    def _train_dummy_models(self):
        np.random.seed(42)
        for attr in self.attractions:
            X = pd.DataFrame({
                'weekday': np.random.randint(0, 7, 1000),
                'is_holiday': np.random.randint(0, 2, 1000),
                'rain_prob': np.random.randint(0, 100, 1000),
                'max_temp': np.random.uniform(5, 35, 1000),
                'elapsed_mins': np.random.randint(0, 600, 1000)
            })
            
            # アトラクションごとに異なるピーク特性（正弦波などで擬似表現）
            base_wait = 30 + np.random.rand(1000) * 20
            phase_shift = np.random.randint(-60, 60)
            time_effect = 40 * np.sin(np.pi * (X['elapsed_mins'] + phase_shift) / 600)
            y = base_wait + time_effect + (X['is_holiday'] * 30) - (X['rain_prob'] * 0.2)
            y = np.maximum(5, y)
            
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
    """
    数理的処理:
    時間枠付きオリエンテーリング問題 (Orienteering Problem with Time Windows)。
    
    目的関数:
    $$ \max_{R \subseteq A} \frac{\sum_{i \in R} u_i}{\sum_{i \in R} (c(i-1, i) + w(i, t_i) + d_i) + \text{Idle Time}} $$
    $u_i$: アトラクション $i$ の満足度 (Utility)
    $c(i, j)$: Manhattan距離に基づく移動時間
    $w(i, t_i)$: 到着時刻 $t_i$ における予測待ち時間
    
    制約条件:
    1. 総所要時間 $\le$ 滞在可能時間
    2. 固定イベント（パレード等）の時間枠 $[e_{start}, e_{end}]$ と体験時間が重複しないこと
    """
    def __init__(self, predictor):
        self.predictor = predictor
        self.ride_duration = 5
        
        # 2. リアルな移動時間モデル (簡易座標系 X, Y)
        self.coords = {
            'エントランス': (0, 0),
            'スプラッシュ・マウンテン': (-15, 25),
            'スペース・マウンテン': (20, 10),
            'ビッグサンダー・マウンテン': (-20, 15),
            '美女と野獣': (15, 20),
            'プーさんのハニーハント': (5, 30)
        }
        self.speed_multipliers = {'ゆっくり': 1.5, '普通': 1.0, '急ぎ': 0.7}

    def get_travel_time(self, attr_from, attr_to, speed_mode):
        x1, y1 = self.coords[attr_from]
        x2, y2 = self.coords[attr_to]
        # マンハッタン距離
        distance = abs(x1 - x2) + abs(y1 - y2)
        # 距離1あたり0.5分とし、歩行速度係数を掛ける
        return int(distance * 0.5 * self.speed_multipliers[speed_mode])

    def optimize(self, target_attrs, utilities, max_mins, conditions, speed_mode, fixed_events):
        best_route = None
        best_timeline = []
        best_efficiency = -1.0
        best_total_time = 0

        # アトラクションの部分集合（全選択から1つまで）を探索 (Orienteering)
        for r in range(len(target_attrs), 0, -1):
            for subset in itertools.combinations(target_attrs, r):
                # 順列全探索
                for route_candidate in itertools.permutations(subset):
                    current_elapsed = 0
                    current_loc = 'エントランス'
                    timeline = []
                    total_utility = sum([utilities[attr] for attr in route_candidate])
                    is_valid = True
                    
                    # 固定イベントのコピー（消化フラグ用）
                    pending_events = sorted(fixed_events, key=lambda x: x['start'])

                    for attr in route_candidate:
                        travel_t = self.get_travel_time(current_loc, attr, speed_mode)
                        arrival_t = current_elapsed + travel_t
                        wait_t = self.predictor.predict(attr, conditions, arrival_t)
                        expected_finish = arrival_t + wait_t + self.ride_duration
                        
                        # 3. スケジュール調整機能 (固定イベントの回避)
                        for ev in pending_events:
                            ev_end = ev['start'] + ev['duration']
                            # 移動・待ち・体験中にイベントが被る場合
                            if not (expected_finish <= ev['start'] or arrival_t >= ev_end):
                                # イベント終了後まで待機（Idle Time）
                                idle_time = ev_end - current_elapsed
                                timeline.append({
                                    'attraction': f"✨ {ev['name']} (固定予定)",
                                    'arrival_mins': current_elapsed,
                                    'wait_time': 0,
                                    'duration': idle_time,
                                    'type': 'event'
                                })
                                current_elapsed = ev_end
                                pending_events.remove(ev)
                                
                                # 時刻が変わったので到着と待ち時間を再計算
                                arrival_t = current_elapsed + self.get_travel_time(current_loc, attr, speed_mode)
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
                            'type': 'ride'
                        })
                        
                        current_elapsed = expected_finish
                        current_loc = attr

                    if is_valid:
                        # 1. 満足度（Utility）最大化ロジック
                        efficiency = total_utility / current_elapsed if current_elapsed > 0 else 0
                        if efficiency > best_efficiency:
                            best_efficiency = efficiency
                            best_route = route_candidate
                            best_timeline = timeline
                            best_total_time = current_elapsed

            # もしこの部分集合のサイズ（例：全部回る）で解が見つかれば、それが最大効率とみなして探索終了
            if best_route is not None:
                break

        return best_route, best_total_time, best_timeline, best_efficiency

# ==========================================
# 3. UI & Simulation (Streamlit)
# ==========================================
def main():
    st.set_page_config(page_title="Advanced Theme Park Optimizer", layout="wide")
    st.title("🎢 AI 次世代ルート最適化 & 混雑回避シミュレーター")
    st.markdown("時間枠制約付きオリエンテーリング問題 (OPTW) のアルゴリズムを応用し、**「最も満足度が高く、かつ混雑ピークを賢く避けるルート」**を計算します。")

    if 'predictor' not in st.session_state:
        st.session_state.predictor = WaitTimePredictor()
        st.session_state.optimizer = RouteOptimizer(st.session_state.predictor)

    predictor = st.session_state.predictor
    optimizer = st.session_state.optimizer

    # --- サイドバー ---
    st.sidebar.header("1. アトラクション & 満足度設定")
    selected_attrs = st.sidebar.multiselect("候補を選択", predictor.attractions, default=predictor.attractions[:4])
    
    utilities = {}
    if selected_attrs:
        st.sidebar.markdown("**乗りたい度 (1-5)**")
        for attr in selected_attrs:
            utilities[attr] = st.sidebar.slider(attr, 1, 5, 3, key=f"u_{attr}")

    st.sidebar.header("2. 移動 & 時間設定")
    speed_mode = st.sidebar.radio("歩行速度", ['ゆっくり', '普通', '急ぎ'], index=1)
    max_stay_hours = st.sidebar.slider("滞在予定時間 (時間)", 2, 12, 8)
    
    st.sidebar.header("3. 固定イベント (パレード等)")
    has_event = st.sidebar.checkbox("固定の予定を追加する")
    fixed_events = []
    if has_event:
        ev_name = st.sidebar.text_input("予定名", "エレクトリカルパレード")
        ev_start = st.sidebar.slider("開始時間 (開園からの経過分)", 0, max_stay_hours*60, 300)
        ev_dur = st.sidebar.slider("所要時間 (分)", 15, 90, 45)
        fixed_events.append({'name': ev_name, 'start': ev_start, 'duration': ev_dur})

    st.sidebar.header("4. 環境データ")
    conditions = {
        'weekday': st.sidebar.selectbox("曜日", [0, 1, 2, 3, 4, 5, 6], format_func=lambda x: ['月','火','水','木','金','土','日'][x]),
        'is_holiday': int(st.sidebar.checkbox("祝日フラグ", value=True)),
        'rain_prob': st.sidebar.slider("降雨確率 (%)", 0, 100, 10),
        'max_temp': st.sidebar.slider("最高気温 (℃)", 0, 40, 25)
    }

    # --- メイン画面 ---
    if st.button("🚀 最適ルート（満足度最大化）を計算", type="primary"):
        if not selected_attrs:
            st.warning("アトラクションを選択してください。")
            return

        with st.spinner('高度な数理最適化モデルを計算中...'):
            max_mins = max_stay_hours * 60
            route, total_time, timeline, efficiency = optimizer.optimize(
                selected_attrs, utilities, max_mins, conditions, speed_mode, fixed_events
            )

        if not route:
            st.error("指定された条件では、どのアトラクションも体験できません。滞在時間を延ばすか、予定を変更してください。")
            return

        # 実行結果のサマリー
        st.subheader("✅ 最適化されたツアースケジュール")
        col1, col2, col3 = st.columns(3)
        total_utility = sum([utilities[a] for a in route])
        col1.metric("体験アトラクション数", f"{len(route)} / {len(selected_attrs)} 個")
        col2.metric("総所要時間", f"{total_time} 分")
        col3.metric("ルート効率スコア (Utility/Time)", f"{efficiency:.4f}")

        # タイムラインのデータフレーム化
        df_timeline = pd.DataFrame(timeline)
        df_timeline['時刻目安 (開園9:00想定)'] = df_timeline['arrival_mins'].apply(
            lambda x: (datetime.strptime("09:00", "%H:%M") + timedelta(minutes=int(x))).strftime("%H:%M")
        )
        display_df = df_timeline[['時刻目安 (開園9:00想定)', 'attraction', 'arrival_mins', 'wait_time']].rename(
            columns={'attraction': 'イベント/アトラクション', 'arrival_mins': '経過(分)', 'wait_time': '予測待ち時間(分)'}
        )
        st.table(display_df)

        # 4. 統計的な「混雑平準化」の可視化 (Plotly)
        st.subheader("📊 混雑回避の分析 (Peak Avoidance Analysis)")
        st.markdown("背景の曲線はパーク全体の平均待ち時間を示しています。AIが**混雑のピーク（山の頂上）を避けて**、待ち時間が落ち込むタイミング（谷）であなたを各アトラクションに誘導していることが確認できます。")

        # 背景の平均混雑カーブを取得
        bg_times, bg_waits = predictor.get_park_average_curve(conditions, max_mins)

        fig = go.Figure()

        # パーク平均混雑度（面グラフ）
        fig.add_trace(go.Scatter(
            x=bg_times, y=bg_waits, 
            fill='tozeroy', 
            mode='none', 
            name='パーク平均混雑度',
            fillcolor='rgba(200, 200, 200, 0.4)'
        ))

        # ユーザーの到着タイミング（散布図・バー）
        ride_events = df_timeline[df_timeline['type'] == 'ride']
        fig.add_trace(go.Scatter(
            x=ride_events['arrival_mins'], 
            y=ride_events['wait_time'],
            mode='markers+text',
            name='AI提案の到着地点',
            text=ride_events['attraction'],
            textposition="top center",
            marker=dict(size=12, color='red', line=dict(width=2, color='darkred'))
        ))

        # 固定イベントの帯を描画
        for ev in fixed_events:
            fig.add_vrect(
                x0=ev['start'], x1=ev['start']+ev['duration'], 
                fillcolor="orange", opacity=0.2, 
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