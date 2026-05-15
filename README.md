# VSC Hand Study Assistant

VSC Hand Study Assistant is a Python desktop application that uses computer vision and hand gesture recognition to control a study timer. The project combines OpenCV, MediaPipe, and a Tkinter-based interface to create a hands-free productivity tool.

## Features

- Real-time hand tracking using MediaPipe
- Gesture-based timer controls
- Confirmation system using a second-hand gesture to prevent accidental actions
- Study session tracking
- Planned CSV database for storing completed study sessions
- Desktop UI with camera preview and timer controls

## Tech Stack

- Python
- OpenCV
- MediaPipe
- Tkinter
- CSV for lightweight local storage

## Project Purpose

This project was built to explore human-computer interaction using computer vision. The goal is to create a study assistant where users can start, pause, resume, and stop study sessions using hand gestures instead of keyboard or mouse input.

## How It Works

The webcam captures real-time video frames using OpenCV. MediaPipe detects hand landmarks from the camera feed. These landmarks are processed to identify gestures such as an open hand or closed fist. The application then maps those gestures to timer actions.

To reduce accidental inputs, the system uses a confirmation step before starting, pausing, continuing, stopping, or resetting the timer.

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/vsc-hand-study-assistant.git
cd vsc-hand-study-assistant
```
