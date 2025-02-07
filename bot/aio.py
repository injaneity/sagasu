import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from aiogram.utils.executor import start_polling
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Telegram Bot Token is not set. Please check your .env file.")

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Define states for email and password input
class UserInput(StatesGroup):
    email = State()
    password = State()

# Start command handler
@dp.message_handler(commands="start")
async def start_command(message: types.Message):
    # Create the reply keyboard
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    credentials_button = KeyboardButton("Enter Credentials")
    scrape_button = KeyboardButton("Scrape Facilities")
    info_button = KeyboardButton("Info")
    github_button = KeyboardButton("\U0001F5C3")  # Unicode for a GitHub-like square icon
    report_button = KeyboardButton("Report Issue")

    keyboard.row(scrape_button, credentials_button)
    keyboard.row(info_button, github_button, report_button)

    # Send the message with the reply keyboard
    await message.reply("Welcome! Choose an option below:", reply_markup=keyboard)

# Handler for "Enter Credentials" button
@dp.message_handler(lambda message: message.text == "Enter Credentials")
async def handle_enter_credentials(message: types.Message, state: FSMContext):
    await UserInput.email.set()
    sent_message = await message.reply("Please enter your email:")
    await state.update_data(email_message_id=sent_message.message_id)

# Handler for "Scrape Facilities" button
@dp.message_handler(lambda message: message.text == "Scrape Facilities")
async def handle_scrape_facilities(message: types.Message):
    await message.reply("Scraping facilities... (This is a placeholder)")

# Handler for "Info" button
@dp.message_handler(lambda message: message.text == "Info")
async def handle_info(message: types.Message):
    await message.reply("This bot helps you manage and scrape facilities. Contact support for more info.")

# Handler for GitHub button
@dp.message_handler(lambda message: message.text == "\U0001F5C3")
async def handle_github(message: types.Message):
    await message.reply("Visit our GitHub repository here: https://github.com/your-repository")

# Handler for "Report Issue" button
@dp.message_handler(lambda message: message.text == "Report Issue")
async def handle_report_issue(message: types.Message):
    await message.reply("Please describe the issue you're experiencing, and we will assist you as soon as possible.")

# Email input handler
@dp.message_handler(state=UserInput.email)
async def email_input(message: types.Message, state: FSMContext):
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        print(f"Failed to delete email message: {e}")

    if "@" in message.text:
        await state.update_data(email=message.text)
        user_data = await state.get_data()
        email_message_id = user_data.get("email_message_id")

        # Remove the "Enter your email" message
        try:
            if email_message_id:
                await bot.delete_message(message.chat.id, email_message_id)
        except Exception as e:
            print(f"Failed to delete email prompt: {e}")

        await UserInput.password.set()
        sent_message = await bot.send_message(message.chat.id, "Please enter your password (at least 8 characters):")
        await state.update_data(password_message_id=sent_message.message_id)
    else:
        await bot.send_message(message.chat.id, "Invalid email. Please try again:")

# Password input handler
@dp.message_handler(state=UserInput.password)
async def password_input(message: types.Message, state: FSMContext):
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        print(f"Failed to delete password message: {e}")

    password = message.text
    if len(password) >= 8:
        user_data = await state.get_data()
        email = user_data.get("email")
        password_message_id = user_data.get("password_message_id")

        # Remove the "Enter your password" message
        try:
            if password_message_id:
                await bot.delete_message(message.chat.id, password_message_id)
        except Exception as e:
            print(f"Failed to delete password prompt: {e}")

        # Print the email and password
        print(f"Email: {email}, Password: {password}")

        await bot.send_message(message.chat.id, "Thank you! Your credentials have been securely processed.")
        await state.finish()
    else:
        await bot.send_message(message.chat.id, "Password too short. Please enter at least 8 characters:")

# Disallow other inputs during the state
@dp.message_handler(state=UserInput)
async def invalid_input(message: types.Message):
    await bot.send_message(message.chat.id, "Invalid input. Please follow the instructions.")

# Main entry point
if __name__ == "__main__":
    # Run the bot
    start_polling(dp, skip_updates=True)
