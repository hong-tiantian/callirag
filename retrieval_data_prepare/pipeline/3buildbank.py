import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
BANK_DIR = BASE_DIR / 'bank'
# 项目根目录（与 data/ 同级），path 存相对此目录的路径
REPO_ROOT = BASE_DIR.parent

ocr = json.load(open(BANK_DIR / 'wxz_ocr.json', encoding='utf8'))
decomp = json.load(open(BANK_DIR / 'decomp.json', encoding='utf8'))

bank = []
skipped = 0
missing_files = 0
invalid_ocr = 0
image_roots = {
    'train': REPO_ROOT / 'data' / 'image' / 'train' / 'wxz',
    'test': REPO_ROOT / 'data' / 'image' / 'test' / 'wxz',
}


def to_posix_abs(p: Path) -> str:
    s = p.resolve().as_posix()
    # Windows: D:/htt/... -> /d/htt/...
    if len(s) >= 3 and s[1] == ':' and s[2] == '/':
        return f"/{s[0].lower()}{s[2:]}"
    return s


def find_wxz_image(fname: str) -> tuple[str | None, Path | None]:
    for split, root in image_roots.items():
        candidate = root / fname
        if candidate.exists():
            return split, candidate
    return None, None


for fname, rec in ocr.items():
    char = rec.get('char')
    conf = rec.get('conf')
    if not char:
        invalid_ocr += 1
        continue
    if char not in decomp:
        skipped += 1
        continue
    split, real_path = find_wxz_image(fname)
    if real_path is None:
        missing_files += 1
        continue

    d = decomp[char]
    top_level = list(d.get('top_level_components', []) or [])
    leaf_components = list(d.get('leaf_components', []) or [])

    bank.append({
        'bank_id': f'wxz_{Path(fname).stem}',
        'wxz_path': to_posix_abs(real_path),
        'split': split,
        'character': char,
        'ocr_conf': conf,
        'content_id': d.get('id'),
        'content_path': d.get('path'),
        'freq': d.get('freq', None),
        'script': d.get('script', 'common'),
        'ids': d.get('ids', ''),
        'layout': d.get('layout', ''),
        'stroke_count': d.get('stroke_count'),
        'top_level_components': top_level,
        'leaf_components': leaf_components,
        'has_unknown': bool(d.get('has_unknown', False)),
        'retrieval_top_level': top_level,
        'retrieval_components': leaf_components,
    })

json.dump(bank, open(BANK_DIR / 'wxz_bank.json','w',encoding='utf8'),
          ensure_ascii=False, indent=2)
print(
    f'bank size: {len(bank)}, skipped (no decomp): {skipped}, '
    f'missing image: {missing_files}, invalid ocr: {invalid_ocr}'
)