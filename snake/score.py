import asyncio
import numpy as np
import pickle


class Score():
    try:
        with open('high_scores.pkl', 'rb') as f:
            high_scores = pickle.load(f)

    except FileNotFoundError as e:
        high_scores = {}

    @classmethod
    def save(cls, size, user_id, score):
        """Saves the score, if it is higher than the previous one.
        size: tuple (size_x, size_y) of the game played.
        user_id: int of the Discord user ID.
        score: int of the user's score.
        """
        try:
            size_scores = cls.high_scores[size]
        except KeyError:
            # user has no data yet, we create one for the given size and score
            cls.high_scores[size] = {user_id: score}
        else:
            # user has data, we check if it has one of given size
            try:
                size_scores[user_id] = max(size_scores[user_id], score)
            except KeyError:
                # user has no data for the given size, we create it
                size_scores[user_id] = score

        # save the scores on file.
        with open('high_scores.pkl', 'wb') as f:
            pickle.dump(cls.high_scores, f)

    @classmethod
    def get(cls, size, user_id):
        """Returns a user's high score in a given size. If user has no score,
        return None."""
        try:
            return cls.high_scores[size][user_id]
        except KeyError:
            return None

    @classmethod
    def get_top(cls, size):
        """Returns only the highest score of a given size. Returns None if it
        does not exist yet."""
        try:
            return max(cls.high_scores[size].values())
        except KeyError:
            return None

    @classmethod
    def get_top_users(cls, size):
        """Returns a list of users ID with the highest score in a given size.
        Returns an empty list if no scores are available at this size."""
        try:
            size_scores = cls.high_scores[size]
        except KeyError:
            return []
        else:
            top_score = max(size_scores.values())

            # assume more than one user can have top score
            top_users = []
            for k in size_scores.keys():
                if size_scores[k] == top_score:
                    top_users.append(k)

            return top_users
