# -*- coding: utf-8 -*-
from collections import defaultdict
from urllib.parse import urlencode
import os
import re
import ast

import chess
import yaml

with open('data/settings.yaml', 'r') as settings_file:
    settings = yaml.load(settings_file, Loader=yaml.FullLoader)


def create_link(text, link):
    return f"[{text}]({link})"

def create_issue_link(source, dest_list):
    issue_link = settings['issues']['link'].format(
        repo=os.environ["GITHUB_REPOSITORY"],
        params=urlencode(settings['issues']['move'], safe="{}"))

    ret = [create_link(dest, issue_link.format(source=source, dest=dest)) for dest in sorted(dest_list)]
    return ", ".join(ret)

def generate_top_moves():
    with open("data/top_moves.txt", 'r') as file:
        dictionary = ast.literal_eval(file.read())

    markdown = "\n"
    markdown += "| Всего ходов |  Шахматист  |\n"
    markdown += "| :---------: | :---------- |\n"

    max_entries = settings['misc']['max_top_moves']
    for key, val in sorted(dictionary.items(), key=lambda x: x[1], reverse=True)[:max_entries]:
        markdown += "| {} | {} |\n".format(val, create_link(key, "https://github.com/" + key[1:]))

    return markdown + "\n"

def generate_last_moves():
    markdown = "\n"
    markdown += "| Ход | Шахматист |\n"
    markdown += "| :--: | :------- |\n"

    counter = 0

    with open("data/last_moves.txt", 'r') as file:
        for line in file.readlines():
            parts = line.rstrip().split(':')

            if not ":" in line:
                continue

            if counter >= settings['misc']['max_last_moves']:
                break

            counter += 1

            match_obj = re.search('([A-H][1-8])([A-H][1-8])', line, re.I)
            if match_obj is not None:
                source = match_obj.group(1).upper()
                dest   = match_obj.group(2).upper()
                markdown += "| `" + source + "` → `" + dest + "` | " + create_link(parts[1], "https://github.com/" + parts[1].lstrip()[1:]) + " |\n"
            else:
                markdown += "| `" + parts[0] + "` | " + create_link(parts[1], "https://github.com/" + parts[1].lstrip()[1:]) + " |\n"

    return markdown + "\n"

def generate_moves_list(board):
    moves_dict = defaultdict(set)

    for move in board.legal_moves:
        source = chess.SQUARE_NAMES[move.from_square].upper()
        dest   = chess.SQUARE_NAMES[move.to_square].upper()
        moves_dict[source].add(dest)

    markdown = ""

    if board.is_game_over():
        issue_link = settings['issues']['link'].format(
            repo=os.environ["GITHUB_REPOSITORY"],
            params=urlencode(settings['issues']['new_game']))
        return "**ИГРА ОКОНЧЕНА!** " + create_link("Нажми сюда", issue_link) + " чтобы начать новую партию :D\n"

    if board.is_check():
        markdown += "**ШАХ!** Выбирай ход внимательно.\n"

    markdown += "|  ОТКУДА  | КУДА (просто кликай на ссылку) |\n"
    markdown += "| :------: | :---------------------------- |\n"

    for source,dest in sorted(moves_dict.items()):
        markdown += "| **" + source + "** | " + create_issue_link(source, dest) + " |\n"

    return markdown

def board_to_markdown(board):
    board_list = [[item for item in line.split(' ')] for line in str(board).split('\n')]
    markdown = ""

    images = {
        "r": "img/black/rook.svg",
        "n": "img/black/knight.svg",
        "b": "img/black/bishop.svg",
        "q": "img/black/queen.svg",
        "k": "img/black/king.svg",
        "p": "img/black/pawn.svg",

        "R": "img/white/rook.svg",
        "N": "img/white/knight.svg",
        "B": "img/white/bishop.svg",
        "Q": "img/white/queen.svg",
        "K": "img/white/king.svg",
        "P": "img/white/pawn.svg",

        ".": "img/blank.png"
    }

    if board.turn == chess.BLACK:
        markdown += "|   | H | G | F | E | D | C | B | A |   |\n"
    else:
        markdown += "|   | A | B | C | D | E | F | G | H |   |\n"
    markdown += "|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|\n"

    rows = range(1, 9)
    if board.turn == chess.BLACK:
        rows = reversed(rows)

    for row in rows:
        markdown += "| **" + str(9 - row) + "** | "
        columns = board_list[row - 1]
        if board.turn == chess.BLACK:
            columns = reversed(columns)

        for elem in columns:
            markdown += "<img src=\"{}\" width=50px> | ".format(images.get(elem, "???"))
        markdown += "**" + str(9 - row) + "** |\n"

    if board.turn == chess.BLACK:
        markdown += "|   | **H** | **G** | **F** | **E** | **D** | **C** | **B** | **A** |   |\n"
    else:
        markdown += "|   | **A** | **B** | **C** | **D** | **E** | **F** | **G** | **H** |   |\n"

    return markdown
