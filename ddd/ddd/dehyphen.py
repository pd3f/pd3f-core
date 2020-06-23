from cleantext import clean

from .score import score_perplexity

# dehyphenation
def dehyphen(lines):
    # special format. 2D List, word should not contain whitespace, except the last words per line
    print(lines)
    for idx, l in enumerate(lines):
        # don't work on last line
        if idx == len(lines) - 1:
            continue
        last_word = l[-1]

        # don't work if ther has to be a newline
        if last_word[-1] == "\n":
            continue

        last_char = clean(last_word.strip()[-1])
        if last_char == "-":
            next_word = lines[idx + 1][0]

            # 1. two words (e.g. part of an abrev.), so do nothing
            option1 = last_word + next_word

            # 2. some compound-word (keep hyphen), remove whitespace
            option2 = last_word.strip() + next_word

            # 3. remove hyphen, most likely to happen
            option3 = last_word.strip()[:-1] + next_word

            scores = score_perplexity([option1, option2, option3], sync=True)
            print(scores)
            best_score_idx = scores.index(min(scores))
            assert best_score_idx in (0, 1, 2)

            # in all cases: remove last element because we add it to the beginning of the next line
            lines[idx].pop()

            # if best_score_idx == 0:
            #     lines[idx + 1][0] = option1

            # add whitespace otherwise

            if best_score_idx == 1:
                lines[idx + 1][0] = " " + option2

            if best_score_idx == 2:
                lines[idx + 1][0] = " " + option3

    return lines
