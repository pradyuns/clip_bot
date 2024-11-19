import asyncio
import signal
from kick_clipper import KickClipper
import os

running = True

def signal_handler(sig, frame):
    global running
    print("Stopping the program...")
    running = False

signal.signal(signal.SIGINT, signal_handler)

async def main(platforms):
    clippers = []

    if 'kick' in platforms:
        kick_channel = "xqc"  # Replace with the desired channel
        clipper = KickClipper(kick_channel, message_threshold=10, time_window=10, clip_duration=30, buffer_duration=20)
        clipper.attach_to_existing_browser()
        await asyncio.sleep(5)  # Give some time for the page to load completely
        clippers.append(clipper)

    try:
        while running:
            for clipper in clippers:
                if not running:
                    break
                
                clipper.capture_frame()
                
                if clipper.should_clip():
                    await clipper.create_clip()
            
            await asyncio.sleep(0.01)  # Small delay to prevent high CPU usage
    finally:
        for clipper in clippers:
            clipper.close()

    print("Program stopped.")

if __name__ == "__main__":
    import sys
    selected_platforms = sys.argv[1:]
    if not selected_platforms:
        print("Please specify at least one platform (e.g., python main.py kick)")
    else:
        asyncio.run(main(selected_platforms))