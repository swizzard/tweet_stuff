import os
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"words.txt")) as f:
    words = [w.rstrip() for w in f.readlines()]
with open(os.path.join(os.path.dirname(os.path.abspath(__file__))),"lowered_words.json") as f:
    lowered_words = [w.rstrip() for w in f.readlines()]

def split_string(s, resource=words):
    found = []
    def rec(remainder, so_far):
        if not remainder:
            found.append(so_far)
        for pos in xrange(1, len(remainder)+1):
            if remainder[:pos] in resource:
                rec(remainder[pos:], so_far+[remainder[:pos]])
    rec(s.lower(),[])
    return found
