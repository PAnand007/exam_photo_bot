# Use Python 3.11
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Set environment variable for production if needed
# ENV BOT_TOKEN=your_bot_token_here

# Run the bot
CMD ["python", "bot.py"]
