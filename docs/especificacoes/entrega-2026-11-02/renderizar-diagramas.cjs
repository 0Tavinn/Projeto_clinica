// Renderiza os arquivos Mermaid desta entrega no navegador local, sem serviço externo.
// Dependências: mermaid 12.2.0, playwright 1.62.1 e um Chromium/Edge instalado.
const fs = require('node:fs');
const path = require('node:path');

const playwright = require(process.env.LUMINA_PLAYWRIGHT_MODULE || 'playwright');
const bundlePath = process.env.LUMINA_MERMAID_BUNDLE ||
  path.join(__dirname, 'node_modules', 'mermaid', 'dist', 'mermaid.min.js');
const browserPath = process.env.LUMINA_BROWSER_PATH;
const base = __dirname;
const sources = path.join(base, 'diagramas');
const output = path.join(base, 'diagramas-renderizados');
fs.mkdirSync(output, { recursive: true });
const bundle = fs.readFileSync(bundlePath, 'utf8');

async function run() {
  const browser = await playwright.chromium.launch({
    headless: true,
    ...(browserPath ? { executablePath: browserPath } : {}),
  });
  const page = await browser.newPage({ deviceScaleFactor: 2 });
  const manifest = [];
  try {
    for (const filename of fs.readdirSync(sources).filter(x => x.endsWith('.mmd')).sort()) {
      const basename = filename.slice(0, -4);
      const source = fs.readFileSync(path.join(sources, filename), 'utf8');
      await page.setContent('<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0;background:white"><div id="diagram" style="display:inline-block;padding:20px;background:white"></div></body></html>');
      await page.addScriptTag({ content: bundle });
      const result = await page.evaluate(async ({ source, basename }) => {
        mermaid.initialize({
          startOnLoad: false,
          securityLevel: 'strict',
          theme: 'base',
          themeVariables: {
            fontFamily: 'Arial, sans-serif', fontSize: '17px',
            primaryColor: '#eaf3f8', primaryTextColor: '#17354b',
            primaryBorderColor: '#7193a8', lineColor: '#496b80',
            secondaryColor: '#f5f9fb', tertiaryColor: '#ffffff',
          },
          flowchart: { htmlLabels: true, nodeSpacing: 30, rankSpacing: 42, curve: 'linear' },
        });
        await mermaid.parse(source);
        const { svg } = await mermaid.render('lumina_' + basename.replace(/[^a-z0-9]/gi, '_'), source);
        const host = document.querySelector('#diagram');
        host.innerHTML = svg;
        const element = host.querySelector('svg');
        const box = element.viewBox.baseVal;
        const width = Math.ceil(box.width);
        const height = Math.ceil(box.height);
        element.setAttribute('width', String(width));
        element.setAttribute('height', String(height));
        element.style.maxWidth = 'none';
        const svgRect = element.getBoundingClientRect();
        const nodes = [...element.querySelectorAll('.node')].map(node => {
          const rect = node.getBoundingClientRect();
          return { top: Math.round(rect.top - svgRect.top), bottom: Math.round(rect.bottom - svgRect.top) };
        });
        return { width, height, nodes, svg: element.outerHTML };
      }, { source, basename });
      await page.setViewportSize({
        width: Math.max(900, result.width + 48),
        height: Math.max(600, result.height + 48),
      });
      fs.writeFileSync(path.join(output, basename + '.svg'), result.svg, 'utf8');
      await page.locator('#diagram').screenshot({
        path: path.join(output, basename + '.png'), timeout: 60000,
      });
      manifest.push({ source: `diagramas/${filename}`,
        svg: `diagramas-renderizados/${basename}.svg`,
        png: `diagramas-renderizados/${basename}.png`,
        width: result.width, height: result.height, nodes: result.nodes });
      process.stdout.write(`${filename}: ${result.width} × ${result.height}\n`);
    }
    fs.writeFileSync(path.join(output, 'manifesto.json'), JSON.stringify(manifest, null, 2) + '\n');
  } finally {
    await browser.close();
  }
}

run().catch(error => { console.error(error); process.exitCode = 1; });
