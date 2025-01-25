import logger_config
import google.generativeai as genai
from local_global import global_config

genai.configure(api_key=global_config["google_ai_studio_API_KEY"])

def upload_to_gemini(path, mime_type="image/jpeg"):
    """Uploads the given file to Gemini.
    See https://ai.google.dev/gemini-api/docs/prompting_with_media
    """
    file = genai.upload_file(path, mime_type=mime_type)
    logger_config.debug(f"Uploaded file '{file.display_name}' as: {file.uri}")
    return file

def delete_file(name):
    """Deletes the file with the given name."""
    genai.delete_file(name)
    logger_config.success(f"Deleted file '{name}'")

def delete_all_files():
    for file in genai.list_files():
        delete_file(file.name)

def wait_for_files_active(files):
    """Waits for the given files to be active.

    Some files uploaded to the Gemini API need to be processed before they can be
    used as prompt inputs. The status can be seen by querying the file's "state"
    field.

    This implementation uses a simple blocking polling loop. Production code
    should probably employ a more sophisticated approach.
    """
    logger_config.debug("Waiting for file processing...")
    for name in (file.name for file in files):
        file = genai.get_file(name)
        while file.state.name == "PROCESSING":
            logger_config.debug("", seconds=10)
            file = genai.get_file(name)

        if file.state.name != "ACTIVE":
            raise Exception(f"File {file.name} failed to process")

    logger_config.success("...all files ready")

def process(system_instruction, user_prompt="", file_path=None, chat_session=None, mime_type="image/jpeg", delete_files=False, response_schema=None):
    logger_config.debug(f"system_instruction: {system_instruction}")
    all_files = [file_path] if file_path else ["no_file"]
    user_payloads = []
    model_responses = []

    if file_path:
        if file_path.endswith(".png"):
            mime_type = "image/png"
        if file_path.endswith(".mp4"):
            mime_type = "video/mp4"
        if file_path.endswith(".mkv"):
            mime_type = "video/x-matroska"

    # Create the model
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

    for i, file in enumerate(all_files):
        if not chat_session or len(all_files) > 1:
            logger_config.info("Starting a new chat session")
            delete_all_files()
            chat_session = model.start_chat()

        text = user_prompt if user_prompt else ""
        if len(all_files) > 1:
            text = f'{user_prompt} Part {i+1} of {len(all_files)}'

        logger_config.debug(f"user_prompt: {user_prompt}")
        user_payloads.append({
            "role": "user",
            "parts": [
                {"text": text}  # Add the text instruction
            ]
        })
        if file != "no_file":
            uploaded_file = upload_to_gemini(file, mime_type=mime_type)
            wait_for_files_active([uploaded_file])
            user_payloads[-1]["parts"].append(uploaded_file)

        response = chat_session.send_message(content=user_payloads[-1])
        model_responses.append({"role": "model", "parts": [response.text]})
        logger_config.debug(f"Google AI studio response: {response.text}")

        if delete_files and file != "no_file":
            delete_file(uploaded_file.name)
            delete_all_files()

    return chat_session, user_payloads, model_responses

if __name__ == "__main__":
    # Example usage
    system_instruction = "Describe the content of this image."
    file_path = "path/to/your/image.jpg"
    # _token_validator(f"{custom_env.TEMP_OUTPUT}/vwjiiqztFl_1.mkv")
