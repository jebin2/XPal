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

- **`twitter.toml`**: Base settings, action counts, AI prompts, UI selectors
- **`.env`**: Store `GEMINI_API_KEYS` API key and `channel_names` = list of channel name comma separated
- **`[channel_name].toml`**: Channel-specific overrides for settings it will create under `config_path`

## Setup Instructions

1. **Prerequisites**: Python 3.7+, Google AI Studio API Key

2. **Installation**:
   ```bash
   git clone https://github.com/jebin2/XPal.git
   cd XPal
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configuration**:
   - Edit `twitter.toml` (settings, prompts) under `config_path`
   - Set API key in `.env`
   - Create `[channel_name].toml` for channel-specific settings under `config_path` dir

4. **Session Setup**: Run `python main.py`, manually login to X first time ony. Cookies will be saved for reuse next time in channel_name.json `config_path`.

## Usage

### Running

```bash
python main.py
```

Bot starts, loads config/session, performs actions (reply, like, quote, post) on channels, waits, and repeats.

## Customization

- **Action Counts**: `reply_count`, `like_count`, `quote_count`, `post_count` etc. in TOML
- **Wait Times**: `wait_second` in `twitter.toml`
- **AI Prompts**: Customize `*_sp` prompts in TOML
- **Channel Settings**: Use `[channel_name].toml` for specific settings under `config_path`
- **Action Types**: Modify `actions` in `twitter.toml` to change action types

**Tweet Responsibly!**