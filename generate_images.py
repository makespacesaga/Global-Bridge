"""
NPO Global Bridge — gpt-image-1 画像生成スクリプト
使い方:
  python generate_images.py              # インタラクティブメニュー
  python generate_images.py --preset hero
  python generate_images.py --all        # 全プリセットを一括生成
  python generate_images.py --prompt "カスタムプロンプト" --name myimage
"""

import os
import sys
import json
import base64
import argparse
import urllib.request
import urllib.error

# ── .env からAPIキー読み込み ────────────────────────────────────────────────
def load_api_key():
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if not os.path.exists(env_path):
        sys.exit(f"[ERROR] .env が見つかりません: {env_path}")
    with open(env_path, encoding='utf-8') as f:
        for line in f:
            if line.startswith('OpenAI_apikey='):
                return line.strip().split('=', 1)[1]
    sys.exit("[ERROR] OpenAI_apikey が .env に見つかりません")


# ── 画像生成プリセット ──────────────────────────────────────────────────────
PRESETS = {
    "hero": {
        "desc": "ヒーロー画像（横長）",
        "file": "hero.jpg",
        "size": "1536x1024",
        "quality": "high",
        "prompt": (
            "Wide cinematic photograph of diverse Japanese and international volunteers "
            "gathered outdoors in Saga Prefecture Japan, working together at a community event, "
            "warm golden hour sunlight through trees, genuine smiles, hopeful atmosphere, "
            "documentary style, shallow depth of field, high resolution"
        )
    },
    "hero_ariake": {
        "desc": "ヒーロー画像・有明海（横長）",
        "file": "hero_ariake.jpg",
        "size": "1536x1024",
        "quality": "high",
        "prompt": (
            "Breathtaking aerial photograph of Ariake Sea tidal flats at golden hour, "
            "Saga Prefecture Japan, vast mud flats reflecting orange sunset, "
            "traditional fishermen silhouettes, misty coastal mountains in background, "
            "cinematic landscape photography, ultra high quality"
        )
    },
    "program_education": {
        "desc": "事業：教育・人材育成",
        "file": "program_education.jpg",
        "size": "1536x1024",
        "quality": "high",
        "prompt": (
            "Warm documentary photograph inside a bright modern classroom in Asia, "
            "Japanese and international students studying together, teacher guiding a group, "
            "laptops and books, natural window light, hopeful and engaged expressions, "
            "authentic feel, high resolution"
        )
    },
    "program_international": {
        "desc": "事業：国際協力",
        "file": "program_international.jpg",
        "size": "1536x1024",
        "quality": "high",
        "prompt": (
            "Authentic documentary photograph of Japanese volunteers working with local community "
            "in Southeast Asia, building a school or community center together, "
            "people of different backgrounds collaborating, bright tropical daylight, "
            "impactful humanitarian moment, photojournalism style"
        )
    },
    "program_environment": {
        "desc": "事業：環境保全",
        "file": "program_environment.jpg",
        "size": "1536x1024",
        "quality": "high",
        "prompt": (
            "Beautiful photograph of Ariake Sea coastline in Saga Japan, "
            "volunteers doing coastal cleanup at low tide, blue sky, "
            "lush green hills in background, environmental conservation atmosphere, "
            "clean and inspiring, wide shot, professional photography"
        )
    },
    "program_children": {
        "desc": "事業：子ども・若者育成",
        "file": "program_children.jpg",
        "size": "1536x1024",
        "quality": "high",
        "prompt": (
            "Joyful documentary photograph of multicultural children playing sports together "
            "outdoors in Japan, mixed Japanese and international kids, bright colorful clothes, "
            "summer sunlight, genuine laughter, inclusive and vibrant scene, "
            "high resolution, warm tones"
        )
    },
    "program_peace": {
        "desc": "事業：平和・人権・参画",
        "file": "program_peace.jpg",
        "size": "1024x1536",
        "quality": "high",
        "prompt": (
            "Powerful documentary photograph of diverse group of people from different backgrounds "
            "standing together in unity, various ages and ethnicities, warm natural lighting, "
            "peaceful and determined expressions, shallow depth of field, "
            "square or portrait format, professional photography"
        )
    },
    "about_director": {
        "desc": "代表挨拶セクション背景",
        "file": "about_bg.jpg",
        "size": "1536x1024",
        "quality": "high",
        "prompt": (
            "Serene aerial photograph of Shiroishi town in Saga Prefecture Japan, "
            "green rice fields and Ariake Sea in distance, morning light, "
            "peaceful rural Japanese landscape, cinematic wide angle, "
            "representing local roots with global vision"
        )
    },
    "cta_bg": {
        "desc": "寄付CTAセクション背景",
        "file": "cta_bg.jpg",
        "size": "1536x1024",
        "quality": "high",
        "prompt": (
            "Inspiring wide photograph of many hands of different skin colors and ages "
            "gently overlapping in unity, warm soft bokeh background, "
            "golden hour light, shallow focus on hands, emotional and human, "
            "charity campaign photography style, horizontal format"
        )
    },
}


