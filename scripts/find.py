#!/usr/bin/env python3
"""在本地目录里找电商 Skill。只读 references/catalog.json，不联网。

例子：
  python3 scripts/find.py --stats
  python3 scripts/find.py --query "差评分析" --platform Amazon
  python3 scripts/find.py --category 达人营销 --platform "TikTok Shop" --limit 5
  python3 scripts/find.py --flow Shopify
  python3 scripts/find.py --web
"""
import argparse, collections, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / 'references' / 'catalog.json'
PAGE = ROOT / 'assets' / 'ecom-skills.html'


def load():
    if not CATALOG.is_file():
        sys.exit(f'找不到目录文件：{CATALOG}。请重新下载整个 jiang-ecom-skills 文件夹。')
    return json.loads(CATALOG.read_text(encoding='utf-8'))


def prompt_for(s):
    where = s.get('dir') or '仓库根目录'
    return (f"帮我安装一个 Skill，名字叫 {s['n']}。\n仓库地址：{s['ru']}\nSkill 在仓库里的位置：{where}\n"
            f"把这个 Skill 的整个文件夹下载到你的 Skill 目录，文件夹名保持 {s['n']}。"
            "装好后读一遍里面的 SKILL.md，告诉我“装好了”，再用一句话说它能帮我干什么、需要我准备什么。")


def match_platform(s, name):
    if not name:
        return True
    want = name.lower().replace(' ', '')
    return any(want in p.lower().replace(' ', '') for p in s['p'])


def search(data, query='', platform='', category='', with_general=False):
    words = [w for w in query.lower().split() if w]
    out = []
    for s in data['skills']:
        ok_plat = match_platform(s, platform) or (with_general and '通用' in s['p'])
        if not ok_plat:
            continue
        if category and category.lower().replace(' ', '') not in s['c'].lower().replace(' ', ''):
            continue
        text = ' '.join([s['t'], s['n'], s['s'], s.get('d', ''), s['r'], s['c'], ' '.join(s['p'])]).lower()
        if not all(w in text for w in words):
            continue
        # 中文名和英文名里命中的排前面，其次看来源仓库的星标
        score = sum(3 for w in words if w in (s['t'] + s['n']).lower()) + (2 if platform and match_platform(s, platform) else 0)
        out.append((score, s.get('st', 0), s))
    out.sort(key=lambda x: (-x[0], -x[1]))
    return [x[2] for x in out]


def show(s, full=True):
    line = f"- {s['t']}（{s['n']}）｜{s['c']}｜{'、'.join(s['p'])}\n  {s['s']}\n  来源：{s['ru']}（★{s.get('st', 0)}，{s['l']}）\n  原文：{s['u']}"
    if full:
        line += '\n  安装提示词：\n    ' + prompt_for(s).replace('\n', '\n    ')
    return line


def main():
    ap = argparse.ArgumentParser(description='在本地目录里找电商 Skill')
    ap.add_argument('--query', '-q', default='', help='要干的活，空格分隔多个词，例如 "差评 分析"')
    ap.add_argument('--platform', '-p', default='', help='平台，例如 Amazon、TikTok Shop、淘宝')
    ap.add_argument('--category', '-c', default='', help='工种，例如 选品调研、图片设计')
    ap.add_argument('--limit', '-n', type=int, default=5)
    ap.add_argument('--flow', metavar='平台', help='按流程列出这个平台每一步能用的 Skill；填 all 看所有平台')
    ap.add_argument('--stats', action='store_true', help='目录有多少 Skill、哪些平台和工种')
    ap.add_argument('--web', action='store_true', help='给出本地网页的路径')
    ap.add_argument('--json', action='store_true', help='用 JSON 输出')
    a = ap.parse_args()
    data = load()
    skills = data['skills']

    if a.web:
        if not PAGE.is_file():
            sys.exit(f'找不到网页文件：{PAGE}')
        print(f'本地网页：{PAGE}\n浏览器地址：{PAGE.as_uri()}')
        return
    if a.stats:
        pc = collections.Counter(p for s in skills for p in s['p'])
        cc = collections.Counter(s['c'] for s in skills)
        info = {'更新日期': data['updated_at'], 'Skill 数': len(skills), '来源仓库数': len({s['r'] for s in skills}),
                '平台': dict(pc.most_common()), '工种': {c: cc.get(c, 0) for c in data['categories']}}
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return
    if a.flow:
        plat = '' if a.flow.lower() == 'all' else a.flow
        print(f"{plat or '所有平台'}：一家店从头到尾每一步能用的 Skill（每步最多 {a.limit} 个，含不限平台的）\n")
        for i, c in enumerate(data['categories'], 1):
            hits = search(data, platform=plat, category=c, with_general=True)
            print(f"{i}. {c}（{len(hits)} 个）—— {data['category_hints'].get(c, '')}")
            for s in hits[:a.limit]:
                print(f"   - {s['t']}（{s['n']}）｜{s['ru']}")
        return

    hits = search(data, a.query, a.platform, a.category)
    if a.json:
        print(json.dumps({'total': len(hits), 'items': [dict(s, install_prompt=prompt_for(s)) for s in hits[:a.limit]]}, ensure_ascii=False, indent=2))
        return
    if not hits:
        print('没找到。换个说法再试，或者去掉平台只按工种找。目录没有覆盖全网，找不到不代表没人做过。')
        return
    print(f'找到 {len(hits)} 个，先列 {min(a.limit, len(hits))} 个：\n')
    print('\n\n'.join(show(s) for s in hits[:a.limit]))


if __name__ == '__main__':
    main()
