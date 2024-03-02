# net-bot

telegram bot at aiogram3\
scans network by python-nmap, and store devices at SQLite\
then gets table to bot


#

### 1. change config

store telegram TOKEN at .env.example from <a href="https://telegram.me/BotFather">BotFather</a>\
change admin ID with ur ID (u can get it from start command if don't know)\
change period of scans at scan.py (optional)


### 2. install

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
cp .env.example .env
sudo apt install nmap python3-nmap -y
```

#

### 3. start scan
```bash
sudo python3 scan.py
```


### 4. start bot

may need new terminal session
```bash
# may need
sudo chown $USER:$USER net_devs.db
# start bot
python3 -m bot
```
