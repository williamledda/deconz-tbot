from http import HTTPStatus

import requests
import subprocess
import configparser
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Application

phoscon_url = ""
lights_map = {"esterno": 1, "viale": 2, "ingresso": 3}
therm_map = {"sala": 6}


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
    if response.status_code == HTTPStatus.OK:
        await update.message.reply_text(f"Lights: {json.dumps(response.json(), indent=1)}")
    else:
        await update.message.reply_text(f"Error: {response.status_code}")


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
        if response.status_code == HTTPStatus.OK:
            await update.message.reply_text(f"On: {json.dumps(response.json(), indent=1)}")
        else:
            await update.message.reply_text(f"Error: {response.status_code}")
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
        if response.status_code == HTTPStatus.OK:
            await update.message.reply_text(f"On: {json.dumps(response.json(), indent=1)}")
        else:
            await update.message.reply_text(f"Error: {response.status_code}")
    else:
        await update.message.reply_text(f"Light {context.args[0]} not found")

async def thermostats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = requests.get(f"{phoscon_url}/sensors")
    if response.status_code == HTTPStatus.OK:
        out = {}
        json_response = response.json()
        for key in json_response.keys():
            if json_response[key]["type"] == 'ZHAThermostat':
                out[key] = json_response[key]

        await update.message.reply_text(f"Thermostats {json.dumps(out, indent=2)}")
    else:
        await update.message.reply_text(f"Error: {response.status_code}")


async def set_heat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) == 0:
        await update.message.reply_text(f"Missing target temperature")
    else:
        try:
            set_point = float(context.args[0]) * 100
            # Clamp to 500
            set_point = max(set_point, 500.0)
            response = requests.put(f"{phoscon_url}/sensors/6/config", data=f'{{ "heatsetpoint": {set_point} }}')

            if response.status_code == HTTPStatus.OK:
                await update.message.reply_text(f"Temperature set: {json.dumps(response.json(), indent=2)}")
            else:
                await update.message.reply_text(f"Error: {response.status_code}")
        except ValueError:
            await update.message.reply_text(f"Error: {context.args[0]} is not a valid temperature")


async def set_heat_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = requests.put(f"{phoscon_url}/sensors/6/config", data='{ "heatsetpoint": 500}')

    if response.status_code == HTTPStatus.OK:
        await update.message.reply_text(f"Thermostat: {json.dumps(response.json(), indent=2)}")
    else:
        await update.message.reply_text(f"Error: {response.status_code}")


async def post_init(my_app: Application) -> None:
    await my_app.bot.set_my_commands([
        ("lights", "Get list of lights"),
        ("thermostats", "Get list of thermostats"),
        ("on", "Light on"),
        ("off", "Light off"),
        ("heat", "Set thermostat temperature"),
        ("heat_off", "Set thermostat off"),
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
        app.add_handler(CommandHandler("thermostats", thermostats))
        app.add_handler(CommandHandler("heat", set_heat))
        app.add_handler(CommandHandler("heat_off", set_heat_off))

        app.run_polling()
    else:
        log("Telegram token is missing! Unable to continue.")

