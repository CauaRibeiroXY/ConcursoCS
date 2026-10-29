"""PDF text extraction respecting multi-column layouts using pdfplumber."""


import pdfplumber


def extract_text_columns(pdf_path: str) -> str:
    """Extract text handling two-column layout.

    Groups words by column (left/right based on x-coordinate),
    then concatenates left-column text then right-column text per page.
    """
    all_pages: list[str] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words(keep_blank_chars=True, x_tolerance=3)
            if not words:
                continue

            # Determine column split: find the gap between columns
            xs = sorted({w["x0"] for w in words})
            # Find largest gap between consecutive x positions
            gaps = [(xs[i + 1] - xs[i], xs[i], xs[i + 1]) for i in range(len(xs) - 1)]
            if not gaps:
                continue
            max_gap = max(gaps, key=lambda g: g[0])
            split_x = (max_gap[1] + max_gap[2]) / 2 if max_gap[0] > 50 else 0

            if split_x == 0:
                # Single column page
                lines = _words_to_lines(words, 0)
                all_pages.append("\n".join(lines))
                continue

            # Split into left/right
            left_words = [w for w in words if w["x0"] < split_x]
            right_words = [w for w in words if w["x0"] >= split_x]

            left_lines = _words_to_lines(left_words, 0)
            right_lines = _words_to_lines(right_words, split_x)

            # Concatenate: left column first, then right column
            page_text = "\n".join(left_lines)
            if right_lines:
                page_text += "\n" + "\n".join(right_lines)
            all_pages.append(page_text)

    return "\n".join(all_pages)


def _words_to_lines(words: list, col_x: float) -> list[str]:
    """Group words into lines based on y-position."""
    if not words:
        return []

    # Sort by vertical position (top), then horizontal
    sorted_words = sorted(words, key=lambda w: (round(w["top"], 0), w["x0"]))

    lines: list[list[dict]] = []
    current_line = [sorted_words[0]]
    current_y = round(sorted_words[0]["top"], 0)

    for w in sorted_words[1:]:
        wy = round(w["top"], 0)
        if abs(wy - current_y) <= 4:
            current_line.append(w)
        else:
            lines.append(current_line)
            current_line = [w]
            current_y = wy
    if current_line:
        lines.append(current_line)

    result = []
    for line in lines:
        text = " ".join(w["text"] for w in line)
        result.append(text)
    return result
