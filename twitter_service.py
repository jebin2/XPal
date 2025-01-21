from local_global import global_config, load_toml
import session_utils
import random
import logger_config
from twitter_reply import TwitterReply
from twitter_like import TwitterLike
from twitter_quote import TwitterQuote
from twitter_prop import TwitterProp
import traceback

class TwitterService(TwitterProp):
    action_map = {
        "reply": TwitterReply,
        "like": TwitterLike,
        "quote": TwitterQuote
	}

    def __init__(self, page, channel_name=None):
        super().__init__(page)
        self.channel_name = channel_name
        load_toml(self.channel_name)
        self.load_page()
        session_utils.load_session(self.page)
        self.reload()

    def load_page(self):
        self.page.goto(global_config["url"])
        self.page.wait_for_load_state("domcontentloaded")
        logger_config.debug("Precaution wait after load...", seconds=5)

    def _get_actions(self):
        actions = ["quote"]
        random.shuffle(actions)
        return actions

    def play(self):
        for type in self._get_actions():
            try:
                action = self.action_map.get(type)(self.page)
                action.start()
            except Exception as e:
                logger_config.error(f"Error occurred for {self.channel_name} :: {type} {str(e)} \m {traceback.format_exc()}")

        return None

