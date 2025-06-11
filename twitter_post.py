from local_global import global_config
import x_utils
from gemiwrap import GeminiWrapper
from custom_logger import logger_config
import json
import random
from twitter_prop import TwitterProp
import common
import os
import remove_metadata

class TwitterPost(TwitterProp):
	def __init__(self, page):
		super().__init__(page)

	def valid(self, user_prompt, file_path):
		if super().valid(user_prompt, file_path):
			is_valid_post = True
			if global_config["post_decider_sp"]:
				geminiWrapper = GeminiWrapper(system_instruction=global_config["post_decider_sp"], delete_files=True)
				model_responses = geminiWrapper.send_message("", file_path=file_path)
				response = json.loads(model_responses[0])
				is_valid_post = True if response["post"].lower() == "yes" else False

			return is_valid_post

		return False

	def _post(self, post, file_path):
		file_path = remove_metadata.clean_media_file(file_path)
		textbox = self.page.locator(global_config["post_textarea_selector"])
		textbox.type(post)
		textbox.type(" ")

		file_input = self.page.locator('input[type="file"]')
		file_input.set_input_files(file_path)

		button_locator = self.page.locator(global_config["post_tweet_selector"])
		button_locator.wait_for(state="visible", timeout=50000)

		self.page.wait_for_timeout(10000)

		x_utils.click(self.page, global_config["post_tweet_selector"])

	def start(self):
		if global_config["media_path"]:
			count = 0

			while True:
				logger_config.info(f'{global_config["wait_second"]} sec scroll')
				x_utils.simulate_human_scroll(self.page, global_config["wait_second"])
				if count > global_config["post_count"]:
					break

				media_files = [
					file for file in common.list_files_recursive(global_config["media_path"]) 
					if file.endswith((".png", ".jpg", ".mkv", ".mp4"))
				]

				if not media_files:
					return

				file_path = random.choice(media_files)


				count += 1
				geminiWrapper = GeminiWrapper(system_instruction=global_config["post_sp"], delete_files=True)
				model_responses = geminiWrapper.send_message("", file_path=file_path)
				response = json.loads(model_responses[0])
				if response["can_post"] == "yes" and len(response["post"]) < 250 and self.valid(response["post"], file_path):
					meta_data = self.image_metadata(file_path)
					new_post_content = response["post"]
					if meta_data and "post" in meta_data:
						if len(f"{new_post_content} {meta_data['post']}") <= 250:
							new_post_content = f"{new_post_content} {meta_data['post']}"

					self._post(new_post_content, file_path)
					if global_config["delete_media_path_after_post"] == "yes":
						common.remove_file(file_path)
						root, ext = os.path.splitext(file_path)
						clean_path = f"{root}_clean{ext}"
						common.remove_file(clean_path)