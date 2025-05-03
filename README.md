# News to Audio WhatsApp Sender

This application fetches news articles from the News API, converts them to audio using AWS Polly, and sends the audio file via WhatsApp using Twilio.

## Features

- Fetch top news articles from various categories and countries
- Convert news text to speech using AWS Polly
- Send audio files via WhatsApp using Twilio
- Fallback to SMS/MMS if WhatsApp sending fails

## Prerequisites

- Python 3.6 or higher
- News API key (get it from [newsapi.org](https://newsapi.org/))
- AWS account with access to Polly service
- Twilio account with WhatsApp capability

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/news-to-audio.git
   cd news-to-audio
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your credentials:
   ```
   python news_to_audio.py --create-env
   ```
   This will create a `.env.template` file. Rename it to `.env` and fill in your credentials.

## Usage

Run the application with default settings:
```
python news_to_audio.py
```

Customize the news category, country, and number of articles:
```
python news_to_audio.py --category business --country gb --count 3
```

### Command-line Arguments

- `--create-env`: Create a template .env file
- `--category`: News category (default: technology)
- `--country`: Country code (default: us)
- `--count`: Number of news articles (default: 5)

### Available News Categories

- business
- entertainment
- general
- health
- science
- sports
- technology

### Country Codes

The News API supports many country codes, including:
- us (United States)
- gb (United Kingdom)
- in (India)
- au (Australia)
- ca (Canada)
- etc.

## WhatsApp Setup

To use WhatsApp with Twilio:

1. Set up a Twilio account and enable WhatsApp sandbox
2. Follow Twilio's instructions to connect your WhatsApp number to the sandbox
3. The recipient must opt-in to receive messages from your Twilio WhatsApp number

## Notes

- For WhatsApp messaging, both the sender and recipient numbers must be properly formatted with country codes
- If WhatsApp sending fails, the application will attempt to send the audio via SMS/MMS as a fallback
- Audio files are saved in the `output` directory

## License

This project is licensed under the MIT License - see the LICENSE file for details.