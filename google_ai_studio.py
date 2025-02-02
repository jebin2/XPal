import logger_config
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from local_global import global_config

USED_API_KEYS = set()
MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".mp4": "video/mp4",
    ".mkv": "video/x-matroska"
}

def upload_to_gemini(path, mime_type="image/jpeg"):
    """Uploads the given file to Gemini."""
    file = genai.upload_file(path, mime_type=mime_type)
    logger_config.debug(f"Uploaded file '{file.display_name}' as: {file.uri}")
    return file

def delete_file(name):
    """Deletes a file by name."""
    genai.delete_file(name)
    logger_config.success(f"Deleted file '{name}'")

def delete_all_files():
    """Deletes all uploaded files."""
    for file in genai.list_files():
        delete_file(file.name)

def wait_for_files_active(files):
    """Waits until uploaded files are active."""
    logger_config.debug("Waiting for file processing...")
    for name in (file.name for file in files):
        file = genai.get_file(name)
        while file.state.name == "PROCESSING":
            logger_config.debug("", seconds=10)
            file = genai.get_file(name)

        if file.state.name != "ACTIVE":
            raise Exception(f"File {file.name} failed to process")
    logger_config.success("All files are ready.")

def handle_quota_exceeded():
    """Switches API key if quota is exceeded."""
    for key in global_config["google_ai_studio_API_KEY"].split(","):
        if key not in USED_API_KEYS:
            logger_config.info(f'Current Key: {key}')
            genai.configure(api_key=key)
            USED_API_KEYS.add(key)
            return

def process(system_instruction, user_prompt="", file_path=None, chat_session=None, delete_files=False, response_schema=None):
    if len(USED_API_KEYS) == 0:
        handle_quota_exceeded()

    logger_config.debug(f"System instruction: {system_instruction}")
    
    all_files = [file_path] if file_path else [None]
    user_payloads, model_responses = [], []

    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_schema": response_schema,
        "response_mime_type": "application/json"
    }

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        # model_name="gemini-2.0-flash-exp",
        # model_name="gemini-1.5-flash",
        generation_config=generation_config,
        system_instruction=system_instruction,
    )

    if not chat_session or len(all_files) > 1:
        logger_config.info("Starting a new chat session")
        delete_all_files()
        chat_session = model.start_chat()

    for i, file in enumerate(all_files):

        text = user_prompt if user_prompt else ""
        if len(all_files) > 1:
            text = f'{user_prompt} Part {i+1} of {len(all_files)}'

        logger_config.debug(f"user_prompt: {text}")
        user_payloads.append({
            "role": "user",
            "parts": [
                {"text": text}
            ]
        })
        if file:
            mime_type = MIME_TYPES.get(file[file.rfind("."):].lower(), "application/octet-stream")
            uploaded_file = upload_to_gemini(file, mime_type=mime_type)
            wait_for_files_active([uploaded_file])
            user_payloads[-1]["parts"].append(uploaded_file)

        response = None
        for _ in range(len(global_config["google_ai_studio_API_KEY"].split(","))):
            try:
                response = chat_session.send_message(content=user_payloads[-1])
                break
            except ResourceExhausted:
                logger_config.warning("Quota exceeded, switching API key...")
                handle_quota_exceeded()

        logger_config.debug(f"Model response: {response}")
        model_responses.append({"role": "model", "parts": [response.text]})
        
        if delete_files and file:
            delete_file(uploaded_file.name)
            delete_all_files()

    return chat_session, user_payloads, model_responses

if __name__ == "__main__":
    system_instruction = "Describe the content of this image."
    file_path = "path/to/your/image.jpg"
