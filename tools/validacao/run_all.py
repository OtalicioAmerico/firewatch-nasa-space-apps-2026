"""Executa a auditoria da Missao 01 de ponta a ponta e grava as saidas em <work-dir>/saidas/.

Uso:  python -I tools/validacao/run_all.py --data-dir <dir dos dados NASA> [--work-dir <dir>]
"""
import os, sys, subprocess, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import R, SCR  # noqa: E402  (valida --data-dir)

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = ['01_inventario', '02_cache_brasil', '03_cobertura_passagens', '04_reconciliacao_banco', '05_delta_t',
         '06_correspondencia', '07_celula_uf_variacao', '08_amostras_sazonalidade', '09_ranking_uf',
         '10_tocantins_municipios', '11_tocantins_resultados', '12_controle_viirs']
out = os.path.join(SCR, 'saidas')
os.makedirs(out, exist_ok=True)
for s in STEPS:
    t0 = time.time()
    r = subprocess.run([sys.executable, '-I', os.path.join(HERE, s + '.py'), '--data-dir', R, '--work-dir', SCR],
                       capture_output=True, text=True, encoding='utf-8')
    open(os.path.join(out, s + '.txt'), 'w', encoding='utf-8').write(r.stdout + (('\n[stderr]\n' + r.stderr) if r.stderr else ''))
    print(f'{s}: exit={r.returncode} {time.time() - t0:.0f}s')
    if r.returncode:
        sys.exit(r.stderr[-800:])
print('saidas em', out)
