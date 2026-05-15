import math


class GestureClassifier:
    def __init__(self):
        pass

    def classify(self, landmarks):
        if not landmarks or len(landmarks) < 21:
            return "no_hand"

        fingers = self._get_finger_states(landmarks)

        thumb_open = fingers["thumb"]
        index_open = fingers["index"]
        middle_open = fingers["middle"]
        ring_open = fingers["ring"]
        pinky_open = fingers["pinky"]

        open_count = sum([
            thumb_open,
            index_open,
            middle_open,
            ring_open,
            pinky_open
        ])

        if open_count >= 4:
            return "open_palm"

        if open_count <= 1:
            return "fist"

        if index_open and middle_open and not ring_open and not pinky_open:
            return "peace"

        if index_open and not middle_open and not ring_open and not pinky_open:
            return "pointing"

        return "unknown"

    def _distance(self, point_a, point_b):
        return math.sqrt(
            (point_a["x"] - point_b["x"]) ** 2 +
            (point_a["y"] - point_b["y"]) ** 2
        )

    def _get_finger_states(self, landmarks):
        wrist = landmarks[0]

        thumb_tip = landmarks[4]
        thumb_mcp = landmarks[2]

        index_tip = landmarks[8]
        index_pip = landmarks[6]

        middle_tip = landmarks[12]
        middle_pip = landmarks[10]

        ring_tip = landmarks[16]
        ring_pip = landmarks[14]

        pinky_tip = landmarks[20]
        pinky_pip = landmarks[18]

        palm_size = self._distance(wrist, landmarks[9])

        if palm_size == 0:
            palm_size = 1

        thumb_open = self._distance(wrist, thumb_tip) > self._distance(wrist, thumb_mcp) + palm_size * 0.15

        index_open = self._distance(wrist, index_tip) > self._distance(wrist, index_pip) + palm_size * 0.20

        middle_open = self._distance(wrist, middle_tip) > self._distance(wrist, middle_pip) + palm_size * 0.20

        ring_open = self._distance(wrist, ring_tip) > self._distance(wrist, ring_pip) + palm_size * 0.20

        pinky_open = self._distance(wrist, pinky_tip) > self._distance(wrist, pinky_pip) + palm_size * 0.20

        return {
            "thumb": thumb_open,
            "index": index_open,
            "middle": middle_open,
            "ring": ring_open,
            "pinky": pinky_open,
        }