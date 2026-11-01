#!/usr/bin/env python3

import csv
import math
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan


class KNNPolicy:
    """教師事例に基づいて行動を分類するAI"""

    def __init__(self, k=3):
        self.k = k
        self.samples = []

        values = [0.25, 0.5, 1.0, 2.0, 3.5]

        for front in values:
            for left in values:
                for right in values:
                    if front >= 1.0:
                        label = "FORWARD"
                    elif left >= right:
                        label = "LEFT"
                    else:
                        label = "RIGHT"

                    self.samples.append(
                        ((front, left, right), label)
                    )

    def predict(self, observation):
        ranked = []

        for features, label in self.samples:
            distance = sum(
                (a - b) ** 2
                for a, b in zip(features, observation)
            )
            ranked.append((distance, label))

        ranked.sort(key=lambda item: item[0])

        votes = [
            label for _, label in ranked[:self.k]
        ]

        return Counter(votes).most_common(1)[0][0]


class AIPatrol(Node):

    def __init__(self):
        super().__init__("ai_patrol_v2")

        self.cmd_pub = self.create_publisher(
            Twist, "/cmd_vel", 10
        )

        self.create_subscription(
            LaserScan, "/scan", self.scan_callback, 10
        )

        self.policy = KNNPolicy()
        self.observation = None
        self.last_scan = None
        self.start_time = None
        self.finished = False
        self.counts = Counter()

        output_dir = Path.home() / "physical_ai_final"
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = (
            "run_" +
            datetime.now().strftime("%Y%m%d_%H%M%S") +
            ".csv"
        )

        self.csv_path = output_dir / filename
        self.csv_file = open(
            self.csv_path, "w", newline=""
        )
        self.writer = csv.writer(self.csv_file)

        self.writer.writerow([
            "time_sec",
            "front_m",
            "left_m",
            "right_m",
            "ai_decision",
            "executed_action",
            "safety_override"
        ])

        self.timer = self.create_timer(
            0.2, self.control_loop
        )

        self.get_logger().info(
            "AI PATROL V2 START"
        )
        self.get_logger().info(
            f"CSV: {self.csv_path}"
        )

    def scan_callback(self, msg):

        def sector(center_deg, width_deg=20):
            distances = []

            for i, value in enumerate(msg.ranges):
                angle = math.degrees(
                    msg.angle_min +
                    i * msg.angle_increment
                )

                difference = (
                    (angle - center_deg + 180) % 360
                ) - 180

                if abs(difference) > width_deg:
                    continue

                if math.isinf(value) and value > 0:
                    distances.append(msg.range_max)

                elif (
                    math.isfinite(value)
                    and msg.range_min <= value <= msg.range_max
                ):
                    distances.append(value)

            return (
                min(min(distances), 3.5)
                if distances else None
            )

        front = sector(0, 25)
        left = sector(60, 20)
        right = sector(-60, 20)

        self.last_scan = time.monotonic()

        if None in (front, left, right):
            self.observation = None
        else:
            self.observation = (
                front, left, right
            )

    def publish_stop(self):
        self.cmd_pub.publish(Twist())

    def control_loop(self):
        if self.finished:
            return

        command = Twist()
        now = time.monotonic()

        # センサー未受信または受信停止
        if (
            self.observation is None
            or self.last_scan is None
            or now - self.last_scan > 1.0
        ):
            self.publish_stop()
            self.get_logger().warn(
                "LiDAR unavailable: STOP"
            )
            return

        # 初めて有効なセンサー値を受信した時点から計測
        if self.start_time is None:
            self.start_time = now

        elapsed = now - self.start_time

        if elapsed >= 70:
            self.finished = True
            self.publish_stop()
            self.timer.cancel()
            self.get_logger().info(
                f"TASK COMPLETED: {dict(self.counts)}"
            )
            self.get_logger().info(
                f"CSV saved: {self.csv_path}"
            )
            self.csv_file.flush()
            return

        front, left, right = self.observation

        # AIモデルによる行動推論
        ai_action = self.policy.predict(
            (front, left, right)
        )

        action = ai_action
        safety_override = False

        # 安全制御：危険な場合はAI判断を補正
        if front < 0.75 and action == "FORWARD":
            action = (
                "LEFT" if left >= right else "RIGHT"
            )
            safety_override = True

        if front < 0.35:
            safe_action = (
                "LEFT" if left >= right else "RIGHT"
            )
            if action != safe_action:
                safety_override = True
            action = safe_action

        if action == "FORWARD":
            command.linear.x = 0.12

        elif action == "LEFT":
            command.angular.z = 0.6

        elif action == "RIGHT":
            command.angular.z = -0.6

        self.cmd_pub.publish(command)
        self.counts[action] += 1

        self.writer.writerow([
            round(elapsed, 2),
            round(front, 3),
            round(left, 3),
            round(right, 3),
            ai_action,
            action,
            int(safety_override)
        ])
        self.csv_file.flush()

        self.get_logger().info(
            f"F={front:.2f} "
            f"L={left:.2f} "
            f"R={right:.2f} "
            f"AI={ai_action} "
            f"EXEC={action} "
            f"SAFETY={int(safety_override)}"
        )

    def close(self):
        self.publish_stop()

        if not self.csv_file.closed:
            self.csv_file.flush()
            self.csv_file.close()

        self.get_logger().info(
            "CSV file closed successfully"
        )

def main():
    rclpy.init()
    robot = AIPatrol()

    try:
        while rclpy.ok() and not robot.finished:
            rclpy.spin_once(
                robot,
                timeout_sec=0.2
            )

    except KeyboardInterrupt:
        robot.get_logger().info(
            "Stopped by user"
        )

    finally:
        robot.close()
        robot.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()

    print("PROGRAM FINISHED")

if __name__ == "__main__":
    main()
