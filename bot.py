import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import ollama

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
AUTHORIZED_USER_ID = int(os.getenv('AUTHORIZED_USER_ID'))
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')

# Authorized groups (add group IDs here)
AUTHORIZED_GROUPS = set()  # You can add group IDs here, e.g., {123456789, 987654321}

# Conversation history storage
conversation_history = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text('Hi! I\'m your AI assistant. Mention me with @ to get a response.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await update.message.reply_text('Help!')

async def authorize_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Authorize a group to use the bot."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    logger.info(f"Authorization attempt by user {user_id} in chat {chat_id}")
    
    # Check if the user is authorized (only you can authorize groups)
    if user_id != AUTHORIZED_USER_ID:
        logger.warning(f"Unauthorized user {user_id} attempted to authorize chat {chat_id}")
        await update.message.reply_text("You are not authorized to use this command.")
        return

    # Check if it's a group chat
    if chat_id > 0:
        logger.warning(f"Authorization attempted in non-group chat {chat_id}")
        await update.message.reply_text("This command can only be used in groups.")
        return

    # Authorize the group
    AUTHORIZED_GROUPS.add(chat_id)
    logger.info(f"Group {chat_id} authorized by user {user_id}")
    await update.message.reply_text(f"This group is now authorized to use the bot. Group ID: {chat_id}")

def is_authorized(update: Update) -> bool:
    """Check if the user or group is authorized to use the bot."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    logger.debug(f"Authorization check - User: {user_id}, Chat: {chat_id}")
    
    # Check if it's a private chat with authorized user
    if chat_id > 0:  # Positive chat_id indicates private chat
        return user_id == AUTHORIZED_USER_ID
    
    # For groups, check if the group is authorized
    # Any member of an authorized group can use the bot
    return chat_id in AUTHORIZED_GROUPS

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages."""
    chat_id = update.effective_chat.id
    
    # For groups, check group authorization
    if chat_id < 0 and chat_id not in AUTHORIZED_GROUPS:
        logger.info(f"Unauthorized group access attempt in chat {chat_id}")
        return

    # For private chats, check user authorization
    if chat_id > 0 and not is_authorized(update):
        logger.info(f"Unauthorized private chat attempt from user {update.effective_user.id}")
        return

    # Check if bot is mentioned
    if update.message and update.message.text:
        bot_username = context.bot.username
        if f"@{bot_username}" in update.message.text:
            # Get the message without the mention
            message = update.message.text.replace(f"@{bot_username}", "").strip()
            
            # Get or initialize conversation history
            if chat_id not in conversation_history:
                conversation_history[chat_id] = []
            
            # Add message to history
            conversation_history[chat_id].append({"role": "user", "content": message})
            
            try:
                # Get response from Ollama
                response = ollama.chat(
                    model='gemma3:4b',
                    messages=conversation_history[chat_id]
                )
                
                # Add response to history
                conversation_history[chat_id].append({"role": "assistant", "content": response['message']['content']})
                
                # Send response
                await update.message.reply_text(response['message']['content'])
            except Exception as e:
                logger.error(f"Error getting response from Ollama: {e}")
                await update.message.reply_text("Sorry, I encountered an error processing your request.")

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("authorize", authorize_group))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main() 