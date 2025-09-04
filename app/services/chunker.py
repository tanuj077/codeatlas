import ast
from typing import List, Dict
from app.core.logger import logger
import tree_sitter_languages
from tree_sitter import Parser

SUPPORTED_TREE_SITTER_LANGS = {"javascript": "javascript", "typescript": "typescript", "java": "java", "go": "go", "c": "c", "cpp": "cpp"}  # Mapped to tree-sitter names

def extract_chunks(file_path: str, language: str) -> List[Dict]:
    """
    Dispatch to language-specific chunking functions with added overlapping and summaries for better retrieval.
    """
    chunks = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()

        if language.lower() == "python":
            chunks = extract_python_chunks(source, file_path)
        elif language.lower() in SUPPORTED_TREE_SITTER_LANGS:
            chunks = extract_treesitter_chunks(source, SUPPORTED_TREE_SITTER_LANGS[language.lower()], file_path)
        else:
            chunks = extract_generic_chunks(source, file_path)

        # Add summaries and overlapping for all chunks
        for chunk in chunks:
            chunk['summary'] = f"Summary: {chunk['type']} named {chunk['name']} in {file_path} (lines {chunk['start_line']}-{chunk['end_line']})"

        # Add overlapping overview chunk for larger files
        lines = source.splitlines()
        if len(lines) > 50:
            overview = '\n'.join(lines[:100])
            chunks.append({
                'code': overview,
                'type': 'overview',
                'name': file_path.split('/')[-1],
                'start_line': 1,
                'end_line': min(100, len(lines)),
                'summary': f"Overview of {file_path}"
            })

        logger.info(f"Extracted {len(chunks)} chunks from {file_path}")
        return chunks
    except Exception as e:
        logger.warning(f"Failed to chunk {file_path}: {e}")
        return []

def extract_python_chunks(source: str, file_path: str) -> List[Dict]:
    """
    Extract classes and functions from Python source using AST, with added line overlaps.
    """
    try:
        chunks = []
        tree = ast.parse(source, filename=file_path)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start_line = node.lineno
                end_line = getattr(node, "end_lineno", node.lineno)
                # Add overlap: include 5 lines before/after for context
                overlap_start = max(1, start_line - 5)
                overlap_end = min(len(source.splitlines()), end_line + 5)
                snippet = '\n'.join(source.splitlines()[overlap_start-1:overlap_end])
                chunks.append({
                    'code': snippet.strip(),
                    'type': 'class' if isinstance(node, ast.ClassDef) else 'function',
                    'name': node.name,
                    'start_line': overlap_start,
                    'end_line': overlap_end
                })
    except Exception as e:
        logger.warning(f"extract_python_chunks failed for {file_path}: {e}")
    return chunks

def extract_treesitter_chunks(source: str, language: str, file_path: str) -> List[Dict]:
    """
    Basic tree-sitter extraction for supported languages.
    """
    try:
        lang = tree_sitter_languages.get_language(language)
        parser = Parser()
        parser.set_language(lang)
        tree = parser.parse(bytes(source, "utf-8"))
        chunks = []
        # Simple traversal for functions/classes (expand as needed)
        for node in tree.root_node.children:
            if node.type in ['function_definition', 'class_definition', 'method_definition']:
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1
                snippet = source[node.start_byte:node.end_byte]
                chunks.append({
                    'code': snippet.strip(),
                    'type': 'class' if isinstance(node, ast.ClassDef) else 'function',
                    'name': node.name,
                    'start_line': start_line,  # Ensure comma after each pair except possibly the last
                    'end_line': end_line,      # Trailing comma is optional but recommended
            })
        return chunks
    except Exception as e:
        logger.warning(f"Tree-sitter failed for {file_path}: {e}")
        return extract_generic_chunks(source, file_path)  # Fallback

def extract_generic_chunks(source: str, file_path: str) -> List[Dict]:
    """
    Fallback: split into overlapping chunks of 100 lines.
    """
    lines = source.splitlines()
    chunk_size = 100
    chunks = []
    for i in range(0, len(lines), chunk_size // 2):
        chunk_lines = lines[i:i + chunk_size]
        chunks.append({
            'code': '\n'.join(chunk_lines).strip(),
            'type': 'generic',
            'name': f"chunk_{i}",
            'start_line': i + 1,
            'end_line': i + len(chunk_lines)
        })
    return chunks
