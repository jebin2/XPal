import json

def convert_playwright_to_netscape(playwright_json, output_file):
	with open(playwright_json, "r") as f:
		data = json.load(f)

	with open(output_file, "w") as f:
		f.write("# Netscape HTTP Cookie File\n")
		for cookie in data:
			domain = cookie["domain"]
			flag = "TRUE" if domain.startswith(".") else "FALSE"
			path = cookie["path"]
			secure = "TRUE" if cookie.get("secure", False) else "FALSE"
			expiry = cookie.get("expires", "0")  # Set to 0 if not available
			name = cookie["name"]
			value = cookie["value"]
			f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expiry}\t{name}\t{value}\n")

	print(f"Converted cookies saved to: {output_file}")