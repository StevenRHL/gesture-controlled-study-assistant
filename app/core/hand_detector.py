import cv2
import mediapipe as mp


class HandDetector:
    def __init__(
        self,
        max_num_hands=2,
        detection_confidence=0.7,
        tracking_confidence=0.7
    ):
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_styles = mp.solutions.drawing_styles

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence
        )

    def detect_hands(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        return results

    def draw_landmarks(self, frame, results):
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_styles.get_default_hand_landmarks_style(),
                    self.mp_styles.get_default_hand_connections_style()
                )

        return frame

    def get_all_hand_positions(self, frame, results):
        """
        Returns a list like this:

        [
            {
                "label": "Left",
                "landmarks": [
                    {"id": 0, "x": 320, "y": 400, "z": -0.01},
                    ...
                ]
            },
            {
                "label": "Right",
                "landmarks": [
                    {"id": 0, "x": 500, "y": 410, "z": -0.02},
                    ...
                ]
            }
        ]
        """

        hands_data = []

        height, width, _ = frame.shape

        if not results.multi_hand_landmarks:
            return hands_data

        for index, hand_landmarks in enumerate(results.multi_hand_landmarks):
            label = "Unknown"

            if results.multi_handedness:
                label = results.multi_handedness[index].classification[0].label

            landmark_positions = []

            for landmark_id, landmark in enumerate(hand_landmarks.landmark):
                x = int(landmark.x * width)
                y = int(landmark.y * height)
                z = landmark.z

                landmark_positions.append({
                    "id": landmark_id,
                    "x": x,
                    "y": y,
                    "z": z
                })

            hands_data.append({
                "label": label,
                "landmarks": landmark_positions
            })

        return hands_data

    def close(self):
        self.hands.close()