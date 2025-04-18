# Telegram Bot PRD

## Project Overview
A Telegram bot that integrates with GPT-4o-mini to provide intelligent responses when directly mentioned (@) in private chats and authorized group chats. The bot also integrates with various APIs to provide additional functionality.

## Core Features
1. **Message Listening**
   - ✅ Bot responds only when directly mentioned using @
   - ✅ Works in private chats with the owner
   - ✅ Works in authorized group chats
   - ✅ Ignores messages where it's not directly mentioned

2. **User Authorization**
   - ✅ Primary user (owner) access control
   - ✅ Group chat authorization system
   - ✅ Whitelist-based access control

3. **LLM Integration**
   - ✅ Integration with GPT-4o-mini
   - ✅ Message context preservation
   - ✅ Conversation history tracking

4. **Context Management**
   - ✅ Maintains conversation history
   - ✅ Configurable context window size (default: 10 messages)
   - ✅ Manual history clearing via /clear command

5. **API Integrations**
   - ✅ Google Calendar Integration https://python.langchain.com/docs/integrations/tools/google_calendar/
     - Event creation and management
     - Calendar view and search
     - Event reminders and notifications
   - ✅ Gmail LangChain Toolkit Integration https://python.langchain.com/docs/integrations/tools/gmail/
     - Email search and retrieval
     - Draft creation and management
     - Message and thread handling
     - OAuth 2.0 authentication
   - [ ] YouTube Integration
     - Video search and retrieval
     - Content analysis
   - [ ] OpenWeatherMap Integration
     - Weather data retrieval
     - Location-based weather information
   - [ ] Passio Nutrition Integration
     - Nutrition information retrieval
     - Food analysis capabilities

## Technical Requirements
1. **Development Environment**
   - ✅ Local development setup
   - ✅ Python-based implementation
   - ✅ Telegram Bot API integration
   - ✅ GPT-4o-mini API integration

2. **Dependencies**
   - ✅ python-telegram-bot library
   - ✅ OpenAI client library
   - ✅ Environment configuration management
   - ✅ Google Calendar API client library 
   - [ ] LangChain Gmail toolkit
   - [ ] YouTube API client library
   - [ ] OpenWeatherMap API client library
   - [ ] Passio Nutrition API client library

3. **Security**
   - ✅ Bot token management
   - ✅ User authorization system
   - ✅ Group chat whitelist
   - ✅ Google Calendar OAuth 2.0 implementation
   - [ ] Gmail OAuth 2.0 implementation
   - [ ] API key management system

## Implementation Status

### Completed Features
- [x] Basic bot setup and configuration
- [x] Message listening and @ mention detection
- [x] User authorization system
- [x] LLM integration with GPT-4o-mini
- [x] Conversation history tracking
- [x] Context window management
- [x] Google Calendar API integration
  - [x] OAuth 2.0 setup
  - [x] Calendar management tools
  - [x] Security implementation

### In Progress
- [ ] Gmail LangChain Toolkit Integration
  - [ ] OAuth 2.0 setup
  - [ ] Email management tools
  - [ ] Security implementation
- [ ] YouTube API Integration
  - [ ] API key setup
  - [ ] Search functionality
- [ ] OpenWeatherMap Integration
  - [ ] API key setup
  - [ ] Weather data retrieval
- [ ] Passio Nutrition Integration
  - [ ] API key setup
  - [ ] Nutrition data retrieval

### Future Enhancements
1. Message rate limiting
2. Customizable context window size
3. Multiple LLM model support
4. Response formatting options
5. Error handling and logging
6. Remote deployment options

## Success Metrics
1. Response accuracy
2. Response time
3. Context preservation effectiveness
4. User satisfaction
5. System stability
6. API integration reliability

## Notes
- Initial focus on local development
- Prioritize security and access control
- Maintain conversation context for better responses
- Regular testing and optimization required
- Uses GPT-4o-mini for responses
- Context window size configurable via environment variables
- Google Calendar integration completed with OAuth 2.0 security
- Next focus on Gmail LangChain toolkit integration 