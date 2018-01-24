# Flash Home
Proof of concept for integrating IOTA flash channels into home automation systems.

## Setup

Please clone this repository recursively:

```
git clone --recursive https://github.com/jinnerbichler/flash-home
```

and run it via

```
docker-compose up coffee-client flash-coffee flash-provider
```

in order to execute the protoype on your local machine.

The following endpoints are provided:

* Home Assistant: [http://localhost:8123](http://localhost:8123) (with UI)
* Flash Server Coffee Machine: http://localhost:3000 (no UI)
* Flash Server Service Provider: http://localhost:3001 (no UI)

**Only Dependencies**:

* Docker
* Docker Compose

## Components

The exemplary setup mainly consists of five components (1) Home Assistant, (2) Flash client of coffee machine, (3) Flash server of coffee machine and (4) Flash server of service profider and (5) a private testnet of the Tangle. An overview of components and their interaction can be seen in the schema below.

![Components](./home-assistant/config/www/architecture.png)

### Home Assistant

**Home Assistant Source:** [https://github.com/home-assistant/home-assistant](https://github.com/home-assistant/home-assistant)

**Home Assistant Config:** `home-assistant/config`

### Flash Client of Coffee Machine

### Flash Server of Coffee Machine

### Flash Servier of Service Provider

### Private Instance of Tangle (Testnet)
