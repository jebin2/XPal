from playwright.sync_api import sync_playwright
from custom_logger import logger_config
from local_global import global_config
import random
from twitter_service import TwitterService
import common
import x_utils
import os
from dotenv import load_dotenv

def new_page(p):
	browser = p.chromium.launch(executable_path='/usr/bin/brave-browser', headless=False, args=["--disable-blink-features=AutomationControlled"])
	context = browser.new_context(
		locale="en-US",
		viewport={"width": 1366, "height": 768}
	)

	return browser, context.new_page()

def start():
	if os.path.exists(".env"):
		load_dotenv()

	with sync_playwright() as p:
		common.create_directory(global_config['base_path'])
		while True:
			channel_names = os.getenv("channel_names", "").split(",")
			random.shuffle(channel_names)
			for channel in channel_names:
				browser, page = new_page(p)
				twitterService = TwitterService(page, channel)
				twitterService.play()

				logger_config.info("60 sec scroll before next channel.")
				x_utils.simulate_human_scroll(page, 60)
				browser.close()

			logger_config.info("Wait 10 minutes for next iteration.", seconds=10*60)


if __name__ == "__main__":
	start()