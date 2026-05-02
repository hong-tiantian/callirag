from configs.fontdiffuser import get_parser
from src.build import build_unet

def make_args():
    parser = get_parser()
    parser.add_argument('--ckpt_dir', type=str, default=None)
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--controlnet', type=bool, default=False)
    parser.add_argument('--character_input', action='store_true')
    parser.add_argument('--content_character', type=str, default=None)
    parser.add_argument('--content_image_path', type=str, default=None)
    parser.add_argument('--style_image_path', type=str, default=None)
    parser.add_argument('--save_image', action='store_true')
    parser.add_argument('--save_image_dir', type=str, default=None)
    parser.add_argument('--device', type=str, default='cuda:0')
    parser.add_argument('--ttf_path', type=str, default='ttf/KaiXinSongA.ttf')
    args = parser.parse_args([])
    style_image_size = args.style_image_size
    content_image_size = args.content_image_size
    args.style_image_size = (style_image_size, style_image_size)
    args.content_image_size = (content_image_size, content_image_size)
    return args

if __name__ == '__main__':
    args = make_args()
    u = build_unet(args=args)
    print(type(u))
    print('OK')
