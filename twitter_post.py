from local_global import global_config
import x_utils
import google_ai_studio
import logger_config
import json
import random
from twitter_prop import TwitterProp
import common

class TwitterPost(TwitterProp):
	def __init__(self, page):
		super().__init__(page)

	def valid(self, user_prompt, file_path):
		if super().valid(user_prompt, file_path):
			is_valid_post = True
			if global_config["reply_decider_sp"]:
				_, _, model_responses = google_ai_studio.process(global_config["reply_decider_sp"], user_prompt, file_path=file_path)
				response = json.loads(model_responses[0]["parts"][0])
				is_valid_post = True if response["reply"].lower() == "yes" else False

			return is_valid_post

		return False

	def _post(self, post, file_path):
		textbox = self.page.locator(global_config["post_textarea_selector"])
		textbox.type(post)
		textbox.type(" ")

		file_input = self.page.locator('input[type="file"]')
		file_input.set_input_files(file_path)

		button_locator = self.page.locator(global_config["post_tweet_selector"])
		button_locator.wait_for(state="visible", timeout=50000)

		self.page.wait_for_timeout(1000)
		while button_locator.is_disabled():
			self.page.wait_for_timeout(100)

		x_utils.click(self.page, global_config["post_tweet_selector"])

	def start(self):
		if global_config["media_path"]:
			count = 0

			while True:
				logger_config.info(f'{global_config["wait_second"]} sec scroll')
				x_utils.simulate_human_scroll(self.page, global_config["wait_second"])
				if count > global_config["post_count"]:
					break

				file_path = random.choice([file for file in common.list_files_recursive(global_config["media_path"]) if file.endswith(".png") or file.endswith(".jpg") or file.endswith(".mkv") or file.endswith(".mp4")])

				count += 1
				_, _, model_responses = google_ai_studio.process(global_config["post_sp"], "", file_path=file_path)
				response = json.loads(model_responses[0]["parts"][0])
				self._post(response["post"], file_path)
				if global_config["delete_media_path_after_post"] == "yes":
					common.remove_file(file_path)