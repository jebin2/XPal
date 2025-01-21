from local_global import global_config
import x_utils
import google_ai_studio
import logger_config
import json
import random
from twitter_prop import TwitterProp

class TwitterQuote(TwitterProp):
	def __init__(self, page):
		super().__init__(page)

	def valid(self, user_prompt, file_path):
		if super().valid(user_prompt, file_path):
			is_valid_post = True
			if global_config["quote_decider_sp"]:
				_, _, model_responses = google_ai_studio.process(global_config["quote_decider_sp"], user_prompt, file_path=file_path)
				response = json.loads(model_responses[0]["parts"][0])
				is_valid_post = True if response["reply"].lower() == "yes" else False

			return is_valid_post

		return False

	def _quote(self, repost_queryselector, reply):
		x_utils.click(self.page, f".current_processing_post {repost_queryselector}")
		x_utils.click(self.page, f"{global_config['quote_tweet_selector']}")
		textbox = self.page.locator(global_config["reply_editor_selector"])
		textbox.type(reply)
		x_utils.click(self.page, global_config["reply_tweet_selector"])
		self._reload()

	def start(self):
		count = 0
		old_post = []
		reply_sp = []
		itr = 0
		while True:
			try:
				reply_sp.append(global_config[f"reply_sp_{itr}"])
				itr += 1
			except:
				break

		while True:
			logger_config.info("Wait for every iteration to avoid limit", seconds=global_config["wait_second"])
			self.page.mouse.wheel(0, 500)
			if count > global_config["reply_count"]:
				break

			logger_config.info(f"Getting new post, old_post:: {old_post}")
			article = x_utils.get_new_post(self.page, old_post)
			if len(article) > 0:
				_, _, model_responses = google_ai_studio.process(global_config["html_parser_sp"], article[0]["html"])
				response = json.loads(model_responses[0]["parts"][0])
				user_prompt = response["description"]
				media_link = response["media_link"]
				repost_queryselector = response["repost_queryselector"]
				file_path = x_utils.download_image(media_link)
				
				old_post.append({
					"description": user_prompt,
					"media_link": media_link
				})

				if self.valid(user_prompt, file_path):
					count += 1
					_, _, model_responses = google_ai_studio.process(random.choice(reply_sp), user_prompt, file_path=file_path)
					response = json.loads(model_responses[0]["parts"][0])
					self._quote(repost_queryselector, response["reply"])