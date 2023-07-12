import os
import re
import argparse

from bs4 import BeautifulSoup
from bs4.element import NavigableString


SNAKEY_PATTERN = re.compile(r"[^0-9a-zA-Z_ ]")


def snakey(name):
    # return SNAKEY_PATTERN.sub("", unidecode(name.replace("&", "and")).strip()).replace(" ", "_")
    return SNAKEY_PATTERN.sub("", name.replace("&", "and")).replace(" ", "_")


def userstuff_to_string(userstuff):
    if isinstance(userstuff, NavigableString):
        return "".join((txt.replace("\n", "") for txt in userstuff.strings))
    if userstuff.name == "br":
        return "\n"
    contents_text = "".join((userstuff_to_string(item) for item in userstuff.contents))
    if userstuff.name == "p":
        contents_text += "\n\n"
    if userstuff.name in ("strong", "b"):
        contents_text = f"**{contents_text.strip()}**"
    if userstuff.name in ("em", "i"):
        contents_text = f"*{contents_text.strip()}*"
    return contents_text


def write_work_meta(args, soup):
    # <dd>Part 7 of <a href="http://archiveofourown.org/series/1650067">A Wheel Inside a Wheel</a></dd>
    preface = soup.find("div", attrs={"id": "preface"})
    source_url = preface.p.find_all("a")[-1].attrs["href"]
    meta = preface.find("div", class_="meta")
    title = meta.h1
    author = meta.find("a", attrs={"rel": "author"})

    series = preface.find("a", attrs={"href": re.compile(r"^http:\/\/archiveofourown\.org\/series\/.+")})
    if series:
        series = series.parent
        series_index = int(series.contents[0].split(" ")[1])
        series_name = series.a.string
        output_folder = os.path.join(args.output, snakey(author.string), snakey(series_name), f"{series_index:03}_{snakey(title.string)}")
    else:
        output_folder = os.path.join(args.output, snakey(author.string), ".no_series", snakey(title.string))

    os.makedirs(output_folder, exist_ok=True)
    with open(os.path.join(output_folder, f".meta.md"), "w") as meta_fn:
        meta_fn.write(f"# {title.string}\n\n")
        meta_fn.write(source_url)
        meta_fn.write("\n\n")
        for blockquote in meta.find_all("blockquote", class_="userstuff"):
            prev = blockquote.previous_sibling
            while prev and prev.name is None:
                prev = prev.previous_sibling
            if prev:
                meta_fn.write(f"## {prev.string}\n\n")
                meta_fn.write(userstuff_to_string(blockquote))

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
            with open(os.path.join(output_folder, f"{idx+1:03}_{snakey(title.string)}.md"), "w") as chapter_fn:
                chapter_fn.write(f"# {title.string}\n\n")
                chapter_fn.write(userstuff_to_string(content))
                if endnote:
                    chapter_fn.write(f"## {endnote.p.string}\n\n")
                    chapter_fn.write(userstuff_to_string(endnote))
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parses AO3 HTML format to plain text organized by chapters")
    parser.add_argument("filenames", nargs="+", type=str, help="input HTML files downloaded from AO3")
    parser.add_argument("-o", "--output", type=str, default=".", help="output folder")
    args = parser.parse_args()

    main(args)
