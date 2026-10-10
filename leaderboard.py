"""leaderboard.py — score persistence, top-5 leaderboard."""
import json, os, sys

LB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leaderboard.json")


class Leaderboard:
    def __init__(self):
        self.scores = []
        self._load()

    @staticmethod
    def _clean(raw):
        """Keep only well-formed entries so a hand-edited or damaged file can
        never crash the score screens."""
        out = []
        for s in raw if isinstance(raw, list) else []:
            try:
                score = int(s['score'])
                init = (''.join(ch for ch in str(s['initials']).upper()
                                if 'A' <= ch <= 'Z') + 'AAA')[:3]
            except (KeyError, TypeError, ValueError, OverflowError):
                continue
            out.append({'initials': init, 'score': score})
        out.sort(key=lambda s: s['score'], reverse=True)
        return out[:5]

    def _load(self):
        if os.path.exists(LB_FILE):
            try:
                with open(LB_FILE) as f:
                    self.scores = self._clean(json.load(f).get('scores', []))
            except Exception as e:
                self.scores = []
                # Unreadable file: set it aside rather than letting the next
                # save silently overwrite whatever scores were in it.
                try:
                    os.replace(LB_FILE, LB_FILE + '.corrupt')
                    print(f"Leaderboard unreadable ({e}); moved to "
                          f"{LB_FILE}.corrupt", file=sys.stderr)
                except OSError:
                    pass

    def save(self):
        # Write to a temp file then swap it in, so a crash or power cut
        # mid-write can't leave a truncated leaderboard behind.
        tmp = LB_FILE + '.tmp'
        try:
            with open(tmp, 'w') as f:
                json.dump({'scores': self.scores}, f, indent=2)
            os.replace(tmp, LB_FILE)
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
