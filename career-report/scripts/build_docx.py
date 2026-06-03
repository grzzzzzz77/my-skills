#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_docx.py —— 把就业评估报告的 Markdown 转成 Word(.docx)。

设计目标：**零外部依赖、可分发**。
  - 只用 Python 3 标准库（zipfile / xml / struct / re）。
  - 不依赖 pandoc / python-docx / libreoffice / textutil 等"碰巧装了的"工具，
    确保任何安装了本 skill 的使用者，只要环境里有 python3 就能转换。
  - .docx 本质是一个装着 OOXML 的 zip，这里直接手写 XML 并打包。

用法:
    python3 build_docx.py <报告.md> <输出.docx> [logo.png]
    # logo 省略时默认用脚本同级 ../assets/logo.png

支持的 Markdown 子集（与本 skill 的报告模板一致）:
    # 一级标题   ## 二级标题   ### 三级标题
    **整行加粗**         → 小标题（独立样式、带段前距）
    普通段落（空行分隔；段内软换行会自动合并）
    > 引用（连续多行合并）
    - 无序列表 / * 无序列表
    1. 有序列表
    | 表头 | … |  +  | --- | … |  表格
    ---  分隔线
    行内 **加粗**、*斜体*、`代码`、[链接文字](http://url)

页眉：logo 右对齐（每页右上角）。页脚：居中页码"第 X 页"。
"""

import sys
import os
import re
import struct
import zipfile

# ---------- 单位换算 ----------
EMU_PER_PX = 9525          # 96dpi 下 1px = 9525 EMU
LOGO_WIDTH_PX = 120        # 页眉 logo 显示宽度（原图 146x73，2:1）


def xml_escape(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def png_size(path):
    """读 PNG 宽高（标准库，不依赖 Pillow）。失败回退 146x73。"""
    try:
        with open(path, "rb") as f:
            head = f.read(24)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            w, h = struct.unpack(">II", head[16:24])
            return w, h
    except Exception:
        pass
    return 146, 73


def smart_join(parts):
    """把一个自然段被软换行拆成的多行重新拼成一段。
    中文之间不加空格；只有跨行处两侧都是 ASCII 字母/数字时才补一个空格（避免把英文单词粘连）。"""
    parts = [p for p in parts if p]
    if not parts:
        return ""
    res = parts[0]
    for p in parts[1:]:
        a, b = res[-1], p[0]
        if a.isascii() and a.isalnum() and b.isascii() and b.isalnum():
            res += " " + p
        else:
            res += p
    return res


# ---------- 行内格式：链接 / 代码 / 加粗 / 斜体 → w:r 序列 ----------
_INLINE = re.compile(r"(\[[^\]]+\]\([^)]+\)|`[^`]+`|\*\*.+?\*\*|\*[^*]+?\*)")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def runs_xml(text, base_rpr="", links=None):
    """把一段含 行内格式 的文本转成若干 run / 超链接。links 为收集到的 (rId,url) 列表。
    加粗/斜体会**递归**解析内部，使"加粗里套链接/代码"等嵌套也能正确呈现。"""
    out = []
    for seg in _INLINE.split(text):
        if not seg:
            continue

        # 链接 [文字](url)（链接文字本身不再嵌套解析，按纯文本处理）
        m = _LINK.fullmatch(seg)
        if m and links is not None:
            txt, url = m.group(1), m.group(2)
            rid = "rId%d" % (101 + len(links))
            links.append((rid, url))
            out.append(
                f'<w:hyperlink r:id="{rid}"><w:r>'
                f'<w:rPr><w:rStyle w:val="Hyperlink"/>{base_rpr}</w:rPr>'
                f'<w:t xml:space="preserve">{xml_escape(txt)}</w:t></w:r></w:hyperlink>'
            )
            continue

        # 行内代码 `code`
        if seg.startswith("`") and seg.endswith("`") and len(seg) > 2:
            out.append(
                f'<w:r><w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/>'
                f'<w:shd w:val="clear" w:color="auto" w:fill="F0F0F0"/>{base_rpr}</w:rPr>'
                f'<w:t xml:space="preserve">{xml_escape(seg[1:-1])}</w:t></w:r>'
            )
            continue

        # 加粗 / 斜体 → 递归解析内部
        if seg.startswith("**") and seg.endswith("**") and len(seg) > 4:
            out.append(runs_xml(seg[2:-2], base_rpr + "<w:b/>", links))
            continue
        if seg.startswith("*") and seg.endswith("*") and len(seg) > 2:
            out.append(runs_xml(seg[1:-1], base_rpr + "<w:i/>", links))
            continue

        # 纯文本
        rpr_xml = f"<w:rPr>{base_rpr}</w:rPr>" if base_rpr else ""
        out.append(
            f'<w:r>{rpr_xml}<w:t xml:space="preserve">{xml_escape(seg)}</w:t></w:r>'
        )
    return "".join(out) or '<w:r><w:t xml:space="preserve"></w:t></w:r>'


# 正文首行缩进 2 字符：firstLineChars 为 Word 原生"按字符数缩进"（随字号缩放）；
# firstLine 是绝对值兜底（约 2×11pt=440twips），兼容部分只认绝对值的渲染器（如 Pages）。
FIRSTLINE_IND = '<w:ind w:firstLineChars="200" w:firstLine="440"/>'


def para(text, style=None, base_rpr="", links=None, indent=False):
    inner = ""
    if style:
        inner += f'<w:pStyle w:val="{style}"/>'
    if indent:
        inner += FIRSTLINE_IND
    ppr = f"<w:pPr>{inner}</w:pPr>" if inner else ""
    return f"<w:p>{ppr}{runs_xml(text, base_rpr, links)}</w:p>"


def listitem(text, num_id, links=None):
    ppr = (f'<w:pPr><w:pStyle w:val="ListParagraph"/>'
           f'<w:numPr><w:ilvl w:val="0"/><w:numId w:val="{num_id}"/></w:numPr></w:pPr>')
    return f"<w:p>{ppr}{runs_xml(text, '', links)}</w:p>"


def quote(text, links=None):
    return para(text, style="Quote", links=links)


def subhead(text, links=None):
    return para(text, style="Subhead", links=links)


def hrule():
    return ('<w:p><w:pPr><w:pBdr>'
            '<w:bottom w:val="single" w:sz="6" w:space="1" w:color="CCCCCC"/>'
            '</w:pBdr></w:pPr></w:p>')


def table(rows, links=None):
    ncol = max(len(r) for r in rows)
    colw = 9000 // ncol
    grid = "".join(f'<w:gridCol w:w="{colw}"/>' for _ in range(ncol))

    def cell(txt, header):
        rpr = "<w:b/>" if header else ""
        shd = ('<w:shd w:val="clear" w:color="auto" w:fill="F2F2F2"/>'
               if header else "")
        return (f'<w:tc><w:tcPr><w:tcW w:w="{colw}" w:type="dxa"/>{shd}'
                f'</w:tcPr>{para(txt, base_rpr=rpr, links=links)}</w:tc>')

    body = ""
    for i, r in enumerate(rows):
        cells = "".join(cell(r[c] if c < len(r) else "", i == 0)
                        for c in range(ncol))
        body += f"<w:tr>{cells}</w:tr>"
    borders = ("<w:tblBorders>" + "".join(
        f'<w:{e} w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
        for e in ("top", "left", "bottom", "right", "insideH", "insideV")
    ) + "</w:tblBorders>")
    return (f'<w:tbl><w:tblPr><w:tblW w:w="9000" w:type="dxa"/>{borders}'
            f'</w:tblPr><w:tblGrid>{grid}</w:tblGrid>{body}</w:tbl>')


_RE_HEAD = re.compile(r"(#{1,6})\s+(.*)")
_RE_BULLET = re.compile(r"[-*]\s+")
_RE_ORDERED = re.compile(r"\d+\.\s+")
_RE_HR = re.compile(r"-{3,}")
_RE_BOLDLINE = re.compile(r"\*\*.+\*\*")  # 整行加粗 = 小标题


def _is_block_start(s):
    """下一行是否是另一个块级元素（用于判断普通段落到哪里截止）。"""
    return bool(_RE_HEAD.match(s) or s.startswith(">") or _RE_BULLET.match(s)
                or _RE_ORDERED.match(s) or _RE_HR.fullmatch(s)
                or s.startswith("|") or _RE_BOLDLINE.fullmatch(s))


def _consume_list(lines, i, n, marker_re, strip_pat, num_id, out, links):
    """解析一段连续的列表。每个列表项 = 标记行 + 其后的软换行续行（合并），
    直到遇到空行、下一个列表项或其它块级元素。返回新的行号 i。"""
    while i < n and marker_re.match(lines[i].strip()):
        buf = [re.sub(strip_pat, "", lines[i].strip())]
        i += 1
        while i < n:
            nxt = lines[i].strip()
            if not nxt or _is_block_start(nxt):
                break
            buf.append(nxt)
            i += 1
        out.append(listitem(smart_join(buf), num_id, links))
    return i


def md_to_body(md):
    links = []
    lines = md.split("\n")
    out = []
    i = 0
    n = len(lines)
    while i < n:
        stripped = lines[i].strip()

        if not stripped:
            i += 1
            continue

        # 分隔线
        if _RE_HR.fullmatch(stripped):
            out.append(hrule())
            i += 1
            continue

        # 表格：当前行以 | 开头，下一行是分隔行
        if (stripped.startswith("|") and i + 1 < n
                and re.fullmatch(r"\|?[\s:|-]+\|?", lines[i + 1].strip())
                and "-" in lines[i + 1]):
            header = [c.strip() for c in stripped.strip("|").split("|")]
            rows = [header]
            i += 2
            while i < n and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            out.append(table(rows, links))
            continue

        # 标题
        m = _RE_HEAD.match(stripped)
        if m:
            level = len(m.group(1))
            style = {1: "Heading1", 2: "Heading2", 3: "Heading3"}.get(level, "Heading3")
            out.append(para(m.group(2), style=style, links=links))
            i += 1
            continue

        # 整行加粗 → 小标题（独立样式、带段前距，不与下文粘连）
        if _RE_BOLDLINE.fullmatch(stripped):
            out.append(subhead(stripped[2:-2], links))
            i += 1
            continue

        # 引用块（合并连续 > 行）
        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            out.append(quote(smart_join(buf), links))
            continue

        # 无序列表（每个列表项会吸收其后的软换行续行）
        if _RE_BULLET.match(stripped):
            i = _consume_list(lines, i, n, _RE_BULLET, r"^[-*]\s+", 1, out, links)
            continue

        # 有序列表
        if _RE_ORDERED.match(stripped):
            i = _consume_list(lines, i, n, _RE_ORDERED, r"^\d+\.\s+", 2, out, links)
            continue

        # 普通段落：合并连续软换行，直到空行或下一个块级元素
        buf = [stripped]
        i += 1
        while i < n:
            nxt = lines[i].strip()
            if not nxt or _is_block_start(nxt):
                break
            buf.append(nxt)
            i += 1
        out.append(para(smart_join(buf), links=links, indent=True))

    return "".join(out), links


# ---------- OOXML 各部件 ----------
NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def content_types(has_logo):
    logo = ('<Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>'
            if has_logo else "")
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Default Extension="png" ContentType="image/png"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
            '<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'
            '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
            f'{logo}</Types>')


def root_rels():
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'<Relationship Id="rId1" Type="{REL}/officeDocument" Target="word/document.xml"/>'
            '</Relationships>')


def document_rels(has_logo, links):
    rels = (f'<Relationship Id="rId1" Type="{REL}/styles" Target="styles.xml"/>'
            f'<Relationship Id="rId2" Type="{REL}/numbering" Target="numbering.xml"/>'
            f'<Relationship Id="rId4" Type="{REL}/footer" Target="footer1.xml"/>')
    if has_logo:
        rels += f'<Relationship Id="rId3" Type="{REL}/header" Target="header1.xml"/>'
    for rid, url in links:
        rels += (f'<Relationship Id="{rid}" Type="{REL}/hyperlink" '
                 f'Target="{xml_escape(url)}" TargetMode="External"/>')
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'{rels}</Relationships>')


def header_rels():
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'<Relationship Id="rId1" Type="{REL}/image" Target="media/logo.png"/>'
            '</Relationships>')


def header_xml(cx, cy):
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:hdr xmlns:w="{NS_W}" xmlns:r="{REL}" '
            'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
            'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<w:p><w:pPr><w:jc w:val="right"/></w:pPr><w:r><w:drawing>'
            f'<wp:inline distT="0" distB="0" distL="0" distR="0">'
            f'<wp:extent cx="{cx}" cy="{cy}"/>'
            '<wp:effectExtent l="0" t="0" r="0" b="0"/>'
            '<wp:docPr id="1" name="logo"/>'
            '<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
            '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:pic><pic:nvPicPr><pic:cNvPr id="1" name="logo.png"/><pic:cNvPicPr/></pic:nvPicPr>'
            '<pic:blipFill><a:blip r:embed="rId1"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
            '</pic:pic></a:graphicData></a:graphic>'
            '</wp:inline></w:drawing></w:r></w:p></w:hdr>')


def footer_xml():
    """居中页码：第 X 页（PAGE 域）。"""
    rpr = '<w:rPr><w:color w:val="888888"/><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr>'
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:ftr xmlns:w="{NS_W}" xmlns:r="{REL}">'
            '<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
            f'<w:r>{rpr}<w:t xml:space="preserve">第 </w:t></w:r>'
            f'<w:r>{rpr}<w:fldChar w:fldCharType="begin"/></w:r>'
            f'<w:r>{rpr}<w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
            f'<w:r>{rpr}<w:fldChar w:fldCharType="end"/></w:r>'
            f'<w:r>{rpr}<w:t xml:space="preserve"> 页</w:t></w:r>'
            '</w:p></w:ftr>')


def numbering_xml():
    bullet = ('<w:abstractNum w:abstractNumId="0"><w:lvl w:ilvl="0">'
              '<w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/>'
              '<w:lvlJc w:val="left"/><w:pPr><w:ind w:left="420" w:hanging="240"/></w:pPr>'
              '<w:rPr><w:rFonts w:ascii="Symbol" w:hAnsi="Symbol" w:hint="default"/></w:rPr>'
              '</w:lvl></w:abstractNum>')
    ordered = ('<w:abstractNum w:abstractNumId="1"><w:lvl w:ilvl="0">'
               '<w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/>'
               '<w:lvlJc w:val="left"/><w:pPr><w:ind w:left="480" w:hanging="300"/></w:pPr>'
               '</w:lvl></w:abstractNum>')
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:numbering xmlns:w="{NS_W}">{bullet}{ordered}'
            '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>'
            '<w:num w:numId="2"><w:abstractNumId w:val="1"/></w:num>'
            '</w:numbering>')


def styles_xml():
    # 中文 eastAsia 用微软雅黑（Windows 普遍存在；Mac 无则自动回退到黑体/苹方，仍为无衬线，观感可接受）
    ea = '<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="微软雅黑"/>'
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:styles xmlns:w="{NS_W}">'
            '<w:docDefaults><w:rPrDefault><w:rPr>'
            f'{ea}<w:sz w:val="22"/><w:szCs w:val="22"/>'
            '</w:rPr></w:rPrDefault>'
            '<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="360" w:lineRule="auto"/></w:pPr></w:pPrDefault>'
            '</w:docDefaults>'
            '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
            # Heading1
            '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/>'
            '<w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="240" w:after="120"/>'
            '<w:pBdr><w:bottom w:val="single" w:sz="12" w:space="4" w:color="BE0004"/></w:pBdr></w:pPr>'
            '<w:rPr><w:b/><w:color w:val="1A1A1A"/><w:sz w:val="36"/><w:szCs w:val="36"/></w:rPr></w:style>'
            # Heading2
            '<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/>'
            '<w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="200" w:after="80"/></w:pPr>'
            '<w:rPr><w:b/><w:color w:val="BE0004"/><w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr></w:style>'
            # Heading3
            '<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/>'
            '<w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="160" w:after="60"/></w:pPr>'
            '<w:rPr><w:b/><w:color w:val="333333"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style>'
            # Subhead（整行加粗的小标题）
            '<w:style w:type="paragraph" w:styleId="Subhead"><w:name w:val="Subhead"/>'
            '<w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="160" w:after="40"/></w:pPr>'
            '<w:rPr><w:b/><w:color w:val="1A1A1A"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style>'
            # Quote
            '<w:style w:type="paragraph" w:styleId="Quote"><w:name w:val="Quote"/>'
            '<w:basedOn w:val="Normal"/><w:pPr>'
            '<w:pBdr><w:left w:val="single" w:sz="18" w:space="8" w:color="D0D0D0"/></w:pBdr>'
            '<w:ind w:left="240"/><w:spacing w:before="60" w:after="60"/></w:pPr>'
            '<w:rPr><w:i/><w:color w:val="595959"/></w:rPr></w:style>'
            # ListParagraph
            '<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/>'
            '<w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="40"/></w:pPr></w:style>'
            # Hyperlink（字符样式：蓝色下划线）
            '<w:style w:type="character" w:styleId="Hyperlink"><w:name w:val="Hyperlink"/>'
            '<w:rPr><w:color w:val="0563C1"/><w:u w:val="single"/></w:rPr></w:style>'
            '</w:styles>')


def document_xml(body, has_logo):
    header_ref = ('<w:headerReference w:type="default" r:id="rId3"/>'
                  if has_logo else "")
    sect = (f'<w:sectPr>{header_ref}'
            '<w:footerReference w:type="default" r:id="rId4"/>'
            '<w:pgSz w:w="11906" w:h="16838"/>'  # A4
            '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" '
            'w:header="567" w:footer="567" w:gutter="0"/>'
            '</w:sectPr>')
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:document xmlns:w="{NS_W}" xmlns:r="{REL}">'
            f'<w:body>{body}{sect}</w:body></w:document>')


def build(md_path, out_path, logo_path):
    with open(md_path, "r", encoding="utf-8") as f:
        md = f.read()
    body, links = md_to_body(md)

    has_logo = bool(logo_path and os.path.exists(logo_path))
    if has_logo:
        w, h = png_size(logo_path)
        cx = LOGO_WIDTH_PX * EMU_PER_PX
        cy = int(cx * h / w)

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types(has_logo))
        z.writestr("_rels/.rels", root_rels())
        z.writestr("word/document.xml", document_xml(body, has_logo))
        z.writestr("word/_rels/document.xml.rels", document_rels(has_logo, links))
        z.writestr("word/styles.xml", styles_xml())
        z.writestr("word/numbering.xml", numbering_xml())
        z.writestr("word/footer1.xml", footer_xml())
        if has_logo:
            z.writestr("word/header1.xml", header_xml(cx, cy))
            z.writestr("word/_rels/header1.xml.rels", header_rels())
            with open(logo_path, "rb") as lf:
                z.writestr("word/media/logo.png", lf.read())
    return out_path


def main():
    if len(sys.argv) < 3:
        print("用法: python3 build_docx.py <报告.md> <输出.docx> [logo.png]",
              file=sys.stderr)
        sys.exit(2)
    md_path, out_path = sys.argv[1], sys.argv[2]
    if len(sys.argv) >= 4:
        logo_path = sys.argv[3]
    else:
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "..", "assets", "logo.png")
    build(md_path, out_path, logo_path)
    print(f"已生成: {out_path}")


if __name__ == "__main__":
    main()
