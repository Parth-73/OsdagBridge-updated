"""Shared formatting for report longtables."""


def repeated_header(row, *, footer=False):
    """Emit the same column-heading row on first and continuation pages."""
    header = "\\hline\n" + row + "\n\\hline\n"
    repeat = header + "\\endfirsthead\n" + header + "\\endhead\n"
    return repeat + ("\\hline\n\\endfoot\n" if footer else "")



def completed_rows(body):
    """Keep the closing rule with the final data row."""
    body = body.rstrip()
    if not body:
        return ""
    return body.removesuffix(r"\hline") + r"\noalign{\nobreak}\specialrule{\arrayrulewidth}{0pt}{0pt}" + "\n"



def load_longtable(caption, columns, heading, rows):
    """Build a PyLaTeX load table with first-page and continuation headings."""
    from pylatex import LongTable, NoEscape

    table = LongTable(NoEscape(columns))
    table.append(NoEscape(r"\caption{\textbf{" + caption + r"}}\\" + "\n"))
    table.append(NoEscape(repeated_header(heading, footer=True)))
    table.append(NoEscape(rows.rstrip().removesuffix(r"\hline")))
    return table.dumps()
