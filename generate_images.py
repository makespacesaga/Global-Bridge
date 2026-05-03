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
    "hero_bridge": {
        "desc": "ヒーロー背景：国際架け橋（フィリピン・日本・世界）",
        "file": "hero_bridge.jpg",
        "size": "1536x1024",
        "quality": "high",
        "prompt": (
            "Award-winning photojournalism photograph, published in National Geographic. "
            "A Japanese female NGO volunteer kneels down and gently holds the hands of a young Filipino girl, "
            "both smiling with profound warmth, surrounded by a lush tropical village. "
            "Other volunteers and local community members work together in the soft-focus background — "
            "building, sharing, laughing. "
            "Late afternoon golden hour light cascades through palm fronds, casting long warm shadows. "
            "Shallow depth of field, f/1.8 bokeh background of a rural Philippine community. "
            "Colors: warm amber, deep emerald green, rich earth tones. "
            "Mood: hope, solidarity, genuine human connection across cultures. "
            "No text, no logos. Ultra-sharp, professional editorial photography, 35mm film aesthetic, "
            "cinematic widescreen 3:2 ratio, breathtaking quality"
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
            "Stunning wide-angle environmental photography, cinematic quality. "
            "Low tide at Ariake Sea tidal flats, Saga Prefecture Japan at golden hour — "
            "vast silver-grey mud flats stretch to the horizon, reflecting the fiery orange and pink sky. "
            "In the foreground, a line of Japanese volunteers in work clothes carefully collect trash along the shoreline, "
            "passing bags to each other with care and determination. "
            "Behind them, traditional fishing boats rest on the mud. "
            "Far background: misty green mountains meet a luminous sunset sky. "
            "Mood: quiet dedication, humanity caring for the earth, reverence for nature. "
            "Shot on large format camera, ultra-sharp, rich tonal depth, "
            "no text, no logos, cinematic widescreen, National Geographic quality"
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
            "Profound documentary portrait, portrait orientation, award-winning photography. "
            "A circle of six people — Japanese, Filipino, African, South Asian, elderly and young — "
            "sit together around a low table outdoors in a peaceful Japanese garden setting, "
            "deep in conversation, hands gesturing expressively, eyes full of understanding and empathy. "
            "One elderly Japanese woman holds the hand of a young African man. "
            "Dappled afternoon light falls through maple tree leaves above. "
            "Expression: thoughtful, warm, united — a moment of genuine cross-cultural dialogue. "
            "Shallow depth of field, f/1.8, warm natural color palette, "
            "rich bokeh of the garden background. "
            "Mood: peace, dignity, mutual respect, belonging. "
            "35mm film photography aesthetic, no text, no logos, portrait 2:3 ratio, "
            "Magnum Photos quality, deeply human"
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
    "purpose_hero": {
        "desc": "設立趣旨書セクションヘッダー背景",
        "file": "purpose_hero.jpg",
        "size": "1536x1024",
        "quality": "high",
        "prompt": (
            "Breathtaking cinematic landscape photograph at dusk. "
            "An ancient stone bridge arches over a calm river, reflecting the burning orange and purple sky. "
            "On the bridge, silhouettes of five to six people from different backgrounds — "
            "Japanese, Filipino, African, European — walk together toward the horizon. "
            "One person carries a child on their back. "
            "Dramatic god rays pierce through storm clouds, illuminating the bridge from above. "
            "Foreground: shallow water with mirror-like reflection. "
            "Color palette: deep navy, burnt orange, golden amber, dark forest green. "
            "Atmosphere: timeless, monumental, deeply moving, like the opening shot of an Oscar-winning film. "
            "Ultra-wide cinematic 3:2, extremely high detail, no text, no logos, "
            "suitable as a dark-overlay background for a nonprofit website header"
        )
    },
    "purpose_activity": {
        "desc": "活動経緯イメージ（東南アジア支援）",
        "file": "purpose_activity.jpg",
        "size": "1024x1536",
        "quality": "high",
        "prompt": (
            "Intimate documentary photograph, portrait orientation, Magnum Photos quality. "
            "Outdoors in a rural Philippine village construction site: "
            "Three people — a Japanese man in his 40s wearing plain work clothes and a cap, "
            "a Filipino woman in her 30s, and a young Filipino teenage boy — "
            "work side by side laying concrete blocks for a school wall, "
            "laughing and talking together naturally. "
            "No branded text or logos on any clothing. Plain work shirts only. "
            "Lush tropical greenery and banana trees in the background. "
            "Bright midday tropical light with soft shadows. "
            "Mood: genuine camaraderie, hard work, joy of building something together. "
            "Shot at eye level, f/2.8, warm natural tones, "
            "rich detail in faces and hands, portrait 2:3 ratio, "
            "raw authentic moment, no staging, no text anywhere in the image"
        )
    },
    "purpose_activity_v2": {
        "desc": "活動経緯イメージv2（コミュニティイベント）",
        "file": "purpose_activity.jpg",
        "size": "1024x1536",
        "quality": "high",
        "prompt": (
            "Wide establishing documentary photograph, portrait orientation, vivid and uplifting. "
            "An outdoor community event in a rural Southeast Asian village under large shade trees — "
            "dozens of local children and adults joyfully receiving school supplies and books "
            "from a group of Japanese and local organizers. "
            "Children in the foreground hold up notebooks and pencils with beaming smiles. "
            "Adults in the middle ground hand out colorful bags. "
            "In the background, more villagers gather, curious and hopeful. "
            "Late afternoon golden light filters through the canopy, casting warm dappled shadows. "
            "The scene bursts with movement, color, laughter, and human warmth. "
            "No text visible on clothing or banners. Plain casual clothes. "
            "Color palette: lush tropical green, golden sunlight, bright clothing. "
            "Mood: generosity, celebration, genuine joy, hope for the future. "
            "f/4.0, natural light, slight elevated angle to show full scene, "
            "portrait 2:3 ratio, publication quality, no artificial staging"
        )
    },
    "line_banner": {
        "desc": "LINEお問い合わせバナー",
        "file": "line_banner.png",
        "size": "1536x1024",
        "quality": "high",
        "prompt": (
            "Clean professional contact banner for a Japanese NPO website. "
            "Bright LINE green background (#06C755), centered white speech bubble icon and bold white Japanese text "
            "'LINEでお問い合わせ' with subtitle 'お気軽にご連絡ください', "
            "modern minimal flat design, slight gradient from lime green to emerald green, "
            "small white arrow icon on the right, rounded rectangle shape, "
            "crisp vector-style illustration, high contrast, no photography, pure graphic design"
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
        "model": "gpt-image-2",
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
        with urllib.request.urlopen(req, timeout=180) as resp:
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
    parser.add_argument("--quality", default="high", choices=["low", "medium", "high", "auto"],
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
