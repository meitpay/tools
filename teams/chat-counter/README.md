# Teams message counter

Count the number of messages in a Teams Chat for a time intervall in months.

## Prerequiste

[python](<https://www.python.org/downloads/>)

[WSL](<https://learn.microsoft.com/en-us/windows/wsl/install>)

[graph Explorer](<https://developer.microsoft.com/en-us/graph/graph-explorer>)

- Use the graph explorer to get your access token and chatId.
- *Note:* You need to request access to use the API to read your chat.

## Usage

### Install requirements

```sh
# setup virtual env
python3 -m venv .venv

# install requirements
pip install -r requirements.txt
```

### dotenv

```sh
# copy .env.example to .env and populate it
cp .env.example .env
```

```sh
TOKEN="<YOUR_TOKEN_HERE>"
CHAT_ID="<YOUR_CHAT_ID_HERE>"

YEAR=
DAY=
START_MONTH=
END_MONTH=
```

### Run

```sh
# run script
python counter.py
```
