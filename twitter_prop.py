from local_global import global_config
import json_repair
from gemini_config import pre_model_wrapper
from custom_logger import logger_config
import x_utils
import piexif
from PIL import Image, PngImagePlugin
import common

class TwitterProp:
	def __init__(self, page):
		self.page = page

	def valid(self, user_prompt, file_path):
		is_valid_post = True
		if not user_prompt and not file_path:
			return False
		if global_config["specifc_post_validation_sp"]:
			geminiWrapper = pre_model_wrapper(system_instruction=global_config["specifc_post_validation_sp"], delete_files=True)
			model_responses = geminiWrapper.send_message(user_prompt, file_path=file_path)
			response = json_repair.loads(model_responses[0])
			is_valid_post = True if response[global_config["specifc_post_key"]].lower() == "yes" else False

		return is_valid_post

	def load_page(self):
		self.page.goto(global_config["url"])
		self.page.wait_for_load_state("domcontentloaded")
		logger_config.debug("Precaution wait after load...", seconds=5)

	def reload(self):
		self.page.reload()
		self.page.wait_for_load_state("domcontentloaded")
		logger_config.debug("Precaution wait after load...", seconds=5)
		# To remove popup
		self.page.keyboard.press("Escape")
		self.page.keyboard.press("Escape")

	def download(self, media_link, tweet_id):
		try:
			file_path = x_utils.download_video(tweet_id)
			if common.file_exists(file_path):
				return "video/mp4", file_path

			file_path = x_utils.download_image(media_link)
			if common.file_exists(file_path):
				return "image/jpeg", file_path

		except:
			pass

		return None, None

	def image_metadata(self, image):
		try:
			data = None
			if image.endswith(".png"):
				with Image.open(image) as img:
					data = img.info.get("metadata")

			elif image.endswith(".jpg"):
				exif_data = piexif.load(image)
				data = exif_data["0th"].get(piexif.ImageIFD.XPComment)

			return json_repair.loads(data)
		except:
			return None


	def go_back(self):
		x_utils.click(self.page, global_config["back_selector"])
		self.page.wait_for_load_state("domcontentloaded")
		logger_config.debug("Precaution wait after load...", seconds=2)
		x_utils.click(self.page, global_config["main_home"])
		if "https://x.com/home" not in self.page.url:
			self.load_page()