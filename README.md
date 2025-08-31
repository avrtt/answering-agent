A Telegram bot that helps you manage and respond to messages from multiple platforms (LinkedIn, Gmail, Facebook, Instagram, Telegram) using AI-generated responses.

Features:
- **Multi-Platform Integration**: Connect to LinkedIn, Gmail, Facebook, Instagram, and Telegram
- **AI-Powered Responses**: Generate contextual responses using OpenAI GPT models
- **Message Queue Management**: Process messages one by one with user control
- **Response Customization**: Edit and improve AI-generated responses
- **Dual Mode Operation**: Local mode (for development) and Cloud mode (for production)
- **User Preferences**: Configure writing style, personality, and response rules

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

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create environment file:
   ```bash
   cp .env.example .env
   ```

4. Configure environment variables:
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
APP_MODE=local  # "local" or "cloud"

# Database (optional, defaults to SQLite)
DATABASE_URL=sqlite:///./answering_agent.db

# Redis (for cloud mode)
REDIS_URL=redis://localhost:6379/0
```

### Getting Telegram bot token

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Create a new bot with `/newbot`
3. Copy the token to your `.env` file

### Getting your chat ID

1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. Copy your chat ID to the `.env` file

## Usage

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

1. **🤖 Generate Response** - AI generates a contextual response
2. **❌ Ignore** - Skip this message
3. **✍️ Answer Manually** - Write your own response

### Response management

After generating a response, you can:

- **✅ Send** - Send the response immediately
- **✏️ Edit** - Provide feedback to improve the response
- **🔄 Regenerate** - Generate a completely new response

## 🏗️ Architecture

### Core components

- **`main.py`** - Main application orchestrator
- **`telegram_bot.py`** - Telegram bot interface
- **`message_manager.py`** - Message queue and response management
- **`ai_agent.py`** - OpenAI integration for response generation
- **`platform_connectors.py`** - Platform-specific connectors
- **`database.py`** - Database management
- **`models.py`** - Database models
- **`config.py`** - Configuration management

### Data flow

1. **Message Polling**: Platform connectors poll for new messages
2. **Queue Management**: New messages are added to the database queue
3. **User Notification**: Telegram bot notifies user of new messages
4. **User Interaction**: User processes messages one by one
5. **Response Generation**: AI generates responses based on user preferences
6. **Message Sending**: Responses are sent back to the original platform

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

## Future Enhancements

- Real platform API integrations
- Advanced message filtering
- Response templates
- Analytics and insights
- Web dashboard
- Multi-user support
- Advanced AI models integration

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review the logs for error messages
3. Create an issue on GitHub
4. Contact the development team


