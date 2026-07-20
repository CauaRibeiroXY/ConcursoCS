def file_to_markdown(path: str) -> str:
    """Convert any supported file (PDF, DOCX, HTML...) to Markdown via markitdown."""
    try:
        from markitdown import MarkItDown

        return MarkItDown().convert(path).text_content
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Falha ao converter o arquivo com markitdown: {exc}")
