import session_utils
import random
from custom_logger import logger_config
from twitter_reply import TwitterReply
from twitter_like import TwitterLike
from twitter_quote import TwitterQuote
from twitter_post import TwitterPost
from twitter_prop import TwitterProp
import traceback

class TwitterService(TwitterProp):
	action_map = {
		"reply": TwitterReply,
		"like": TwitterLike,
		"quote": TwitterQuote,
		"post": TwitterPost
	}

	def __init__(self, browser_manager, page, twitter_config, channel_name=None):
		super().__init__(browser_manager, page, twitter_config)
		self.channel_name = channel_name
		self.load_page()
		session_utils.load_session(self.page, self.did_login, self.twitter_config)
		self.reload()

	def _get_actions(self):
		actions = self.twitter_config["actions"].split(",")
		random.shuffle(actions)
		return actions

	def did_login(self):
		try:
			locator = self.page.locator(self.twitter_config["post_textarea_selector"])
			return locator.is_visible()
		except Exception as e:
			print(e)

		return False

	def play(self):
		for type in self._get_actions():
			try:
				action = self.action_map.get(type)(self.browser_manager, self.page)
				action.start()
			except Exception as e:
				logger_config.error(f"Error occurred for {self.channel_name} :: {type} {str(e)} \m {traceback.format_exc()}")
				self.load_page()

		return None

