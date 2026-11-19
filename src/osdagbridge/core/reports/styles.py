"""Shared LaTeX and chart presentation settings."""

import re

from .report_utils import _tex

OSDAG_GREEN = "#91B014"
CHART_PASS = "#537710"
CHART_FAILURE = "#BD252E"
CHART_TEXT = "#252B24"
CHART_GRID = "#DCE1D7"
CHART_DPI = 180
CHART_WIDTH = 8.4
CHART_LABEL_SIZE = 10
UR_LIMIT = 1.0


def _header_text(value):
    # Bound the running header to two lines. Full metadata appears on the cover.
    value = " ".join(value.split())
    if len(value) > 46:
        value = value[:43].rstrip() + "..."
    return break_long_words(value)


def break_long_words(value):
    """Allow unspaced identifiers to wrap while preserving their visible text."""
    return "".join(
        r"\allowbreak{}".join(_tex(word[i:i + 12]) for i in range(0, len(word), 12))
        if len(word) > 12 and not word.isspace() else _tex(word)
        for word in re.split(r"(\s+)", str(value or ""))
    )


def preamble(project_name, job_number, report_date, report_version='Rev 0'):
    left_header = _header_text(f"{project_name or ''} | {job_number or ''}".strip(" |"))
    right_header = _header_text(f"{report_date or ''} | {report_version or ''}".strip(" |"))
    return r"""
\documentclass[12pt,a4paper]{report}

% Packages
\usepackage[a4paper,hmargin=16mm,top=14mm,bottom=17mm,
  includeheadfoot,headheight=28pt,headsep=10pt,footskip=39pt]{geometry}
\usepackage{graphicx}
\setkeys{Gin}{height=0.67\textheight,keepaspectratio}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{booktabs}
\usepackage{array}
\usepackage{tabularx}
\usepackage{float}
\usepackage{fancyhdr}
\usepackage[hidelinks]{hyperref}
\usepackage{xcolor}
\usepackage{setspace}
\usepackage{enumitem}
\usepackage{caption}

\captionsetup{
    labelfont=bf,
    font=small,
    justification=raggedright,
    singlelinecheck=false,
    format=plain
}
\usepackage{subcaption}
\usepackage{multirow}
\usepackage{colortbl}
\usepackage{longtable}
\setlength{\LTleft}{\fill}
\setlength{\LTright}{\fill}
\usepackage{titlesec}
\usepackage{titletoc}
\usepackage{lastpage}
\usepackage{makecell}
\usepackage{etoolbox}
\usepackage{needspace}

% A member group uses a starred row break and a partial rule with no break.
% Keep the penalty before the rule's vertical glue, where TeX can break.
\makeatletter
\let\report@cline\@cline
\patchcmd{\report@cline}{\vskip-\arrayrulewidth}{\nobreak\vskip-\arrayrulewidth}{}{}
\newcommand{\reportcline}[1]{\report@cline#1\@nil}
\makeatother


\numberwithin{table}{chapter}
\numberwithin{figure}{chapter}
% Table layout and spacing: consistent padding, row height, and longtable pre/post skips
\setlength{\tabcolsep}{4pt}
\renewcommand{\arraystretch}{1.12}
\setlength{\LTpre}{4pt}
\setlength{\LTpost}{6pt}
\setlength{\intextsep}{10pt plus 2pt minus 2pt}
\setlength{\textfloatsep}{12pt plus 2pt minus 2pt}
\setlength{\emergencystretch}{2em}
% Table rules (outline thickness) and small extra row height for clarity
\setlength{\arrayrulewidth}{0.5pt}
\setlength{\extrarowheight}{0.6pt}

% Give fixed tables some room. Longtable manages its own page breaks.
\BeforeBeginEnvironment{table}{\needspace{5\baselineskip}}

\definecolor{osdagGreen}{HTML}{""" + OSDAG_GREEN.lstrip("#") + r"""}
\definecolor{reportFailure}{HTML}{""" + CHART_FAILURE.lstrip("#") + r"""}

\newcommand{\reportfooter}{%
  \fancyfoot[L]{\footnotesize
    \shortstack[l]{\textit{* Software default value}\\
      Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}}%
  \fancyfoot[R]{\footnotesize Page \thepage\ of \pageref{LastPage}}%
  \renewcommand{\footrulewidth}{1pt}%
  \renewcommand{\footrule}{{\color{osdagGreen}\hrule width\headwidth height\footrulewidth}\vskip 3pt}%
}
\newcommand{\reportpagestyle}{%
  \fancyhf{}%
  \fancyhead[L]{\parbox[b]{0.61\textwidth}{\footnotesize\raggedright """ + left_header + r"""}}%
  \fancyhead[R]{\parbox[b]{0.36\textwidth}{\footnotesize\raggedleft """ + right_header + r"""}}%
  \renewcommand{\headrulewidth}{1pt}%
  \renewcommand{\headrule}{{\color{osdagGreen}\hrule width\headwidth height\headrulewidth}}%
  \reportfooter
}
\fancypagestyle{main}{\reportpagestyle}
\fancypagestyle{plain}{\reportpagestyle}
\fancypagestyle{firstpage}{%
  \fancyhf{}%
  \renewcommand{\headrulewidth}{0pt}%
  \reportfooter
}
\pagestyle{main}
\setstretch{1.15}

% Custom Commands
\newcommand{\placeholder}[1]{\textit{\textless #1\textgreater}}
\newcommand{\todo}[1]{\colorbox{yellow}{TODO: #1}}
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}
\newcolumntype{R}[1]{>{\raggedleft\arraybackslash}p{#1}}

% Software-default asterisk
\newcommand{\sdstar}{\textsuperscript{*}}

\title{\Large\textbf{OsdagBridge} \\ \normalsize Open Source Software for Steel Girder Bridge Design \\ \vspace{2cm} \large Design Report}
\author{}
\date{}

\begin{document}
\titleformat{\chapter}[block]
  {\normalfont\Large\bfseries\centering}{\thechapter}{1em}{}
\titlespacing*{\chapter}{0pt}{0pt}{10pt}
"""
