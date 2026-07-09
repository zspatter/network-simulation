"""
PDF rendering for scenario_report.py, kept in its own module so the optional `reportlab`
dependency (see pyproject.toml's `report` extra) is only imported when `--formats` actually
includes `pdf` - the default markdown/csv path never touches this module.
"""
from pathlib import Path
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from scenario_report import (
    DEFAULT_REFERENCE_STRATEGY,
    HorizonResult,
    _significance_floor_note,
    _significance_rows,
    _summary_rows,
    _trajectory_rows,
)

_TABLE_STYLE = TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTSIZE', (0, 0), (-1, -1), 8),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f2f2f2')]),
])


def write_pdf_report(horizon_results: List[HorizonResult], output_path: Path,
                     network_node_count: int, transplant_hospital_count: int,
                     opo_count: int) -> None:
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    story = [Paragraph('National Allocation Strategy Scenario Report', styles['Title']),
            Spacer(1, 12),
            Paragraph('Methodology', styles['Heading2']),
            Paragraph(
                    f'Network: {network_node_count} real nodes ({transplant_hospital_count} '
                    f'transplant hospitals, {opo_count} Organ Procurement Organizations) from '
                    'the OPTN membership directory, geocoded via the US Census Bureau geocoder '
                    '(Nominatim fallback). See the accompanying Markdown/CSV report for full '
                    'methodology, calibration sourcing, and per-strategy tier descriptions.',
                    styles['BodyText']),
            Spacer(1, 12)]

    summary_headers = ['strategy', 'transplanted', 'wasted', 'deaths', 'hi-acuity\ndeaths',
                       'median\nwait', 'life-years', 'final\nwait list']
    trajectory_headers = ['strategy', 'year', 'wait list size']
    significance_headers = ['strategy', 'metric', 'mean diff', '95% CI', 'effect\nsize',
                            'adj. p', 'sig']

    for result in horizon_results:
        story.append(Paragraph(f'{result.years}-Year Horizon ({result.seeds} seed(s))',
                               styles['Heading2']))

        story.append(Paragraph('Summary', styles['Heading3']))
        story.append(Table([summary_headers] + _summary_rows(result), style=_TABLE_STYLE))
        story.append(Spacer(1, 12))

        trajectory_rows = [trajectory_headers] + _trajectory_rows(result.trials_by_strategy)
        story.append(Paragraph('Wait-List Size Trajectory (by year)', styles['Heading3']))
        story.append(Table(trajectory_rows, style=_TABLE_STYLE))
        story.append(Spacer(1, 12))

        if result.significance:
            significance_rows = [significance_headers] + _significance_rows(result.significance)
            story.append(Paragraph(f'Significance vs. {DEFAULT_REFERENCE_STRATEGY}',
                                   styles['Heading3']))
            story.append(Table(significance_rows, style=_TABLE_STYLE))
            floor_note = _significance_floor_note(result.seeds, result.significance)
            if floor_note:
                story.append(Spacer(1, 6))
                # The markdown emphasis markers render literally in reportlab - strip them.
                story.append(Paragraph(floor_note.replace('**', '').replace('`', ''),
                                       styles['BodyText']))

        story.append(Spacer(1, 20))

    doc.build(story)
