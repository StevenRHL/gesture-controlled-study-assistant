import cv2

from app.core.camera import Camera
from app.core.hand_detector import HandDetector
from app.core.gesture_classifier import GestureClassifier
from app.core.gesture_state import GestureState
from app.core.confirmation_manager import ConfirmationManager
from app.features.study_timer import StudyTimer


def get_requested_action(right_gesture, study_timer):
    status = study_timer.get_status()

    if right_gesture == "open_palm":
        if status == "ready":
            return "start"

        if status == "paused":
            return "resume"

    if right_gesture == "fist":
        if status == "running":
            return "pause"

    if right_gesture == "peace":
        if status in ["running", "paused"]:
            return "stop"

    if right_gesture == "pointing":
        return "reset"

    return None


def run_confirmed_action(action, study_timer):
    if action == "start":
        study_timer.start()

    elif action == "resume":
        study_timer.resume()

    elif action == "pause":
        study_timer.pause()

    elif action == "stop":
        study_timer.stop()

    elif action == "reset":
        study_timer.reset()


def main():
    camera = Camera(camera_index=0)
    hand_detector = HandDetector(max_num_hands=2)
    gesture_classifier = GestureClassifier()

    left_state = GestureState(required_frames=8)
    right_state = GestureState(required_frames=8)

    confirmation_manager = ConfirmationManager(timeout_seconds=3)

    study_timer = StudyTimer(study_minutes=1)

    previous_requested_action = None
    previous_left_gesture = None

    try:
        camera.open()

        while True:
            frame = camera.read_frame()

            if frame is None:
                print("Failed to read frame from camera.")
                break

            frame = cv2.flip(frame, 1)

            results = hand_detector.detect_hands(frame)
            frame = hand_detector.draw_landmarks(frame, results)

            hands_data = hand_detector.get_all_hand_positions(frame, results)

            raw_left_gesture = "no_hand"
            raw_right_gesture = "no_hand"

            for hand in hands_data:
                label = hand["label"]
                landmarks = hand["landmarks"]

                gesture = gesture_classifier.classify(landmarks)

                # If left and right feel swapped, swap these two assignments.
                if label == "Left":
                    raw_left_gesture = gesture
                elif label == "Right":
                    raw_right_gesture = gesture

            stable_left_gesture = left_state.update(raw_left_gesture)
            stable_right_gesture = right_state.update(raw_right_gesture)

            confirmation_manager.update()

            requested_action = get_requested_action(
                stable_right_gesture,
                study_timer
            )

            if requested_action is not None:
                if requested_action != previous_requested_action:
                    confirmation_manager.request_action(requested_action)
                    previous_requested_action = requested_action

            if requested_action is None:
                previous_requested_action = None

            left_fist_just_happened = (
                stable_left_gesture == "fist"
                and previous_left_gesture != "fist"
            )

            if left_fist_just_happened and confirmation_manager.has_pending_action():
                confirmed_action = confirmation_manager.confirm()
                run_confirmed_action(confirmed_action, study_timer)
                previous_requested_action = None

            previous_left_gesture = stable_left_gesture

            timer_text = study_timer.get_display_time()
            timer_status = study_timer.get_status()
            confirm_message = confirmation_manager.get_message()

            cv2.putText(
                frame,
                f"Left Stable: {stable_left_gesture}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 0),
                2
            )

            cv2.putText(
                frame,
                f"Right Stable: {stable_right_gesture}",
                (20, 75),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 0),
                2
            )

            cv2.putText(
                frame,
                f"Timer: {timer_text}",
                (20, 130),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"Status: {timer_status}",
                (20, 175),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (255, 255, 255),
                2
            )

            if confirm_message is not None:
                cv2.rectangle(
                    frame,
                    (10, 215),
                    (frame.shape[1] - 10, 275),
                    (0, 0, 0),
                    -1
                )

                cv2.putText(
                    frame,
                    confirm_message,
                    (30, 255),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 255, 255),
                    2
                )

            cv2.putText(
                frame,
                "Right hand chooses action | Left fist confirms | Q=quit",
                (20, frame.shape[0] - 55),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (200, 200, 200),
                1
            )

            cv2.putText(
                frame,
                "Right open=start/resume | right fist=pause | peace=stop | point=reset",
                (20, frame.shape[0] - 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (200, 200, 200),
                1
            )

            cv2.imshow("Two-Hand Gesture Study Tool", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

    except RuntimeError as error:
        print(error)

    finally:
        camera.release()
        hand_detector.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()