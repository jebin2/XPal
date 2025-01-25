import json
import common
from local_global import global_config
import logger_config

def save_session(page):
	if not common.file_exists(f"{global_config['base_path']}/twitter_{global_config['channel_name']}.json"):
		logger_config.info("Please signup within 90sec. Next time it will be reused.", seconds=90)
		cookies = page.context.cookies()
		with open(f"{global_config['base_path']}/twitter_{global_config['channel_name']}.json", 'w') as f:
			json.dump(cookies, f)

def load_session(page):
	if common.file_exists(f"{global_config['base_path']}/twitter_{global_config['channel_name']}.json"):
		with open(f"{global_config['base_path']}/twitter_{global_config['channel_name']}.json", 'r') as f:
			cookies = json.load(f)
			page.context.add_cookies(cookies)
			return True
	else:
		save_session(page)
		return load_session(page)