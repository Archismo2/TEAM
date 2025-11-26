# MIT License
# Copyright (c) 2019-2022 JetsonHacks
# See LICENSE for OpenCV license and additional information

# https://docs.opencv.org/3.3.1/d7/d8b/tutorial_py_face_detection.html
# On the Jetson Nano, OpenCV comes preinstalled
# Data files are in /usr/sharc/OpenCV

import cv2
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

def gstreamer_pipeline(
    capture_width=1920,
    capture_height=1080,
    display_width=960,
    display_height=540,
    framerate=30,
    flip_method=0,
):
    return (
        "nvarguscamerasrc ! "
        "video/x-raw(memory:NVMM), "
        "width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink drop=True"
        % (
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

class RobotFollower(Node):
    def __init__(self):
        super().__init__('robot_follower')
        self.publisher = self.create_publisher(String, 'follower_cmd', 10)

    def send_cmd(self, msg):
        self.publisher.publish(String(data=msg))
        self.get_logger().info(f"Command: {msg}")


def object_track(follower_node):
    window_title = "Robot Tracker"

    # Load your custom trained cascade
    robot_cascade = cv2.CascadeClassifier(
        "/home/jetson/cascades/robot_cascade.xml"
    )

    video_capture = cv2.VideoCapture(gstreamer_pipeline(), cv2.CAP_GSTREAMER)

    if not video_capture.isOpened():
        print("Unable to open camera")
        return

    cv2.namedWindow(window_title, cv2.WINDOW_AUTOSIZE)

    while True:
        ret, frame = video_capture.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        robots = robot_cascade.detectMultiScale(gray, 1.3, 5)

        frame_h, frame_w = frame.shape[:2]
        left_region = frame_w // 3
        right_region = 2 * (frame_w // 3)

        robot_found = False

        for (x, y, w, h) in robots:
            robot_found = True
            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 255), 2)

            # Compute centroid
            cx = x + w // 2
            cy = y + h // 2
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

            # Decide navigation commands
            if cx < left_region:
                follower_node.send_cmd("turn_left")
            elif cx > right_region:
                follower_node.send_cmd("turn_right")
            else:
                follower_node.send_cmd("forward")

            break  # Track only first detection

        if not robot_found:
            follower_node.send_cmd("search")

        # Display regions for debugging
        cv2.line(frame, (left_region, 0), (left_region, frame_h), (255, 0, 0), 2)
        cv2.line(frame, (right_region, 0), (right_region, frame_h), (255, 0, 0), 2)

        if cv2.getWindowProperty(window_title, cv2.WND_PROP_AUTOSIZE) >= 0:
            cv2.imshow(window_title, frame)
        else:
            break

        keyCode = cv2.waitKey(10) & 0xFF
        if keyCode == 27 or keyCode == ord("q"):
            break

    video_capture.release()
    cv2.destroyAllWindows()


def main():
    rclpy.init()
    follower_node = RobotFollower()

    try:
        object_track(follower_node)
    finally:
        follower_node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
