# WhatsApp News Sender

This application fetches news articles, converts them to audio using AWS Polly, and sends them via WhatsApp using Twilio.

## Features

- Fetch news articles from NewsData.io API
- Convert news text to speech using AWS Polly
- Send audio files via WhatsApp using Twilio
- Web interface to register recipient phone numbers

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up your environment variables in `.env` file (see `.env.template` for reference)
4. Run the web application:
   ```
   python app.py
   ```
5. Open your browser and navigate to `http://localhost:5000`
6. Register your phone number to receive news updates

## Running the News Sender

After registering your phone number through the web interface, you can run the news sender script:

```
python news_to_audio.py
```

## Command Line Options

```
python news_to_audio.py --category technology --country us --count 5
```

- `--category`: News category (default: technology)
- `--country`: Country code (default: us)
- `--count`: Number of news articles (default: 5)
- `--create-env`: Create a template .env file

## Requirements

- Python 3.6+
- AWS account with Polly access
- Twilio account with WhatsApp capabilities
- NewsData.io API key