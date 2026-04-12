import re
from pathlib import Path
from typing import List, Tuple

from .schemas.models import JavaChunk, JavaChunkMetadata


class FileScanner:
    def __init__(self, root_dir: Path):
        self.root_dir = Path(root_dir).expanduser()

    def scan(self) -> List[Path]:
        src_dir = self.root_dir / "src"
        if not src_dir.exists():
            return []
        return list(src_dir.rglob("*.java"))


class Chunker:
    def __init__(self, threshold: int = 1000, max_chars: int = 6000):
        self.threshold = threshold
        self.max_chars = max_chars

    def chunk(self, file_path: str, content: str) -> List[JavaChunk]:
        # Approximate token count by word count
        approx_tokens = len(content.split())
        imports, sig, members = self._extract_context(content)
        metadata = JavaChunkMetadata(
            file_path=file_path,
            imports=imports,
            class_signature=sig,
            member_variables=members,
            chunk_type="full_file",
        )

        if approx_tokens < self.threshold and len(content) < self.max_chars:
            return [JavaChunk(content=content, metadata=metadata)]

        # Split by method (improved regex)
        # Matches typical method declarations including annotations and generics
        # Look for: [Annotations] [Modifiers] <Generics> ReturnType Name([Args]) [throws ...] {
        method_pattern = r"\n\s*(?:(?:@[\w\d(.,\s)]+)\s*)*(?:(?:public|private|protected|static|final|native|synchronized|abstract|transient|volatile|strictfp)\s+)*[\w<>[\]]+\s+\w+\s*\([^)]*\)\s*(?:throws\s+[\w\d.,\s]+)?\s*\{"
        
        parts = re.split(f"({method_pattern})", content)
        
        raw_chunks = []
        if len(parts) > 1:
            # First part is class header
            header = parts[0].strip()
            if header:
                raw_chunks.append((header, "header"))
            
            # parts[1::2] are the matched patterns (method signatures)
            # parts[2::2] are the contents between matches
            for i in range(1, len(parts), 2):
                sig_part = parts[i]
                body_part = parts[i+1] if i+1 < len(parts) else ""
                raw_chunks.append((sig_part + body_part, "method"))
        else:
            raw_chunks.append((content, "full_file"))

        final_chunks = []
        for text, ctype in raw_chunks:
            text = text.strip()
            if not text:
                continue
            
            if len(text) > self.max_chars:
                # Recursive fallback for very large chunks
                final_chunks.extend(self._recursive_split(text, metadata, ctype))
            else:
                chunk_metadata = metadata.model_copy()
                chunk_metadata.chunk_type = ctype
                final_chunks.append(JavaChunk(content=text, metadata=chunk_metadata))
        
        return final_chunks

    def _recursive_split(self, text: str, base_metadata: JavaChunkMetadata, original_type: str) -> List[JavaChunk]:
        chunks = []
        # Split by roughly max_chars, trying to break at newlines
        start = 0
        while start < len(text):
            end = start + self.max_chars
            if end >= len(text):
                chunk_text = text[start:]
                start = len(text)
            else:
                # Try to find last newline before max_chars
                last_newline = text.rfind("\n", start, end)
                if last_newline != -1 and last_newline > start + (self.max_chars // 2):
                    end = last_newline
                chunk_text = text[start:end].strip()
                start = end
            
            if chunk_text:
                metadata = base_metadata.model_copy()
                metadata.chunk_type = f"{original_type}_split"
                chunks.append(JavaChunk(content=chunk_text, metadata=metadata))
        return chunks

    def _extract_context(self, content: str) -> Tuple[str, str, str]:
        lines = content.splitlines()
        imports = "\n".join([line for line in lines if line.strip().startswith("import")])

        # Simple class signature extraction
        sig = ""
        for line in lines:
            if "class" in line and "{" in line:
                sig = line.split("{")[0].strip()
                break

        # Simple member variables extraction
        # (lines ending with ; inside class but outside methods)
        # This is a bit tricky with regex, so we just take lines that look like fields
        members = []
        for line in lines:
            if ";" in line and not any(
                kw in line for kw in ["import", "package", "return", "throw"]
            ):
                # Heuristic: must have access modifier
                if any(kw in line for kw in ["private", "protected", "public"]):
                    members.append(line.strip())


        return imports, sig, "\n".join(members)
