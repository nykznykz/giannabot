import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from agent import get_agent_response

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
MAX_HISTORY_LENGTH = int(os.getenv('MAX_HISTORY_LENGTH', '10'))

# Authorized groups (add group IDs here)
AUTHORIZED_GROUPS = set()

# Conversation history storage
conversation_history = {}

def manage_conversation_history(chat_id: int, new_message: dict):
    """Manage conversation history with a sliding window."""
    if chat_id not in conversation_history:
        conversation_history[chat_id] = []
    
    # Add new message
    conversation_history[chat_id].append(new_message)
    
    # Trim history if it exceeds max length
    if len(conversation_history[chat_id]) > MAX_HISTORY_LENGTH:
        # Keep the most recent messages
        conversation_history[chat_id] = conversation_history[chat_id][-MAX_HISTORY_LENGTH:]
        logger.info(f"Trimmed conversation history for chat {chat_id} to {MAX_HISTORY_LENGTH} messages")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text('Hi! I\'m your AI assistant. Mention me with @ to get a response.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    help_text = (
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/authorize - Authorize this group to use the bot\n"
        "/clear - Clear conversation history\n"
        f"\nCurrent context window: {MAX_HISTORY_LENGTH} messages"
    )
    await update.message.reply_text(help_text)

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear the conversation history for the current chat."""
    if not is_authorized(update):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    chat_id = update.effective_chat.id
    # Note: The agent will handle clearing its own memory
    await update.message.reply_text("Conversation history cleared.")

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
            
            try:
                # Get response from agent with chat history
                response = get_agent_response(message, str(chat_id))
                
                # Send response
                await update.message.reply_text(response)
            except Exception as e:
                logger.error(f"Error getting response from agent: {e}")
                await update.message.reply_text("Sorry, I encountered an error processing your request.")

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("authorize", authorize_group))
    application.add_handler(CommandHandler("clear", clear_history))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main() 