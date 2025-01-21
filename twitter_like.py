from twitter_prop import TwitterProp
from local_global import global_config
import json
import logger_config
import google_ai_studio
import x_utils

class TwitterLike(TwitterProp):
	def __init__(self, page):
		super().__init__(page)

	def valid(self, user_prompt, file_path):
		if super().valid(user_prompt, file_path):
			is_valid_post = True
			if global_config["like_decider_sp"]:
				_, _, model_responses = google_ai_studio.process(global_config["like_decider_sp"], user_prompt, file_path=file_path)
				response = json.loads(model_responses[0]["parts"][0])
				is_valid_post = True if response["like"].lower() == "yes" else False

			return is_valid_post

		return False

	def _like(self, like_queryselector):
		x_utils.click(self.page, f".current_processing_post {like_queryselector}")

	def start(self):
		count = 0
		old_post = []
		while True:
			logger_config.info("Wait for every iteration to avoid limit", seconds=global_config["wait_second"])
			self.page.mouse.wheel(0, 500)
			if count > global_config["like_count"]:
				break

			logger_config.info(f"Getting new post, old_post:: {old_post}")
			article = x_utils.get_new_post(self.page, old_post)
			if len(article) > 0:
				_, _, model_responses = google_ai_studio.process(global_config["html_parser_sp"], article[0]["html"])
				response = json.loads(model_responses[0]["parts"][0])
				user_prompt = response["description"]
				media_link = response["media_link"]
				like_queryselector = response["like_queryselector"]
				file_path = x_utils.download_image(media_link)
				
				old_post.append({
					"description": user_prompt,
					"media_link": media_link
				})

				if self.valid(user_prompt, file_path):
					count += 1
					_, _, model_responses = google_ai_studio.process(global_config["html_parser_sp"], user_prompt, file_path=file_path)
					response = json.loads(model_responses[0]["parts"][0])
					self._like(like_queryselector)