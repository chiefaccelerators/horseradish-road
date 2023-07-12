import os
import glob
import urllib.parse

# download of https://docs.google.com/spreadsheets/d/1CpUJRlolijBJOxYlqVlaIQzDWjBqP5hkHiog3BRjTpI/edit#gid=0
SOURCE_TSV = "wiaw timeline - Sheet1.tsv"
TARGET_EN = "series-A Wheel Inside a Wheel"
TARGET_ZH = "series-【授翻】轮中之轮"

next_format = '---\n[<div style="text-align: right">Next Chronological Chapter</div>]({link})'


def zh_idx(en_idx):
    # magical knowledge about how en series index maps to zh series index
    # will need updating
    return en_idx - 1


def main():
    # read the source csv file
    keys = None
    data = []
    with open(SOURCE_TSV, "r") as timeline_fn:
        for line in timeline_fn:
            values = line.strip("\n").split("\t")
            if not keys:
                keys = values
            else:
                data.append({key: value for key, value in zip(keys, values)})

    # TODO: implement partial chapters once given some kind of search string for where to anchor link
    # for now only take first entry
    dedupe = set()
    filenames_list = []
    for entry in data:
        book = entry["Book"]
        try:
            chapter = int(entry["Chapter"])
        except ValueError:
            continue
        if (book, chapter) in dedupe:
            continue
        dedupe.add((book, chapter))
        # en
        try:
            filename = glob.glob(f"{TARGET_EN}/*-{book}/{chapter:03}*")[0]
        except IndexError:
            continue
        filenames_list.append(filename)
    for idx, filename in enumerate(filenames_list[:-1]):
        filesize = os.stat(filename).st_size
        print(filename)
        with open(filename, "r+") as chapter_fn:
            # slow lazy impl
            file_lines = chapter_fn.read().splitlines()
            final_line = file_lines[-1]
            if final_line.startswith('[<div style="text-align: right">Next Chronological Chapter</div>]'):
                chapter_fn.seek(filesize - (len(file_lines[-3]) + len(file_lines[-2]) + len(file_lines[-1]) + 2))
            else:
                chapter_fn.seek(filesize)
            next_filename = filenames_list[idx + 1]
            chapter_fn.write(next_format.format(link=urllib.parse.quote(next_filename)))
            chapter_fn.write("\n")


if __name__ == "__main__":
    main()
