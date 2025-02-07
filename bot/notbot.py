import json
import os
from dotenv import load_dotenv
from telegram.constants import ParseMode
from telegram.ext import MessageHandler, filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)
from .async_do import scrape_smu_fbs
from .async_do import fill_missing_timeslots


def read_token_env():
    """
    read bot token from a .env file
    """
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        print("One or more credentials are missing in the .env file")
        return None
    else:
        return bot_token


def read_token_json(token_filepath):
    """
    !NOTE
    this function is now deprecated as bot token
    is saved as a .env file instead

    read locally stored bot api token stored as a
    json file
    """
    try:
        with open(token_filepath, "r") as file:
            data = json.load(file)
        return data["bot_token"]
    except FileNotFoundError:
        print("File not found. Please check the file path.")
        return None
    except json.JSONDecodeError:
        print("Error decoding JSON. Please check the file format.")
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Poke to start scraping 🤯", callback_data="run_script")],
        [
            InlineKeyboardButton(
                "Pinch to alert help desk 📖", callback_data="view_help"
            )
        ],
        [InlineKeyboardButton("Tickle to open settings ⚙️", callback_data="settings")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        'Welcome to <a href="https://github.com/gongahkia/sagasu">Sagasu</a>!',
        parse_mode=ParseMode.HTML,
    )
    await update.message.reply_text(
        "Ello! Click one option below 👋", reply_markup=reply_markup
    )


async def run_script(callback_query: Update, context: ContextTypes.DEFAULT_TYPE):
    await callback_query.answer()
    print("Running the scraping script...")
    TARGET_URL = "https://fbs.intranet.smu.edu.sg/home"
    # CREDENTIALS_FILEPATH = "credentials.json"

    USER_EMAIL = context.user_data.get("email")
    USER_PASSWORD = context.user_data.get("password")

    # print(USER_EMAIL, USER_PASSWORD)
    # if not USER_EMAIL:
    #     await callback_query.message.reply_text("Email not provided lah! Go set it in settings. 💀")
    #     return
    # elif not USER_PASSWORD:
    #     await callback_query.message.reply_text("Password is missing leh! Go set it in settings. 🤡")
    #     return

    try:

        result = await scrape_smu_fbs(TARGET_URL, USER_EMAIL, USER_PASSWORD)

        result_errors = result[0]
        result_final_booking_log = result[1]
        metrics = result_final_booking_log["metrics"]
        scraped_configuration = result_final_booking_log["scraped"]["config"]
        scraped_results = result_final_booking_log["scraped"]["result"]

        # ----- REPLY THE USER -----

        await callback_query.message.reply_text(
            f"Scraping carried out on at <b>{metrics['scraping_date']} ⏲️</b>\n\n"
            f"<b>Your scraping configuration ⚙️</b>\n"
            f"<i>Target date:</i> {scraped_configuration['date']}\n"
            f"<i>Target start time:</i> {scraped_configuration['start_time']}\n"
            f"<i>Target end time:</i> {scraped_configuration['end_time']}\n"
            f"<i>Target duration:</i> {scraped_configuration['duration']}\n"
            f"<i>Target buildings:</i> {', '.join(scraped_configuration['building_names'])}\n"
            f"<i>Target floors:</i> {', '.join(scraped_configuration['floors'])}\n"
            f"<i>Target facility types:</i> {', '.join(scraped_configuration['facility_types'])}\n"
            f"<i>Target room capacity:</i> {scraped_configuration['room_capacity']}\n"
            f"<i>Target equipment:</i> {', '.join(scraped_configuration['equipment'])}",
            parse_mode=ParseMode.HTML,
        )

        print("Scraping completed successfully.")

        if len(result_errors) > 0:
            response_text = ""
            response_text = "\n".join(result_errors)
            max_length = 4096
            for i in range(0, len(response_text), max_length):
                await callback_query.message.reply_text(
                    response_text[i : i + max_length]
                )
        else:
            for room, bookings in scraped_results.items():
                complete_bookings = fill_missing_timeslots(bookings)
                response_text = ""
                response_text += f"<code>{room}</code> 🏠\n\n"
                for booking in complete_bookings:
                    if booking["available"]:
                        response_text += f"<i>Timeslot:</i> {booking['timeslot']}\n"
                        response_text += f"<i>Status:</i> <u><a href='https://fbs.intranet.smu.edu.sg/home'>Available to book</a></u> ✅\n\n"
                    else:
                        if booking["details"]:
                            response_text += f"<i>Timeslot:</i> {booking['timeslot']}\n"
                            response_text += f"<i>Status:</i> Booked ❌\n"
                            response_text += f"<i>Purpose:</i> {booking['details']['Purpose of Booking']}\n"
                            response_text += f"<i>Booker:</i> {booking['details']['Booked for User Name']} ({booking['details']['Booked for User Email Address']})\n"
                            response_text += f"<i>Booking ref no:</i> {booking['details']['Booking Reference Number']}\n\n"
                        else:
                            response_text += f"<i>Timeslot:</i> {booking['timeslot']}\n"
                            response_text += f"<i>Status:</i> Outside hours and cannot be booked 🔒\n\n"
                await callback_query.message.reply_text(
                    response_text, parse_mode=ParseMode.HTML
                )
            await callback_query.message.reply_text(
                "<b><i>All results have been displayed! 🥳</i></b>",
                parse_mode=ParseMode.HTML,
            )

    except Exception as e:
        print(f"Error during scraping: {e}")
        await callback_query.message.reply_text(
            "An error occurred during the scraping process. Report the issue @gongahkia."
        )

    finally:
        if context.bot_data.get("browser"):
            await context.bot_data["browser"].close()
            print("Browser closed.")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "run_script":

        USER_EMAIL = context.user_data.get("email")
        USER_PASSWORD = context.user_data.get("password")

        # print(USER_EMAIL, USER_PASSWORD)

        if not USER_EMAIL:
            await query.message.reply_text(
                "Email not provided lah! Go set it in settings. 💀"
            )
            return
        elif not USER_PASSWORD:
            await query.message.reply_text(
                "Password is missing leh! Go set it in settings. 🤡"
            )
            return
        else:
            await query.message.reply_text(
                "Email and Password found! Initiating scraping... 👌"
            )

        new_keyboard = [
            [
                InlineKeyboardButton(
                    "Oke the script is running 🏃...", callback_data="disabled"
                )
            ]
        ]
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(new_keyboard)
        )
        try:
            await run_script(query, context)
        except Exception as e:
            print(f"Error during scraping: {e}")
            try:
                await query.edit_message_text(
                    "An error occurred during the scraping process. 🌋"
                )
            except Exception as edit_error:
                print(f"Failed to edit message: {edit_error}")
    elif query.data == "view_help":
        await query.edit_message_text(
            "<code>Sagasu</code> scrapes SMU FBS data.\n\nType /start to see all options\nType /help for help\nType /settings to adjust your configurations",
            parse_mode=ParseMode.HTML,
        )
    elif query.data == "settings":
        await query.message.reply_text("Please enter your SMU email address 📧")
        context.user_data["settings_state"] = "awaiting_email"


