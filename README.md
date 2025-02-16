# Twitter Automation Bot with AI Content Generation

A Python bot automating Twitter actions using Google AI Studio for content and analysis. Likes, replies, quotes, and posts tweets with AI assistance.

## Features

- Automated Twitter Actions (like, reply, quote, post)
- Google AI Studio integration for content generation
- Configurable actions & frequency via TOML files
- Session management using cookies for persistent login
- Detailed logging with colored output
- Media download and processing
- Modular code design
- Channel rotation for multiple accounts
- Rate limit aware with configurable wait times

## Configuration

Uses TOML files: `twitter.toml` (base config), `[channel_name].toml` (channel overrides), `.env` (sensitive keys).

- **`twitter.toml`**: Base settings, API keys, channel list, action counts, AI prompts, UI selectors
- **`.env`**: Store `GEMINI_API_KEYS` API key and channel_names = list of channel name comma separated
- **`[channel_name].toml`**: Channel-specific overrides for settings

## Setup Instructions

1. **Prerequisites**: Python 3.7+, Brave Browser, Google AI Studio API Key, TOML library

2. **Installation**:
   ```bash
   git clone <repository_url>
   cd <repository_directory>
   pip install -r requirements.txt
   ```

3. **Configuration**:
   - Edit `twitter.toml` (settings, prompts)
   - Set API key in `.env` under base_path dir
   - Create `[channel_name].toml` for channel-specific settings under base_path dir

4. **Session Setup**: Run `python main.py`, manually login to Twitter in Brave browser within 90s. Cookies saved for reuse.

## Usage

### Running

```bash
python main.py
```

Bot starts, loads config/session, performs actions (reply, like, quote, post) on channels, waits, and repeats.

## Customization

- **Action Counts**: `reply_count`, `like_count`, etc. in TOML
- **Wait Times**: `wait_second` in `twitter.toml`
- **AI Prompts**: Customize `*_sp` prompts in TOML
- **Channel Settings**: Use `[channel_name].toml` for specific settings
- **Action Types**: Modify `_get_actions` in `twitter_service.py` to change action types


## Disclaimer

Use responsibly, comply with Twitter TOS, be aware of rate limits, UI changes may require selector updates. Session cookies are sensitive. `headless=False` for setup, consider `headless=True` for automation.

**Tweet Responsibly!**
