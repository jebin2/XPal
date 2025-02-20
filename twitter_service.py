from local_global import load_toml
import session_utils
import random
from custom_logger import logger_config
from twitter_reply import TwitterReply
from twitter_like import TwitterLike
from twitter_quote import TwitterQuote
from twitter_post import TwitterPost
from twitter_prop import TwitterProp
import traceback
from local_global import global_config

class TwitterService(TwitterProp):
	action_map = {
		"reply": TwitterReply,
		"like": TwitterLike,
		"quote": TwitterQuote,
		"post": TwitterPost
	}

	def __init__(self, page, channel_name=None):
		super().__init__(page)
		self.channel_name = channel_name
		load_toml(self.channel_name)
		self.load_page()
		session_utils.load_session(self.page)
		self.reload()

	def _get_actions(self):
		actions = global_config["actions"].split(",")
		random.shuffle(actions)
		return actions

	def play(self):
		for type in self._get_actions():
			try:
				action = self.action_map.get(type)(self.page)
				action.start()
			except Exception as e:
				logger_config.error(f"Error occurred for {self.channel_name} :: {type} {str(e)} \m {traceback.format_exc()}")
				self.load_page()

		return None

