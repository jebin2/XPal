import toml
import json
from custom_logger import logger_config
import os

global_config = {}

def load_toml(channel_name=None):
	with open("twitter.toml", 'r') as file:
		toml_data = toml.load(file)
		global_config.update(toml_data)

	if channel_name:
		if not os.path.exists(f"{global_config['config_path']}/{channel_name}.toml"):
			content = f"""channel_name = "{channel_name}"
"""
			with open(f"{global_config['config_path']}/{channel_name}.toml", 'w') as f:
				f.write(content)

		with open(f"{global_config['config_path']}/{channel_name}.toml", 'r') as file:
			toml_data = toml.load(file)
			global_config.update(toml_data)

	with open(f"{global_config['config_path']}/.private.toml", 'r') as file:
		toml_data = toml.load(file)
		global_config.update(toml_data)

	logger_config.info(json.dumps(global_config, indent=4))

load_toml()