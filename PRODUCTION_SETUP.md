# Production Setup Guide

## Overview
This guide will help you set up the Answering Agent for production use with real platform API integrations.

## Current Status ✅
- ✅ **Telegram Bot**: Working and tested
- ✅ **Mock Connectors**: All platforms (LinkedIn, Gmail, Facebook, Instagram) working with mock data
- ✅ **Real API Integrations**: Implemented with fallback to mock connectors
- ✅ **Error Handling**: Comprehensive error handling and rate limiting
- ✅ **Async Issues**: Fixed event loop conflicts

## Environment Configuration

Update your `.env` file with the following variables:

```bash
# Telegram Bot Configuration (REQUIRED - Already working)
TELEGRAM_BOT_TOKEN=8330305422:AAHRE8NYaCQ84snZ8w7-VTT7jTa07QEezpw
TELEGRAM_CHAT_ID=903233207

# OpenAI Configuration (REQUIRED for AI responses)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4

# Application Mode
APP_MODE=local

# Database Configuration
DATABASE_URL=sqlite:///./answering_agent.db

# Redis Configuration (for cloud mode)
REDIS_URL=redis://localhost:6379/0

# Response Generation Settings
MAX_RESPONSE_LENGTH=500
RESPONSE_STYLE=professional

# LinkedIn API Configuration (OPTIONAL - falls back to mock if not configured)
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
LINKEDIN_ACCESS_TOKEN=your_linkedin_access_token

# Facebook API Configuration (OPTIONAL - falls back to mock if not configured)
FACEBOOK_ACCESS_TOKEN=your_facebook_access_token
FACEBOOK_PAGE_ID=your_facebook_page_id

# Instagram API Configuration (OPTIONAL - falls back to mock if not configured)
INSTAGRAM_USERNAME=your_instagram_username
INSTAGRAM_PASSWORD=your_instagram_password

# Gmail API Configuration (OPTIONAL - falls back to mock if not configured)
GMAIL_CREDENTIALS_FILE=path/to/gmail_credentials.json
```

## Platform API Setup Instructions

### 1. LinkedIn API Setup
1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/)
2. Create a new app
3. Get your Client ID and Client Secret
4. Request access to Messaging API
5. Generate an access token
6. Add to .env file

### 2. Facebook API Setup
1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create a new app
3. Add Messenger product
4. Generate a page access token
5. Get your page ID
6. Add to .env file

### 3. Instagram API Setup
1. Go to [Instagram Basic Display](https://developers.facebook.com/docs/instagram-basic-display-api/)
2. Create a new app
3. Add Instagram Basic Display product
4. Get your username and password
5. Add to .env file

### 4. Gmail API Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Gmail API
4. Create credentials (OAuth 2.0)
5. Download credentials JSON file
6. Add path to .env file

## Testing the System

### 1. Test Telegram Bot
```bash
# Start the application
source venv/bin/activate
python main.py
```

The bot should:
- ✅ Connect to all platforms
- ✅ Receive mock messages from LinkedIn, Gmail, Facebook, Instagram
- ✅ Send Telegram notifications for new messages
- ✅ Allow you to process messages via Telegram commands

### 2. Test Real Platform Integration
1. Configure one platform's API credentials in .env
2. Restart the application
3. Check logs for successful connection
4. The system will automatically use real API instead of mock

## Production Deployment

### 1. Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your production credentials
```

### 2. Database Setup
```bash
# Initialize database
python -c "from database import db_manager; db_manager.init_db()"
```

### 3. Run in Production
```bash
# For local production
python main.py

# For cloud deployment (using systemd)
sudo systemctl enable answering-agent
sudo systemctl start answering-agent
```

## Monitoring and Logging

### Log Levels
- `INFO`: Normal operation
- `WARNING`: API fallbacks, rate limits
- `ERROR`: Connection failures, API errors

### Key Metrics to Monitor
- Platform connection status
- Message processing rate
- API rate limit usage
- Error rates per platform

## Troubleshooting

### Common Issues

1. **Telegram Bot Not Responding**
   - Check TELEGRAM_BOT_TOKEN is valid
   - Verify TELEGRAM_CHAT_ID is correct
   - Check bot permissions

2. **Platform API Failures**
   - System automatically falls back to mock connectors
   - Check API credentials in .env
   - Verify API permissions and rate limits

3. **Database Issues**
   - Check DATABASE_URL configuration
   - Ensure write permissions to database file

4. **Rate Limiting**
   - Each platform has built-in rate limiting
   - System automatically handles rate limit resets
   - Check logs for rate limit warnings

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py
```

## Security Considerations

1. **API Keys**: Never commit .env file to version control
2. **Access Tokens**: Rotate tokens regularly
3. **Rate Limiting**: Respect platform rate limits
4. **Data Privacy**: Ensure compliance with platform terms of service

## Performance Optimization

1. **Polling Interval**: Adjust message polling frequency in main.py
2. **Database**: Consider PostgreSQL for high-volume usage
3. **Caching**: Implement Redis caching for API responses
4. **Scaling**: Use Celery for background task processing

## Support

For issues or questions:
1. Check the logs for error messages
2. Verify environment configuration
3. Test individual platform connections
4. Review platform API documentation

## Next Steps

1. ✅ **MVP Complete**: Telegram bot working with mock connectors
2. 🔄 **Production Ready**: Real API integrations implemented
3. 📈 **Scale**: Add more platforms, improve error handling
4. 🚀 **Deploy**: Production deployment with monitoring
