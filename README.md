# Telegram Bot with GPT-4o-mini Integration

A Telegram bot that integrates with GPT-4o-mini to provide intelligent responses when directly mentioned (@) in private chats and authorized group chats.

## Setup

1. Clone this repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your configuration:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   AUTHORIZED_USER_ID=your_telegram_user_id
   OPENAI_API_KEY=your_openai_api_key
   ```
5. Run the bot:
   ```bash
   python bot.py
   ```

## Configuration

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token (obtain from @BotFather)
- `AUTHORIZED_USER_ID`: Your Telegram user ID (can be obtained from @userinfobot)
- `OPENAI_API_KEY`: Your OpenAI API key for GPT-4o-mini access

## Usage

1. Start a private chat with your bot
2. In group chats, mention the bot using @
3. The bot will respond only to authorized users and in authorized groups

## Features

- Direct @ mention detection
- User authorization
- Group chat authorization
- Conversation context preservation
- GPT-4o-mini integration 