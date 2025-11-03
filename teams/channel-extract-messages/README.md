# Teams Extract Messages from Teams -> Channel

Extract messages from a MS Teams Channel from a given date.

## Prerequiste

[python](<https://www.python.org/downloads/>)

[WSL](<https://learn.microsoft.com/en-us/windows/wsl/install>)

[graph Explorer](<https://developer.microsoft.com/en-us/graph/graph-explorer>)

[Filtering](<https://community.powerplatform.com/forums/thread/details/?threadid=8cab61e2-ef6e-46f9-95d5-f49a3df4885b>)

- Use the graph explorer to get your access token and chatId.
- *Note:* You need to request access to use the API to read your chat.

## Usage

### Install requirements

```sh
# setup virtual env
python3 -m venv .venv

# use .venv
source ./venv/bin/activate

# install requirements
pip install -r requirements.txt
```

### Variables

```sh
# copy .env.example to .env and populate it
cp .env.example .env
```

```sh
# Teams
GRAPH_ACCESS_TOKEN='<YOUR_TOKEN>'
TEAM_ID='<YOUR_TEAM_ID>'
CHANNEL_ID='<YOUR_CHANNEL_ID>'

# Start date for message extraction
START_DATE_UTC="2025-01-01T00:00:00.000Z"

```

### Run

```sh
# Get all messages
python3 get_all_messages.py

# convert to xlsx
python3 convert_to_excel.py <input-json-file> <output-excel-file.xlsx>

```
