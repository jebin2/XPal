from local_global import global_config
import x_utils
import google_ai_studio
import logger_config
import json
import random

class TwitterReply:
	def __init__(self, page):
		self.page = page

	def _valid(self, user_prompt, file_path):
		is_valid_post = True
		if global_config["specifc_post_validation_sp"]:
			_, _, model_responses = google_ai_studio.process(global_config["specifc_post_validation_sp"], user_prompt, file_path=file_path)
			response = json.loads(model_responses[0]["parts"][0])
			is_valid_post = True if response[global_config["specifc_post_key"]].lower() == "yes" else False

		return is_valid_post

	def _reload(self):
		self.page.reload()
		self.page.wait_for_load_state("domcontentloaded")
		logger_config.debug("Precaution wait after load...", seconds=5)

	def _reply(self, reply_queryselector, reply):
		x_utils.click(self.page, f".current_processing_post {reply_queryselector}")
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
				reply_queryselector = response["reply_queryselector"]
				file_path = x_utils.download_image(media_link)
				
				old_post.append({
					"description": user_prompt,
					"media_link": media_link
				})

				if self._valid(user_prompt, file_path):
					count += 1
					_, _, model_responses = google_ai_studio.process(random.choice(reply_sp), user_prompt, file_path=file_path)
					response = json.loads(model_responses[0]["parts"][0])
					self._reply(reply_queryselector, response["reply"])