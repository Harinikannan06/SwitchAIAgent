# Switch AI Debugging Assistant

An AI-powered programming debugging assistant integrated with the Switch platform.

## Features
- Accepts programming errors and problem statements in Switch rooms.
- Explains error meanings and root causes.
- Suggests corrected code and solutions.
- Provides expected outputs and debugging tips.

## Technology Stack
- Python
- Flask
- OpenCode
- Switch platform

## Local Setup

1. Install Python 3.11 or later.
2. Clone this repository.
3. Create and activate a virtual environment.
4. Install dependencies:

   pip install -r requirements.txt

5. Create a .env file with your OpenCode server password:

   OPENCODE_SERVER_PASSWORD=your_password

6. Start your OpenCode server on 127.0.0.1:4096.
7. Run the Flask application:

   python app.py

## Security
Never commit your .env file, API keys, or passwords.

## Project
Created for Flip the Switch Hackathon 2026.
