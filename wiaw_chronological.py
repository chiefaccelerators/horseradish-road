import os
import glob
import urllib.parse

# download of https://docs.google.com/spreadsheets/d/1CpUJRlolijBJOxYlqVlaIQzDWjBqP5hkHiog3BRjTpI/edit#gid=0
SOURCE_TSV = "wiaw timeline - Sheet1.tsv"
TARGET_EN = "series-A Wheel Inside a Wheel"
TARGET_ZH = "series-【授翻】轮中之轮"

next_format = "---\n[Next Chronological Chapter]({link})"


def zh_idx(en_idx):
    # magical knowledge about how en series index maps to zh series index
    # will need updating
    return en_idx - 1


def append_next_chapter_links(filename_list, replace_str):
    for idx, filename in enumerate(filename_list[:-1]):
        filesize = os.stat(filename).st_size
        print(filename)
        with open(filename, "r+") as chapter_fn:
            # slow lazy impl
            file_lines = chapter_fn.read().splitlines()
            final_line = file_lines[-1]
            if final_line.startswith("[Next Chronological Chapter]"):
                write_from = filesize - (len(file_lines[-3]) + len(file_lines[-2]) + len(file_lines[-1]) + 2)
            else:
                write_from = filesize
            chapter_fn.seek(write_from)
            chapter_fn.truncate(write_from)
            next_filename = filename_list[idx + 1].replace(replace_str, "..")
            chapter_fn.write(next_format.format(link=urllib.parse.quote(next_filename)))
            chapter_fn.write("\n")


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
    filenames_list_en = []
    filenames_list_zh = []
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
            filenames_list_en.append(filename)
        except IndexError:
            continue
        # zh
        index = int(filename.split("/")[1].split("-")[0])
        try:
            filename = glob.glob(f"{TARGET_ZH}/{zh_idx(index):03}-*/{chapter:03}*")[0]
            filenames_list_zh.append(filename)
        except IndexError:
            continue

    append_next_chapter_links(filenames_list_en, TARGET_EN)
    append_next_chapter_links(filenames_list_zh, TARGET_ZH)


if __name__ == "__main__":
    main()
