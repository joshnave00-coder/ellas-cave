"""leaderboard.py — score persistence, top-5 leaderboard."""
import json, os, sys

LB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leaderboard.json")


class Leaderboard:
    def __init__(self):
        self.scores = []
        self._load()

    def _load(self):
        if os.path.exists(LB_FILE):
            try:
                with open(LB_FILE) as f:
                    self.scores = json.load(f).get('scores', [])
            except Exception:
                self.scores = []

    def save(self):
        try:
            with open(LB_FILE, 'w') as f:
                json.dump({'scores': self.scores}, f, indent=2)
        except Exception as e:
            print(f"Leaderboard save error: {e}", file=sys.stderr)

    def qualifies(self, score):
        if score <= 0:
            return False
        if len(self.scores) < 5:
            return True
        return score > min(s['score'] for s in self.scores)

    def add(self, initials, score):
        init = (initials.upper() + 'AAA')[:3]
        self.scores.append({'initials': init, 'score': int(score)})
        self.scores.sort(key=lambda s: s['score'], reverse=True)
        self.scores = self.scores[:5]
        self.save()

    def top5(self):
        return self.scores[:5]


LEADERBOARD = Leaderboard()
