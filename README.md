A Telegram bot that helps you manage and respond to messages from multiple platforms (LinkedIn, Gmail, Facebook, Instagram, Telegram) using AI-generated responses.

Features:
- **Multi-Platform Integration**: Connect to LinkedIn, Gmail, Facebook, Instagram, and Telegram
- **AI-Powered Responses**: Generate contextual responses using OpenAI GPT models
- **Message Queue Management**: Process messages one by one with user control
- **Response Customization**: Edit and improve AI-generated responses
- **Dual Mode Operation**: Local mode (for development) and Cloud mode (for production)
- **User Preferences**: Configure writing style, personality, and response rules
- **Message Type Detection**: Automatically detect and style responses based on message type (business, personal, support, networking, sales)
- **Person-Specific Responses**: Customize responses based on individual people and relationships
- **Web Search Integration**: Search Google and personal information sources during response generation
- **Personal Information Search**: Automatically find and include contact details, interests, projects, and other personal information

```
Use case:
- Telegram bot pulls and show any message I recieve in LinkedIn, Telegram, Facebook, Instagram or Gmail.
- Once received any message, the bot holds the conversation until I answer to this message. After answering through the bot, it continues to the next message in the queue. So we have to implement a storage for only active (unanswered) messages.
- Each message awaits for my decision, basically one of three options (buttons): "Generate response", "Ignore", "Answer manually".
- If I choose "Generate response", the agent creates a LLM-generated answer to that message.
- Once generated, the bot asks me to review the response. If I agree, it sends the message to the person. If I want to make changes, I ask it for fixes (in chat bot style), get preview, and then repeat until I'll push the "Send" button.
- To configure my generated responses, we will create a set of rules that defines my writing style, preferences, interests, personality and so on.
- If I choose "Ignore", we just read the message, ignore it and skip to the next one.
- If I choose "Answer manually", the bot should ask me to write a manual response, then send it to the person.
- The server for the bot works in two modes (and I can switch between them): on cloud (so it's working all the time and I get notifications from the bot even if my computer isn't running) and local (default mode: start the app > start receiving messages from the bot, saving them to the queue). The storage clears after stopping the app in local mode. In cloud mode it stores everything as it received, in the same order.
- The repository should be well-documented in README.md file.
My goal is to automate responding and interact with messages through Telegram, so I'm not going to open social media websites or email directly. I want to start the bot locally (to start receiving messages) on startup. I'm using Arch Linux.
```

## Requirements

- Python 3.8+
- Telegram Bot Token
- OpenAI API Key

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd answering-agent
   ```

2. (Optional) Create a virtual environment:
   ```
   python3 -m venv venv && source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create environment file:
   ```bash
   cp .env.example .env
   ```

5. Configure environment variables:
   ```bash
   # Edit .env file with your credentials
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_CHAT_ID=your_telegram_chat_id
   OPENAI_API_KEY=your_openai_api_key
   APP_MODE=local # or "cloud"
   ```

## Configuration

### Environment variables

Create a `.env` file with the following variables:

```env
# Telegram bot configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# OpenAI configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4

# Application mode
APP_MODE=local # "local" or "cloud"

# Database (optional, defaults to SQLite)
DATABASE_URL=sqlite:///./answering_agent.db

# Web Search Configuration
GOOGLE_SEARCH_API_KEY=your_google_search_api_key
GOOGLE_SEARCH_ENGINE_ID=your_google_search_engine_id

# Redis (for cloud mode)
REDIS_URL=redis://localhost:6379/0
# Personal Information Sources
PERSONAL_WEBSITE=https://avrtt.github.io/about
GITHUB_PROFILE=https://github.com/avrtt
LINKEDIN_PROFILE=your_linkedin_profile_url
TWITTER_PROFILE=your_twitter_profile_url

# Enhanced Features
ENABLE_MESSAGE_TYPE_DETECTION=true
ENABLE_PERSON_SPECIFIC_RESPONSES=true
ENABLE_GOOGLE_SEARCH=true
ENABLE_PERSONAL_INFO_SEARCH=true
```

### Getting Telegram bot token

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Create a new bot with `/newbot`
3. Copy the token to your `.env` file

### Getting Google Search API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Custom Search API
4. Create credentials (API Key)
5. Copy the API key to your `.env` file

### Getting Google Custom Search Engine ID

