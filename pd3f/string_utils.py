def strip_spaces_line_end(text):
    """Removing spaces at the end of a line.

    For instance in this string `the text  \n` the space is removed.
    While `the text\n` the string is unchanged.
    """
    if len(text) < 2:
        return text
    if text[-1] == "\n":
        if text[-2] == " ":
            return strip_spaces_line_end(text[:-2]) + "\n"
    return text
