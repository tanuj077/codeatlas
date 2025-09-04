from app.services import chunker

PYTHON_CODE = """
class MyClass:
    def method(self):
        pass

def my_function():
    return 42
"""

GENERIC_CODE = """
// This is a comment
int main() { return 0; }
"""

MULTI_CODE = """
class First:
    pass

def func_one():
    pass

class Second:
    pass

def func_two():
    pass
"""

def create_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def test_extract_python_chunks(tmp_path):
    file_path = tmp_path / "test.py"
    create_file(file_path, PYTHON_CODE)
    chunks = chunker.extract_chunks(str(file_path), "Python")
    types = {c['type'] for c in chunks}
    names = {c['name'] for c in chunks}
    assert "class" in types
    assert "function" in types
    assert "MyClass" in names
    assert "my_function" in names

def test_extract_python_chunks_syntax_error(tmp_path):
    file_path = tmp_path / "bad.py"
    create_file(file_path, "def broken(:\n    pass")
    chunks = chunker.extract_chunks(str(file_path), "Python")
    assert chunks == []

def test_extract_treesitter_chunks_placeholder(tmp_path):
    file_path = tmp_path / "test.js"
    create_file(file_path, GENERIC_CODE)
    chunks = chunker.extract_chunks(str(file_path), "JavaScript")
    assert chunks == []

def test_extract_generic_chunks(tmp_path):
    file_path = tmp_path / "test.unknown"
    create_file(file_path, GENERIC_CODE)
    chunks = chunker.extract_chunks(str(file_path), "UnknownLang")
    assert len(chunks) == 1
    assert chunks[0]['type'] == 'generic'
    print("Actual name: ", chunks[0]['name'])
    assert chunks[0]['name'] == "chunk_0"
    assert GENERIC_CODE.strip() in chunks[0]['code']
    
def test_extract_multiple_python_chunks(tmp_path):
    file_path = tmp_path/"multi.py"
    create_file(file_path, MULTI_CODE)
    chunks = chunker.extract_chunks(str(file_path), "Python")
    types = [c['type'] for c in chunks]
    names = [c['name'] for c in chunks]
    assert types.count("class") == 2
    assert types.count("function") == 2
    assert "First" in names
    assert "Second" in names
    assert "func_one" in names
    assert "func_two" in names
    
def test_extract_empty_file(tmp_path):
    file_path = tmp_path/"empty.py"
    create_file(file_path, "")
    chunks = chunker.extract_chunks(str(file_path), "Python")
    assert chunks == []