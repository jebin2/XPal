from custom_logger import logger_config
pre_model_wrapper=None
try:
	from functools import partial
	from gemiwrap import GeminiWrapper

	pre_model_wrapper = partial(GeminiWrapper, model_name="gemini-flash-latest")
except:
	logger_config.warning("Gemini Wrapper is not initialised.")