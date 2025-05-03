import unittest
import os
from unittest.mock import patch, MagicMock
from news_to_audio import NewsToAudio

class TestNewsToAudio(unittest.TestCase):
    
    def setUp(self):
        # Create a mock environment for testing
        self.env_patcher = patch.dict('os.environ', {
            'NEWS_API_KEY': 'test_news_api_key',
            'AWS_ACCESS_KEY_ID': 'test_aws_access_key',
            'AWS_SECRET_ACCESS_KEY': 'test_aws_secret_key',
            'AWS_REGION': 'us-east-1',
            'TWILIO_ACCOUNT_SID': 'test_twilio_sid',
            'TWILIO_AUTH_TOKEN': 'test_twilio_token',
            'TWILIO_PHONE_NUMBER': '+1234567890',
            'RECIPIENT_PHONE_NUMBER': '+0987654321'
        })
        self.env_patcher.start()
        
        # Create the NewsToAudio instance with mocked clients
        self.news_to_audio = NewsToAudio()
        
        # Mock the AWS Polly client
        self.news_to_audio.polly_client = MagicMock()
        
        # Mock the Twilio client
        self.news_to_audio.twilio_client = MagicMock()
    
    def tearDown(self):
        self.env_patcher.stop()
        
        # Clean up any test files
        if os.path.exists('output/test_audio.mp3'):
            os.remove('output/test_audio.mp3')
    
    @patch('requests.get')
    def test_fetch_news(self, mock_get):
        # Mock the response from News API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'ok',
            'articles': [
                {
                    'title': 'Test Article 1',
                    'description': 'This is a test article',
                    'source': {'name': 'Test Source'}
                },
                {
                    'title': 'Test Article 2',
                    'description': 'This is another test article',
                    'source': {'name': 'Another Test Source'}
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Call the fetch_news method
        articles = self.news_to_audio.fetch_news(category='technology', country='us', page_size=2)
        
        # Assert that the method returns the expected articles
        self.assertEqual(len(articles), 2)
        self.assertEqual(articles[0]['title'], 'Test Article 1')
        self.assertEqual(articles[1]['title'], 'Test Article 2')
        
        # Assert that the method called requests.get with the correct parameters
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], 'https://newsapi.org/v2/top-headlines')
        self.assertEqual(kwargs['params']['category'], 'technology')
        self.assertEqual(kwargs['params']['country'], 'us')
        self.assertEqual(kwargs['params']['pageSize'], 2)
    
    def test_prepare_news_text(self):
        # Test with empty articles
        text = self.news_to_audio.prepare_news_text([])
        self.assertEqual(text, "No news articles available at the moment.")
        
        # Test with articles
        articles = [
            {
                'title': 'Test Article 1',
                'description': 'This is a test article',
                'source': {'name': 'Test Source'}
            },
            {
                'title': 'Test Article 2',
                'description': 'This is another test article',
                'source': {'name': 'Another Test Source'}
            }
        ]
        
        text = self.news_to_audio.prepare_news_text(articles)
        self.assertIn("Today's top news headlines", text)
        self.assertIn("Test Article 1", text)
        self.assertIn("Test Article 2", text)
        self.assertIn("Test Source", text)
        self.assertIn("Another Test Source", text)
    
    def test_convert_text_to_speech(self):
        # Mock the response from AWS Polly
        mock_stream = MagicMock()
        mock_stream.read.return_value = b'test audio data'
        
        self.news_to_audio.polly_client.synthesize_speech.return_value = {
            'AudioStream': mock_stream
        }
        
        # Call the convert_text_to_speech method
        output_path = self.news_to_audio.convert_text_to_speech("Test text", "test_audio.mp3")
        
        # Assert that the method returns the expected output path
        self.assertEqual(output_path, os.path.join('output', 'test_audio.mp3'))
        
        # Assert that the method called polly_client.synthesize_speech with the correct parameters
        self.news_to_audio.polly_client.synthesize_speech.assert_called_once_with(
            Text="Test text",
            OutputFormat='mp3',
            VoiceId='Joanna'
        )
        
        # Assert that the file was created
        self.assertTrue(os.path.exists(output_path))
    
    @patch('os.path.exists')
    def test_send_audio_via_whatsapp(self, mock_exists):
        # Mock that the file exists
        mock_exists.return_value = True
        
        # Mock the Twilio client's messages.create method
        mock_message = MagicMock()
        mock_message.sid = 'test_sid'
        self.news_to_audio.twilio_client.messages.create.return_value = mock_message
        
        # Call the send_audio_via_whatsapp method
        success = self.news_to_audio.send_audio_via_whatsapp('output/test_audio.mp3')
        
        # Assert that the method returns True
        self.assertTrue(success)
        
        # Assert that the method called twilio_client.messages.create with the correct parameters
        self.news_to_audio.twilio_client.messages.create.assert_called_once()
        kwargs = self.news_to_audio.twilio_client.messages.create.call_args[1]
        self.assertEqual(kwargs['from_'], 'whatsapp:+1234567890')
        self.assertEqual(kwargs['to'], 'whatsapp:+0987654321')
        self.assertIn('file://', kwargs['media_url'][0])
    
    def test_create_env_template(self):
        # Call the create_env_template method
        success = NewsToAudio.create_env_template('.env.test')
        
        # Assert that the method returns True
        self.assertTrue(success)
        
        # Assert that the file was created
        self.assertTrue(os.path.exists('.env.test'))
        
        # Clean up
        os.remove('.env.test')

if __name__ == '__main__':
    unittest.main()