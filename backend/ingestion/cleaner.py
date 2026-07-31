import re
import unicodedata

class TextCleaner:
    """Sanitizes and cleans raw extracted text before chunking."""

    @staticmethod
    def clean(text: str) -> str:
        if not text:
            return ""
        
        # Normalize unicode characters
        text = unicodedata.normalize("NFKC", text)

        # Remove control characters except newlines and tabs
        text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C" or ch in ("\n", "\r", "\t"))

        # Replace carriage returns with standard newlines
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Collapse horizontal whitespace (spaces, tabs) into a single space per line
        lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.split("\n")]

        # Collapse more than 3 consecutive newlines into 2
        cleaned_text = "\n".join(lines)
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)

        return cleaned_text.strip()
