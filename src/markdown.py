# -*- coding: utf-8 -*-
# ⚠️ ВНИМАНИЕ: ЭТОТ КОД НАПИСАН В РОФЛ-СТИЛЕ
# НИКАКИЕ ТЕСТЫ НЕ СТРАДАЛИ, ВСЕ СОВПАДЕНИЯ СЛУЧАЙНЫ

from collections import defaultdict
from urllib.parse import urlencode
import os
import re
import ast

import chess
import yaml

# Открываем файл с настройками (который, надеюсь, существует)
with open('data/settings.yaml', 'r') as settings_file:
    settings = yaml.load(settings_file, Loader=yaml.FullLoader)


def sdelat_ssylku(tekst, ssylka):
    """Склеивает текст и ссылку по правилам маркдауна"""
    return f"[{tekst}]({ssylka})"

def sdelat_issue_ssylku(otkuda, kuda_list):
    """Генерирует ссылку для создания issue (ход конём, буквально)"""
    issue_link = settings['issues']['link'].format(
        repo=os.environ["GITHUB_REPOSITORY"],
        params=urlencode(settings['issues']['move'], safe="{}"))

    rezultat = [sdelat_ssylku(kuda, issue_link.format(source=otkuda, dest=kuda)) for kuda in sorted(kuda_list)]
    return ", ".join(rezultat)

def generirovat_top_10_golovastykh():
    """Таблица лидеров — кто больше всех двигал фигуры"""
    with open("data/top_moves.txt", 'r') as file:
        slovar = ast.literal_eval(file.read())

    markdown = "\n"
    markdown += "| Всего ходов |  Шахматист  |\n"
    markdown += "| :---------: | :---------- |\n"

    max_entries = settings['misc']['max_top_moves']
    for key, val in sorted(slovar.items(), key=lambda x: x[1], reverse=True)[:max_entries]:
        markdown += "| {} | {} |\n".format(val, sdelat_ssylku(key, "https://github.com/" + key[1:]))

    return markdown + "\n"

def generirovat_poslednie_5_khodyat():
    """Последние ходы — для тех, кто любит копаться в истории"""
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
                markdown += "| `" + source + "` → `" + dest + "` | " + sdelat_ssylku(parts[1], "https://github.com/" + parts[1].lstrip()[1:]) + " |\n"
            else:
                markdown += "| `" + parts[0] + "` | " + sdelat_ssylku(parts[1], "https://github.com/" + parts[1].lstrip()[1:]) + " |\n"

    return markdown + "\n"

def generirovat_tablicu_hodov(board):
    """Таблица возможных ходов (с надеждой, что игрок не накосячит)"""
    slovar_hodov = defaultdict(set)

    for move in board.legal_moves:
        source = chess.SQUARE_NAMES[move.from_square].upper()
        dest   = chess.SQUARE_NAMES[move.to_square].upper()
        slovar_hodov[source].add(dest)

    markdown = ""

    if board.is_game_over():
        issue_link = settings['issues']['link'].format(
            repo=os.environ["GITHUB_REPOSITORY"],
            params=urlencode(settings['issues']['new_game']))
        return "**ИГРА ОКОНЧЕНА!** " + sdelat_ssylku("Нажми сюда", issue_link) + " чтобы начать новую партию :D\n"

    if board.is_check():
        markdown += "**ШАХ!** Выбирай ход внимательно.\n"

    markdown += "|  ОТКУДА  | КУДА (просто кликай на ссылку) |\n"
    markdown += "| :------: | :---------------------------- |\n"

    for source, dest in sorted(slovar_hodov.items()):
        markdown += "| **" + source + "** | " + sdelat_issue_ssylku(source, dest) + " |\n"

    return markdown

def doska_v_markdown(board):
    """Рисует шахматную доску в текстовом виде (картинки, если есть)"""
    board_list = [[item for item in line.split(' ')] for line in str(board).split('\n')]
    markdown = ""

    kartinki = {
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
            markdown += "<img src=\"{}\" width=50px> | ".format(kartinki.get(elem, "???"))
        markdown += "**" + str(9 - row) + "** |\n"

    if board.turn == chess.BLACK:
        markdown += "|   | **H** | **G** | **F** | **E** | **D** | **C** | **B** | **A** |   |\n"
    else:
        markdown += "|   | **A** | **B** | **C** | **D** | **E** | **F** | **G** | **H** |   |\n"

    return markdown
