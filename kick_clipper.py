import time
from datetime import datetime
import asyncio
import os
import subprocess
from typing import List, Tuple
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import cv2
import numpy as np
from collections import deque
import mss

class KickClipper:
    def __init__(self, channel: str, message_threshold: int = 10, time_window: int = 10, clip_duration: int = 30, buffer_duration: int = 40):
        self.channel = channel
        self.base_url = f"https://kick.com/{channel}"
        self.message_threshold = message_threshold
        self.time_window = time_window
        self.clip_duration = clip_duration
        self.buffer_duration = buffer_duration
        self.message_times: List[Tuple[float, int]] = []
        self.last_clip_time = 0
        self.driver: webdriver.Chrome | None = None
        self.frame_buffer = deque(maxlen=int(buffer_duration * 30))  # Assuming 30 fps
        self.sct = mss.mss()
        self.last_capture_time = 0
        self.capture_interval = 1 / 30  # Capture at 30 fps

    def attach_to_existing_browser(self) -> None:
        options = Options()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        self.driver = webdriver.Chrome(options=options)
        print(f"Attached to existing Chrome window. Current URL: {self.driver.current_url}")

    def is_stream_live(self) -> bool:
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

    def get_chat_messages(self) -> List[str]:
        try:
            chat_messages = self.driver.find_elements(By.CSS_SELECTOR, ".chat-entry-content")
            return [msg.text for msg in chat_messages]
        except NoSuchElementException:
            print("Chat messages not found")
            return []
        except Exception as e:
            print(f"Error getting chat messages: {str(e)}")
            return []

    def capture_frame(self) -> None:
        current_time = time.time()
        if current_time - self.last_capture_time < self.capture_interval:
            return  # Skip this frame if not enough time has passed

        try:
            video = self.driver.find_element(By.TAG_NAME, "video")
            location = video.location
            size = video.size
            screenshot = self.sct.grab({
                "top": int(location['y']),
                "left": int(location['x']),
                "width": int(size['width']),
                "height": int(size['height'])
            })
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)
            self.frame_buffer.append(frame)
            self.last_capture_time = current_time
        except Exception as e:
            print(f"Error capturing frame: {str(e)}")

    async def create_clip(self) -> None:
        print(f"Starting clip creation for channel: {self.channel}")
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clips_dir = os.path.join(os.getcwd(), "clips")
            os.makedirs(clips_dir, exist_ok=True)
            
            temp_video_file = os.path.join(clips_dir, f"{self.channel}_{timestamp}_temp_video.mp4")
            final_output_file = os.path.join(clips_dir, f"{self.channel}_{timestamp}.mp4")

            if not self.frame_buffer:
                print("No frames in buffer, cannot create clip.")
                return

            await self._create_clip_with_audio(temp_video_file, final_output_file)

            # Clean up temporary file
            os.remove(temp_video_file)

            self.last_clip_time = time.time()

        except Exception as e:
            print(f"Error creating clip: {str(e)}")
            import traceback
            traceback.print_exc()

    async def _create_clip_with_audio(self, temp_video_file: str, final_output_file: str) -> None:
        print(f"Creating clip with audio: {final_output_file}")
        frame_size = self.frame_buffer[0].shape[:2][::-1]
        
        ffmpeg_command = [
            'ffmpeg',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-s', f'{frame_size[0]}x{frame_size[1]}',
            '-pix_fmt', 'rgb24',
            '-r', '30',
            '-i', '-',
            '-f', 'avfoundation',
            '-i', ':0',
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-c:a', 'aac',
            '-strict', 'experimental',
            '-b:a', '192k',
            '-t', str(self.clip_duration),
            final_output_file
        ]
        
        process = await asyncio.create_subprocess_exec(
            *ffmpeg_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            for frame in self.frame_buffer:
                process.stdin.write(frame.tobytes())
                await asyncio.sleep(0)  # Yield control to allow other tasks to run

            extra_frames = int(5 * 30)  # 5 more seconds at 30 fps
            for _ in range(extra_frames):
                self.capture_frame()
                process.stdin.write(self.frame_buffer[-1].tobytes())
                await asyncio.sleep(0)

        finally:
            if process.stdin:
                process.stdin.close()
            stdout, stderr = await process.communicate()

        if process.returncode != 0:
            print(f"Error creating clip with audio: {stderr.decode()}")
            raise RuntimeError("Clip creation with audio failed")

        print(f"Clip saved: {final_output_file}")
        print(f"Final file size: {os.path.getsize(final_output_file)} bytes")

    def close(self) -> None:
        if self.driver:
            self.driver.quit()

    def should_clip(self) -> bool:
        current_time = time.time()
        if current_time - self.last_clip_time < self.clip_duration:
            return False

        try:
            if not self.is_stream_live():
                return False

            chat_messages = self.get_chat_messages()
            self.message_times.append((current_time, len(chat_messages)))
            self.message_times = [
                (t, c) for t, c in self.message_times if current_time - t <= self.time_window
            ]
            
            total_messages = sum(count for _, count in self.message_times)
            
            if total_messages >= self.message_threshold:
                print(f"Message surge detected: {total_messages} messages in {self.time_window} seconds")
                return True
            return False
        except Exception as e:
            print(f"Error in should_clip: {str(e)}")
            return False
