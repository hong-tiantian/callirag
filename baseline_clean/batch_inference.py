"""
FontDiffuser baseline inference（批量推理脚本）
用途：
- 该脚本用于批量执行 FontDiffuser 推理（style × content），用于 baseline 对比。
- 在本项目中，它用于验证我在 idea 中提出的检索增强思路（retrieval/RAG）是否相比原始 FontDiffuser baseline 有提升。
说明：
- 只加载一次模型，然后循环不同的 (style_image, content_image) 组合，避免每张图重复起进程。
- 支持断点续跑：若输出目录已存在 out_with_cs.jpg，可自动跳过。
运行方式（示例）：
  python /d/htt/baseline_clean/batch_inference.py
"""

import glob
import os
import sys

# ---------- 配置 ----------
ROOT = os.path.abspath(os.path.dirname(__file__))
# wxz 用例：content 与 retrieval_data_prepare/cases/gt 编号一致；style 为 cases 下的 style_wxz0322.jpg
CONTENT_DIR = os.path.join(ROOT, "retrieval_data_prepare", "cases", "content")
STYLE_DIR = os.path.join(ROOT, "retrieval_data_prepare", "cases")
# 只匹配该风格图，避免 cases 根目录将来出现其它 jpg 时被误用
STYLE_GLOB = "style_wxz0322*.jpg"
OUTPUT_BASE = os.path.join(ROOT, "output", "baseline")
CKPT_DIR = os.path.join(ROOT, "FontDiffuser", "ckpt")
FONTDIFFUSER_ROOT = os.path.join(ROOT, "FontDiffuser")

# 与 FontDiffuser/utils.py 中 save_image_with_content_style 一致：有该文件视为本轮已成功出图
OUTPUT_MARKER = "out_with_cs.jpg"
# 为 True 时：若对应 save_dir 下已有 OUTPUT_MARKER，则不再推理（断点续跑、避免重复覆盖）
SKIP_IF_OUTPUT_EXISTS = True


def _output_done(save_dir):
    return os.path.isfile(os.path.join(save_dir, OUTPUT_MARKER))


def main():
    content_images = sorted(
        f for f in os.listdir(CONTENT_DIR) if f.lower().endswith(".jpg")
    )
    style_images = sorted(
        os.path.basename(p) for p in glob.glob(os.path.join(STYLE_DIR, STYLE_GLOB))
    )
    if not style_images:
        print(f"未在 {STYLE_DIR} 找到匹配 {STYLE_GLOB} 的文件")
        return
    if not content_images:
        print(f"未在 CONTENT_DIR 找到 jpg: {CONTENT_DIR}")
        return

    total = len(style_images) * len(content_images)
    already = 0
    for sf in style_images:
        sn = os.path.splitext(sf)[0]
        for cf in content_images:
            cn = os.path.splitext(cf)[0]
            if _output_done(os.path.join(OUTPUT_BASE, sn, cn)):
                already += 1

    print(
        f"计划共 {total} 对；磁盘上已有 {already} 张 {OUTPUT_MARKER}；"
        f"待跑约 {total - already} 对。"
        + ("" if SKIP_IF_OUTPUT_EXISTS else "（SKIP_IF_OUTPUT_EXISTS=False，将全部重跑）")
    )
    if SKIP_IF_OUTPUT_EXISTS and already >= total:
        print("全部已完成，未加载模型，直接退出。")
        return

    done = 0  # 已尝试的序号（含跳过）
    ran = 0  # 实际推理次数

    argv_bak = sys.argv
    sys.path.insert(0, FONTDIFFUSER_ROOT)
    os.chdir(FONTDIFFUSER_ROOT)
    try:
        sys.argv = [
            os.path.join(FONTDIFFUSER_ROOT, "sample.py"),
            f"--ckpt_dir={CKPT_DIR}",
            "--save_image",
            "--device=cuda:0",
            "--algorithm_type=dpmsolver++",
            "--guidance_type=classifier-free",
            "--guidance_scale=7.5",
            "--num_inference_steps=20",
            "--method=multistep",
            # 占位，循环里会覆盖
            "--content_image_path=__dummy__.jpg",
            "--style_image_path=__dummy__.jpg",
            "--save_image_dir=__dummy_out__",
        ]
        from sample import arg_parse, load_fontdiffuer_pipeline, sampling

        args = arg_parse()
        print("正在加载模型（仅一次）…")
        pipe = load_fontdiffuer_pipeline(args=args)
        print(f"开始批量: {len(style_images)} 个 style × {len(content_images)} 个 content = {total} 张\n")

        for style_file in style_images:
            style_name = os.path.splitext(style_file)[0]
            for content_file in content_images:
                content_name = os.path.splitext(content_file)[0]
                save_dir = os.path.join(OUTPUT_BASE, style_name, content_name)
                os.makedirs(save_dir, exist_ok=True)

                done += 1
                if SKIP_IF_OUTPUT_EXISTS and _output_done(save_dir):
                    print(
                        f"[{done}/{total}] 跳过（已有 {OUTPUT_MARKER}）"
                        f" style={style_name}, content={content_name}"
                    )
                    continue

                args.content_image_path = os.path.join(CONTENT_DIR, content_file)
                args.style_image_path = os.path.join(STYLE_DIR, style_file)
                args.save_image_dir = save_dir

                ran += 1
                print(
                    f"[{done}/{total} | 本次推理第 {ran} 张] "
                    f"style={style_name}, content={content_name}"
                )
                sampling(args=args, pipe=pipe)
    finally:
        sys.argv = argv_bak

    print(f"All done（本进程实际推理 {ran} 张，其余为跳过或此前已有）。")


if __name__ == "__main__":
    main()
