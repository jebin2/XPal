from local_global import global_config
import x_utils
from gemini_config import pre_model_wrapper
from custom_logger import logger_config
import json_repair
import random
from twitter_prop import TwitterProp

class TwitterQuote(TwitterProp):
	
	def __init__(self, browser_manager, page):
		super().__init__(browser_manager, page)

	def valid(self, user_prompt, file_path, mimetype=None):
		if super().valid(user_prompt, file_path, mimetype):
			is_valid_post = True
			if global_config["quote_decider_sp"]:
				response = None
				if mimetype == "image/jpeg" or not file_path:
					response = x_utils.get_response_from_perplexity(self.browser_manager, global_config["quote_decider_sp"], user_prompt, file_path)
				if not response:
					geminiWrapper = pre_model_wrapper(system_instruction=global_config["quote_decider_sp"], delete_files=True)
					model_responses = geminiWrapper.send_message(user_prompt, file_path=file_path)
					response = model_responses[0]
				response = json_repair.loads(response)
				is_valid_post = True if response["quote"].lower() == "yes" else False

			return is_valid_post

		return False

	def _quote(self, repost_queryselector, reply, id):
		x_utils.click(self.page, f'article:has(a[href*="{id}"]) div div div')
		self.page.wait_for_load_state("domcontentloaded")
		x_utils.click(self.page, f'article:has(a[href*="{id}"]) >> {repost_queryselector}')
		
		# Evaluate with more detailed feedback
		result = self.page.evaluate("""() => {
			try {
				const menuItems = document.querySelectorAll("#layers [role='menu'] a");
				if (menuItems.length > 2) {
					return { success: false, error: 'Unknown menu items found' };
				}
				
				const retweetButton = document.querySelector("#layers [role='menu'] [data-testid='retweetConfirm']");
				if (!retweetButton) {
					return { success: false, error: 'Retweet button not found' };
				}
				
				const quoteButton = retweetButton.nextElementSibling;
				if (!quoteButton) {
					return { success: false, error: 'Quote button not found' };
				}
				
				quoteButton.click();
				return { success: true };
			} catch (err) {
				return { success: false, error: err.message };
			}
		}""")

		if result.get('success'):
			logger_config.debug("Wait to read post", seconds=random.randint(5, 8))
			
			textbox = self.page.locator(global_config["reply_editor_selector"])
			textbox.type(reply)
			textbox.type(" ")
			x_utils.click(self.page, global_config["reply_tweet_selector"])
			
		self.go_back()


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
			if count > global_config["quote_count"] or max_itr < 0:
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
				repost_queryselector = response["repost_queryselector"]
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
					if len(response["reply"]) < 250:
						self._quote(repost_queryselector, response["reply"], article[0]["id"])
			else:
				self.reload()