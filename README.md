# physical-ai-final-project
AI autonomous patrol robot using ROS 2 and Gazebo
### Overview
ROS 2 Humble、Gazebo、TurtleBot3 Burgerを使用したAI自律巡回・障害物回避ロボットです。

LiDARの距離情報を入力とし、k近傍法（k-NN）によって前進・左旋回・右旋回を推論します。また、障害物への接近時には安全制御が行動を補正します。

### Technologies
- ROS 2 Humble
- Gazebo Classic
- TurtleBot3 Burger
- Python 3
- k-Nearest Neighbors（独自実装）
- LiDAR（LaserScan）

### Files
- `ai_robot_v2.py`：AI推論・ロボット制御・CSV記録
- `ai_dashboard.py`：AI判断の可視化
- `sample_run.csv`：実験で取得した制御ログ

### How to Run

ROS 2 Humble、Gazebo Classic、およびTurtleBot3関連パッケージがインストールされ、ROS 2のトピック `/cmd_vel` と `/scan` が利用できる環境を前提とします。

**1. Gazebo起動**

```bash
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

**2. AI制御**

別のターミナルで実行します。

```bash
source /opt/ros/humble/setup.bash
python3 ai_robot_v2.py
```

**3. AI判断の可視化**

さらに別のターミナルで実行します。

```bash
python3 ai_dashboard.py
```

AI制御とダッシュボードは同一の作業ディレクトリ構成で実行してください。プログラムはホームディレクトリ直下の`physical_ai_final`フォルダをログ保存先として使用します。

### AI Method

センサー入力：
- 前方距離
- 左方向距離
- 右方向距離

推論結果：
- FORWARD：前進
- LEFT：左旋回
- RIGHT：右旋回

k-NNによる行動分類には、ルールから生成した125件の教師事例を使用しています。

### Experiment

Gazeboの障害物付きワールドにて、障害物回避を伴う自律走行を確認しました。

約70秒の走行実験を行い、351件の制御記録をCSVに保存しました。

### Limitations

現在の制御は局所的な障害物回避であり、地図作成、経路計画、目的地到達の保証は行いません。狭い通路や複雑な障害物配置では、立ち往生する可能性があります。

### Future Work

- 学習データの改善
- 自律経路計画の導入
- 回避成功率の定量評価
- 未知の障害物配置への対応強化
