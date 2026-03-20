class States:
    MENU_MODE: int
    RANDOM_MODE: int
    GPT_MODE: int
    TALK_SELECT: int
    TALK_DIALOG: int
    QUIZ_SELECT: int
    QUIZ_QUESTION: int

MODES_MAP = {
    "MENU_MODE": "MENU",
    "RANDOM_MODE": "RANDOM",
    "GPT_MODE": "GPT",
    "TALK_SELECT": "TALK",
    "TALK_DIALOG": "TALK",
    "QUIZ_SELECT": "QUIZ",
    "QUIZ_QUESTION": "QUIZ"
}

MODES = {}

for i, (state_name, group_name) in enumerate(MODES_MAP.items()):
    setattr(States, state_name, i)
    MODES[i] = group_name
