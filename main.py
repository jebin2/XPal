from playwright.sync_api import sync_playwright
from custom_logger import logger_config
from local_global import global_config
import random
from twitter_service import TwitterService
import common
import x_utils
from dotenv import load_dotenv
from datetime import datetime, time as date_time
import os

def is_time_run():
	now = datetime.now().time()
	return now < date_time(6, 00) or now > date_time(18, 00)

def new_page(p):
	browser = p.chromium.launch(executable_path='/usr/bin/brave-browser', headless=False, args=["--disable-blink-features=AutomationControlled"])
	context = browser.new_context(
		locale="en-US",
		viewport={"width": 1366, "height": 768}
	)

	return browser, context.new_page()

def start():
	if common.file_exists(".env"):
		load_dotenv()

	with sync_playwright() as p:
		common.create_directory(global_config['config_path'])
		while True:
			# if not is_time_run():
			# 	logger_config.info("its not time to run yet. will run between 6 PM and end at 6 AM", overwrite=True)
			# 	continue

			channel_names = os.getenv("channel_names", "").split(",")
			random.shuffle(channel_names)
			for channel in channel_names:
				browser, page = new_page(p)
				try:
					twitterService = TwitterService(page, channel)
					twitterService.play()

					logger_config.info("60 sec scroll before next channel.")
					x_utils.simulate_human_scroll(page, 60)
				except Exception as e:
					logger_config.warning(f"Error occurred: {e}")

				browser.close()

			logger_config.info("Wait 10 minutes for next iteration.", seconds=10*60)


if __name__ == "__main__":
	start()