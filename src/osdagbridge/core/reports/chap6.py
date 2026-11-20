def ch6_drawings(fig_paths):
    """Render captured engineering drawings and mark unavailable views."""

    heading = r"""
\chapter{Drawings and Visualizations}
\label{ch:drawings}
"""
    drawing_keys = (
        "final_geometry", "cross_section", "girder_top", "girder_3d",
        "section_preview", "stiffener_preview", "cb_diagram",
        "cb_bracing", "cb_top_chord", "cb_bottom_chord",
        "ed_diagram", "ed_bracing", "ed_top_chord", "ed_bottom_chord",
    )
    if not any(fig_paths.get(key) for key in drawing_keys):
        return heading + "CAD drawings were unavailable when this report was generated."

    def _sec_fig(path, title, label=None):
        """Figure block: image first, numbered below. Placeholder if no path."""
        label_tex = (r'\label{' + label + '}' + "\n") if label else ''
        if path:
            p = path.replace('\\', '/')
            return (r'\begin{figure}[H]' + '\n'
                    r'\centering' + '\n'
                    r'\vspace{4pt}' + '\n'
                    r'\includegraphics[width=0.85\textwidth]{' + p + '}' + '\n'
                    r'\caption{' + title + '}\n'
                    + label_tex
                    + r'\end{figure}' + '\n'
                    )
        return r"\par\noindent\textit{Drawing unavailable: " + title + "}\n"

    sup3d  = _sec_fig(fig_paths.get('final_geometry'),   'Overall 3D Bridge Superstructure',   'fig:bridge-3d')
    cs     = _sec_fig(fig_paths.get('cross_section'),     'Typical Cross Section',              'fig:cross-section')
    gtop   = _sec_fig(fig_paths.get('girder_top'),         'Top View',                          'fig:top-view')
    g3d    = _sec_fig(fig_paths.get('girder_3d'),          '3D View of Plate Girders',          'fig:girder-3d')
    gxsec  = _sec_fig(fig_paths.get('section_preview'),   'Cross Section of Plate Girder',     'fig:girder-xsec')
    gside  = _sec_fig(fig_paths.get('stiffener_preview'),  'Side View of Girder',              'fig:girder-side')
    cbdia  = _sec_fig(fig_paths.get('cb_diagram'),         'Cross Bracing Layout',             'fig:cb-layout')

    def _sec_cell(path, title, label=None):
        """One minipage cell: image above, numbered below (for side-by-side row)."""
        label_tex = (r'\label{' + label + '}') if label else ''
        if path:
            p = path.replace('\\', '/')
            body = r'\includegraphics[width=\linewidth]{' + p + '}'
        else:
            return (r'\begin{minipage}[t]{0.31\textwidth}\centering\textit{Drawing unavailable: '
                    + title + r'}\end{minipage}')
        return (r'\begin{minipage}[t]{0.31\textwidth}' + '\n'
                r'\centering' + '\n'
                + body + '\n'
                r'\captionsetup{hypcap=false}\captionof{figure}{' + title + '}\n'
                + label_tex + '\n'
                r'\end{minipage}')

    # Cross Bracing section views (Figures 6.8, 6.9, 6.10) — 3 columns
    cb_bracing = _sec_cell(
        fig_paths.get('cb_bracing'),
        'Cross Bracing -- Bracing Section',
        'fig:cb-bracing-sec'
    )

    cb_top = _sec_cell(
        fig_paths.get('cb_top_chord'),
        'Cross Bracing -- Top Chord Section',
        'fig:cb-top-chord'
    )

    cb_bottom = _sec_cell(
        fig_paths.get('cb_bottom_chord'),
        'Cross Bracing -- Bottom Chord Section',
        'fig:cb-bottom-chord'
    )
    cb_sections_row = (
    r'\noindent' + '\n'
    + cb_bracing + '\n'
    + r'\hfill' + '\n'
    + cb_top + '\n'
    + r'\hfill' + '\n'
    + cb_bottom
)

    eddia  = _sec_fig(fig_paths.get('ed_diagram'),        'End Diaphragm Layout',              'fig:ed-layout')

    # End Diaphragm section views (Figures 6.12, 6.13, 6.14) — 3 columns
    ed_bracing = _sec_cell(
        fig_paths.get('ed_bracing'),
        'End Diaphragm -- Bracing Section',
        'fig:ed-bracing-sec'
    )

    ed_top = _sec_cell(
        fig_paths.get('ed_top_chord'),
        'End Diaphragm -- Top Chord Section',
        'fig:ed-top-chord'
    )

    ed_bottom = _sec_cell(
        fig_paths.get('ed_bottom_chord'),
        'End Diaphragm -- Bottom Chord Section',
        'fig:ed-bottom-chord'
    )
    ed_sections_row = (
    r'\noindent' + '\n'
    + ed_bracing + '\n'
    + r'\hfill' + '\n'
    + ed_top + '\n'
    + r'\hfill' + '\n'
    + ed_bottom
)

    return (heading + r"""

Captured CAD views are shown where available. Unavailable drawings are identified in the corresponding section.

\section{Bridge Configuration and Layout}
\label{sec:bridge-layout}

"""
            + sup3d + '\n\n'
            + cs + '\n\n'
            + gtop + r"""

\section{Plate Girder --- Detailed Views}
\label{sec:girder-views}

"""
            + g3d + '\n\n'
            + gxsec + '\n\n'
            + gside + r"""

\section{Cross Bracing Detail}
\label{sec:bracing-detail}

"""
            + cbdia + '\n\n'
            + cb_sections_row + r"""
            

\section{End Diaphragm Detail}
\label{sec:diaphragm-detail}

"""
            + eddia + '\n\n'
            + ed_sections_row + r"""

""")
