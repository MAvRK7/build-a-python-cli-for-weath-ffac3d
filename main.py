refined_code
```
#!/usr/bin/env python3
"""
Weather CLI: A production-quality Python CLI for weather forecasting with email alerts.

This script provides a command-line interface to fetch current weather forecasts and send email
alerts for specific conditions (e.g., hot, cold, rain) using the OpenWeatherMap API.

Features:
- Fetch current weather for a city (forecast subcommand).
- Check conditions and send email alerts if met (alert subcommand).

Dependencies:
- requests (for API calls)
- python-dotenv (for loading environment variables)
- smtplib, email (standard library for sending emails)
- Install via: pip install requests python-dotenv

Setup:
1. Sign up for a free OpenWeatherMap account at https://openweathermap.org/api and get an API key.
2. Create a .env file in the script directory with:
   API_KEY=your_openweathermap_api_key
   EMAIL=your_sender_email@gmail.com
   EMAIL_PASSWORD=your_app_password (use Gmail app password, not regular password)
3. For Gmail: Enable 2FA and generate an app password at https://myaccount.google.com/apppasswords.
4. Make the script executable: chmod +x weather_cli.py
5. Run examples:
   python weather_cli.py forecast London
   python weather_cli.py alert London hot user@example.com

Usage:
python weather_cli.py <command> [args]
Commands:
  forecast <city>     : Get current weather for the city.
  alert <city> <condition> <email> : Send alert if condition met.
    Conditions: hot (temp > 30°C), cold (temp < 0°C), rain (raining).

Error Handling:
- Logs errors to stderr.
- Graceful failures for invalid cities, API issues, or email problems.
"""

import os
import sys
import logging
import requests
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
import argparse

# Load environment variables
load_dotenv()

# Setup logging for production quality
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_weather(city, api_key):
    """
    Fetch current weather data for a city from OpenWeatherMap API.
    
    Args:
        city (str): City name.
        api_key (str): OpenWeatherMap API key.
    
    Returns:
        dict: Weather data JSON.
    
    Raises:
        ValueError: On API error.
    """
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data['cod'] != 200:
            raise ValueError(f"City not found or API error: {data.get('message', 'Unknown error')}")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise ValueError(f"Failed to fetch weather for {city}: {e}")

def send_email(to_email, subject, body, from_email, password):
    """
    Send an email alert using SMTP (Gmail).
    
    Args:
        to_email (str): Recipient email.
        subject (str): Email subject.
        body (str): Email body.
        from_email (str): Sender email.
        password (str): Sender password/app password.
    
    Raises:
        ValueError: On SMTP error.
    """
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        logger.info(f"Email sent to {to_email}")
    except smtplib.SMTPException as e:
        logger.error(f"Email sending failed: {e}")
        raise ValueError(f"Failed to send email: {e}")

def main():
    parser = argparse.ArgumentParser(description="Weather CLI for forecasts and alerts")
    subparsers = parser.add_subparsers(dest='command', help='Available commands', required=True)

    # Forecast subcommand
    forecast_parser = subparsers.add_parser('forecast', help='Get current weather forecast for a city')
    forecast_parser.add_argument('city', help='City name (e.g., London)')

    # Alert subcommand
    alert_parser = subparsers.add_parser('alert', help='Send email alert if weather condition is met')
    alert_parser.add_argument('city', help='City name')
    alert_parser.add_argument('condition', choices=['hot', 'cold', 'rain'], help='Condition to check')
    alert_parser.add_argument('email', help='Recipient email address')

    args = parser.parse_args()

    # Load env vars
    api_key = os.getenv('API_KEY')
    from_email = os.getenv('EMAIL')
    email_password = os.getenv('EMAIL_PASSWORD')

    if not all([api_key, from_email, email_password]):
        logger.error("Missing environment variables. Ensure .env has API_KEY, EMAIL, EMAIL_PASSWORD.")
        sys.exit(1)

    try:
        weather_data = get_weather(args.city, api_key)

        if args.command == 'forecast':
            temp = weather_data['main']['temp']
            description = weather_data['weather'][0]['description']
            logger.info(f"Forecast for {args.city}: {description}, {temp}°C")
            print(f"Weather in {args.city}: {description.title()}, Temperature: {temp}°C")

        elif args.command == 'alert':
            temp = weather_data['main']['temp']
            main_weather = weather_data['weather'][0]['main']
            description = weather_data['weather'][0]['description']

            alert_triggered = False
            alert_message = ""

            if args.condition == 'hot' and temp > 30:
                alert_triggered = True
                alert_message = f"Hot weather alert in {args.city}! Temperature: {temp}°C"
            elif args.condition == 'cold' and temp < 0:
                alert_triggered = True
                alert_message = f"Cold weather alert in {args.city}! Temperature: {temp}°C"
            elif args.condition == 'rain' and main_weather == 'Rain':
                alert_triggered = True
                alert_message = f"Rain alert in {args.city}! Weather: {description}"
            else:
                logger.info(f"No alert for {args.condition} in {args.city}")
                print("No alert needed - condition not met.")
                return

            if alert_triggered:
                subject = f"Weather Alert: {args.condition.title()} in {args.city}"
                body = f"{alert_message}\n\nCurrent conditions: {description}, {temp}°C at {weather_data['dt_txt'] if 'dt_txt' in weather_data else 'now'}."
                send_email(args.email, subject, body, from_email, email_password)
                print(f"Alert sent to {args.email}!")

    except ValueError as e:
        logger.error(str(e))
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```