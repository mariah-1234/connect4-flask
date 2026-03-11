import random

from game import Game
from puissance4 import check_victory
from save_to_db import save_game_from_list
from ai_moves import choose_move


def generate_game(confidence):

    game = Game()
    moves = []

    while True:

        valid = game.valid_moves()

        if not valid:
            break

        # choisir le coup selon le niveau
        confidence = random.choice([0,1,2,3])
        col = choose_move(game.board, confidence)

        if col is None:
            break

        game.play(col)

        moves.append(col)

        winner, line = check_victory(game.board)

        if winner:
            break

    return moves


def generate_games(n=1000):

    for i in range(n):

        # choisir un niveau aléatoire
        confidence = random.randint(0,3)

        moves = generate_game(confidence)

        save_game_from_list(
            player1="AI",
            player2="AI",
            mode=0,
            moves_list=moves,
            confidence=confidence
        )

        if i % 100 == 0:
            print("Parties générées :", i)


if __name__ == "__main__":

    generate_games(1000)