async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("settings_state") == "awaiting_email":
        context.user_data["email"] = update.message.text
        await update.message.reply_text(
            "SMU email saved!\nPlease enter your password 🔑"
        )
        context.user_data["settings_state"] = "awaiting_password"
        # print("Email received:", context.user_data['email'])
    else:
        await update.message.reply_text(
            "Don't cut queue lah you.\nType /settings to enter your email 🐻‍❄️."
        )


async def handle_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("settings_state") == "awaiting_password":
        context.user_data["password"] = update.message.text
        await update.message.reply_text("Password saved!\nSettings updated ☑️")
        context.user_data["settings_state"] = None
        # print("Password received:", context.user_data['password'])
    else:
        await update.message.reply_text(
            "Don't cut queue lah you.\nType /settings to enter your password 🐻."
        )


async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("settings_state")
    if state == "awaiting_email":
        await handle_email(update, context)
    elif state == "awaiting_password":
        await handle_password(update, context)
    else:
        await update.message.reply_text(
            "Quit yapping bruh, I'm not expecting any input right now.\nType /settings to configure. 🦜"
        )


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["settings_state"] = "awaiting_email"
    await update.message.reply_text("Please enter your SMU email address 📧")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "<code>Sagasu</code> scrapes SMU FBS data.\n\nType /start to see all options\nType /help for help\nType /settings to adjust your configurations",
        parse_mode=ParseMode.HTML,
    )


def main():
    app = ApplicationBuilder().token(read_token_env()).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT, handle_text_input))
    print("Bot is polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
