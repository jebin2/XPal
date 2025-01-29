from local_global import global_config
import x_utils
import google_ai_studio
import logger_config
import json
import random
from twitter_prop import TwitterProp

class TwitterReply(TwitterProp):
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

	def _reply(self, reply_queryselector, reply, id):
		x_utils.click(self.page, f'article:has(a[href*="{id}"])')
		self.page.wait_for_load_state("domcontentloaded")
		x_utils.click(self.page, f'article:has(a[href*="{id}"]) >> {reply_queryselector}')
		element = self.page.query_selector(global_config["disable_warning_selector"])
		if element:
			x_utils.click(self.page, global_config["disable_warning_selector"])
			# To remove popup
			self.page.keyboard.press("Escape")
			self.page.keyboard.press("Escape")
		else:
			textbox = self.page.locator(global_config["reply_editor_selector"])
			textbox.type(reply)
			textbox.type(" ")
			x_utils.click(self.page, global_config["reply_tweet_selector"])
			x_utils.click(self.page, global_config["back_selector"])
			self.page.wait_for_load_state("domcontentloaded")

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

		max_itr = 20
		while True:
			if max_itr == 10:
				self.reload()

			max_itr -= 1
			logger_config.info(f'{global_config["wait_second"]} sec scroll')
			x_utils.simulate_human_scroll(self.page, global_config["wait_second"])
			if count > global_config["reply_count"] or max_itr < 0:
				break

			logger_config.info(f"Getting new post, old_post:: {old_post}")
			article = x_utils.get_new_post(self.page, old_post)
			if len(article) > 0:
				_, _, model_responses = google_ai_studio.process(global_config["html_parser_sp"], article[0]["html"])
				response = json.loads(model_responses[0]["parts"][0])
				user_prompt = response["description"]
				media_link = response["media_link"]
				reply_queryselector = response["reply_queryselector"]
				mime_type, file_path = self.download(media_link)
				
				old_post.append(article[0]["id"])

				if self.valid(user_prompt, file_path):
					count += 1
					_, _, model_responses = google_ai_studio.process(random.choice(reply_sp), user_prompt, file_path=file_path, mime_type=mime_type)
					response = json.loads(model_responses[0]["parts"][0])
					self._reply(reply_queryselector, response["reply"], article[0]["id"])
			else:
				self.reload()