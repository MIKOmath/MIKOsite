from django import template

register = template.Library()

@register.filter
def upper(value):
    return value.upper()

@register.filter

def latex_preview(text):
    delimiters = [
        "$$", "$", "\\(", "\\)", "\\begin{equation}", "\\end{equation}",
        "\\begin{align}", "\\end{align}", "\\begin{alignat}", "\\end{alignat}",
        "\\begin{gather}", "\\end{gather}", "\\begin{CD}", "\\end{CD}",
        "\\[", "\\]"
    ]

    def is_latex_boundary(index):
        for delim in delimiters:
            if text[index:].startswith(delim) and (index == 0 or text[index-1] != '\\'):
                return True
        return False

    total_length = len(text)

    if total_length <= 50:
        return text

    if total_length <= 125:
        target_length = 50
    else:
        target_length = int(total_length * 0.4)

    in_latex = False
    last_space = -1
    i = 0
    while i < target_length:
        if is_latex_boundary(i):
            in_latex = not in_latex
            # Skip the entire delimiter
            for delim in delimiters:
                if text[i:].startswith(delim):
                    i += len(delim) - 1
                    break
        elif text[i].isspace() and not in_latex:
            last_space = i
        i += 1

    if last_space == -1 or in_latex:
        # If we're still in a LaTeX expression or haven't found a space,
        # continue until we find the end of the current LaTeX expression or a space
        while i < total_length:
            if is_latex_boundary(i):
                in_latex = not in_latex
                # Skip the entire delimiter
                for delim in delimiters:
                    if text[i:].startswith(delim):
                        i += len(delim) - 1
                        break
            elif text[i].isspace() and not in_latex:
                last_space = i
                break
            i += 1

    preview = text[:last_space + 1] if last_space != -1 else text
    return preview + ('...' if len(preview) < total_length else '')


# register.filter("latex_preview", latex_preview)