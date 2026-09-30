#!/usr/bin/env python3
"""
Revisión de cumplimiento del repositorio (corre en cada push y se puede correr a mano):

    python tools/revisar_cumplimiento.py

Falla (código 1) si encuentra:
  1. Archivos sensibles versionados: .env, claves privadas, .claude/settings.local.json.
  2. Secretos con formato conocido (claves de AWS, GitHub, Anthropic, OpenAI, Google, Slack, llaves privadas).
  3. Carpetas de datos de terceros (`raw/<fuente>/`) que no estén registradas en FUENTES.md.
  4. Skills en .claude/skills/ que no estén registradas en FUENTES.md, o de terceros sin su archivo LICENSE.
  5. Scripts que descargan de internet sin usar descarga_responsable (User-Agent propio, robots.txt, pausa).
  6. Copias de descarga_responsable.py que no sean idénticas entre sí (nadie puede relajar las reglas en una copia).

Por qué: ver la sección "Cumplimiento legal" de CLAUDE.md y FUENTES.md.
"""
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FUENTES = RAIZ / 'FUENTES.md'

SENSIBLES = [
    re.compile(r'(^|/)\.env(\..+)?$'),
    re.compile(r'\.(pem|key|p12|pfx)$'),
    re.compile(r'(^|/)id_(rsa|ed25519|ecdsa)(\.pub)?$'),
    re.compile(r'(^|/)\.claude/settings\.local\.json$'),
]
SECRETOS = {
    'clave AWS': re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
    'token GitHub': re.compile(r'\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b|\bgithub_pat_[A-Za-z0-9_]{60,}'),
    'clave Anthropic': re.compile(r'\bsk-ant-[A-Za-z0-9_-]{20,}'),
    'clave OpenAI': re.compile(r'\bsk-(proj-)?[A-Za-z0-9]{32,}\b'),
    'clave Google': re.compile(r'\bAIza[0-9A-Za-z_-]{35}\b'),
    'token Slack': re.compile(r'\bxox[abprs]-[A-Za-z0-9-]{10,}'),
    'llave privada': re.compile(r'-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
}
DESCARGA = re.compile(r'\brequests\.(get|post|Session|request)\b|\burlopen\(|\burllib\.request\b|\bhttpx\.')
LICENCIAS = ('Apache', 'MIT', 'GPL', 'BSD', 'MPL', 'licencia')


def versionados():
    out = subprocess.run(['git', 'ls-files', '-z'], cwd=RAIZ, capture_output=True, check=True).stdout
    return [p for p in out.decode('utf-8', 'replace').split('\0') if p]


def es_texto(ruta):
    try:
        return b'\0' not in (RAIZ / ruta).read_bytes()[:4096]
    except OSError:
        return False


def main():
    errores = []
    archivos = versionados()
    fuentes = FUENTES.read_text(encoding='utf-8') if FUENTES.exists() else ''
    if not fuentes:
        errores.append('Falta FUENTES.md en la raíz del repositorio.')

    for f in archivos:
        if any(p.search(f) for p in SENSIBLES):
            errores.append(f'Archivo sensible versionado: {f} (sacarlo con git rm --cached y agregarlo a .gitignore)')

    for f in archivos:
        if f.endswith('revisar_cumplimiento.py') or not es_texto(f):
            continue
        texto = (RAIZ / f).read_text(encoding='utf-8', errors='replace')
        for nombre, patron in SECRETOS.items():
            m = patron.search(texto)
            if m:
                linea = texto.count('\n', 0, m.start()) + 1
                errores.append(f'Posible {nombre} en {f}:{linea} (revocarla y quitarla del historial)')

    carpetas_raw = set()
    for f in archivos:
        partes = f.split('/')
        if 'raw' in partes[:-2]:
            carpetas_raw.add('/'.join(partes[:partes.index('raw') + 2]))
    carpetas_raw = sorted(carpetas_raw)
    for c in carpetas_raw:
        corto = 'raw/' + c.split('raw/', 1)[1]
        if corto not in fuentes and c not in fuentes:
            errores.append(f'Fuente sin registrar: {c}/ no aparece en FUENTES.md (agregar origen, fecha y condición de uso)')

    skills = sorted({f.split('/')[2] for f in archivos if f.startswith('.claude/skills/') and f.count('/') >= 3})
    for s in skills:
        ruta = f'.claude/skills/{s}/'
        filas = [l for l in fuentes.splitlines() if ruta in l or f'skill `{s}`' in l or f'`{s}`' in l]
        if not filas:
            errores.append(f'Skill sin registrar en FUENTES.md: {ruta} (indicar si es propia o de terceros y su licencia)')
        elif any(any(x in l for x in LICENCIAS) and 'propia' not in l.lower() for l in filas) \
                and not any(f.startswith(ruta + 'LICENSE') for f in archivos):
            errores.append(f'Skill de terceros sin LICENSE: {ruta} (copiar LICENSE y NOTICE del proyecto original)')

    for f in archivos:
        if not f.endswith('.py') or f.startswith('.claude/skills/') or f.endswith('descarga_responsable.py') \
                or f.endswith('revisar_cumplimiento.py'):
            continue
        texto = (RAIZ / f).read_text(encoding='utf-8', errors='replace')
        if DESCARGA.search(texto) and 'descarga_responsable' not in texto:
            errores.append(f'Descarga sin reglas en {f}: usar sesion()/permitido()/pausa() de descarga_responsable')

    copias = [f for f in archivos if f.endswith('descarga_responsable.py')]
    if len({(RAIZ / f).read_bytes() for f in copias}) > 1:
        errores.append('Las copias de descarga_responsable.py no son idénticas: ' + ', '.join(copias)
                       + ' (actualizar todas a la misma versión)')

    if errores:
        print('REVISIÓN DE CUMPLIMIENTO: FALLA\n')
        print('\n'.join(f'- {e}' for e in errores))
        return 1
    print(f'REVISIÓN DE CUMPLIMIENTO: OK ({len(archivos)} archivos, {len(carpetas_raw)} carpetas de fuentes, '
          f'{len(skills)} skills)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
