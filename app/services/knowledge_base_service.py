from pathlib import Path


class KnowledgeBaseService:
    def __init__(self, knowledge_base_dir: str = "knowledge_base"):
        self.knowledge_base_dir = Path(knowledge_base_dir)
        self.documents = self._load_documents()

    def _load_documents(self) -> list[dict]:
        documents = []
        if not self.knowledge_base_dir.exists():
            return documents

        for file_path in sorted(self.knowledge_base_dir.glob("*.md")):
            content = file_path.read_text(encoding="utf-8")
            documents.append(
                {
                    "document_id": file_path.stem,
                    "title": self._title_from_file(file_path),
                    "source_uri": file_path.as_posix(),
                    "content": content,
                    "keywords": self._keywords_for_file(file_path.name),
                }
            )
        return documents

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        query_lower = query.lower()
        scored_documents = []
        generic_query_words = {
            "does",
            "from",
            "have",
            "policy",
            "support",
            "that",
            "this",
            "what",
            "with",
            "your",
        }

        for document in self.documents:
            score = 0
            for keyword in document["keywords"]:
                if keyword in query_lower:
                    score += 3

            title_words = document["title"].lower().split()
            for word in title_words:
                if word not in generic_query_words and word in query_lower:
                    score += 2

            content_lower = document["content"].lower()
            for query_word in query_lower.split():
                cleaned_word = query_word.strip(".,?!:;()[]{}").lower()
                if (
                    len(cleaned_word) >= 4
                    and cleaned_word not in generic_query_words
                    and cleaned_word in content_lower
                ):
                    score += 1

            if score > 0:
                scored_documents.append(
                    {
                        **document,
                        "score": score,
                    }
                )

        scored_documents.sort(
            key=lambda item: item["score"],
            reverse=True,
        )
        return scored_documents[:top_k]

    def _title_from_file(self, file_path: Path) -> str:
        return file_path.stem.replace("_", " ").title()

    def _keywords_for_file(self, file_name: str) -> list[str]:
        if "refund" in file_name:
            return [
                "refund",
                "return",
                "damaged",
                "defective",
                "wrong item",
                "money back",
                "order never arrived",
            ]
        if "shipping" in file_name:
            return [
                "shipping",
                "delivery",
                "package",
                "arrive",
                "delayed",
                "expedited",
            ]
        if "account" in file_name:
            return [
                "account",
                "email",
                "login",
                "password",
                "settings",
                "ownership",
            ]
        return []
