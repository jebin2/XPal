from playwright.sync_api import sync_playwright, Playwright, Browser, Page, BrowserContext
from custom_logger import logger_config
from local_global import global_config
from dotenv import load_dotenv
from datetime import datetime, time as date_time
import os
import subprocess
import json

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

def new_context_and_page(browser: Browser) -> tuple[BrowserContext | None, Page | None]:
	context = None
	page = None
	try:
		from minimize_active_window import save_active_window, minimize_active_window, restore_previous_focus
		save_active_window()
		context = browser.new_context(
			locale="en-US",
			viewport={"width": 1366, "height": 768}
			# Consider adding user_agent override if needed
		)
		page = context.new_page()
		minimize_active_window()
		restore_previous_focus()
		return context, page
	except Exception as e:
		logger_config.error(f"Failed to create new context/page: {e}")
		if context:
			try: context.close()
			except: pass
		return None, None

def initial_setup():
	import common
	if common.file_exists(".env"):
		logger_config.debug("Loading .env file")
		load_dotenv()
	else:
		logger_config.warning(".env file not found.")

	common.create_directory(global_config['config_path'])
	logger_config.info("Configuration directory ensured.")

def get_chrome_neko_url():
    try:
        # Call curl to get debugger JSON
        result = subprocess.run(
            ["curl", "-s", "http://localhost:9223/json/version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=2  # seconds
        )
        if result.returncode == 0:
            json_data = json.loads(result.stdout.decode())
            ws_url = json_data.get("webSocketDebuggerUrl", None)
            if ws_url:
                logger_config.success(f"✅ Found running Chrome debugger: {ws_url}")
                return ws_url
    except Exception as e:
        logger_config.error(f"⚠️ Error checking Chrome debugger: {e}")
    return None

def start():
	import gc

	initial_setup()

	# --- Main Loop ---
	while True:
		if not is_time_run():
			continue

		playwright_instance: Playwright | None = None
		browser: Browser | None = None

		try:
			logger_config.debug("Starting Playwright connection...")
			playwright_instance = sync_playwright().start()

			logger_config.info("Launching browser...")
			executable_path = '/usr/bin/brave-browser'
			if not os.path.exists(executable_path):
				 # Fallback or error
				logger_config.warning(f"Brave not found at {executable_path}. Trying default chromium.")
				executable_path = None # Let Playwright find default

			neko_url = get_chrome_neko_url()
			if neko_url:
				browser = playwright_instance.chromium.connect_over_cdp(neko_url)
				logger_config.success("using neko docker url")
			else:
				browser = playwright_instance.chromium.launch(
					executable_path=executable_path,
					headless=False,
					args=[
						"--disable-blink-features=AutomationControlled",
						# "--no-sandbox", # Often needed in docker/linux environments
						# "--disable-setuid-sandbox",
						# "--disable-dev-shm-usage", # Helps in constrained environments
						# "--disable-gpu" # Can sometimes reduce memory
					]
				)
			logger_config.success("Browser launched successfully.")

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
					logger_config.info(f"--- Starting channel: {channel} ---")
					context: BrowserContext | None = None
					page: Page | None = None
					try:
						context, page = new_context_and_page(browser)
						if page is None or context is None:
							logger_config.error(f"Skipping channel {channel} due to page creation failure.")
							continue

						twitterService = TwitterService(page, channel)
						twitterService.play()

						logger_config.info(f"Simulating scroll for {channel}...")
						x_utils.simulate_human_scroll(page, 60)
						logger_config.success(f"--- Finished channel: {channel} ---")

					except Exception as e:
						logger_config.error(f"Error processing channel '{channel}': {e}")
						# Optional: Take screenshot on error
						# if page:
						#	 try: page.screenshot(path=f"error_{channel}_{datetime.now():%Y%m%d_%H%M%S}.png")
						#	 except: pass
					finally:
						logger_config.debug(f"Closing context and page for channel {channel}")
						if page:
							try: page.close()
							except Exception as page_close_err: logger_config.warning(f"Error closing page for {channel}: {page_close_err}")
						if context:
							try: context.close()
							except Exception as context_close_err: logger_config.warning(f"Error closing context for {channel}: {context_close_err}")
						gc.collect()

		except Exception as outer_e:
			logger_config.error(f"Critical error during run cycle setup or browser operation: {outer_e}")
		finally:
			if browser:
				try:
					logger_config.info("Closing browser...")
					browser.close()
					logger_config.success("Browser closed.")
				except Exception as browser_close_err:
					logger_config.warning(f"Error closing browser: {browser_close_err}")

			if playwright_instance:
				try:
					logger_config.debug("Stopping Playwright connection...")
					playwright_instance.stop()
					logger_config.success("Playwright stopped.")
				except Exception as pw_stop_err:
					logger_config.warning(f"Error stopping Playwright: {pw_stop_err}")
			gc.collect()

		wait_seconds = 10 * 60
		logger_config.info(f"Run cycle finished. Waiting {wait_seconds // 60} minutes before next time check.", seconds=wait_seconds)


if __name__ == "__main__":
	start()