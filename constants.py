from fbchat.models import *


react_mapping = {
                            MessageReaction.WOW: "wow",
                            MessageReaction.HEART: "love",
                            MessageReaction.YES: "yes",
                            MessageReaction.NO: "no",
                            MessageReaction.SAD: "sad",
                            MessageReaction.SMILE: "haha",
                            MessageReaction.ANGRY: "grr"
                        }

react_mapping_inv = {
                            "wow" : MessageReaction.WOW,
                            "love" : MessageReaction.HEART,
                            "yes" : MessageReaction.YES,
                            "no" : MessageReaction.NO,
                            "sad" : MessageReaction.SAD,
                            "haha" :MessageReaction.SMILE,
                            "grr" : MessageReaction.ANGRY
                        }

login_page = [
        "┌─────────┐                      ",
        "│ courier │                      ",
        "├─────────┴───────────┐          ",
        "│ a cli for messenger │          ",
        "└─────────────────────┘          ",
        "",
        '',
        "┌ login ────────────────────────┐",
        "│                               │",
        "└───────────────────────────────┘",
        "┌ password ─────────────────────┐",
        "│                               │",
        "└───────────────────────────────┘",
        "",
        "tab to edit, enter to login      ",
       
    ]

splash_page = [
        "┌─────────┐                      ",
        "│ courier │                      ",
        "├─────────┴───────────┐          ",
        "│ a cli for messenger │          ",
        "└─────────────────────┘          ",
       
    ]
