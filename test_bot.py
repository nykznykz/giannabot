import os
import pytest
from dotenv import load_dotenv
import bot

# Load environment variables
load_dotenv()

@pytest.fixture
def authorized_user_id():
    """Fixture for authorized user ID."""
    return int(os.getenv('AUTHORIZED_USER_ID'))

@pytest.fixture
def unauthorized_user_id():
    """Fixture for unauthorized user ID."""
    return 999999

@pytest.fixture
def private_chat_id():
    """Fixture for private chat ID."""
    return 12345

@pytest.fixture
def group_chat_id():
    """Fixture for group chat ID."""
    return -12345

def create_mock_update(user_id: int, chat_id: int):
    """Create a mock update object."""
    return type('obj', (object,), {
        'effective_user': type('obj', (object,), {'id': user_id}),
        'effective_chat': type('obj', (object,), {'id': chat_id})
    })

class TestAuthorization:
    """Test authorization functionality."""

    def test_private_chat_authorized(self, authorized_user_id, private_chat_id):
        """Test authorized user in private chat."""
        update = create_mock_update(authorized_user_id, private_chat_id)
        assert bot.is_authorized(update), "Authorized user should be allowed in private chat"

    def test_private_chat_unauthorized(self, unauthorized_user_id, private_chat_id):
        """Test unauthorized user in private chat."""
        update = create_mock_update(unauthorized_user_id, private_chat_id)
        assert not bot.is_authorized(update), "Unauthorized user should not be allowed in private chat"

    def test_group_chat_authorized(self, unauthorized_user_id, group_chat_id):
        """Test user in authorized group."""
        bot.AUTHORIZED_GROUPS.add(group_chat_id)
        update = create_mock_update(unauthorized_user_id, group_chat_id)
        assert bot.is_authorized(update), "Any user should be allowed in authorized group"

class TestContextManagement:
    """Test context management functionality."""

    def test_add_message_to_history(self):
        """Test adding message to conversation history."""
        chat_id = 12345
        test_message = {"role": "user", "content": "test message"}
        bot.manage_conversation_history(chat_id, test_message)
        assert chat_id in bot.conversation_history, "Chat should be in conversation history"
        assert len(bot.conversation_history[chat_id]) == 1, "History should contain one message"

    def test_clear_history(self):
        """Test clearing conversation history."""
        chat_id = 12345
        bot.conversation_history[chat_id] = []
        assert len(bot.conversation_history[chat_id]) == 0, "History should be empty after clearing"

    def test_history_length_limit(self):
        """Test conversation history length limit."""
        chat_id = 12345
        bot.conversation_history[chat_id] = []
        
        # Add messages up to limit + 1
        for i in range(bot.MAX_HISTORY_LENGTH + 1):
            message = {"role": "user", "content": f"test message {i}"}
            bot.manage_conversation_history(chat_id, message)
        
        assert len(bot.conversation_history[chat_id]) == bot.MAX_HISTORY_LENGTH, \
            "History should be limited to MAX_HISTORY_LENGTH"

def main():
    """Run all tests."""
    print("Starting bot tests...")
    
    # Run authorization tests
    test_authorization()
    
    # Run context management tests
    test_context_management()
    
    print("\nAll tests completed!")

if __name__ == '__main__':
    run(main()) 