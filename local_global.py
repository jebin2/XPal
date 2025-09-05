def load_toml(channel_name=None):
	import toml
	import common
	config = {}

	# Load base config
	with open("twitter.toml", 'r') as file:
		config.update(toml.load(file))

	channel_file = f"{config['config_path']}/{channel_name}.toml"
	if not common.file_exists(channel_file):
		with open(channel_file, 'w') as f:
			f.write(f'channel_name = "{channel_name}"\n')
	with open(channel_file, 'r') as file:
		config.update(toml.load(file))

	private_file = f"{config['config_path']}/.private.toml"
	if common.file_exists(private_file):
		with open(private_file, 'r') as file:
			config.update(toml.load(file))

	return config