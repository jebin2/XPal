from local_global import global_config
import json
import google_ai_studio
import logger_config
import x_utils

class TwitterProp:
	def __init__(self, page):
		self.page = page

	def valid(self, user_prompt, file_path):
		is_valid_post = True
		if global_config["specifc_post_validation_sp"]:
			_, _, model_responses = google_ai_studio.process(global_config["specifc_post_validation_sp"], user_prompt, file_path=file_path)
			response = json.loads(model_responses[0]["parts"][0])
			is_valid_post = True if response[global_config["specifc_post_key"]].lower() == "yes" else False

		return is_valid_post

	def load_page(self):
		self.page.goto(global_config["url"])
		self.page.wait_for_load_state("domcontentloaded")
		logger_config.debug("Precaution wait after load...", seconds=5)

	def reload(self):
		self.page.reload()
		self.page.wait_for_load_state("domcontentloaded")
		logger_config.debug("Precaution wait after load...", seconds=5)
		# To remove popup
		self.page.keyboard.press("Escape")
		self.page.keyboard.press("Escape")

	def download(self, media_link, tweet_id):
		try:
			file_path = x_utils.download_video(tweet_id)
			if file_path:
				return "video/mp4", file_path

			file_path = x_utils.download_image(media_link)
			return "image/jpeg", file_path

		except:
			pass

		return None, None

	def go_back(self):
		x_utils.click(self.page, global_config["back_selector"])
		self.page.wait_for_load_state("domcontentloaded")
		logger_config.debug("Precaution wait after load...", seconds=2)
		if "https://x.com/home" not in self.page.url:
			self.load_page()