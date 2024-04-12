# communal-billing-bot
 
## set-up
### Copy credentails.json file
### Create .env file
### Install dependencies
```sh
pipenv install
```
### Activate virtual environment
```sh
pipenv shell
```

## Pipenv commands

#### Deactivate
```bash
deactivate
```
#### Remove
```bash
pipenv --venv
``` 
```
rm -rf path/to/venv
```

## Run

```sh
uvicorn src.main:app --reload
```