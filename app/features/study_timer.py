import time


class StudyTimer:
    def __init__(self, study_minutes=0.2):
        self.study_seconds = study_minutes * 60
        self.remaining_seconds = self.study_seconds

        self.is_running = False
        self.is_finished = False

        self.start_time = None
        self.paused_at = None

    def start(self):
        if not self.is_running and not self.is_finished:
            self.is_running = True
            self.start_time = time.time()
            print("Timer started.")

    def pause(self):
        if self.is_running:
            elapsed = time.time() - self.start_time
            self.remaining_seconds -= int(elapsed)

            if self.remaining_seconds < 0:
                self.remaining_seconds = 0

            self.is_running = False
            self.paused_at = time.time()
            print("Timer paused.")

    def resume(self):
        if not self.is_running and not self.is_finished and self.remaining_seconds > 0:
            self.is_running = True
            self.start_time = time.time()
            print("Timer resumed.")

    def stop(self):
        self.is_running = False
        self.is_finished = True
        self.remaining_seconds = 0
        print("Timer stopped.")

    def reset(self):
        self.remaining_seconds = self.study_seconds
        self.is_running = False
        self.is_finished = False
        self.start_time = None
        self.paused_at = None
        print("Timer reset.")

    def update(self):
        if self.is_running:
            elapsed = time.time() - self.start_time
            current_remaining = self.remaining_seconds - int(elapsed)

            if current_remaining <= 0:
                self.remaining_seconds = 0
                self.is_running = False
                self.is_finished = True
                print("Study session finished.")
                return 0

            return current_remaining

        return self.remaining_seconds

    def get_display_time(self):
        current_seconds = self.update()

        minutes = current_seconds // 60
        seconds = current_seconds % 60

        return f"{minutes:02d}:{seconds:02d}"

    def get_status(self):
        if self.is_finished:
            return "finished"

        if self.is_running:
            return "running"

        if self.remaining_seconds < self.study_seconds:
            return "paused"

        return "ready"