1. Go to [Google Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Create a new search engine
3. Configure it to search the entire web
4. Copy the Search Engine ID to your `.env` file

### Getting your chat ID

1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. Copy your chat ID to the `.env` file

## Usage

### Initial Setup

1. Run the application - it will automatically create the necessary database tables:
   ```bash
   python main.py
   ```

### Running the bot

1. Start the application:
   ```bash
   python main.py
   ```

2. Interact with the bot:
   - Send `/start` to initialize the bot
   - Use `/next` to process the next message in queue
   - Follow the interactive prompts to manage messages

Bot commands

- `/start` - Initialize the bot and show welcome message
- `/next` - Process the next message in queue
- `/help` - Show help information

### Message actions

When a new message arrives, you can choose from three actions:

1. **🤖 Generate Response** - AI generates a contextual response using:
   - Message type detection (business, personal, support, networking, sales)
   - Person-specific preferences and conversation history
   - Web search results and personal information
   - User preferences and writing style
2. **❌ Ignore** - Skip this message
3. **✍️ Answer Manually** - Write your own response

### Response management

After generating a response, you can:

- **✅ Send** - Send the response immediately
- **✏️ Edit** - Provide feedback to improve the response
- **🔄 Regenerate** - Generate a completely new response

## Architecture

### Core components

- **`main.py`** - Main application orchestrator with integrated database migration
- **`telegram_bot.py`** - Telegram bot interface
- **`message_manager.py`** - Message queue and response management with integrated message type detection
- **`ai_agent.py`** - OpenAI integration with enhanced features (message type detection, web search, person-specific responses)
- **`platform_connectors.py`** - Platform-specific connectors
- **`database.py`** - Database management
- **`models.py`** - Database models including enhanced feature models
- **`config.py`** - Configuration management

### Data flow

1. **Message Polling**: Platform connectors poll for new messages
2. **Message Type Detection**: Automatically detect message type (business, personal, support, networking, sales)
3. **Queue Management**: New messages are added to the database queue with type classification
4. **User Notification**: Telegram bot notifies user of new messages
5. **User Interaction**: User processes messages one by one
6. **Enhanced Response Generation**: AI generates responses using:
   - Message type-specific styling
   - Person-specific preferences and conversation history
   - Web search results and personal information
   - User preferences and writing style
7. **Message Sending**: Responses are sent back to the original platform
8. **Conversation History**: Update conversation history for future context

## Enhanced Features

### Message Type Detection

The agent automatically detects message types and applies appropriate styling:

- **Business**: Professional, formal, solution-oriented responses
- **Personal**: Warm, friendly, conversational responses
- **Support**: Helpful, patient, solution-focused responses
- **Networking**: Professional, engaging, relationship-building responses
- **Sales**: Informative, persuasive, value-focused responses

### Person-Specific Responses

Configure different response styles for individual people:

```bash
# Configure person-specific responses
python configure_enhanced_features.py person-config
```

Features:
- Custom writing style per person
- Relationship type classification (friend, colleague, client, etc.)
- Conversation history tracking
- Platform-specific preferences

### Web Search Integration

The agent can search for information during response generation:

- **Google Search**: Find relevant information from the web
- **Personal Information**: Automatically retrieve contact details, interests, projects
- **GitHub Integration**: Access your repositories and projects
- **Personal Website**: Scrape information from your about page

### Personal Information Sources

Configure your personal information sources in `.env`:

```env
PERSONAL_WEBSITE=https://avrtt.github.io/about
GITHUB_PROFILE=https://github.com/avrtt
LINKEDIN_PROFILE=your_linkedin_profile_url
TWITTER_PROFILE=your_twitter_profile_url
```

The agent will automatically include relevant information when someone asks about:
- Contact details
- Interests and hobbies
- Projects and work
- Skills and experience
- Resume information

## Modes

### Local mode (default)

- Messages are stored locally in SQLite database
- Storage is cleared when the application stops
- Suitable for development and testing
- No external dependencies required

### Cloud mode

- Messages are stored persistently
- Requires Redis for message queuing
- Suitable for production deployment
- Messages persist across application restarts

## Testing

The MVP includes mock connectors for all platforms:

- **MockLinkedInConnector** - Simulates LinkedIn messages
- **MockGmailConnector** - Simulates Gmail messages
- **MockTelegramConnector** - Simulates Telegram messages
- **MockFacebookConnector** - Simulates Facebook messages
- **MockInstagramConnector** - Simulates Instagram messages

### Running Tests

```bash
pytest tests/
```

## Deployment

### Local development

1. Install dependencies
2. Configure environment variables
3. Run `python main.py`

### Production Deployment

1. Set `APP_MODE=cloud` in environment
2. Configure Redis for message queuing
3. Use a process manager like PM2 or systemd
4. Set up proper logging and monitoring

### Systemd Service (Arch Linux)

Create `/etc/systemd/system/answering-agent.service`:

```ini
[Unit]
Description=Answering Agent Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/answering-agent
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable answering-agent
sudo systemctl start answering-agent
```

## Customization

### User preferences

Configure your response style by modifying the `UserPreferences` model:

- **Writing style**: Professional, casual, formal, etc.
- **Personality traits**: Friendly, direct, humorous, etc.
- **Interests**: Topics you're passionate about
- **Response rules**: Custom rules for response generation

### Message type styles

Configure different styles for different message types:

```bash
# The system automatically creates default message type styles on first run
# You can customize them by editing the database or modifying the code
```

### Person-specific configurations

Configure responses for specific people:

```bash
# Add a new person configuration
python configure.py add-person

# List all person configurations
python configure.py list-persons
```

### Platform connectors

To add real platform connectors:

1. Implement the `PlatformConnector` interface
2. Add authentication logic
3. Replace mock connectors in `PlatformManager`
4. Update configuration with API keys

## Troubleshooting

### Common issues

1. **Bot not responding**: Check Telegram token and chat ID
2. **AI responses failing**: Verify OpenAI API key and quota
3. **Database errors**: Ensure write permissions for SQLite file
4. **Platform connection issues**: Check network connectivity

### Logs

The application logs to stdout. For production, redirect to a log file:

```bash
python main.py > app.log 2>&1
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## To-do

- Automate local run on startup
- Advanced message filtering
- Analytics
- Enhanced web search capabilities
- More platform integrations
- Response quality metrics

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review the logs for error messages
3. Create an issue on GitHub
4. Contact the development team


