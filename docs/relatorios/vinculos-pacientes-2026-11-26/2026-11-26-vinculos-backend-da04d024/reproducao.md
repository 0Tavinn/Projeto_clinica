# Reprodução isolada para revisão independente

Fonte: /home/paulinho/Work/Projeto_clinica/lumina_odonto.
Referência Git: 67068ac969cb7b34396b5d94e4ee09a7001ef8b4 + alterações locais identificadas.
Execute no Ubuntu WSL com Docker disponível. O runner cria banco/volume/rede/imagem exclusivos,
sem portas publicadas, verifica rótulos antes da limpeza e executa o CMD original da imagem.
Não usa Compose diário. O schema só é provisionado no banco novo lumina_links_scratch.
As credenciais constantes do runner são exclusivamente fictícias desse ensaio.

Confira os hashes antes de ensaiar; divergência exige nova identificação da candidata.
Use nova pasta para não sobrescrever estas evidências:

```bash
python3 - <<'CHECK'
from pathlib import Path
import hashlib, json, shutil, subprocess, uuid
root = Path('/home/paulinho/Work/Projeto_clinica')
evidence = Path('/home/paulinho/Work/lumina-qa-evidence/2026-11-26-vinculos-backend-da04d024')
assert subprocess.check_output(['git', '-C', str(root), 'branch', '--show-current'], text=True).strip() == 'fix/prontuario-correcoes-qa'
assert subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip() == '67068ac969cb7b34396b5d94e4ee09a7001ef8b4'
for name, expected in json.loads((evidence / 'final-file-hashes.json').read_text()).items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
out = evidence.parent / ('reteste-vinculos-' + uuid.uuid4().hex[:12])
out.mkdir(exist_ok=False)
for name in ('verify_candidate.py', 'probe_access.py'):
    shutil.copy2(evidence / name, out / name)
(out / 'paths.json').write_text(json.dumps({'root': str(root), 'source': str(root / 'lumina_odonto'), 'output': str(out)}, indent=2))
print('Evidências do novo ensaio:', out, flush=True)
subprocess.run(['python3', str(out / 'verify_candidate.py')], check=True)
CHECK
```

Internamente, a imagem roda python -m pytest -q --disable-warnings --tb=short;
o probe usa HTTP real contra Uvicorn e conexões PostgreSQL independentes.
O runner requer Docker e imagem postgres:16; dependências da imagem podem mudar
por versões não fixadas. Compare versions.json e a identidade da nova imagem,
sem presumir a mesma versão de bibliotecas ou o mesmo resultado.

As sondagens de espera consultam pg_stat_activity e usam change_link de produção
na transação que detém o bloqueio; outras mutações administrativas são exercitadas
por HTTP. Não se trata de duas chamadas HTTP simultâneas de revogação.
