import logger_config
import requests
import common
from local_global import global_config

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

def download_video(url):
    try:
        response = requests.get(url, stream=True)
        path = f"{global_config['base_path']}/video.mp4"
        common.remove_file(path)
        if response.status_code == 200:
            with open(path, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024):
                    file.write(chunk)

            logger_config.success(f"Video downloaded as {path}")
            return path
    except:
        pass

    return None

def get_new_post(page, old_post=[]):
    return page.evaluate(
        """
        (oldPost) => {
            let main = document.getElementsByTagName("main")[0];
            let home_timeline;
            for (let div of main.querySelectorAll("div")) {
                if (div.ariaLabel === "Home timeline") {
                    home_timeline = div;
                    break;
                }
            }
            let articles = [];
            let postLimit = 20;  // Max posts to check

            while(postLimit > 0) {
                for (post of home_timeline.querySelectorAll("article")) {
                    post.classList.remove("current_processing_post");
                    postLimit--;
                    if (postLimit > 0) {
                        break;
                    }
                    post.scrollIntoView({ behavior: "smooth" })
                    outerHTML = post.outerHTML
                    const match = outerHTML.match(/\/status\/(.*?)"/);
                    if (match) {
                        console.log(match[1]);
                        if (oldPost.includes(match[1])) {
                            continue;
                        }
                        post.classList.add("current_processing_post");
                        articles.push({
                            "visible": 1,
                            "html": post.outerHTML,
                            "id": match[1]
                        });
                        postLimit = -1;
                        break;  // Return immediately after finding a new post
                    }
                }
            }

            return articles;
        }
        """,
        old_post
    )
