from concurrent.futures import ThreadPoolExecutor
from custom_logger import logger_config
from datetime import datetime, time as date_time
import os
from browser_manager.browser_config import BrowserConfig
from browser_manager import BrowserManager
import traceback
import threading
import common
import time
import signal
import sys
from dotenv import load_dotenv
if common.file_exists(".env"):
	logger_config.debug("Loading .env file")
	load_dotenv()
else:
	logger_config.warning(".env file not found.")

# Global shutdown flag
shutdown_event = threading.Event()

def signal_handler(signum, frame):
	"""Handle Ctrl+C gracefully"""
	logger_config.info("Shutdown signal received. Stopping all threads...")
	shutdown_event.set()
	sys.exit(0)

def is_time_run(twitter_config):
	try:
		start_at = int(twitter_config['start_at']) # e.g., 18 for 6 PM
		end_at = int(twitter_config['end_at'])   # e.g., 6 for 6 AM

		now = datetime.now().time()

		# Handle overnight case (e.g., start 18:00, end 06:00)
		if start_at > end_at:
			if now >= date_time(start_at, 0) or now < date_time(end_at, 0):
				return True
		# Handle same-day case (e.g., start 09:00, end 17:00)
		else:
			if date_time(start_at, 0) <= now < date_time(end_at, 0):
				return True

		logger_config.info(f"Outside run time. Will run between {start_at:02d}:00 and {end_at:02d}:00.", overwrite=True, seconds=60)
		return False
	except:
		return True # Or False

def process_channel(channel, index):
	"""Process a single channel in its own thread with independent timing loop"""
	from local_global import load_toml
	twitter_config = load_toml(channel_name=channel)
	import gc
	thread_id = threading.current_thread().ident
	logger_config.info(f"[Thread {thread_id}] Channel '{channel}' thread started")

	# --- Channel-specific Main Loop ---
	while not shutdown_event.is_set():
		if not is_time_run(twitter_config):
			# Check shutdown every 10 seconds instead of sleeping for full 60 seconds
			for _ in range(6):  # 6 * 10 = 60 seconds
				if shutdown_event.wait(10):  # Wait 10 seconds or until shutdown
					logger_config.info(f"[Thread {thread_id}] Channel '{channel}' shutting down...")
					return
			continue

		logger_config.info(f"[Thread {thread_id}] --- Starting channel: {channel} ---")
		
		try:
			import x_utils
			from twitter_service import TwitterService
			
			config = BrowserConfig()
			config.docker_name = f"xpal_{channel}"
			config.user_data_dir = os.path.abspath(f"{twitter_config['config_path']}/{channel}")
			config.starting_server_port_to_check = [30081, 31081, 32081, 33081, 34081, 35081][index]
			config.starting_debug_port_to_check = [40224, 41224, 42224, 43224, 44224, 45224][index]
			os.makedirs(config.user_data_dir, exist_ok=True)
			
			try:
				browser_manager = BrowserManager(config)
				with browser_manager as page:
					twitterService = TwitterService(browser_manager, page, twitter_config, channel)
					if twitterService.did_login():
						twitterService.play()
						
						logger_config.info(f"[Thread {thread_id}] Simulating scroll for {channel}...")
						x_utils.simulate_human_scroll(page, 60)
						logger_config.success(f"[Thread {thread_id}] --- Finished channel: {channel} ---", seconds=60)
					else: 
						logger_config.warning(f"[Thread {thread_id}] --- Not logged in: {channel} ---")
						
			except Exception as e:
				logger_config.error(f"[Thread {thread_id}] Error processing channel '{channel}': {e} {traceback.format_exc()}")
				
		except Exception as e:
			logger_config.error(f"[Thread {thread_id}] Critical error in channel '{channel}': {e} {traceback.format_exc()}")
		finally:
			gc.collect()
		
		wait_seconds = 10 * 1 * 60
		logger_config.info(f"[Thread {thread_id}] Channel '{channel}' cycle finished. Waiting {wait_seconds // 60} minutes before next time check.")
		
		# Check shutdown every 10 seconds during the wait period
		for _ in range(wait_seconds // 10):  # 6 iterations for 60 seconds
			if shutdown_event.wait(10):  # Wait 10 seconds or until shutdown
				logger_config.info(f"[Thread {thread_id}] Channel '{channel}' shutting down...")
				return
	
	logger_config.info(f"[Thread {thread_id}] Channel '{channel}' thread stopped.")

def start():
	# Set up signal handlers for graceful shutdown
	signal.signal(signal.SIGINT, signal_handler)
	signal.signal(signal.SIGTERM, signal_handler)

	try:
		channel_names_str = os.getenv("CHANNEL_NAMES", "")
		channel_names = [name.strip() for name in channel_names_str.split(",") if name.strip()]

		if not channel_names:
			logger_config.warning("No valid channel names found in environment variable 'CHANNEL_NAMES'. Exiting.")
			return
		
		temp_path = "tempOutput"
		common.remove_directory(temp_path)
		common.create_directory(temp_path)
		
		import random
		random.shuffle(channel_names)
		logger_config.info(f"Starting {len(channel_names)} independent channel threads: {', '.join(channel_names)}")

		# Start each channel in its own independent thread
		max_workers = min(len(channel_names), 10)  # Limit concurrent threads
		print(f"Starting {max_workers} channel threads")
		
		with ThreadPoolExecutor(max_workers=max_workers) as executor:
			futures = []
			
			# Submit each channel to run indefinitely in its own thread
			for i, channel in enumerate(channel_names):
				future = executor.submit(process_channel, channel, i)
				futures.append(future)
			
			logger_config.success("All channel threads started successfully.")
			
			# Keep the main thread alive and monitor for any thread failures
			try:
				# Wait for shutdown signal or thread completion
				while not shutdown_event.is_set():
					# Check if any thread has finished (which shouldn't happen normally)
					done_futures = [f for f in futures if f.done()]
					if done_futures:
						for future in done_futures:
							try:
								future.result()  # Get any exception that occurred
							except Exception as e:
								logger_config.error(f"A channel thread failed: {e}")
						break
					
					# Sleep briefly and check again
					time.sleep(1)
					
			except KeyboardInterrupt:
				logger_config.info("Received interrupt signal. Shutting down...")
				shutdown_event.set()
			except Exception as e:
				logger_config.error(f"A channel thread failed unexpectedly: {e}")
				shutdown_event.set()

	except Exception as outer_e:
		logger_config.error(f"Critical error during startup: {outer_e}")
		shutdown_event.set()
		raise
	finally:
		logger_config.info("Shutdown complete.")


if __name__ == "__main__":
	start()