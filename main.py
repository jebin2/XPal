from playwright.sync_api import sync_playwright
import logger_config
from local_global import global_config
import random
from twitter_service import TwitterService

def new_page(p):
	browser = p.chromium.launch(executable_path='/usr/bin/brave-browser', headless=False, args=["--disable-blink-features=AutomationControlled"])
	context = browser.new_context(
		locale="en-US",
		viewport={"width": 1366, "height": 768}
	)

	return browser, context.new_page()

def start():
	with sync_playwright() as p:
		while True:
			channel_names = global_config["channel_names"].split(",")
			random.shuffle(channel_names)
			for channel in channel_names:
				browser, page = new_page(p)
				twitterService = TwitterService(page, channel)
				twitterService.play()

				logger_config.info("Wait before next channel", seconds=50)
				browser.close()

			logger_config.info("Wait 1 hour for next iteration.")


if __name__ == "__main__":
    start()