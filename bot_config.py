"""
Bot Configuration — maps each bot to its token, username, and agent.
"""

BOT_CONFIG = {
    "bighead": {
        "token_env": "TELEGRAM_BOT_TOKEN_BIGHEAD",
        "username": "Lamboeye_bot",
        "display_name": "Big Head",
        "agent_key": "kk",  # Big Head handles KK/general until Monkey is added
    },
    "donkey": {
        "token_env": "TELEGRAM_BOT_TOKEN_DONKEY",
        "username": "ximen_donkey_bot",
        "display_name": "Donkey",
        "agent_key": "intelligence",
    },
    "ox": {
        "token_env": "TELEGRAM_BOT_TOKEN_OX",
        "username": "ximen_ox_bot",
        "display_name": "Ox",
        "agent_key": "todo",
    },
    "pig": {
        "token_env": "TELEGRAM_BOT_TOKEN_PIG",
        "username": "ximen_piggie_bot",
        "display_name": "Pig",
        "agent_key": "research",
    },
    "dog": {
        "token_env": "TELEGRAM_BOT_TOKEN_DOG",
        "username": "ximen_dog_bot",
        "display_name": "Dog",
        "agent_key": "health",
    },
}

# Reverse mapping: agent_key -> bot_key
AGENT_TO_BOT = {cfg["agent_key"]: key for key, cfg in BOT_CONFIG.items()}

# Bot username -> bot_key (case-insensitive lookup)
USERNAME_TO_BOT = {cfg["username"].lower(): key for key, cfg in BOT_CONFIG.items()}
