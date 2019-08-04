import re
from sqlite_file_index import FileIndex
from pathlib import Path
from typing import Optional, Iterable


def multi_substring_pattern(substrings: list):
    return re.compile(
        '|'.join(
            sorted(
                map(re.escape, substrings),
                key=len, reverse=True,
            )
        ),
        flags=re.IGNORECASE,
    )


class TaggedFileIndex(FileIndex):
    tags = [
        'bass',
        'guitar',
        'drums',
        'kick',
    ]

    tag_groups = {
        'drums': (
            'kick',
            'hat',
            'cymbal',
        ),

        'bass': (
            'guitar',
        )
    }

    tag_regex = multi_substring_pattern(tags)

    def initial_file_tags(self, path: Path):
        return set(
            self.tag_regex.findall(
                str(path)
            )
        )


if __name__ == '__main__':
    index = TaggedFileIndex.create_new()
    index.add_paths(
        (r'T:\__SORTED\__KITS',),
        recursive=True
    )

    for node in index.get_tag('guitar').get_files_with_tag():
        print(node)

    index.save_as('tagging_test.db')