# ── API 呼び出し ───────────────────────────────────────────────────────────
def generate_image(api_key, prompt, size, quality, output_path):
    body = json.dumps({
        "model": "gpt-image-1",
        "prompt": prompt,
        "n": 1,
        "size": size,
        "quality": quality,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json; charset=utf-8",
        },
    )

    print(f"  → API 呼び出し中... ({size}, quality={quality})")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode()
        sys.exit(f"[ERROR] HTTP {e.code}: {detail}")

    b64 = result["data"][0].get("b64_json")
    if not b64:
        sys.exit(f"[ERROR] b64_json がレスポンスにありません: {result}")

    img_bytes = base64.b64decode(b64)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(img_bytes)

    size_kb = len(img_bytes) // 1024
    print(f"  [OK] 保存: {output_path}  ({size_kb} KB)")


# ── メイン ────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="NPO Global Bridge 画像生成")
    parser.add_argument("--preset", choices=list(PRESETS.keys()), help="プリセット名")
    parser.add_argument("--all", action="store_true", help="全プリセットを生成")
    parser.add_argument("--prompt", help="カスタムプロンプト")
    parser.add_argument("--name", default="custom", help="出力ファイル名（拡張子なし）")
    parser.add_argument("--size", default="1536x1024",
                        choices=["1024x1024", "1536x1024", "1024x1536"],
                        help="画像サイズ")
    parser.add_argument("--quality", default="high", choices=["standard", "high"],
                        help="画質")
    args = parser.parse_args()

    api_key = load_api_key()
    image_dir = os.path.join(os.path.dirname(__file__), "image")
    os.makedirs(image_dir, exist_ok=True)

    # カスタムプロンプト
    if args.prompt:
        out = os.path.join(image_dir, f"{args.name}.png")
        print(f"\n[カスタム生成]")
        print(f"  プロンプト: {args.prompt[:80]}...")
        generate_image(api_key, args.prompt, args.size, args.quality, out)
        return

    # 全プリセット
    if args.all:
        print(f"\n[一括生成] {len(PRESETS)} 枚\n")
        for key, preset in PRESETS.items():
            print(f"▶ {key}  ({preset['desc']})")
            out = os.path.join(image_dir, preset["file"])
            generate_image(api_key, preset["prompt"], preset["size"], preset["quality"], out)
            print()
        print("✅ 全画像の生成が完了しました")
        return

    # 特定プリセット
    if args.preset:
        preset = PRESETS[args.preset]
        print(f"\n[プリセット: {args.preset}]  {preset['desc']}")
        out = os.path.join(image_dir, preset["file"])
        generate_image(api_key, preset["prompt"], preset["size"], preset["quality"], out)
        return

    # インタラクティブメニュー
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  NPO Global Bridge — 画像生成メニュー  (gpt-image-1)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    keys = list(PRESETS.keys())
    for i, key in enumerate(keys):
        p = PRESETS[key]
        print(f"  {i+1:2d}. [{key}]  {p['desc']}  ({p['size']})")
    print(f"  {len(keys)+1:2d}. [all]  全プリセットを生成")
    print(f"   0. キャンセル\n")

    choice = input("番号を入力してください > ").strip()
    if choice == "0":
        print("キャンセルしました")
        return
    if choice == str(len(keys) + 1):
        for key, preset in PRESETS.items():
            print(f"\n▶ {key}  ({preset['desc']})")
            out = os.path.join(image_dir, preset["file"])
            generate_image(api_key, preset["prompt"], preset["size"], preset["quality"], out)
        print("\n✅ 完了")
        return
    try:
        idx = int(choice) - 1
        key = keys[idx]
    except (ValueError, IndexError):
        sys.exit("[ERROR] 無効な番号です")

    preset = PRESETS[key]
    print(f"\n▶ {key}  ({preset['desc']})")
    print(f"  プロンプト: {preset['prompt'][:100]}...")
    out = os.path.join(image_dir, preset["file"])
    generate_image(api_key, preset["prompt"], preset["size"], preset["quality"], out)
    print("\n✅ 完了")


if __name__ == "__main__":
    main()
