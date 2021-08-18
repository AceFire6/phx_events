# PHX Events

PHX Events is an AsyncIO library to set up a websocket connection with 
[Phoenix](https://phoenixframework.org/) in Python 3.9+ via Phoenix Channels.

## Developing

This project uses [`pip-tools`](https://github.com/jazzband/pip-tools/) to manage dependencies.

### 1. Create a virtualenv

Note: Creating the virtualenv can be done however you want. We will assume you've done created a new
virtualenv and activated it from this point.

### 2. Install `pip-tools`:

```shell
pip install pip-tools
```

### 3. Install Dependencies

```shell
pip-sync requirements/core.txt requirements/dev.txt 
```
