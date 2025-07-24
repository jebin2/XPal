import json
import common
from local_global import global_config

def save_session(page, validator):
	# if not common.file_exists(f"{global_config['config_path']}/twitter_{global_config['channel_name']}.json"):
	if not validator():
		page.evaluate("""
			const overlay = document.createElement('div');
			let timeLeft = 300;  // 300 seconds countdown

			overlay.innerHTML = `Please sign in first time. Next time it will be reused.<br>Please Sign in within <span id="countdown">300</span> sec.`;
			overlay.style.position = 'fixed';
			overlay.style.top = '10px';  // Position at the top
			overlay.style.left = '10px';  // Position at the left
			overlay.style.background = 'rgba(0, 0, 0, 0.7)'; // Dark background
			overlay.style.color = '#FF0000';  // Dark red text
			overlay.style.fontSize = '20px';
			overlay.style.fontWeight = 'bold';
			overlay.style.padding = '10px 15px';
			overlay.style.border = '3px solid yellow';
			overlay.style.borderRadius = '5px';
			overlay.style.boxShadow = '0 0 10px yellow';
			overlay.style.zIndex = '9999';
			overlay.style.textAlign = 'center';
			overlay.style.animation = 'blink 1s infinite';  // Apply blinking animation

			// Add CSS animation for blinking
			const style = document.createElement('style');
			style.innerHTML = `
				@keyframes blink {
					0% { opacity: 1; }
					50% { opacity: 0; }
					100% { opacity: 1; }
				}
			`;
			document.head.appendChild(style);

			document.body.appendChild(overlay);

			// Countdown function
			const countdown = setInterval(() => {
				timeLeft -= 1;
				document.getElementById("countdown").innerText = timeLeft;

				if (timeLeft <= 0) {
					clearInterval(countdown);
					overlay.remove();
				}
			}, 1000);  // Update every second
""")

		while not validator():
			if validator():
				break
		# cookies = page.context.cookies()
		# with open(f"{global_config['config_path']}/twitter_{global_config['channel_name']}.json", 'w') as f:
		# 	json.dump(cookies, f)

def load_session(page, validator):
	# if common.file_exists(f"{global_config['config_path']}/twitter_{global_config['channel_name']}.json"):
	# 	with open(f"{global_config['config_path']}/twitter_{global_config['channel_name']}.json", 'r') as f:
	# 		cookies = json.load(f)
	# 		page.context.add_cookies(cookies)
	# 		return True
	if validator():
		return True
	else:
		save_session(page, validator)
		return load_session(page, validator)