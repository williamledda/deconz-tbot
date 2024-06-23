# deconz-tbot service

How to install `deconz-tbot.service` and enable at system boot:

```bash
sudo cp service/deconz-bot.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable nyborg-bot.service
```