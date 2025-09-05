from custom_logger import logger_config
import requests
import common
import time
import random
import subprocess, os
import json
import cookie_converter
import json_repair

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

def download_image(url, twitter_config):
	try:
		format = url.split('format=')[-1].split('&')[0].lower() if 'format=' in url else url.split('.')[-1].lower()

		valid_formats = {"jpg", "jpeg", "png", "gif", "bmp", "tiff"}
		if format not in valid_formats:
			raise ValueError(f"Unsupported format: {format}. Supported formats are: {', '.join(valid_formats)}")

		response = requests.get(url, stream=True)
		response.raise_for_status()

		path = f"{twitter_config['config_path']}/{twitter_config['channel_name']}_image.{format}"
		common.remove_file(path)

		with open(path, "wb") as file:
			file.write(response.content)

		logger_config.success(f"Image downloaded as {path}")
		return path

	except Exception as e:
		logger_config.warning(f"Failed to download the image: {e}")

	return None

def download_video(tweet_id, twitter_config):
	try:
		path = f"whoa/{twitter_config['channel_name']}_video.mp4"
		cookie = "whoa/cookies.txt"
		if not common.file_exists(cookie):
			cookie_converter.convert_playwright_to_netscape(f"{twitter_config['config_path']}/twitter_{twitter_config['channel_name']}.json", cookie)

		common.remove_file(path)

		command_metadata = [
			"yt-dlp",
			"--extractor-args", "generic:impersonate=firefox",
			"--cookies", cookie,
			"--dump-json",
			f"{twitter_config['url']}/{twitter_config['channel_name']}/status/{tweet_id}",
		]

		result = subprocess.run(command_metadata, capture_output=True, text=True)

		if result.returncode != 0:
			logger_config.warning(f"yt-dlp metadata command failed: {result.stderr}")
			return None

		try:
			metadata = json_repair.loads(result.stdout)
		except json.JSONDecodeError:
			logger_config.warning(f"Failed to parse JSON metadata: {result.stdout}")
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
			"--extractor-args", "generic:impersonate=firefox",
			"--cookies", cookie,
			f"{twitter_config['url']}/{twitter_config['channel_name']}/status/{tweet_id}",
			"-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
			"-o", path
		]

		subprocess.run(command)
		if common.file_exists(path):
			logger_config.success(f"Video downloaded as {path}")
			return path
		else:
			logger_config.warning(f"Video download command failed, but yt-dlp did not raise an exception.")
			return None
	except Exception as e:
		logger_config.warning(f"Failed to download the video: {e}")
		return None

