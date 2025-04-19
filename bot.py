import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from agent import get_agent_response, chat_memories
import json
from image_tool import get_photo_description
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
        "/get_haircut_times - Get the available times for a haircut\n"
        "/get_booking_details - Get the booking details for a haircut\n"
        "\nYou can also:\n"
        "- Mention me with @ to get a response\n"
        f"\nCurrent context window: {MAX_HISTORY_LENGTH} messages"
    )
    await update.message.reply_text(help_text)

async def get_haircut_times_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    # For groups, check group authorization
    if chat_id < 0 and chat_id not in AUTHORIZED_GROUPS:
        logger.info(f"Unauthorized group access attempt in chat {chat_id}")
        return

    # For private chats, check user authorization
    if chat_id > 0 and not is_authorized(update):
        logger.info(f"Unauthorized private chat attempt from user {update.effective_user.id}")
        return
    """Get the available times for a haircut."""
    await update.message.reply_text("Getting haircut times...")
    from haircut_tool import get_slots
    # Get the screenshot of available slots
    await get_slots()
    # Send the image
    with open("haircut_slots.png", "rb") as photo:
        await update.message.reply_photo(photo, caption="Available haircut slots")

async def get_booking_details_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    # For groups, check group authorization
    if chat_id < 0 and chat_id not in AUTHORIZED_GROUPS:
        logger.info(f"Unauthorized group access attempt in chat {chat_id}")
        return

    # For private chats, check user authorization
    if chat_id > 0 and not is_authorized(update):
        logger.info(f"Unauthorized private chat attempt from user {update.effective_user.id}")
        return
    """Get the available times for a haircut."""
    from haircut_tool import book_slot
    raw = update.message.text.replace("/get_booking_details ", "")

    from datetime import datetime, timezone, timedelta

    # Parse it
    dt = datetime.strptime(raw, "%Y%m%d %H%M")

    # Add timezone offset (UTC+8)
    dt = dt.replace(tzinfo=timezone(timedelta(hours=8)))

    # Format it in ISO 8601
    iso_string = dt.isoformat()

    print(iso_string)

    await update.message.reply_text(f"Getting booking details for {dt}...")
    # Get the screenshot of available slots
    await book_slot(iso_string)
    # Send the image
    with open("haircut_form.png", "rb") as photo:
        await update.message.reply_photo(photo, caption="Booking details form")

    with open("haircut_confirmation.png", "rb") as photo:
        await update.message.reply_photo(photo, caption="Booking detail confirmation")

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear the conversation history for the current chat."""
    if not is_authorized(update):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    chat_id = update.effective_chat.id
    
    # Clear the conversation history
    if chat_id in conversation_history:
        conversation_history[chat_id] = []
    
    # Clear the agent's memory
    if str(chat_id) in chat_memories:
        chat_memories[str(chat_id)].clear()
    
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
    
    print(update.message)

    # Check if bot is mentioned
    if update.message and update.message.text:
        bot_username = context.bot.username
        if f"@{bot_username}" in update.message.text:
            # Get the message without the mention
            message = update.message.text.replace(f"@{bot_username}", "").strip()
            
            # Get reply context if it exists
            context_message = None
            if update.message.reply_to_message:
                if update.message.reply_to_message.location:
                    # This is a location message
                    location = update.message.reply_to_message.location
                    context_message = f"Coordinates Provided (Latitude: {location.latitude}, Longitude: {location.longitude})"
                    # Now you can access location.latitude and location.longitude
                else:
                    # This is not a location message
                    context_message = update.message.reply_to_message.text
            
            try:
                # Pass both the message and context to the agent
                response = get_agent_response(message, str(chat_id), context_message)
                await update.message.reply_text(response)
            except Exception as e:
                logger.error(f"Error getting response from agent: {e}")
                await update.message.reply_text("Sorry, I encountered an error processing your request.")
    elif update.message and update.message.sticker:
        print("received sticker")
        file = await context.bot.get_file(update.message.sticker.file_id)
        await file.download_to_drive("data/sticker.jpg")
        message = "Received a sticker. Saved in data/sticker.jpg"
        try: 
            response = get_agent_response(message, str(chat_id), context_message=None)
            # reply = get_photo_description("data/sticker.jpg")
            await update.message.reply_text(response)
        except Exception as e:
            logger.error(f"Error getting response from agent: {e}")
            await update.message.reply_text("Sorry, I encountered an error processing your request.")
    else:
        print(update.message)
        

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("authorize", authorize_group))
    application.add_handler(CommandHandler("clear", clear_history))
    application.add_handler(CommandHandler("get_haircut_times", get_haircut_times_command))
    application.add_handler(CommandHandler("get_booking_details", get_booking_details_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Sticker.ALL, handle_message))
    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main() 