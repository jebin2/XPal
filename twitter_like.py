from twitter_prop import TwitterProp
from local_global import global_config
import json
from custom_logger import logger_config
from gemini_config import pre_model_wrapper
import x_utils
import json_repair

class TwitterLike(TwitterProp):
	
	def __init__(self, browser_manager, page):
		super().__init__(browser_manager, page)

	def valid(self, user_prompt, file_path, mimetype=None):
		if super().valid(user_prompt, file_path, mimetype):
			is_valid_post = True
			if global_config["like_decider_sp"]:
				response = None
				if mimetype == "image/jpeg" or not file_path:
					response = x_utils.get_response_from_perplexity(self.browser_manager, global_config["like_decider_sp"], user_prompt, file_path)
				if not response:
					geminiWrapper = pre_model_wrapper(system_instruction=global_config["like_decider_sp"], delete_files=True)
					model_responses = geminiWrapper.send_message(user_prompt, file_path=file_path)
					response = model_responses[0]
				response = json_repair.loads(response)
				is_valid_post = True if response["like"].lower() == "yes" else False

			return is_valid_post

		return False

	def _like(self, like_queryselector, id):
		x_utils.click(self.page, f'article:has(a[href*="{id}"]) div div div')
		self.page.wait_for_load_state("domcontentloaded")
		x_utils.click(self.page, f'article:has(a[href*="{id}"]) >> {like_queryselector}')
		self.go_back()

	def start(self):
		count = 0
		old_post = []
		max_itr = 20
		while True:
			if max_itr == 10:
				self.reload()

			max_itr -= 1
			logger_config.info(f'{global_config["wait_second"]} sec scroll')
			x_utils.simulate_human_scroll(self.page, global_config["wait_second"])
			if count > global_config["like_count"] or max_itr < 0:
				break

			logger_config.info(f"Getting new post, old_post:: {old_post}")
			article = x_utils.get_new_post(self.page, old_post)
			if len(article) > 0:
				# geminiWrapper = pre_model_wrapper(system_instruction=global_config["html_parser_sp"], delete_files=True)
				# model_responses = geminiWrapper.send_message(article[0]["html"])
				# response = json_repair.loads(model_responses[0])
				response = x_utils.extract_tweet_info(article[0]["html"])
				user_prompt = response["description"]
				media_link = response["media_link"]
				like_queryselector = response["like_queryselector"]
				mimetype, file_path = self.download(media_link, article[0]["id"])
				
				old_post.append(article[0]["id"])

				if self.valid(user_prompt, file_path, mimetype):
					count += 1
					self._like(like_queryselector, article[0]["id"])
			else:
				self.reload()