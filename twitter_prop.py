import json_repair
from gemini_config import pre_model_wrapper
from custom_logger import logger_config
import x_utils
import piexif
from PIL import Image, PngImagePlugin
import common
import json, subprocess, os

class TwitterProp:
	def __init__(self, browser_manager, page, twitter_config):
		self.browser_manager = browser_manager
		self.page = page
		self.twitter_config = twitter_config

	def valid(self, user_prompt, file_path, mimetype=None):
		is_valid_post = True
		if not user_prompt and not file_path:
			return False
		if self.twitter_config["specifc_post_validation_sp"]:
			response = None
			if mimetype == "image/jpeg" or not file_path:
				response = x_utils.get_response_from_perplexity(self.browser_manager, self.twitter_config["specifc_post_validation_sp"], user_prompt, file_path)
			if not response:
				geminiWrapper = pre_model_wrapper(system_instruction=self.twitter_config["specifc_post_validation_sp"], delete_files=True)
				model_responses = geminiWrapper.send_message(user_prompt, file_path=file_path)
				response = model_responses[0]
			response = json_repair.loads(response)
			is_valid_post = True if response[self.twitter_config["specifc_post_key"]].lower() == "yes" else False

		return is_valid_post

	def load_page(self):
		self.page.goto(self.twitter_config["url"])
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
			file_path = x_utils.download_video(tweet_id, self.twitter_config)
			if common.file_exists(file_path):
				return "video/mp4", file_path

			file_path = x_utils.download_image(media_link, self.twitter_config)
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

			elif image.endswith(".mp4"):
				result = subprocess.run(
					["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", image],
					stdout=subprocess.PIPE,
					stderr=subprocess.PIPE,
					text=True
				)
				info = json.loads(result.stdout)
				tags = info.get("format", {}).get("tags", {})
				data = tags.get("description")

			return json_repair.loads(data)
		except:
			return None

	def get_media_files(self):
		if os.getenv("USE_HF_DATA", "false").lower() == "true":
			from custom_lib.lib.hf_dataset_client import HFDatasetClient
			hf_client = HFDatasetClient()
			media_files = hf_client.list_files()
			cond_path = self.twitter_config["media_path"].split("/")[-1]
			media_files = [
				file for file in media_files
				if cond_path in file and file.endswith((".png", ".jpg", ".mkv", ".mp4"))
			]
			return media_files

		media_files = [
			file for file in common.list_files_recursive(self.twitter_config["media_path"])
			if file.endswith((".png", ".jpg", ".mkv", ".mp4"))
		]
		media_files.sort(key=os.path.getmtime, reverse=True)
		return media_files

	def get_media_files_downloaded(self, file_path):
		if os.getenv("USE_HF_DATA", "false").lower() == "true":
			temp_path = f"tempOutput/{os.path.basename(file_path)}"
			from custom_lib.lib.hf_dataset_client import HFDatasetClient
			hf_client = HFDatasetClient()
			hf_client.download(file_path, temp_path)
			return temp_path

		return file_path

	def delete_media_file(self, file_path):
		if os.getenv("USE_HF_DATA", "false").lower() == "true":
			from custom_lib.lib.hf_dataset_client import HFDatasetClient
			hf_client = HFDatasetClient()
			hf_client.delete(file_path)
		else:
			common.remove_file(file_path)

	def go_back(self):
		x_utils.click(self.page, self.twitter_config["back_selector"])
		self.page.wait_for_load_state("domcontentloaded")
		logger_config.debug("Precaution wait after load...", seconds=2)
		x_utils.click(self.page, self.twitter_config["main_home"])
		if "https://x.com/home" not in self.page.url:
			self.load_page()