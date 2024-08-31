import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import cv2
import numpy as np
from collections import deque

class KickClipper:
    def __init__(self, channel, message_threshold=10, time_window=10, clip_duration=30, buffer_duration=40):
        self.channel = channel
        self.base_url = f"https://kick.com/{channel}"
        self.message_threshold = message_threshold
        self.time_window = time_window
        self.clip_duration = clip_duration
        self.buffer_duration = buffer_duration
        self.message_times = []
        self.last_clip_time = 0
        self.driver = None
        self.frame_buffer = deque(maxlen=int(buffer_duration * 30))  # Assuming 30 fps

    def attach_to_existing_browser(self):
        options = Options()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        self.driver = webdriver.Chrome(options=options)
        print(f"Attached to existing Chrome window. Current URL: {self.driver.current_url}")

    def is_stream_live(self):
        try:
            video = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "video"))
            )
            return self.driver.execute_script("return arguments[0].paused === false;", video)
        except TimeoutException:
            print("Timeout waiting for video player")
            return False
        except Exception as e:
            print(f"Error checking stream status: {str(e)}")
            return False

    def get_chat_messages(self):
        try:
            chat_messages = self.driver.find_elements(By.CSS_SELECTOR, ".chat-entry-content")
            return [msg.text for msg in chat_messages]
        except NoSuchElementException:
            print("Chat messages not found")
            return []
        except Exception as e:
            print(f"Error getting chat messages: {str(e)}")
            return []

    def capture_frame(self):
        video = self.driver.find_element(By.TAG_NAME, "video")
        location = video.location
        size = video.size
        screenshot = self.driver.get_screenshot_as_png()
        frame = cv2.imdecode(np.frombuffer(screenshot, np.uint8), -1)
        video_frame = frame[location['y']:location['y']+size['height'],
                            location['x']:location['x']+size['width']]
        self.frame_buffer.append(video_frame)

    def should_clip(self):
        current_time = time.time()
        if current_time - self.last_clip_time < self.clip_duration:
            return False

        try:
            if not self.is_stream_live():
                print(f"The channel {self.channel} is not live.")
                return False

            chat_messages = self.get_chat_messages()
            self.message_times.append((current_time, len(chat_messages)))
            self.message_times = [
                (t, c) for t, c in self.message_times if current_time - t <= self.time_window
            ]
            
            total_messages = sum(count for _, count in self.message_times)
            print(f"Current message count in {self.time_window} seconds: {total_messages}")

            return total_messages >= self.message_threshold
        except Exception as e:
            print(f"Error in should_clip: {str(e)}")
            return False

    def create_clip(self):
        print(f"Creating clip for channel: {self.channel}")
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"clips/{self.channel}_{timestamp}.mp4"

            if not self.frame_buffer:
                print("No frames in buffer, cannot create clip.")
                return

            frame_size = self.frame_buffer[0].shape[:2][::-1]
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_file, fourcc, 30.0, frame_size)

            # Write buffered frames
            for frame in self.frame_buffer:
                out.write(frame)

            # Capture a few more seconds
            extra_frames = int(5 * 30)  # 5 more seconds at 30 fps
            for _ in range(extra_frames):
                self.capture_frame()
                out.write(self.frame_buffer[-1])

            out.release()
            print(f"Clip saved: {output_file}")
            self.last_clip_time = time.time()

        except Exception as e:
            print(f"Error creating clip: {str(e)}")

    def close(self):
        if self.driver:
            self.driver.quit()
