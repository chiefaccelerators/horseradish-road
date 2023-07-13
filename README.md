## Reading *A Wheel Inside a Wheel* in chronological order

Start from [Life Out of Balance ch.1](series-A%20Wheel%20Inside%20a%20Wheel/004-Life%20Out%20of%20Balance/001-First%20Few%20Desperate%20Hours.md) and follow "Next Chronological Chapter" link at end of each chapter.

## Requirements
- python 3+
- beautifulsoup4

## [ao3_parse.py](ao3_parse.py)

Parses AO3 HTML fics to a folder structure ending in 1 markdown file per chapter.
```
python ao3_parse.py .source/*
```

## [wiaw_chrnological.py](wiaw_chrnological.py)

Script that applies the "Next Chronological Chapter" links to output of [ao3_parse.py](ao3_parse.py) for *A Wheel Inside a Wheel*, based on [this sheet](wiaw%20timeline%20-%20Sheet1.tsv).

## /.source

HTML files downloaded from AO3 through the download button for use with [ao3_parse.py](ao3_parse.py), all rights belong to original authors.
Hoping to automate this by workid later.
