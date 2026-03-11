import random

from game import Game
from puissance4 import check_victory
from save_to_db import save_game_from_list


def generate_random_game():

    game = Game()
    moves = []

    while True:

        valid = game.valid_moves()

        if not valid:
            break

        col = random.choice(valid)

        game.play(col)

        moves.append(col)

        winner, line = check_victory(game.board)

        # arrêter dès qu'il y a un gagnant
        if winner:
            break

    return moves


def generate_many_games(n):

    print("Début génération...")

    for i in range(n):

        moves = generate_random_game()

        save_game_from_list(
            player1="RandomAI",
            player2="RandomAI",
            mode=0,
            moves_list=moves
        )

        if i % 100 == 0:
            print("Parties générées :", i)

    print("FIN")


if __name__ == "__main__":

    generate_many_games(5000)