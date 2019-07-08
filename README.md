### Introduction
- Creates a hierarchical file index in an sqlite database for fast searching and navigation.
- All nodes are mapped to objects for ease of use.
- Threadsafe and process-safe.

### Installation
`pip install git+https://github.com/0xf0f/sqlite-file-index`

### Examples
##### Creation/Loading
```python
from sqlite_file_index import FileIndex

file_index = FileIndex.load_or_create('index.db')
```

##### Indexing
```python
# Adding entire directories to the index:
directories = [
    r'C:\Users\admin\Documents'
    r'C:\Users\admin\Desktop'
]

file_index.add_paths(
    directories,
    recursive=True,
)
```
```python
# Adding individual files to the index:
files = [
    r'C:\Users\admin\Desktop\file_1.txt',
    r'C:\Users\admin\Desktop\file_2.txt',
]

file_index.add_paths(files)
```

##### Searching
```python
# Searching the entire index by keyword:
for node in file_index.search('.txt'):
    print(node)
```

```python
# Searching a specific folder:
folder_node = file_index.get_folder_node_by_path(
    r'C:\Desktop'
)

if folder_node:
    for node in folder_node.search('.txt'):
        print(node)
```

##### Navigation
```python
# Stepping through entire index:
for node in file_index.get_root_nodes():
    print(node)
    for sub_node in node.iterdir(recursive=True):
        print(sub_node)
```

```python
# Stepping through a specific folder:
folder_node = file_index.get_folder_node_by_path(
    r'C:\Desktop'
)

if folder_node:
    for node in folder_node.iterdir(recursive=True):
        print(node)
```
