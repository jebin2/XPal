import x_utils
from gemini_config import pre_model_wrapper
from custom_logger import logger_config
import json_repair
import random
from twitter_prop import TwitterProp

class TwitterReply(TwitterProp):
	def __init__(self, browser_manager, page):
		super().__init__(browser_manager, page)

	def valid(self, user_prompt, file_path, mimetype=None):
		if super().valid(user_prompt, file_path, mimetype):
			is_valid_post = True
			if self.twitter_config["reply_decider_sp"]:
				response = None
				if mimetype == "image/jpeg" or not file_path:
					response = x_utils.get_response_from_perplexity(self.browser_manager, self.twitter_config["reply_decider_sp"], user_prompt, file_path)
				if not response:
					geminiWrapper = pre_model_wrapper(system_instruction=self.twitter_config["reply_decider_sp"], delete_files=True)
					model_responses = geminiWrapper.send_message(user_prompt, file_path=file_path)
					response = model_responses[0]
				response = json_repair.loads(response)
				is_valid_post = True if response["reply"].lower() == "yes" else False

			return is_valid_post

		return False

	def _reply(self, reply_queryselector, reply, id):
		x_utils.click(self.page, f'article:has(a[href*="{id}"]) div div div')
		self.page.wait_for_load_state("domcontentloaded")
		x_utils.click(self.page, f'article:has(a[href*="{id}"]) >> {reply_queryselector}')
		element = self.page.query_selector(self.twitter_config["reply_editor_selector"])
		if element:
			textbox = self.page.locator(self.twitter_config["reply_editor_selector"])
			textbox.type(reply)
			textbox.type(" ")
			x_utils.click(self.page, self.twitter_config["reply_tweet_selector"])
		else:
			x_utils.click(self.page, self.twitter_config["disable_warning_selector"])
			# To remove popup
			self.page.keyboard.press("Escape")
			self.page.keyboard.press("Escape")

		self.go_back()

	def start(self):
		count = 0
		old_post = []
		reply_sp = []
		itr = 0
		while True:
			try:
				reply_sp.append(self.twitter_config[f"reply_sp_{itr}"])
				itr += 1
			except:
				break

		max_itr = 20
		while True:
			if max_itr == 10:
				self.reload()

			max_itr -= 1
			logger_config.info(f'{self.twitter_config["wait_second"]} sec scroll')
			x_utils.simulate_human_scroll(self.page, self.twitter_config["wait_second"])
			if count > self.twitter_config["reply_count"] or max_itr < 0:
				break

			logger_config.info(f"Getting new post, old_post:: {old_post}")
			article = x_utils.get_new_post(self.page, self.twitter_config, old_post)
			if len(article) > 0:
				# geminiWrapper = pre_model_wrapper(system_instruction=self.twitter_config["html_parser_sp"], delete_files=True)
				# model_responses = geminiWrapper.send_message(article[0]["html"])
				# response = json_repair.loads(model_responses[0])
				response = x_utils.extract_tweet_info(article[0]["html"])
				user_prompt = response["description"]
				media_link = response["media_link"]
				reply_queryselector = response["reply_queryselector"]
				mimetype, file_path = self.download(media_link, article[0]["id"])
				
				old_post.append(article[0]["id"])
				if media_link and media_link is not None and file_path is None and media_link.startswith("https://"):
					continue

				if self.valid(user_prompt, file_path, mimetype):
					count += 1
					response = None
					if mimetype == "image/jpeg" or not file_path:
						response = x_utils.get_response_from_perplexity(self.browser_manager, random.choice(reply_sp), user_prompt, file_path)
					if not response:
						geminiWrapper = pre_model_wrapper(system_instruction=random.choice(reply_sp), delete_files=True)
						model_responses = geminiWrapper.send_message(user_prompt, file_path=file_path)
						response = model_responses[0]
					response = json_repair.loads(response)
					self._reply(reply_queryselector, response["reply"], article[0]["id"])
			else:
				self.reload()