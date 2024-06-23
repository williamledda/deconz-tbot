import requests
import subprocess
import configparser
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Application

phoscon_url = ""
lights_map = {"esterno": 1, "viale": 2}


def log(message: str) -> None:
    print(f"{message}", flush=True)


async def reboot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    log("Rebooting...")
    await update.message.reply_text('Rebooting...')
    result = subprocess.run(["reboot"])
    if result.returncode != 0:
        log("Reboot failed.")


async def power_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    log("Power off...")
    await update.message.reply_text("Powering off...")
    result = subprocess.run(["poweroff"])
    if result.returncode != 0:
        log("poweroff")


async def restart_deconz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Restarting deconz-gui service...')
    result = subprocess.run(["sudo", "systemctl", "restart", "deconz-gui"])
    if result.returncode != 0:
        log("Restart deconz failed")


async def get_lights(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = requests.get(f"{phoscon_url}/lights")
    await update.message.reply_text(f"Lights: {response.json()}")


async def set_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) == 0:
        reply = ""
        log("Switch on all lights...")
        for light_id in lights_map.values():
            response = requests.put(f"{phoscon_url}/lights/{light_id}/state", data='{"on": true}')
            reply += f"{response.json()}\n"
        await update.message.reply_text(f"On: {reply}")
    elif context.args[0].lower() in lights_map:
        log(f"Switch on {context.args[0].lower()} lights...")
        light_id = lights_map[context.args[0].lower()]
        response = requests.put(f"{phoscon_url}/lights/{light_id}/state", data='{"on": true}')
        await update.message.reply_text(f"On: {response.json()}")
    else:
        await update.message.reply_text(f"Light {context.args[0]} not found")


async def set_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) == 0:
        reply = ""
        log("Switch off all lights...")
        for id in lights_map.values():
            response = requests.put(f"{phoscon_url}/lights/{id}/state", data='{"on": false}')
            reply += f"{response.json()}\n"
        await update.message.reply_text(f"Off: {reply}")
    elif context.args[0].lower() in lights_map:
        log(f"Switch off {context.args[0].lower()} lights...")
        light_id = lights_map[context.args[0].lower()]
        response = requests.put(f"{phoscon_url}/lights/{light_id}/state", data='{"on": false}')
        await update.message.reply_text(f"Off: {response.json()}")
    else:
        await update.message.reply_text(f"Light {context.args[0]} not found")


async def post_init(my_app: Application) -> None:
    await my_app.bot.set_my_commands([
        ("lights", "Get list of lights"),
        ("on", "Light on"),
        ("off", "Light off"),
        ("poweroff", "Power off gateway"),
        ("reboot", "Reboot gateway"),
        ("restart_service", "Restart only deconz"),
    ])

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read("conf/bot_config.ini")

    phoscon_url = f"http://{config.get('phoscon', 'address')}/api/{config.get('phoscon', 'token')}"

    if "bot" in config and "token" in config['bot']:
        app = ApplicationBuilder().token(config['bot']['token']).post_init(post_init).build()
        app.add_handler(CommandHandler("reboot", reboot))
        app.add_handler(CommandHandler("poweroff", power_off))
        app.add_handler(CommandHandler("restart_service", restart_deconz))
        app.add_handler(CommandHandler("lights", get_lights))
        app.add_handler(CommandHandler("on", set_on))
        app.add_handler(CommandHandler("off", set_off))

        app.run_polling()
    else:
        log("Telegram token is missing! Unable to continue.")

