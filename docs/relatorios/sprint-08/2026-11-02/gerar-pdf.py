"""Gera o PDF parcial da Sprint 08 do Markdown e dos JPGs originais recebidos.

Requer ReportLab e Pillow. Não executa nem altera a aplicação Lumina Odonto.
"""

from pathlib import Path
import html
import re

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image as PDFImage, LongTable, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, TableStyle,
)

BASE = Path(__file__).resolve().parent
SOURCE = BASE / 'relatorio-parcial-sprint-08.md'
OUTPUT = BASE / 'Lumina-Odonto-Sprint-08-consolidacao-parcial-2026-11-02.pdf'

font_pairs = [
    (Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
     Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')),
    (Path('C:/Windows/Fonts/arial.ttf'), Path('C:/Windows/Fonts/arialbd.ttf')),
]
regular, bold = next(((a, b) for a, b in font_pairs if a.exists() and b.exists()), (None, None))
if regular is None:
    raise RuntimeError('Disponibilize DejaVu Sans no Linux ou Arial no Windows.')
pdfmetrics.registerFont(TTFont('Lumina', str(regular)))
pdfmetrics.registerFont(TTFont('Lumina-Bold', str(bold)))
pdfmetrics.registerFontFamily('Lumina', normal='Lumina', bold='Lumina-Bold', italic='Lumina', boldItalic='Lumina-Bold')

PAGE_W, PAGE_H = landscape(A3)
LEFT = RIGHT = 48
TOP = 46
BOTTOM = 46
WIDTH = PAGE_W - LEFT - RIGHT
HEIGHT = PAGE_H - TOP - BOTTOM

doc = SimpleDocTemplate(
    str(OUTPUT), pagesize=(PAGE_W, PAGE_H),
    leftMargin=LEFT, rightMargin=RIGHT, topMargin=TOP, bottomMargin=BOTTOM,
    title='Lumina Odonto — Sprint 08: consolidação parcial e planejamento de conclusão',
    author='Lumina Odonto — relatório documental para Paulo Sérgio e Cassiano Augusto',
    subject='Estado parcial; QA independente posterior pendente; imagens históricas v0.2',
)

blue = colors.HexColor('#17354b')
styles = {
    'title': ParagraphStyle('title', fontName='Lumina-Bold', fontSize=22, leading=28,
                            textColor=blue, alignment=TA_CENTER, spaceAfter=16),
    'h2': ParagraphStyle('h2', fontName='Lumina-Bold', fontSize=14, leading=19,
                         textColor=blue, spaceBefore=16, spaceAfter=8,
                         keepWithNext=True),
    'h3': ParagraphStyle('h3', fontName='Lumina-Bold', fontSize=11.5, leading=16,
                         textColor=colors.HexColor('#245673'), spaceBefore=11,
                         spaceAfter=6, keepWithNext=True),
    'body': ParagraphStyle('body', fontName='Lumina', fontSize=10.2, leading=14.4,
                           textColor=colors.HexColor('#172b39'), spaceAfter=9,
                           splitLongWords=1),
    'list': ParagraphStyle('list', fontName='Lumina', fontSize=10.2, leading=14.4,
                           textColor=colors.HexColor('#172b39'), leftIndent=18,
                           firstLineIndent=-14, spaceAfter=6, splitLongWords=1),
    'cell': ParagraphStyle('cell', fontName='Lumina', fontSize=8.4, leading=11.6,
                           textColor=colors.HexColor('#172b39'), splitLongWords=1),
    'cellhead': ParagraphStyle('cellhead', fontName='Lumina-Bold', fontSize=8.5,
                               leading=11.7, textColor=blue, splitLongWords=1),
    'figure': ParagraphStyle('figure', fontName='Lumina-Bold', fontSize=13,
                             leading=17, textColor=blue, spaceAfter=7),
    'warning': ParagraphStyle('warning', fontName='Lumina-Bold', fontSize=10.5,
                              leading=15, textColor=colors.HexColor('#8a2d1f'),
                              spaceAfter=7),
}

TOKEN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)|\*\*(.+?)\*\*|`([^`]+)`')
IMAGE = re.compile(r'^!\[([^\]]+)\]\(([^)]+)\)$')


def inline(source):
    result = []
    cursor = 0
    for match in TOKEN.finditer(source):
        result.append(html.escape(source[cursor:match.start()]))
        if match.group(1) is not None:
            label = html.escape(match.group(1))
            target = html.escape(match.group(2), quote=True)
            if target.startswith('https://'):
                result.append(f'<link href="{target}" color="#135a87"><u>{label}</u></link>')
            else:
                result.append(f'<font color="#135a87"><u>{label}</u></font>')
        elif match.group(3) is not None:
            result.append('<b>' + html.escape(match.group(3)) + '</b>')
        else:
            result.append('<font size="9">' + html.escape(match.group(4)) + '</font>')
        cursor = match.end()
    result.append(html.escape(source[cursor:]))
    return ''.join(result)


def table_widths(headers):
    n = len(headers)
    if n == 5:
        factors = [.17, .25, .11, .25, .22]
    elif n == 4 and 'Prioridade' in headers[0]:
        factors = [.08, .35, .31, .26]
    elif n == 4:
        factors = [.16, .30, .18, .36]
    elif n == 3 and 'Achado' in headers[0]:
        factors = [.24, .46, .30]
    elif n == 3:
        factors = [.23, .33, .44]
    elif n == 2:
        factors = [.38, .62]
    else:
        factors = [1 / n] * n
    return [WIDTH * value for value in factors]


def make_table(lines):
    rows = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if all(re.fullmatch(r':?-{3,}:?', cell or '') for cell in cells):
            continue
        rows.append(cells)
    count = len(rows[0])
    if any(len(row) != count for row in rows):
        raise ValueError('Tabela com número desigual de colunas')
    contents = [[Paragraph(inline(cell), styles['cellhead' if row_index == 0 else 'cell'])
                 for cell in row] for row_index, row in enumerate(rows)]
    table = LongTable(contents, colWidths=table_widths(rows[0]), repeatRows=1,
                      splitByRow=1)
    rules = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e7f0f5')),
        ('LINEBELOW', (0, 0), (-1, 0), .7, colors.HexColor('#8ba9ba')),
        ('INNERGRID', (0, 1), (-1, -1), .3, colors.HexColor('#cad8e2')),
        ('BOX', (0, 0), (-1, -1), .5, colors.HexColor('#a5bdca')),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]
    for row_index in range(2, len(contents), 2):
        rules.append(('BACKGROUND', (0, row_index), (-1, row_index), colors.HexColor('#f7fafc')))
    table.setStyle(TableStyle(rules))
    return table


def add_figure(story, caption, target):
    path = (BASE / target).resolve()
    if not path.is_file() or BASE not in path.parents:
        raise FileNotFoundError(path)
    number = re.search(r'S08-(\d+)', caption)
    figure_number = int(number.group(1)) if number else None
    story.append(PageBreak())
    story.append(Paragraph(inline(caption), styles['figure']))
    warning = ('FIGURA HISTÓRICA v0.2 — planejamento, sem prova de execução. '
               'A especificação v0.4 prevalece em caso de divergência.')
    if figure_number == 5:
        warning = ('FIGURA 5 DESATUALIZADA — não usar valor recebido e forma de pagamento '
                   'como campos novos da v0.4. Pagamento externo é confirmado pela recepção.')
    story.append(Paragraph(html.escape(warning), styles['warning']))
    with PILImage.open(path) as picture:
        width, height = picture.size
    factor = min((WIDTH - 8) / width, (HEIGHT - 95) / height)
    image = PDFImage(str(path), width=width * factor, height=height * factor)
    image.hAlign = 'CENTER'
    story.append(image)


def footer(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#a9becb'))
    canvas.setLineWidth(.5)
    canvas.line(LEFT, 33, PAGE_W - RIGHT, 33)
    canvas.setFont('Lumina', 8)
    canvas.setFillColor(colors.HexColor('#526778'))
    canvas.drawString(LEFT, 20, 'Lumina Odonto · Sprint 08 · parcial · 02/11/2026 · sem aceite integral')
    canvas.drawRightString(PAGE_W - RIGHT, 20, f'Página {document.page}')
    canvas.restoreState()


lines = SOURCE.read_text(encoding='utf-8').splitlines()
story = []
pending_caption = None
i = 0
while i < len(lines):
    line = lines[i]
    if not line.strip():
        i += 1
        continue
    if line.startswith('**Figura S08-'):
        pending_caption = line
        i += 1
        continue
    match = IMAGE.match(line)
    if match:
        add_figure(story, pending_caption or match.group(1), match.group(2))
        pending_caption = None
        i += 1
        continue
    if line.startswith('|'):
        group = []
        while i < len(lines) and lines[i].startswith('|'):
            group.append(lines[i])
            i += 1
        story.extend((make_table(group), Spacer(1, 10)))
        continue
    if line.startswith('# '):
        story.extend((Spacer(1, 35), Paragraph(inline(line[2:]), styles['title'])))
        i += 1
        continue
    if line.startswith('## '):
        story.append(Paragraph(inline(line[3:]), styles['h2']))
        i += 1
        continue
    if line.startswith('### '):
        story.append(Paragraph(inline(line[4:]), styles['h3']))
        i += 1
        continue
    list_match = re.match(r'^(\d+\. |- )(.*)$', line)
    if list_match:
        marker = '• ' if list_match.group(1) == '- ' else list_match.group(1)
        story.append(Paragraph(html.escape(marker) + inline(list_match.group(2)), styles['list']))
        i += 1
        continue
    paragraph = []
    while i < len(lines):
        line = lines[i]
        if (not line.strip() or line.startswith(('# ', '## ', '### ', '|', '!['))
                or line.startswith('**Figura S08-')
                or re.match(r'^(\d+\. |- )', line)):
            break
        paragraph.append(inline(line.strip()) + ('<br/>' if line.endswith('  ') else ' '))
        i += 1
    story.append(Paragraph(''.join(paragraph).strip(), styles['body']))

doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUTPUT)
print('bytes', OUTPUT.stat().st_size)
