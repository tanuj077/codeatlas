import pytest
from app.services import crawler

def create_file(path, content="print('hello')"):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def test_collect_code_files_basic(tmp_path):
    file_path = tmp_path / "test.py"
    create_file(file_path)
    files = crawler.collect_code_files(str(tmp_path))
    assert len(files) == 1
    assert files[0][0].endswith("test.py")
    assert files[0][1] == "Python"

def test_collect_code_files_exclude_dirs(tmp_path):
    excluded_dir = tmp_path / ".git"
    excluded_dir.mkdir()
    file_path = excluded_dir / "test.py"
    create_file(file_path)
    files = crawler.collect_code_files(str(tmp_path))
    assert all(".git" not in f[0] for f in files)

def test_collect_code_files_max_file_size(tmp_path):
    file_path = tmp_path / "big.py"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("a" * (crawler.MAX_FILE_SIZE + 1))
    files = crawler.collect_code_files(str(tmp_path))
    assert not files  # Should be excluded

def test_collect_code_files_skip_hidden(tmp_path):
    file_path = tmp_path / ".hidden.py"
    create_file(file_path)
    files = crawler.collect_code_files(str(tmp_path), skip_hidden=True)
    assert not files

def test_collect_code_files_symlink(tmp_path):
    real_file = tmp_path / "real.py"
    create_file(real_file)
    symlink = tmp_path / "link.py"
    symlink.symlink_to(real_file)
    files = crawler.collect_code_files(str(tmp_path))
    assert any(f[0].endswith("real.py") for f in files)
    assert not any(f[0].endswith("link.py") for f in files)

def test_collect_code_files_invalid_root():
    with pytest.raises(ValueError):
        crawler.collect_code_files("/invalid/path/doesnotexist")

def test_collect_code_files_path_traversal(tmp_path):
    # Create a file outside the root
    outside_dir = tmp_path.parent
    outside_file = outside_dir / "outside.py"
    with open(outside_file, "w", encoding="utf-8") as f:
        f.write("print('should not be found')")

    # Create a symlink inside the root pointing to the outside file
    symlink = tmp_path / "evil_link.py"
    symlink.symlink_to(outside_file)

    files = crawler.collect_code_files(str(tmp_path))
    # The symlink should not be followed/collected
    assert not any("evil_link.py" in f[0] for f in files)
    assert not any("outside.py" in f[0] for f in files)