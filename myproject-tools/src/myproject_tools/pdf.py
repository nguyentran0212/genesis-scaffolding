from pathlib import Path

import pymupdf4llm


def convert_pdf_to_markdown(
    pdf_path: Path, output_dir: Path | None = None, prune_references: bool = True
) -> str:
    """
    Converts a PDF (like an ArXiv paper) to Markdown text.

    Args:
        pdf_path: Path to the local PDF file.
        output_dir: Optional directory to save the .md file.

    Returns:
        str: The converted Markdown content.
    """
    try:
        # Convert the PDF to Markdown text
        # write_images=False keeps it lightweight; set to True if you want the figures.
        md_text = pymupdf4llm.to_markdown(str(pdf_path), write_images=False)

        # Ensure md_text is a string (handle list-return edge case)
        if isinstance(md_text, list):
            md_text = "\n".join(
                [page.get("text", "") if isinstance(page, dict) else str(page) for page in md_text]
            )

        # ArXiv Specific Pruning: Stop at References
        # Agents rarely need the full bibliography for immediate reasoning.
        if prune_references:
            # Common headers in ArXiv papers
            for header in ["## References", "## BIBLIOGRAPHY", "## Acknowledgments", "**References**"]:
                if header in md_text:
                    md_text = (
                        md_text.split(header)[0]
                        + f"\n\n(Note: {header} and subsequent content pruned for brevity.)"
                    )
                    break

        # Optionally save to disk
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            md_filename = pdf_path.stem + ".md"
            with open(output_dir / md_filename, "w", encoding="utf-8") as f:
                f.write(md_text)
            print(output_dir / md_filename)

        return md_text

    except Exception as e:
        print(f"Failed to convert {pdf_path}: {e}")
        return ""


def main():
    convert_pdf_to_markdown(
        Path("/home/gentran/Documents/myproject/inbox/2505.08588v1.pdf"), output_dir=Path("./inbox")
    )


if __name__ == "__main__":
    main()
