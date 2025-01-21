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
        response = requests.get(url)
        path = f"{global_config['base_path']}/image.jpg"
        common.remove_file()
        with open(path, "wb") as file:
            file.write(response.content)

        logger_config.success(f"Image downloaded as {path}")
        return path
    except:
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
            let postLimit = 200;  // Max posts to check

            while(postLimit > 0) {
                for (post of home_timeline.querySelectorAll("article")) {
                    post.classList.remove("current_processing_post");
                    postLimit--;
                    if (postLimit > 0) {
                        break;
                    }
                    post.scrollIntoView({ behavior: "smooth" })
                    let text = post.innerText.replace(/[^a-zA-Z \\n]/g, '').replace(/\\n/g, '').toLowerCase();
                    console.log(text)
                    let has_data = oldPost.filter(old => {
                        let old_text = old.description.replace(/[^a-zA-Z \\n]/g, '').replace(/\\n/g, '').toLowerCase();
                        if (old_text && text) {
                            console.log(old_text);
                            return text.includes(old.media_link) || text.includes(old_text);
                        }
                        return true;
                    });

                    if (!has_data[0]) {
                        post.classList.add("current_processing_post");
                        articles.push({
                            "visible": 1,
                            "html": post.outerHTML,
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
