from sqlite_file_index import FileIndex
from pathlib import Path

index = FileIndex.load_from('test.db')
# index.add_paths(
#     map(Path,
#         [
#             r'T:\__SORTED\__KITS'
#         ]
#     )
# )
folder = index.get_folder_node_by_path(r'T:\__SORTED\__KITS\superdrums8000')
for file in folder.search('snare', recursive=True):
# for file in folder.iterdir(recursive=True):
    print(file.path)

# subfolders = folder.file_index.db.execute(
#     f'''
#     with recursive subfolders(n) as (
#         values(?)
#         union all select id from folders, subfolders where parent=subfolders.n
#     )
#
#     select * from folders where parent in subfolders
#     union all
#     select * from files where parent in subfolders
#     order by path collate nocase asc;
#     ''', (folder.id,)
# )
#
# subfolders = folder.file_index.db.execute(
#     f'''
#     select * from folders where parent=?
#     union all
#     select * from files where parent=?
#     order by path collate nocase asc;
#     ''', (folder.id, folder.id)
# )
#
# for row in subfolders:
#     print(dict(row))

# index.vacuum()
