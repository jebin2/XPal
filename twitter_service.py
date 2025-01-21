from local_global import global_config, load_toml
import session_utils
import random
import logger_config
from twitter_reply import TwitterReply
from twitter_like import TwitterLike
import traceback

class TwitterService:
    action_map = {
        "reply": TwitterReply,
        "like": TwitterLike
	}

    def __init__(self, page, channel_name=None):
        self.page = page
        self.channel_name = channel_name
        load_toml(self.channel_name)
        self.load_page()
        session_utils.load_session(self.page)
        self.reload()

    def load_page(self):
        self.page.goto(global_config["url"])
        self.page.wait_for_load_state("domcontentloaded")
        logger_config.debug("Precaution wait after load...", seconds=5)

    def reload(self):
        self.page.reload()
        self.page.wait_for_load_state("domcontentloaded")
        logger_config.debug("Precaution wait after load...", seconds=5)

    def _get_actions(self):
        actions = ["reply", "like"]
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

