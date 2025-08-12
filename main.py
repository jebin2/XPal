from custom_logger import logger_config
from local_global import global_config
from dotenv import load_dotenv
from datetime import datetime, time as date_time
import os
from browser_manager.browser_config import BrowserConfig
from browser_manager import BrowserManager
import traceback

def is_time_run():
	try:
		start_at = int(global_config['start_at']) # e.g., 18 for 6 PM
		end_at = int(global_config['end_at'])   # e.g., 6 for 6 AM

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

def initial_setup():
	import common
	if common.file_exists(".env"):
		logger_config.debug("Loading .env file")
		load_dotenv()
	else:
		logger_config.warning(".env file not found.")

	common.create_directory(global_config['config_path'])
	logger_config.info("Configuration directory ensured.")

def start():
	import gc

	initial_setup()

	# --- Main Loop ---
	while True:
		if not is_time_run():
			continue

		try:
			channel_names_str = os.getenv("channel_names", "")
			channel_names = [name.strip() for name in channel_names_str.split(",") if name.strip()]

			if not channel_names:
				logger_config.warning("No valid channel names found in environment variable 'channel_names'. Skipping channel processing.")
				# Continue to the sleep part of this cycle

			else:
				import x_utils
				from twitter_service import TwitterService
				import random

				random.shuffle(channel_names)
				logger_config.info(f"Processing {len(channel_names)} channels: {', '.join(channel_names)}")

				for channel in channel_names:
					import common
					temp_path = "tempOutput"
					common.remove_directory(temp_path)
					common.create_directory(temp_path)
					logger_config.info(f"--- Starting channel: {channel} ---")
					config = BrowserConfig()
					config.docker_name = "xpal"
					config.user_data_dir = os.path.abspath(f"{global_config['config_path']}/{channel}")
					os.makedirs(config.user_data_dir, exist_ok=True)
					try:
						browser_manager = BrowserManager(config)
						with browser_manager as page:
							twitterService = TwitterService(browser_manager, page, channel)
							if twitterService.did_login():
								twitterService.play()

								logger_config.info(f"Simulating scroll for {channel}...")
								x_utils.simulate_human_scroll(page, 60)
								logger_config.success(f"--- Finished channel: {channel} ---", seconds=60)
							else: logger_config.warning(f"--- Not logged in: {channel} ---")

					except Exception as e:
						logger_config.error(f"Error processing channel '{channel}': {e} {traceback.format_exc()}")

		except Exception as outer_e:
			logger_config.error(f"Critical error during run cycle setup or browser operation: {outer_e}")
		finally:
			gc.collect()

		wait_seconds = 1 * 60
		logger_config.info(f"Run cycle finished. Waiting {wait_seconds // 60} minutes before next time check.", seconds=wait_seconds)


if __name__ == "__main__":
	start()