class GestureState:
    
    def __init__(self, required_frames=8):
        self.required_frames = required_frames
        self.current_gesture = None
        self.last_stable_gesture = None
        self.counter = 0

    def update(self, detected_gesture):
        """
        Takes the raw detected gesture and returns a stable gesture.

        Example:
        Raw: open_palm, open_palm, open_palm, open_palm...
        Stable: open_palm

        Raw: open_palm, unknown, open_palm
        Stable: keeps previous stable gesture
        """

        if detected_gesture == self.current_gesture:
            self.counter += 1
        else:
            self.current_gesture = detected_gesture
            self.counter = 1

        if self.counter >= self.required_frames:
            self.last_stable_gesture = self.current_gesture

        return self.last_stable_gesture