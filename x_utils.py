from custom_logger import logger_config
import requests
import common
from local_global import global_config
import time
import random
import subprocess
import json

def click(page, name, timeout=1000 * 60 * 2):
	logger_config.debug(f"Checking availability for {name}")
	page.wait_for_selector(name, timeout=timeout)
	element = page.query_selector(name)
	if element:
		logger_config.debug(f"Element found {name}")
		# page.hover(name, force=True)
		page.click(name, delay=4000, force=True)
		logger_config.debug(f"Clicked {name}")
		logger_config.debug("Waiting after clicked", seconds=4)
	else:
		raise ValueError(f'Element {name} does not exists.')

def download_image(url):
	try:
		format = url.split('format=')[-1].split('&')[0].lower() if 'format=' in url else url.split('.')[-1].lower()

		valid_formats = {"jpg", "jpeg", "png", "gif", "bmp", "tiff"}
		if format not in valid_formats:
			raise ValueError(f"Unsupported format: {format}. Supported formats are: {', '.join(valid_formats)}")

		response = requests.get(url, stream=True)
		response.raise_for_status()

		path = f"{global_config['base_path']}/image.{format}"
		common.remove_file(path)

		with open(path, "wb") as file:
			file.write(response.content)

		logger_config.success(f"Image downloaded as {path}")
		return path

	except Exception as e:
		logger_config.error(f"Failed to download the image: {e}")

	return None

def download_video(tweet_id):
	try:
		path = "whoa/video.mp4"
		cookie = "whoa/cookies.txt"
		common.remove_file(path)

		command_metadata = [
			"yt-dlp",
			"--cookies", cookie,
			"--dump-json",
			f"{global_config['url']}/{global_config['channel_name']}/status/{tweet_id}",
		]

		result = subprocess.run(command_metadata, capture_output=True, text=True)

		if result.returncode != 0:
			logger_config.error(f"yt-dlp metadata command failed: {result.stderr}")
			return None

		try:
			metadata = json.loads(result.stdout)
		except json.JSONDecodeError:
			logger_config.error(f"Failed to parse JSON metadata: {result.stdout}")
			return None

		is_live = metadata.get('is_live', False)

		if is_live:
			logger_config.info(f"Video {tweet_id} is a live stream. Skipping download.")
			return None
		
		if metadata.get("duration", 0) > 30 * 60:
			logger_config.info(f"Video {tweet_id} is a longer than 30 mins. Skipping download.")
			return None

		command = [
			"yt-dlp",
			"--cookies", cookie,
			f"{global_config['url']}/{global_config['channel_name']}/status/{tweet_id}",
			"-o", path
		]

		subprocess.run(command)
		if common.file_exists(path):
			logger_config.success(f"Video downloaded as {path}")
			return path
		else:
			logger_config.error(f"Video download command failed, but yt-dlp did not raise an exception.")
			return None
	except Exception as e:
		logger_config.error(f"Failed to download the video: {e}")
		return None

def get_new_post(page, old_post=[]):
	obj = {
		"old_post": old_post,
		"channel_name": global_config['channel_name']
	}
	return page.evaluate(
		"""
		(obj) => {
			function isElementInViewport(element) {
				const rect = element.getBoundingClientRect();
				const windowHeight = window.innerHeight || document.documentElement.clientHeight;
				const windowWidth = window.innerWidth || document.documentElement.clientWidth;

				const styles = window.getComputedStyle(element);
				if (styles.display === 'none' || styles.visibility === 'hidden' || styles.opacity === '0' || rect.width === 0 || rect.height === 0) {
					return false;
				}

				return (
					rect.top <= windowHeight &&
					rect.bottom >= 0 &&
					rect.left <= windowWidth &&
					rect.right >= 0
				);
			}

			let articles = [];
			let postLimit = 20;  // Max posts to check

			for (let post of document.querySelectorAll("main div[aria-label='Home timeline'] article")) {
				if (postLimit <= 0) break;

				const isVisible = isElementInViewport(post);
				if (!isVisible) continue; // Skip if not visible

				let shouldSkip = false;
				let divs = post.querySelectorAll('div[data-testid]');
				for (let div of divs) {
					if (div.getAttribute('data-testid')?.toLowerCase() === ("useravatar-container-" + obj.channel_name).toLowerCase()) {
						console.log("ignore logged-in account");
						shouldSkip = true;
						break;
					}
				}
				if (shouldSkip) continue;

				const outerHTML = post.outerHTML;
				const match = outerHTML.match(/\/status\/(.*?)"/);
				if (match) {
					console.log(match[1]);
					if (obj.old_post.includes(match[1])) {
						continue;
					}
					articles.push({
						"visible": isVisible ? 1 : 0,  // Add visibility status to output
						"html": outerHTML,
						"id": match[1]
					});
					postLimit = -1;
					break;  // Return immediately after finding a new post
				}
				postLimit--;
			}
			return articles;
		}
		""",
		obj
	)

def simulate_human_scroll(page, duration_seconds):
	"""
	Simulates ultra-smooth human-like scrolling behavior on Twitter with occasional sudden scrolls.
	
	Args:
		page (Page): Playwright page object
		duration_seconds (int): Duration to scroll in seconds
	"""
	start_time = time.time()
	
	def smooth_scroll(distance, direction):
		"""Helper function for smooth scrolling"""
		remaining = distance
		while remaining > 0:
			increment = random.randint(5, 10)
			increment = min(increment, remaining)
			page.mouse.wheel(0, increment * direction)
			page.wait_for_timeout(random.randint(20, 30))
			remaining -= increment
	
	def sudden_scroll():
		"""Helper function for sudden scrolls to top/bottom"""
		# Decide whether to scroll to top or bottom
		to_top = random.choice([True, False])
		
		if to_top:
			# Rapid scroll to top with slightly varying speeds
			for _ in range(10):  # Multiple quick scrolls
				page.mouse.wheel(0, -800)
				page.wait_for_timeout(random.randint(30, 50))
			# Ensure we're at the top
			page.evaluate("window.scrollTo(0, 0)")
		else:
			# Rapid scroll to bottom
			for _ in range(10):  # Multiple quick scrolls
				page.mouse.wheel(0, 800)
				page.wait_for_timeout(random.randint(30, 50))
	
	while time.time() - start_time < duration_seconds:
		# 2% chance of sudden scroll to top/bottom
		if random.random() < 0.02:
			sudden_scroll()
			# Pause after sudden scroll to simulate orientation
			time.sleep(random.uniform(1, 2))
			continue
			
		# Normal smooth scrolling behavior
		total_scroll = random.randint(300, 800)
		direction = random.choices([1, -1], weights=[0.9, 0.1])[0]
		
		smooth_scroll(total_scroll, direction)
		
		# Wait briefly for content to settle
		page.wait_for_timeout(200)
		
		# Natural reading pause
		read_time = random.uniform(1, 3)
		time.sleep(read_time)
		
		# Occasional longer pause (15% chance)
		if random.random() < 0.15:
			time.sleep(random.uniform(1.5, 3))
		
		# Check for new tweets
		try:
			page.wait_for_selector('[data-testid="tweet"]', timeout=800)
		except:
			time.sleep(0.5)