def get_new_post(page, twitter_config, old_post=[]):
	obj = {
		"old_post": old_post,
		"channel_name": twitter_config['channel_name']
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
				page.mouse.wheel(0, -random.randint(500, 800))
				page.wait_for_timeout(random.randint(30, 50))
			# Ensure we're at the top
			page.evaluate("window.scrollTo(0, 0)")
		else:
			# Rapid scroll to bottom
			for _ in range(10):  # Multiple quick scrolls
				page.mouse.wheel(0, random.randint(500, 800))
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

def extract_tweet_info(article_html: str) -> dict:
	from bs4 import BeautifulSoup
	soup = BeautifulSoup(article_html, 'html.parser')

	tweet_data = {
		"description": "",
		"media_link": None,
		"video_preview": None,
		"reply_queryselector": "[data-testid='reply']",
		"repost_queryselector": "[data-testid='retweet']",
		"like_queryselector": "[data-testid='like']"
	}

	# 1. Extract tweet text (content inside <span> inside <div> with lang attr)
	tweet_text_parts = soup.select('div[lang] span')
	tweet_data["description"] = ' '.join(part.get_text(strip=True) for part in tweet_text_parts)

	# 2. Extract images
	image_tags = soup.select('img[src*="twimg.com/media"]')
	tweet_data["media_link"] = [img['src'] for img in image_tags if 'src' in img.attrs]
	if tweet_data["media_link"]:
		tweet_data["media_link"] = tweet_data["media_link"][0]
	else:
		tweet_data["media_link"] = None

	# 3. Extract video preview (Twitter often uses poster image from <video> or <img>)
	video_preview_tag = soup.select_one('video, img[src*="video_thumb"]')
	if video_preview_tag:
		tweet_data["video_preview"] = video_preview_tag.get('poster') or video_preview_tag.get('src')

	print(tweet_data)
	return tweet_data

def get_response_from_perplexity(browser_manager, system_prompt, user_prompt, file_path):
	try:
		if user_prompt and common.file_exists(file_path):
			logger_config.info("Opening new browser tab...")
			new_tab = browser_manager.new_page()
			try:
				with open(os.getenv("COOKIE_2"), "r") as f:
					saved_cookies = json.load(f)
				new_tab.context.add_cookies(saved_cookies)
			except: pass

			logger_config.info("Navigating to https://perplexity.ai...")
			new_tab.goto("https://perplexity.ai")

			logger_config.info("Waiting for menu button to appear (10s)...")
			new_tab.wait_for_selector('.grow.block button[data-state="closed"]', timeout=10000)
			
			logger_config.info("Clicking the dropdown to select model...")
			new_tab.click('.grow.block button[data-state="closed"]')

			logger_config.info("Waiting for menu items to load (2s)...")
			new_tab.wait_for_timeout(2000)

			logger_config.info("Looking for menu item containing 'gemini'...")
			menu_items = new_tab.query_selector_all('div[role="menuitem"]')
			found = False
			for item in menu_items:
				text = item.inner_text().lower()
				if "gemini" in text:
					logger_config.info(f"Found model menu item: {text}. Clicking it...")
					item.click()
					new_tab.wait_for_timeout(2000)
					found = True
					break
			if not found:
				logger_config.warning("No menu item containing 'gemini' found.")

			logger_config.info("Clicking the ask input box...")
			new_tab.click('#ask-input')

			prompt = f"""System Instruction: {system_prompt}\n\nUser Prompt: {user_prompt}"""
			logger_config.info("Filling in prompt text...")
			new_tab.fill('#ask-input', prompt)

			upload_image_to_perplexity(new_tab, file_path)

			logger_config.info("Waiting for submit button to be visible...")
			new_tab.wait_for_selector('button[data-testid="submit-button"]', state='visible')

			logger_config.info("Clicking the submit button...")
			new_tab.click('button[data-testid="submit-button"]')

			logger_config.info("Waiting for response to generate (2s)...")
			new_tab.wait_for_timeout(2000)

			logger_config.info("Waiting for copy-code button to appear...")
			new_tab.wait_for_selector('button[data-testid="copy-code-button"]', state='visible')

			logger_config.info("Clicking the copy-code button to copy response...")
			new_tab.click('button[data-testid="copy-code-button"]')

			logger_config.info("Waiting a moment before reading clipboard...")
			new_tab.wait_for_timeout(2000)

			response = new_tab.evaluate("document.querySelector('code').innerText")
			new_tab.wait_for_timeout(2000)
			logger_config.info("Successfully copied response from clipboard.")
			print(response)

			logger_config.info("Parsing response as JSON...")
			new_tab.close()
			return response

	except Exception as e:
		logger_config.error(f"An error occurred in get_response_from_perplexity: {e}")

	return None

def upload_image_to_perplexity(page, file_path):
	try:
		if file_path:
			# Click the paperclip or "Attach files" button
			upload_button_selector = "button[aria-label='Attach files']"
			logger_config.info("Waiting for upload button to appear...")
			page.wait_for_selector(upload_button_selector, state='visible', timeout=10000)
			logger_config.info("Clicking upload button...")
			page.click(upload_button_selector)

			# Wait for the file input to render in the DOM
			file_input_selector = "input[type='file']"
			logger_config.info("Waiting for file input element...")
			page.wait_for_selector(file_input_selector, state="attached", timeout=5000)

			logger_config.info(f"Setting input file: {file_path}")
			page.set_input_files(file_input_selector, file_path)

			# Wait for upload to finish (heuristic: wait for thumbnail or cancel button to appear)
			logger_config.info("Waiting for upload preview or cancel button (max 20s)...")
			page.wait_for_timeout(2000)  # short wait before checking
			page.wait_for_selector("button[aria-label='Cancel upload'], img", timeout=20000)

			logger_config.info("Upload completed successfully.")
			return True

	except Exception as e:
		logger_config.error(f"Failed to upload image to Perplexity: {e}")
	return False