# -*- coding: utf-8 -*-
"""把 协议/设计服务标准协议书.md 解析为小工具用的 data.js(构建期脚本,不打进 zip)。

目录层级按 md 的目录清单生成:
- 条目、顺序、归属和文字来自目录清单
- 正文标题只用于匹配跳转目标，不自动加入目录
- 编号仅从 md 目录文本中提取(md 只给前 5 章编号),不自创
"""
import json
import io
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
MD = os.path.join(ROOT, "..", "协议", "设计服务标准协议书.md")
OUT = os.path.join(ROOT, "1.0.0", "assets", "data.js")

with io.open(MD, encoding="utf-8") as f:
    lines = f.read().splitlines()

# 阅读版省略纸质签署页的排版提示；源文件及实际签署内容保留。
PRINT_ONLY_NOTICES = {"（以下无正文，为签署页）"}
lines = [ln for ln in lines
         if re.sub(r"^[-+*]\s+", "", ln.strip()) not in PRINT_ONLY_NOTICES]

def is_h2(s):
    return s.startswith("## ")

def norm(s):
    return s.replace("模版", "模板")

# ---------- 按 ## 切章,EN+CN 成对 ----------
chapters = []          # {en, cn, lines[]}
cur = None
pending_en = None
for ln in lines:
    if is_h2(ln):
        title = ln[3:].strip()
        is_en = not re.search(r"[一-鿿]", title)
        if pending_en is None and is_en:
            pending_en = title
            continue
        cur = {"en": pending_en or "", "cn": title, "lines": []}
        pending_en = None
        chapters.append(cur)
        continue
    if cur is not None:
        cur["lines"].append(ln)

# ---------- 章内分块 ----------
def parse_blocks(lines):
    blocks = []
    i = 0
    n = len(lines)
    while i < n:
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        heading = re.match(r"^(#{3,6})\s+(.+)$", s)
        if heading:
            blocks.append({"t": "h" + str(len(heading.group(1))), "cn": heading.group(2).strip()})
            i += 1
            continue
        item = re.match(r"^(?:(\d+)\.\s+|[-+*]\s+)(.+)$", s)
        if item:
            kind = "ol" if item.group(1) else "ul"
            items = []
            while i < n:
                current = lines[i].strip()
                if not current:
                    i += 1
                    continue
                match = re.match(r"^(?:(\d+)\.\s+|[-+*]\s+)(.+)$", current)
                if not match or ("ol" if match.group(1) else "ul") != kind:
                    break
                items.append({"cn": match.group(2), "num": match.group(1) or ""})
                i += 1
            blocks.append({"t": kind, "items": items})
            continue
        if s.startswith("|"):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c or "---") for c in cells):
                    rows.append(cells)
                i += 1
            cleaned = []
            for row in rows:
                cleaned.append([
                    [seg.strip() for seg in re.split(r"<br\s*/?>", cell.replace("&nbsp;", " "))]
                    for cell in row
                ])
            blocks.append({"t": "table", "rows": cleaned})
            continue
        blocks.append({"t": "p", "cn": s})
        i += 1
    return blocks

# ---------- 正文与目录分开：目录清单决定收录范围、文字及归属 ----------
result = [
    {"en": ch["en"], "cn": ch["cn"], "blocks": parse_blocks(ch["lines"])}
    for ch in chapters if ch["cn"] != "目录"
]

def key(text):
    text = re.sub(r"\s+", "", norm(text))
    text = re.sub(r"^\d+\.", "", text)
    return re.sub(r"补充条款\d+：", "补充条款：", text)

# 每个正文块有独立锚点；同名标题按正文出现顺序匹配，避免不同选项串位。
candidates = []
for ci, ch in enumerate(result):
    candidates.append((key(ch["cn"]), ci, "ch-" + str(ci)))
    for bi, block in enumerate(ch["blocks"]):
        target = "ch-%d-b%d" % (ci, bi)
        if "cn" in block:
            candidates.append((key(block["cn"]), ci, target))
        for ii, item in enumerate(block.get("items", [])):
            candidates.append((key(item["cn"]), ci, target + "-i" + str(ii)))

used = set()
def locate(title, scope=None):
    matches = [(i, c) for i, c in enumerate(candidates)
               if c[0] == key(title) and i not in used]
    scoped = [(i, c) for i, c in matches if c[1] == scope]
    if scoped:
        matches = scoped
    if not matches:
        raise ValueError("目录条目未匹配正文：" + title)
    i, candidate = matches[0]
    used.add(i)
    return candidate[1], candidate[2]

toc = []
parent = None
numbered_parent = False
for ln in next(ch["lines"] for ch in chapters if ch["cn"] == "目录"):
    if not ln.strip():
        continue
    indent = len(ln) - len(ln.lstrip())
    text = ln.strip()
    numbered = re.match(r"^(\d+)\.\s+(.+)$", text)
    label = numbered.group(2) if numbered else re.sub(r"^[-+*]\s+", "", text)
    if indent == 0:
        numbered_parent = bool(numbered)
        ch, target = (-1, "doc-toc") if label == "目录" else locate(label)
        parent = {"num": numbered.group(1) if numbered else "", "cn": label,
                  "ch": ch, "target": target, "subs": []}
        toc.append(parent)
    else:
        # 01. 标记宽度为四列；无序列表标记宽度为两列。
        depth = 1 + max(0, (indent - (4 if numbered_parent else 2)) // 2)
        ch, target = locate(label, parent["ch"])
        parent["subs"].append({"cn": text if numbered else label,
                               "lvl": 2 + depth, "ch": ch, "target": target})

data = {
    "title": "设计服务标准协议书",
    "titleEn": "DESIGN SERVICES STANDARD AGREEMENT",
    "toc": toc,
    "chapters": result,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
with io.open(OUT, "w", encoding="utf-8") as f:
    f.write("// 由 build_data.py 生成,请勿手改\n")
    f.write("window.AGREEMENT_DATA = ")
    f.write(payload)
    f.write(";\n")

print("chapters:", len(result))
print("toc entries:")
for e in toc:
    print("  %2s %-28s ch=%-3d subs=%d" % (e["num"], e["cn"], e["ch"], len(e["subs"])))
print("total blocks:", sum(len(c["blocks"]) for c in result))
print("data.js bytes:", os.path.getsize(OUT))
