# Made by Autism

import asyncio
import logging
import os
import time
import openai
from openai import OpenAI
from nextcord.ext import commands

logger = logging.getLogger('discord')
client = OpenAI()

# Load the OpenAI API key from Replit secrets
openai.api_key = os.getenv('OPENAI_API_KEY')

# Load Assistant ID
ASSISTANT_ID = os.getenv('ASSISTANT_ID')

def wait_on_run(run, thread_id):
    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run

class HeliusChatBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_semaphore = asyncio.Semaphore(50)
        self.user_threads = {}  # Stores thread IDs for each user
        self.helius_assistant_id = ASSISTANT_ID        
        self.last_bot_message_id = None  # Track the last message ID sent by the bot
        self.allowed_channel_ids = [1112510368879743146]  # Allowed channel IDs

    @commands.Cog.listener()
    async def on_ready(self):
        print("Helius is alive!")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.channel.id not in self.allowed_channel_ids:
            return

        is_mention = self.bot.user in message.mentions
        is_reply = message.reference and message.reference.message_id == self.last_bot_message_id

        if is_mention or is_reply:
            user_id = message.author.id
            if user_id not in self.user_threads:
                self.user_threads[user_id] = client.beta.threads.create().id

            async with message.channel.typing():
                async with self.api_semaphore:
                    try:
                        client.beta.threads.messages.create(
                            thread_id=self.user_threads[user_id],
                            role="user",
                            content=message.content
                        )

                        run = client.beta.threads.runs.create(
                            thread_id=self.user_threads[user_id],
                            assistant_id=self.helius_assistant_id
                        )

                        run = wait_on_run(run, self.user_threads[user_id])

                        messages = client.beta.threads.messages.list(thread_id=self.user_threads[user_id]).data
                        latest_assistant_message = next((msg for msg in messages if msg.role == "assistant"), None)

                        if latest_assistant_message:
                            response_texts = []
                            for content_item in latest_assistant_message.content:
                                # Debugging: Print attributes of the content item
                                # print(dir(content_item))
                                # Assuming 'text' attribute has a 'value' attribute
                                if hasattr(content_item, 'text') and hasattr(content_item.text, 'value'):
                                    response_texts.append(content_item.text.value)
                            response_text = ' '.join(response_texts)
                            bot_message = await message.channel.send(response_text)
                            self.last_bot_message_id = bot_message.id

                    except Exception as e:
                        logger.error(f"Error while generating response: {str(e)}")
                        await message.channel.send("Sorry, I'm having trouble generating a response.")

def setup(bot):
    bot.add_cog(HeliusChatBot(bot))