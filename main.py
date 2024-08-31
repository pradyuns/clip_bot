import asyncio
import signal
from kick_clipper import KickClipper

# Global flag to indicate if the program should continue running
running = True

def signal_handler(sig, frame):
    global running
    print("Stopping the program...")
    running = False

signal.signal(signal.SIGINT, signal_handler)

async def main(platforms):
    clippers = []

    if 'kick' in platforms:
        kick_channel = "fousey"  # Replace with the desired channel
        clipper = KickClipper(kick_channel, message_threshold=10, time_window=10, clip_duration=30, buffer_duration=20)
        clipper.attach_to_existing_browser()
        clippers.append(clipper)

    try:
        while running:
            for clipper in clippers:
                if not running:
                    break
                
                clipper.capture_frame()  # Continuously capture frames
                
                if clipper.should_clip():
                    clipper.create_clip()
            
            await asyncio.sleep(1/30)  # Capture at roughly 30 fps
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