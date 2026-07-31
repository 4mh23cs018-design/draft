from typing import List, Dict, Any

class RecursiveChunker:
    """Recursively splits document text into overlapping chunks based on logical separators."""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: List[str] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = min(chunk_overlap, chunk_size - 1) if chunk_size > 1 else 0
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """Recursive helper function to split text into pieces under chunk_size."""
        if not text:
            return []
        
        if len(text) <= self.chunk_size:
            return [text]

        # If no separators remain, do hard character-level splitting
        if not separators:
            return [text[i:i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]

        separator = separators[-1]
        new_separators = []

        for i, s in enumerate(separators):
            if s == "":
                separator = ""
                break
            if s in text:
                separator = s
                new_separators = separators[i + 1:]
                break

        if separator:
            splits = text.split(separator)
        else:
            # Fallback character level split
            splits = list(text)

        final_chunks = []
        good_splits = []

        for split in splits:
            if len(split) < self.chunk_size:
                good_splits.append(split)
            else:
                if good_splits:
                    merged = separator.join(good_splits)
                    final_chunks.extend(self._split_text(merged, new_separators))
                    good_splits = []
                final_chunks.extend(self._split_text(split, new_separators))

        if good_splits:
            merged = separator.join(good_splits)
            final_chunks.extend(self._split_text(merged, new_separators))

        return final_chunks

    def chunk_pages(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Chunks text while retaining page numbers and generating chunk metadata.
        pages: list of dicts with {"page_number": int, "text": str}
        """
        chunks: List[Dict[str, Any]] = []
        global_chunk_idx = 0

        for page in pages:
            page_num = page.get("page_number", 1)
            page_text = page.get("text", "").strip()
            if not page_text:
                continue

            raw_splits = self._split_text(page_text, self.separators)

            # Combine splits into overlapping chunks up to chunk_size
            current_chunk = []
            current_len = 0

            for piece in raw_splits:
                piece_len = len(piece)
                if current_len + piece_len > self.chunk_size and current_chunk:
                    chunk_str = " ".join(current_chunk).strip()
                    if chunk_str:
                        chunks.append({
                            "chunk_index": global_chunk_idx,
                            "page_number": page_num,
                            "content": chunk_str
                        })
                        global_chunk_idx += 1

                    # Keep overlap from end of previous chunk
                    overlap_len = 0
                    overlap_pieces = []
                    for prev_piece in reversed(current_chunk):
                        if overlap_len + len(prev_piece) <= self.chunk_overlap:
                            overlap_pieces.insert(0, prev_piece)
                            overlap_len += len(prev_piece)
                        else:
                            break

                    current_chunk = overlap_pieces
                    current_len = sum(len(p) for p in current_chunk)

                current_chunk.append(piece)
                current_len += piece_len

            if current_chunk:
                chunk_str = " ".join(current_chunk).strip()
                if chunk_str:
                    chunks.append({
                        "chunk_index": global_chunk_idx,
                        "page_number": page_num,
                        "content": chunk_str
                    })
                    global_chunk_idx += 1

        return chunks
