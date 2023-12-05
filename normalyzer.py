class Normalyzer(object):
    def normalazye(self, scores, smallIsBetter=0):
        vsmall = 0.00001
        minscore = min(scores.values())
        maxscore = max(scores.values())
        for (key, val) in scores.items():
            if smallIsBetter:
                scores[key] = float(minscore) / max(vsmall, val)
            else:
                scores[key] = float(val) / maxscore
        return scores
