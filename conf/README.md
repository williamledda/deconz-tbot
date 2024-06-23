# deconz-bot config

To run deconz-bot you need a configuration file file called `bot_config.ini` inside the `conf`.
To do so, follow the following steps:

1. Create a file called `bot_config.ini` inside the `conf`
2. Copy the content of the following template into the file
3. Customize the template with your telegram token, the IP address of your Phoscon gateway and the API token


```ini
[bot]
token=<Your telegram bot API token>

[phoscon]
address=<IP address of your gateway>
token=<Your Phoscon API>
```
