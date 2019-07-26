### Introduction
A module for managing a hierarchical database of 
files and folders. An example application could be for storing media 
libraries (e.g. keeping track of a large number of audio and video files 
in media applications, quickly searching through them).

### Features
- Fast searching and navigation:

- All nodes are mapped to objects for ease of use:
    - Object Oriented API for intuitive usage and easy integration into
    existing projects.
    
- Threadsafe and process-safe:
    - File indexes are able to be used simultaneously across multiple
    threads and processes without locking errors.
    
- Custom metadata columns:
    - Able to define custom metadata columns for files and folders and
    

### Installation
`pip install sqlite-file-index`

Or to install latest version from this repo:

`pip install git+https://github.com/0xf0f/sqlite-file-index`

### Examples
##### Creation/Loading
```python
from sqlite_file_index import FileIndex

file_index = FileIndex.load_or_create('index.db')
```

##### Saving
```python
file_index = FileIndex.create_new(':memory:')
file_index.save_as('dump.db')
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
    r'C:\Users\admin\Desktop'
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
    r'C:\Users\admin\Desktop'
)

if folder_node:
    for node in folder_node.iterdir(recursive=True):
        print(node)
```
