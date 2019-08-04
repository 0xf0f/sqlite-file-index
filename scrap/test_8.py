from typing import Optional, Iterable

from sqlite_file_index import FileIndex
from pathlib import Path

cd = Path(__file__).parents[1]


class TestIndex(FileIndex):
    tags = [
        'git'
    ]


    def initial_file_tags(self, path: Path) -> Optional[Iterable[str]]:
        if 'git' in str(path).lower():
            return 'git',

    def initial_folder_tags(self, path: Path) -> Optional[Iterable[str]]:
        if 'git' in str(path).lower():
            return 'git',


# if __name__ == '__main__':
#     index = TestIndex.create_new()
#     index.add_paths(
#         (cd,), recursive=True
#     )
#     tag = index.get_tag('git')
#     for node in tag.get_files_with_tag():
#         print(node)
#
#     tag = index.add_tag('test')
#     for node in index.search('test', yield_folders=True):
#         node.add_tag(tag, commit=False)
#     index.db.commit()
#
#     index.save_as('tag_test.db')

if __name__ == '__main__':
    index = TestIndex.load_from('tag_test.db')
    for node in index.get_tag('test').get_files_with_tag():
        print(node)
        node.add_tag('test')
