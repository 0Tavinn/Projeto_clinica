"""Monta o PDF de alinhamento a partir do Markdown e dos PNGs Mermaid locais.

Requer Python, ReportLab e Pillow. Não executa a aplicação clínica nem usa rede.
"""

from io import BytesIO
from pathlib import Path
import html
import json
import re

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A3
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, LongTable, TableStyle,
    Image as PDFImage, PageBreak,
)

BASE = Path(__file__).resolve().parent
MARKDOWN = BASE / 'fluxo-atendimento-mvp-v0.4.md'
OUTPUT = BASE / 'Lumina-Odonto-Fluxo-atendimento-MVP-v0.4.pdf'
MANIFEST = {Path(item['svg']).stem: item for item in json.loads(
    (BASE / 'diagramas-renderizados/manifesto.json').read_text(encoding='utf-8'))}

font_candidates = [
    (Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
     Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')),
    (Path('C:/Windows/Fonts/arial.ttf'), Path('C:/Windows/Fonts/arialbd.ttf')),
]
regular, bold = next(((a, b) for a, b in font_candidates if a.exists() and b.exists()), (None, None))
if regular is None:
    raise RuntimeError('Instale DejaVu Sans ou disponibilize Arial regular e bold.')
pdfmetrics.registerFont(TTFont('Lumina', str(regular)))
pdfmetrics.registerFont(TTFont('Lumina-Bold', str(bold)))
pdfmetrics.registerFontFamily('Lumina', normal='Lumina', bold='Lumina-Bold', italic='Lumina', boldItalic='Lumina-Bold')

PAGE_W, PAGE_H = A3
LEFT = RIGHT = 45
TOP = 52
BOTTOM = 48
WIDTH = PAGE_W - LEFT - RIGHT
doc = SimpleDocTemplate(str(OUTPUT), pagesize=A3,
    leftMargin=LEFT, rightMargin=RIGHT, topMargin=TOP, bottomMargin=BOTTOM,
    title='Lumina Odonto — Fluxo de atendimento do MVP — versão 0.4',
    author='Lumina Odonto — documento de alinhamento a partir das decisões de Paulo Sérgio',
    subject='Especificação funcional, diagramas Mermaid e pendências; sem aceite de implementação')

ink = colors.HexColor('#17354b')
styles = {
    'title': ParagraphStyle('title', fontName='Lumina-Bold', fontSize=21, leading=27,
                            textColor=ink, alignment=TA_CENTER, spaceAfter=18),
    'h2': ParagraphStyle('h2', fontName='Lumina-Bold', fontSize=14, leading=19,
                         textColor=ink, spaceBefore=16, spaceAfter=9, keepWithNext=True),
    'h3': ParagraphStyle('h3', fontName='Lumina-Bold', fontSize=11.5, leading=16,
                         textColor=colors.HexColor('#255575'), spaceBefore=11,
                         spaceAfter=6, keepWithNext=True),
    'body': ParagraphStyle('body', fontName='Lumina', fontSize=10, leading=14.5,
                           textColor=colors.HexColor('#1c2933'), spaceAfter=9,
                           allowWidows=0, allowOrphans=0),
    'list': ParagraphStyle('list', fontName='Lumina', fontSize=10, leading=14.5,
                           textColor=colors.HexColor('#1c2933'), leftIndent=20,
                           firstLineIndent=-14, spaceAfter=5),
    'cell': ParagraphStyle('cell', fontName='Lumina', fontSize=8.4, leading=11.7,
                           textColor=colors.HexColor('#1c2933'), splitLongWords=1),
    'headcell': ParagraphStyle('headcell', fontName='Lumina-Bold', fontSize=8.5,
                               leading=11.8, textColor=ink, splitLongWords=1),
    'figure': ParagraphStyle('figure', fontName='Lumina-Bold', fontSize=12,
                             leading=16, textColor=ink, spaceAfter=6),
    'source': ParagraphStyle('source', fontName='Lumina', fontSize=8.2,
                             leading=11, textColor=colors.HexColor('#526778'), spaceAfter=9),
}

TOKEN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)|\*\*(.+?)\*\*|`([^`]+)`')
IMAGE = re.compile(r'^!\[([^\]]+)\]\(([^)]+)\)$')


def inline(source):
    out = []
    cursor = 0
    for match in TOKEN.finditer(source):
        out.append(html.escape(source[cursor:match.start()]))
        if match.group(1) is not None:
            out.append('<font color="#165d8b"><u>' + html.escape(match.group(1)) + '</u></font>')
        elif match.group(3) is not None:
            out.append('<b>' + html.escape(match.group(3)) + '</b>')
        else:
            out.append('<font size="9">' + html.escape(match.group(4)) + '</font>')
        cursor = match.end()
    out.append(html.escape(source[cursor:]))
    return ''.join(out)


def widths(headers):
    n = len(headers)
    joined = ' '.join(headers)
    if n == 3 and 'Responsabilidade no fluxo' in joined:
        factors = [.17, .40, .43]
    elif n == 3 and 'Etapa' in headers[0]:
        factors = [.18, .42, .40]
    elif n == 3 and 'Parte' in headers[0]:
        factors = [.16, .40, .44]
    elif n == 3 and 'Cenário' in headers[0]:
        factors = [.27, .50, .23]
    elif n == 3:
        factors = [.24, .39, .37]
    elif n == 2 and 'Classificação' in headers[0]:
        factors = [.28, .72]
    elif n == 2:
        factors = [.43, .57]
    else:
        factors = [1 / n] * n
    return [WIDTH * factor for factor in factors]


def make_table(lines):
    raw = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if all(re.fullmatch(r':?-{3,}:?', cell or '') for cell in cells):
            continue
        raw.append(cells)
    n = len(raw[0])
    if any(len(row) != n for row in raw):
        raise ValueError('Tabela Markdown com número desigual de colunas.')
    cells = [[Paragraph(inline(cell), styles['headcell' if i == 0 else 'cell'])
              for cell in row] for i, row in enumerate(raw)]
    table = LongTable(cells, colWidths=widths(raw[0]), repeatRows=1, splitByRow=1)
    formatting = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e7f0f5')),
        ('LINEBELOW', (0, 0), (-1, 0), .7, colors.HexColor('#8ba9ba')),
        ('INNERGRID', (0, 1), (-1, -1), .3, colors.HexColor('#c9d7e1')),
        ('BOX', (0, 0), (-1, -1), .5, colors.HexColor('#a5bdca')),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]
    for i in range(2, len(cells), 2):
        formatting.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f7fafc')))
    table.setStyle(TableStyle(formatting))
    return table


def segment_bounds(item, image):
    # As capturas têm 20 px CSS de margem; procurar cortes entre os nós.
    dpr = image.width / (item['width'] + 40)
    total = image.height / dpr
    blocked = [(node['top'] + 10, node['bottom'] + 30) for node in item['nodes']]
    start = 0
    pieces = []
    while start < total - 1:
        limit = min(total, start + 1400)
        if total - limit < 130:
            limit = total
        if limit < total:
            choices = [y for y in range(int(limit), int(max(start + 350, limit - 350)), -4)
                       if all(not (a <= y <= b) for a, b in blocked)]
            if choices:
                limit = choices[0]
        if limit <= start + 100:
            limit = min(total, start + 1400)
        pieces.append((start, limit))
        start = limit
    return dpr, pieces


buffers = []


def add_diagram(story, alt, target):
    name = Path(target).stem
    item = MANIFEST[name]
    image_path = BASE / item['png']
    with PILImage.open(image_path) as image:
        dpr, bounds = segment_bounds(item, image)
        factor = min(.70, WIDTH / (image.width / dpr))
        for number, (start, end) in enumerate(bounds, 1):
            story.append(PageBreak())
            title = alt + (f' — trecho {number} de {len(bounds)}' if len(bounds) > 1 else '')
            story.append(Paragraph(html.escape(title), styles['figure']))
            story.append(Paragraph(
                'Versão 0.4 · fonte Mermaid: diagramas/' + name + '.mmd · '
                'diagrama de alinhamento, sem prova de implementação.', styles['source']))
            top = max(0, round(start * dpr))
            bottom = min(image.height, round(end * dpr))
            section = image.crop((0, top, image.width, bottom))
            stream = BytesIO()
            section.save(stream, format='PNG')
            stream.seek(0)
            buffers.append(stream)
            figure = PDFImage(stream)
            figure.drawWidth = (image.width / dpr) * factor
            figure.drawHeight = ((bottom - top) / dpr) * factor
            figure.hAlign = 'CENTER'
            story.append(figure)


def footer(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#adbfca'))
    canvas.setLineWidth(.5)
    canvas.line(LEFT, 35, PAGE_W - RIGHT, 35)
    canvas.setFont('Lumina', 8)
    canvas.setFillColor(colors.HexColor('#526b7a'))
    canvas.drawString(LEFT, 22, 'Lumina Odonto · Fluxo de atendimento do MVP · v0.4 · 02/11/2026 · alinhamento')
    canvas.drawRightString(PAGE_W - RIGHT, 22, f'Página {document.page}')
    canvas.restoreState()


lines = MARKDOWN.read_text(encoding='utf-8').splitlines()
story = []
i = 0
while i < len(lines):
    line = lines[i]
    if not line.strip():
        i += 1
        continue
    image_match = IMAGE.match(line)
    if image_match:
        add_diagram(story, image_match.group(1), image_match.group(2))
        i += 1
        continue
    if line.startswith('|'):
        group = []
        while i < len(lines) and lines[i].startswith('|'):
            group.append(lines[i])
            i += 1
        story.extend((make_table(group), Spacer(1, 11)))
        continue
    if line.startswith('# '):
        story.extend((Spacer(1, 120), Paragraph(inline(line[2:]), styles['title'])))
        i += 1
        continue
    if line.startswith('## '):
        if line == '## Sumário':
            story.append(PageBreak())
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
                or re.match(r'^(\d+\. |- )', line)):
            break
        paragraph.append(inline(line.strip()) + ('<br/>' if line.endswith('  ') else ' '))
        i += 1
    story.append(Paragraph(''.join(paragraph).strip(), styles['body']))

doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUTPUT)
print(OUTPUT.stat().st_size)
