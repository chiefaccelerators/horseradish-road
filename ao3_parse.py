import os
import re
import argparse
from functools import partial

from bs4 import BeautifulSoup
from bs4.element import NavigableString


SNAKEY_PATTERN = re.compile(r"[^0-9a-zA-Z_ ]")


def snakey(name):
    return SNAKEY_PATTERN.sub("", name.replace("&", "and")).replace(" ", "_")


# smh windows
ILLEGAL_CHAR_PATTERN = re.compile(r"[<>:\"\/\\\|\?\*]")
safe_fd = partial(ILLEGAL_CHAR_PATTERN.sub, "")
MD_ESCAPE_PATTERN = re.compile(r"([\\\`\*\_\{\}\[\]\(\)\#\+\-\.\!\|])")
escape_md = partial(MD_ESCAPE_PATTERN.sub, r"\\\1")


def html_to_md(tag):
    # special case footnote
    if tag.name == "a" and tag.attrs.get("name"):
        if tag.attrs["name"].startswith("_ftnref"):
            ftn_idx = tag.attrs["name"][7:]
            return f"[^{ftn_idx}]"
        elif tag.attrs["name"].startswith("_ftn"):
            ftn_idx = tag.attrs["name"][4:]
            return f"[^{ftn_idx}]:"

    if isinstance(tag, NavigableString):
        return "".join((escape_md(txt).replace("\n", "") for txt in tag.strings))
    if tag.name == "br":
        return "\n"
    contents_text = "".join((html_to_md(item) for item in tag.contents))
    if not contents_text.strip():
        return ""
    if tag.name == "p":
        contents_text += "\n\n"
    if tag.name in ("strong", "b"):
        contents_text = f"**{contents_text.strip()}**"
    if tag.name in ("em", "i"):
        contents_text = f"*{contents_text.strip()}*"
    if tag.name == "li":
        if tag.parent.name == "ul":
            contents_text = f"- {contents_text.strip()}\n"
        elif tag.parent.name == "ol":
            contents_text = f"1. {contents_text.strip()}\n"
    # TODO: optimize this call
    return contents_text


def write_work_meta(args, soup):
    preface = soup.find("div", attrs={"id": "preface"})
    source_url = preface.p.find_all("a")[-1].attrs["href"]
    meta = preface.find("div", class_="meta")
    title = meta.h1
    byline = meta.find("div", class_="byline")
    authors = byline.find_all("a", attrs={"rel": "author"})

    series = preface.find("a", attrs={"href": re.compile(r"^http:\/\/archiveofourown\.org\/series\/.+")})
    if series:
        series = series.parent
        series_index = int(series.contents[0].split(" ")[1])
        series_name = series.a.string
        output_folder = os.path.join(args.output, f"series-{safe_fd(series_name)}", f"{series_index:03}-{safe_fd(title.string)}")
    else:
        authors_string = "-".join((author.string for author in authors))
        output_folder = os.path.join(args.output, f"author-{safe_fd(authors_string)}", safe_fd(title.string))

    os.makedirs(output_folder, exist_ok=True)
    with open(os.path.join(output_folder, f".meta.md"), "w") as meta_fn:
        meta_fn.write(f"# {title.string}\n\n")
        authors_string = ", ".join((author.string for author in authors))
        meta_fn.write(f"by {authors_string}\n\n")
        try:
            meta_fn.write(html_to_md(meta.ul.li))
        except AttributeError:
            pass
        meta_fn.write(source_url)
        meta_fn.write("\n\n")
        for blockquote in meta.find_all("blockquote", class_="userstuff"):
            prev = blockquote.previous_sibling
            while prev and prev.name is None:
                prev = prev.previous_sibling
            if prev:
                meta_fn.write(f"## {prev.string}\n\n")
                meta_fn.write(html_to_md(blockquote))

    return output_folder


def write_chapters(args, soup, output_folder):
    chapters = soup.find("div", attrs={"id": "chapters"})
    sorted_items = []
    current_items = []
    for item in chapters:
        if isinstance(item, NavigableString):
            continue
        if item.attrs["class"] == ["meta", "group"] and current_items:
            sorted_items.append(current_items)
            current_items = []
        current_items.append(item)
    sorted_items.append(current_items)
    for idx, group in enumerate(sorted_items):
        try:
            if group[0].name == "h2":
                title = group[0]
            else:
                title = group[0].h2
            content = group[1]
            try:
                endnote = group[2]
            except IndexError:
                endnote = None
            with open(os.path.join(output_folder, f"{idx+1:03}-{safe_fd(title.string)}.md"), "w") as chapter_fn:
                chapter_fn.write(f"# {title.string}\n\n")
                chapter_fn.write(html_to_md(content))
                if endnote:
                    chapter_fn.write(f"## {endnote.p.string}\n\n")
                    chapter_fn.write(html_to_md(endnote))
        except Exception:
            print(group[0])
            raise


def main(args):
    for filename in args.filenames:
        if filename.endswith(".html"):
            print(f"Parsing {filename}")
            with open(filename) as fp:
                soup = BeautifulSoup(fp, "html.parser")
                output_folder = write_work_meta(args, soup)
                write_chapters(args, soup, output_folder)
            print(f"Wrote {output_folder}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parses AO3 HTML format to plain text organized by chapters")
    parser.add_argument("filenames", nargs="+", type=str, help="input HTML files downloaded from AO3")
    parser.add_argument("-o", "--output", type=str, default=".", help="output folder")
    args = parser.parse_args()

    main(args)
