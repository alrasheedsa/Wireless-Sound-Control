# AI-Powered Gesture & Face Recognition Control System

A high-performance **Full-Stack AI** application that integrates **Computer Vision** with a web backend. This system enables secure, touchless control of Windows system volume using hand gestures, authenticated by real-time facial recognition.

## 🚀 Key Technical Features
* **Multi-Modal AI Logic**: Combines `MediaPipe` for hand landmark tracking and `face_recognition` for identity verification.
* **Identity-Based Control**: Implemented a security layer where the system only responds to gestures if a pre-registered "Authorized User" is detected in the frame.
* **Real-time System Integration**: Direct control of Windows Master Volume via the `PyCaw` library, mapping finger distance to volume percentages.
* **Dynamic Web Interface**: Real-time video streaming and data updates (Volume/Authorization status) powered by **WebSockets (Socket.io)**.
* **Secure Backend**: Stateless authentication using **JWT Tokens** and encrypted password management via `Werkzeug`.
* **Database Management**: Automated logging of volume control history and facial encoding storage in **MySQL**.



## 🛠️ Tech Stack
* **Backend**: Python (Flask).
* **AI/CV**: OpenCV, MediaPipe, Face-Recognition.
* **Frontend**: HTML5, CSS3, JavaScript (Socket.IO).
* **Database**: MySQL.
* **System Control**: PyCaw (Python Core Audio Windows Library).

## 📁 Project Structure
* `/Core`: Contains `Gesture_Face_Volume.py` (AI Logic) and `database.py` (DB Connection).
* `/Web`: Frontend templates and static assets (CSS/JS).
* `app.py`: The central Flask server managing API routes and WebSocket threads.
* `wireless.sql`: Database schema and initial configuration.

## ⚙️ Setup & Installation
1. **Clone the Repo**: Download the project files.
2. **Install Dependencies**: Run `pip install -r requirements.txt`.
3. **Database Setup**: Import `wireless.sql` into MySQL and update credentials in `app.py`.
4. **Run Application**: Execute `python app.py` and access the dashboard via `localhost:5000`.

---
**Developed by Mohammed Alrasheed And Faris Almutiri**
*Bachelor of Computer Science - Al-Majma'ah University*