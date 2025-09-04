import os
from app.core.logger import logger

# Directories to exclude
EXCLUDE_DIRS = {'.git', '__pycache__', 'node_modules', 'venv', '.idea', '.vscode'}

# Max file size (bytes)
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

# File extensions mapped to languages
EXTENSION_LANGUAGE_MAP = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.java': 'Java',
    '.ts': 'TypeScript',
    '.cpp': 'C++',
    '.c': 'C',
    '.go': 'Go'
}

def is_text_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            f.read(1024)
        return True
    except Exception:
        return False

def collect_code_files(root_dir, extensions=None, verbose=False, skip_hidden=True):
    """
    Crawl the directory and collect source code files.

    Args:
        root_dir (str): Path to the codebase root
        extensions (set): Allowed extensions, defaults to EXTENSION_LANGUAGE_MAP
        verbose (bool): Print collected files
        skip_hidden (bool): Skip hidden files and directories

    Returns:
        list of tuples: (full_path, language)
    """
    # Sanitize and validate root_dir
    root_dir = os.path.abspath(root_dir)
    if not os.path.isdir(root_dir):
        raise ValueError("Invalid root directory")

    if extensions is None:
        extensions = set(EXTENSION_LANGUAGE_MAP.keys())

    code_files = []

    for dirpath, dirnames, filenames in os.walk(root_dir, followlinks=False):
        dirpath = os.path.abspath(dirpath)
        # Prevent path traversal: ensure dirpath is within root_dir
        if not dirpath.startswith(root_dir):
            logger.warning(f"Path traversal attempt detected: {dirpath}")
            continue

        # Exclude unwanted and hidden directories
        dirnames[:] = [
            d for d in dirnames
            if d not in EXCLUDE_DIRS and (not skip_hidden or not d.startswith('.'))
        ]

        for file in filenames:
            if skip_hidden and file.startswith('.'):
                continue
            ext = os.path.splitext(file)[1].lower()
            if ext in extensions:
                full_path = os.path.abspath(os.path.join(dirpath, file))
                # Prevent path traversal: ensure full_path is within root_dir
                if not full_path.startswith(root_dir):
                    logger.warning(f"Path traversal attempt detected: {full_path}")
                    continue
                # Skip symlinks
                if os.path.islink(full_path):
                    continue
                try:
                    if os.path.getsize(full_path) <= MAX_FILE_SIZE and is_text_file(full_path):
                        language = EXTENSION_LANGUAGE_MAP.get(ext, 'Unknown')
                        code_files.append((full_path, language))
                        if verbose:
                            logger.info(f"Collected: {full_path} [{language}]")
                except Exception as e:
                    logger.warning(f"Skipped {full_path}: {e}")

    logger.info(f"Total files collected: {len(code_files)}")
    return code_files
