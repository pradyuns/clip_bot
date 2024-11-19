# clip_bot

## Project Overview

`clip_bot` is a tool designed to automate the creation of highlight clips from Kick.com streams. It leverages Python to capture and create clips based on chat activity and artificial intelligence.

## Key Components

- **Browser Interaction**: Utilizes Selenium for interacting with web browsers.
- **Screen Capture and Video Processing**: Uses OpenCV and MSS for capturing and processing video frames.
- **Audio Capture and Video Encoding**: Employs FFmpeg for audio capture and video encoding.
- **Asynchronous Operations**: Implements asyncio for non-blocking operations.
- **Chat Monitoring**: Detects chat surges to trigger clip creation.

## Main Objectives

1. Efficiently capture stream content.
2. Detect chat surges to trigger clip creation.
3. Create high-quality video clips with audio.
4. Provide a user-friendly interface for managing the clipping process.

## Technical Requirements

- Python 3.8+
- Selenium WebDriver
- OpenCV
- FFmpeg
- SQLite (for data storage)

## Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd clip_bot
   ```

2. **Create a Virtual Environment**:
   ```bash
   python3.8 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Settings**:
   - Adjust settings in the configuration file (e.g., `config.json` or `config.yaml`).

## Usage

- **Run the Clip Bot**:
  ```bash
  python main.py
  ```

- **Command-line Options**:
  - Use `--help` to see available options and configurations.

## Development Guidelines

Refer to the `.cursorrules` file for detailed development guidelines, including project structure, best practices, and testing protocols.

## Contributing

Contributions are welcome! Please read the `CONTRIBUTING.md` for guidelines on how to contribute to this project.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Acknowledgments

Special thanks to all contributors and the open-source community for their support and collaboration.
