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
    def __init__(self, threshold: int = 1000):
        self.threshold = threshold

    def chunk(self, file_path: str, content: str) -> List[JavaChunk]:
        # Approximate token count by word count
        approx_tokens = len(content.split())

        imports, sig, members = self._extract_context(content)

        if approx_tokens < self.threshold:
            return [
                JavaChunk(
                    content=content,
                    metadata=JavaChunkMetadata(
                        file_path=file_path,
                        imports=imports,
                        class_signature=sig,
                        member_variables=members,
                        chunk_type="full_file",
                    ),
                )
            ]

        # Split by method (very simple regex)
        # Matches typical method declarations: [public|private|protected] [static] [final] <T> name(...) {
        methods = re.split(
            r"\n\s*(?:public|private|protected|static|\s)+\s+[\w<>[\]]+\s+\w+\s*\([^)]*\)\s*\{",
            content,
        )

        chunks = []
        # First part is usually class header/members
        for m in methods:
            if not m.strip():
                continue
            chunks.append(
                JavaChunk(
                    content=m.strip(),
                    metadata=JavaChunkMetadata(
                        file_path=file_path,
                        imports=imports,
                        class_signature=sig,
                        member_variables=members,
                        chunk_type="method",
                    ),
                )
            )
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
