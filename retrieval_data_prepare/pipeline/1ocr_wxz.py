from paddleocr import PaddleOCR
import os, json, glob
from pathlib import Path
from tqdm import tqdm

ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    lang='ch',
    enable_mkldnn=False,
)
results = {}
PROJECT_ROOT = Path(__file__).resolve().parents[2]
IMAGE_BASE = PROJECT_ROOT / "data" / "image"

image_roots = [
    str(IMAGE_BASE / "train" / "wxz"),
    str(IMAGE_BASE / "test" / "wxz"),
]

image_paths = []
for root in image_roots:
    image_paths.extend(glob.glob(os.path.join(root, '*.jpg')))

for p in tqdm(sorted(image_paths)):
    r = ocr.predict(p)
    if not r:
        continue
    res = r[0]
    texts = res.get('rec_texts', []) or []
    scores = res.get('rec_scores', []) or []
    if len(texts) == 0:
        continue
    text, conf = texts[0], float(scores[0])
    if len(text) == 1 and conf > 0.85:
        results[os.path.basename(p)] = {'char': text, 'conf': conf}

json.dump(results, open('retrieval_data_prepare/bank/wxz_ocr.json', 'w', encoding='utf8'), ensure_ascii=False)
