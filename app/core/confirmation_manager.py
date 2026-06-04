import time


class ConfirmationManager:
    def __init__(self, timeout_seconds=3):
        self.pending_action = None
        self.message = None
        self.created_at = None
        self.timeout_seconds = timeout_seconds

    def request_action(self, action):
        if action is None:
            return

        if self.pending_action == action:
            return

        self.pending_action = action
        self.message = f"Confirm {action.upper()} with left fist"
        self.created_at = time.time()

    def update(self):
        if self.pending_action is None:
            return

        elapsed = time.time() - self.created_at

        if elapsed > self.timeout_seconds:
            self.clear()

    def confirm(self):
        if self.pending_action is None:
            return None

        action = self.pending_action
        self.clear()
        return action

    def clear(self):
        self.pending_action = None
        self.message = None
        self.created_at = None

    def has_pending_action(self):
        return self.pending_action is not None

    def get_message(self):
        return self.message
