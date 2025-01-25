import toml
import json
import logger_config

global_config = {}

def load_toml(channel_name=None):
    with open("twitter.toml", 'r') as file:
        toml_data = toml.load(file)
        global_config.update(toml_data)

    if channel_name:
        with open(f"{global_config['base_path']}/{channel_name}.toml", 'r') as file:
            toml_data = toml.load(file)
            global_config.update(toml_data)

    with open(f"{global_config['base_path']}/.private.toml", 'r') as file:
        toml_data = toml.load(file)
        global_config.update(toml_data)

    logger_config.info(json.dumps(global_config, indent=4))

load_toml()