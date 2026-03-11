def parse_moves(replay_json):

    moves = []

    for move in replay_json:

        column = move["args"]["column"]

        moves.append(column)

    return moves