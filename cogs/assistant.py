#Made by Autism

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
        self.helius_assistant_id = "asst_Ha98jCNa9rIRvw8L7dFXUZyh"  # Your HELIUS assistant ID
        self.last_bot_message_id = None  # Track the last message ID sent by the bot
        self.allowed_channel_ids = [1112510368879743146]  # Allowed channel ID

    @commands.Cog.listener()
    async def on_ready(self):
        print("Helius is alive!")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.channel.id not in self.allowed_channel_ids:
            return

        # Check if the message is a mention of the bot or a reply to the bot's last message
        is_mention = self.bot.user in message.mentions
        is_reply = message.reference and message.reference.message_id == self.last_bot_message_id

        if is_mention or is_reply:
            user_id = message.author.id
            if user_id not in self.user_threads:
                self.user_threads[user_id] = client.beta.threads.create().id

            async with message.channel.typing():
                async with self.api_semaphore:
                    try:
                        # Adding the user's message to the thread
                        client.beta.threads.messages.create(
                            thread_id=self.user_threads[user_id],
                            role="user",
                            content=message.content
                        )

                        # Make the assistant process the conversation and generate a response
                        run = client.beta.threads.runs.create(
                            thread_id=self.user_threads[user_id],
                            assistant_id=self.helius_assistant_id
                        )

                        # Wait for the run to complete
                        run = wait_on_run(run, self.user_threads[user_id])

                        # Fetching the latest messages in the thread including the assistant's response
                        messages = client.beta.threads.messages.list(thread_id=self.user_threads[user_id]).data

                        # Displaying the assistant's response
                        for msg in messages:
                            if msg.role == "assistant":
                                bot_message = await message.channel.send(f"HELIUS: {msg.content}")
                                self.last_bot_message_id = bot_message.id

                    except Exception as e:
                        logger.error(f"Error while generating response: {str(e)}")
                        await message.channel.send("Sorry, I'm having trouble generating a response.")

def setup(bot):
    bot.add_cog(HeliusChatBot(bot))
