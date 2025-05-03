import os
import requests
import boto3
import time
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class NewsToAudio:
    def __init__(self):
        # Initialize API keys and credentials from environment variables
        self.news_api_key = os.getenv('NEWS_API_KEY')
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_REGION')
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.recipient_phone_number = os.getenv('RECIPIENT_PHONE_NUMBER')
        
        # Initialize AWS Polly client
        self.polly_client = boto3.client(
            'polly',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.aws_region
        )
        
        # Initialize Twilio client
        self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
        
        # Create output directory if it doesn't exist
        os.makedirs('output', exist_ok=True)
    
    def fetch_news(self, category='technology', country='us', page_size=5):
        """
        Fetch news articles from News API
        """
        url = f'https://newsdata.io/api/1/news'
        params = {
            'country': country,
            'category': category,
            'apiKey': self.news_api_key,
            'size' : 3
        }
        
        try:
            response = requests.get(url, params=params)
            print(response)
            response.raise_for_status()  # Raise exception for HTTP errors
            news_data = response.json()
            
            if news_data['status'] == 'success':
                return news_data['results']
            else:
                print(f"Error fetching news: {news_data.get('message', 'Unknown error')}")
                return []
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return []
    
    def prepare_news_text(self, articles):
        """
        Prepare news text from articles for text-to-speech conversion
        """
        if not articles:
            return "No news articles available at the moment."
        
        news_text = "Today's top news headlines. "
        
        for i, article in enumerate(articles, 1):
            title = article.get('title', 'No title')
            description = article.get('description', 'No description available')
            source = article.get('source_name','No source available')
            
            news_text += f"News {i}. From {source}. {title}. {description}. "
        
        news_text += "That's all for today's news update."
        return news_text
    
    def convert_text_to_speech(self, text, output_filename='news_audio.mp3'):
        """
        Convert text to speech using AWS Polly
        """
        try:
            response = self.polly_client.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId='Joanna',  # You can choose different voices
                
            )
            
            output_path = os.path.join('output', output_filename)
            
            # Save the audio content
            if "AudioStream" in response:
                with open(output_path, 'wb') as file:
                    file.write(response['AudioStream'].read())
                print(f"Audio saved to {output_path}")
                
            else:
                print("No AudioStream in the response")
                return None
            # Step 3: Upload to S3
            s3_client = boto3.client('s3')
            bucket_name = 'temp-storage-mp3'  # 🔁 Replace with your bucket name
            s3_key = f"audio/{output_filename}"

            s3_client.upload_file(output_path, 
                                  bucket_name, 
                                  s3_key,
                                  ExtraArgs={'ContentType': 'audio/mpeg'}
                                  )

            # Step 4: Return public URL
            region = s3_client.meta.region_name
            s3_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{s3_key}"
            return s3_url
        except Exception as e:
            print(f"Error in text-to-speech conversion: {e}")
            return None
    
    
    def send_audio_via_whatsapp(self, s3_url):
        """
        Send the audio file via WhatsApp using Twilio
        """
        # if not audio_file_path or not os.path.exists(audio_file_path):
        #     print("Audio file not found")
        #     return False
        print(s3_url)
        try:
            # Format the WhatsApp number with the 'whatsapp:' prefix
            # WhatsApp numbers must be in the format 'whatsapp:+1234567890'
            whatsapp_from = f"whatsapp:{self.twilio_phone_number}"
            whatsapp_to = f"whatsapp:{self.recipient_phone_number}"
            
            # For WhatsApp, Twilio requires media to be hosted at a publicly accessible URL
            # We'll use Twilio's Media API to upload the file
        
            media = self.twilio_client.messages.create(
                body="Here's your news audio update for today!",
                from_=whatsapp_from,
                to=whatsapp_to,
                media_url=[s3_url]
            )
            print(f"Message sent! SID: {media.sid}")
            
            return True
        except Exception as e:
            print(f"Error sending WhatsApp message: {e}")
            print("Note: To use WhatsApp with Twilio, you need to:")
            print("1. Have an approved WhatsApp sender")
            print("2. The recipient must have opted in to receive messages")
            print("3. Use a Twilio-approved message template for the first message")
            
            # Fallback to SMS with MMS attachment if WhatsApp fails
            try:
                print("Attempting to send as SMS with MMS attachment instead...")
            
                message = self.twilio_client.messages.create(
                    body="Here's your news audio update for today!",
                    from_=self.twilio_phone_number,
                    to=self.recipient_phone_number,
                    media_url=[s3_url]
                )
                print(f"SMS message sent! SID: {message.sid}")
                return True
            except Exception as sms_error:
                print(f"Error sending SMS message: {sms_error}")
                return False
    
    def run(self):
        """
        Run the complete process: fetch news, convert to audio, and send via WhatsApp
        """
        print("Fetching news articles...")
        articles = self.fetch_news()
        
        if not articles:
            print("No articles found. Exiting.")
            return
        
        print(f"Found {len(articles)} articles. Preparing text...")
        news_text = self.prepare_news_text(articles)
        
        print("Converting text to speech...")
        audio_file_path = self.convert_text_to_speech(news_text)
        
    
        print("Sending audio via WhatsApp...")
        success = self.send_audio_via_whatsapp(audio_file_path)
        
        if success:
            print("Process completed successfully!")
        else:
            print("Failed to send audio via WhatsApp.")
            
    @staticmethod
    def create_env_template(output_path='.env.template'):
        """
        Create a template .env file with all required environment variables
        """
        env_template = """# News API credentials
NEWS_API_KEY=your_news_api_key_here

# AWS credentials
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=us-east-1

# Twilio credentials
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=your_twilio_phone_number_here
RECIPIENT_PHONE_NUMBER=recipient_phone_number_here
"""
        try:
            with open(output_path, 'w') as f:
                f.write(env_template)
            print(f"Environment template created at {output_path}")
            print("Copy this file to .env and fill in your actual credentials")
            return True
        except Exception as e:
            print(f"Error creating environment template: {e}")
            return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='News to Audio WhatsApp Sender')
    parser.add_argument('--create-env', action='store_true', help='Create a template .env file')
    parser.add_argument('--category', type=str, default='technology', help='News category (default: technology)')
    parser.add_argument('--country', type=str, default='us', help='Country code (default: us)')
    parser.add_argument('--count', type=int, default=5, help='Number of news articles (default: 5)')
    
    args = parser.parse_args()
    
    if args.create_env:
        NewsToAudio.create_env_template()
    else:
        try:
            news_to_audio = NewsToAudio()
            print(f"Fetching {args.count} {args.category} news articles from {args.country}...")
            articles = news_to_audio.fetch_news(category=args.category, country=args.country, page_size=args.count)
            
            if not articles:
                print("No articles found. Exiting.")
                exit(1)
            
            print(f"Found {len(articles)} articles. Preparing text...")
            news_text = news_to_audio.prepare_news_text(articles)
            
            print("Converting text to speech...")
            audio_file_path = news_to_audio.convert_text_to_speech(news_text)
            
            if audio_file_path:
                print("Sending audio via WhatsApp...")
                success = news_to_audio.send_audio_via_whatsapp(audio_file_path)
                
                if success:
                    print("Process completed successfully!")
                else:
                    print("Failed to send audio via WhatsApp.")
            else:
                print("Failed to convert text to speech.")
        except Exception as e:
            print(f"Error: {e}")
            print("Make sure you have set up your .env file with all required credentials.")
            print("Run with --create-env to create a template .env file.")