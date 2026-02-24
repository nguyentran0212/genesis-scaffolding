import re
import tarfile
import zipfile
from pathlib import Path

import arxiv
import httpx

from .pdf import convert_pdf_to_markdown


def _format_result(
    result: arxiv.Result,
    pdf_path: Path | None = None,
    md_path: Path | None = None,
    source_path: Path | None = None,
) -> dict:
    """Helper to standardize paper metadata output."""
    return {
        "entry_id": result.entry_id,
        "short_id": result.entry_id.split("/")[-1],
        "title": result.title,
        "authors": [author.name for author in result.authors],
        "summary": result.summary,
        "published": result.published.strftime("%Y-%m-%d"),
        "updated": result.updated.strftime("%Y-%m-%d"),
        "journal_ref": result.journal_ref,
        "doi": result.doi,
        "primary_category": result.primary_category,
        "categories": result.categories,
        "pdf_url": result.pdf_url,
        "links": [{"title": link.title, "url": link.href} for link in result.links] if result.links else [],
        "pdf_path": pdf_path,
        "md_path": md_path,
        "source_path": source_path,
    }


def download_paper_pdf(paper_id: str, download_dir: Path, convert_to_markdown: bool = True) -> Path | None:
    """
    Directly download the PDF of a specific paper by its arXiv ID without using the search client.

    Args:
        paper_id (str): arXiv ID of the paper (e.g. "2107.05580").
        download_dir (Path): Base directory for storage.

    Returns:
        Path | None: Path to the downloaded PDF, or None if the download failed.
    """
    # Predictable direct PDF URL
    url = f"https://arxiv.org/pdf/{paper_id}.pdf"

    # Create a specific folder for the paper or save directly to download_dir
    # Usually better to keep the PDF name clean
    pdf_path = download_dir / f"{paper_id}.pdf"

    try:
        download_dir.mkdir(parents=True, exist_ok=True)

        with httpx.stream("GET", url, follow_redirects=True) as response:
            # ArXiv returns 403 or 404 if the ID is wrong or access is blocked
            response.raise_for_status()

            with open(pdf_path, "wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)

        convert_pdf_to_markdown(pdf_path=pdf_path, output_dir=download_dir)

        return pdf_path

    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e.response.status_code} for ID {paper_id}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def download_paper_source(paper_id: str, download_dir: Path) -> Path | None:
    """
    Download the LaTeX source of a specific paper by its arXiv ID.

    Args:
        paper_id (str): arXiv ID of the paper (e.g. "2107.05580" or "quant-ph/0201082v1")
        download_dir (Optional[str]): Directory to download the source to. If None, uses AI/tmp/arxiv/paper_id/

    Returns:
        Path | None: Path to the extracted source folder, or empty if cannot download
    """
    # Direct e-print URL
    url = f"https://arxiv.org/e-print/{paper_id}"
    tarballs_path = download_dir / "tarballs"
    tarballs_path.mkdir(parents=True, exist_ok=True)
    archive_path = download_dir / "tarballs" / f"{paper_id}.tar.gz"

    with httpx.stream("GET", url, follow_redirects=True) as response:
        response.raise_for_status()
        with open(archive_path, "wb") as f:
            for chunk in response.iter_bytes():
                f.write(chunk)

    source_dir = download_dir / paper_id
    source_dir.mkdir(exist_ok=True)
    # Better extraction logic
    try:
        if tarfile.is_tarfile(archive_path):
            with tarfile.open(archive_path) as tar:
                tar.extractall(path=source_dir, filter="data")
        elif zipfile.is_zipfile(archive_path):
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                zip_ref.extractall(source_dir)
        return source_dir
    except Exception as e:
        print(f"Extraction failed: {e}")
        return


def extract_arxiv_id(input_str: str) -> str:
    """
    Extracts an arXiv ID from a URL or a string.
    Supports:
    - Modern IDs: 2301.12345, 0704.0001
    - Legacy IDs: hep-th/9901001, math.CO/0101001
    - URLs: https://arxiv.org/abs/2301.12345, https://arxiv.org/pdf/2301.12345.pdf
    - Prefixes: arXiv:2301.12345
    """
    # Pattern for modern IDs (YYMM.NNNNN)
    modern_pattern = r"(\d{4}\.\d{4,5}(v\d+)?)"
    # Pattern for legacy IDs (subject/YYMMNNN)
    legacy_pattern = r"([a-z\-]+(?:\.[A-Z]{2})?/\d{7}(v\d+)?)"

    # Combined search for both patterns
    full_pattern = f"({modern_pattern}|{legacy_pattern})"
    match = re.search(full_pattern, input_str, re.IGNORECASE)

    if match:
        return match.group(0)

    # Fallback: if no pattern matches, return original (it might already be a clean ID)
    return input_str.strip()


def get_paper_details(
    paper_id: str,
    download_dir: Path | None = None,
    download_pdf: bool = False,
    download_source: bool = False,
) -> dict | None:
    """
    Get detailed information about a specific paper by its arXiv ID.
    Optimized to bypass the default library delays by using a custom Client.
    """

    # Parse paper ID
    parsed_paper_id: str | None = extract_arxiv_id(paper_id)

    try:
        # fetching a single specific resource.
        client = arxiv.Client(page_size=1, num_retries=3)

        search = arxiv.Search(id_list=[parsed_paper_id])

        # Use next() to get the first result immediately from the generator
        result = next(client.results(search))

        # Download PDF if requested
        pdf_path: Path | None = None
        md_path: Path | None = None
        if download_dir and download_pdf:
            try:
                # Extract paper ID from the result's entry_id
                parsed_paper_id = result.entry_id.split("/")[
                    -1
                ]  # Handle both arxiv IDs like "1234.56789" and "cs/1234567"
                pdf_path = download_paper_pdf(paper_id=parsed_paper_id, download_dir=download_dir)
                if not pdf_path:
                    raise Exception("Cannot download PDF")
                md_path = pdf_path.with_suffix(".md")
            except Exception:
                # Silently handle download errors to prevent interference with agent
                pass

        # Download source if requested
        source_path: Path | None = None
        if download_dir and download_source:
            try:
                # Extract paper ID from the result's entry_id
                parsed_paper_id = result.entry_id.split("/")[
                    -1
                ]  # Handle both arxiv IDs like "1234.56789" and "cs/1234567"
                source_path = download_paper_source(paper_id=parsed_paper_id, download_dir=download_dir)
            except Exception:
                # Silently handle download errors to prevent interference with agent
                pass

        return _format_result(result, pdf_path=pdf_path, md_path=md_path, source_path=source_path)

    except StopIteration:
        print(f"No paper found with ID: {parsed_paper_id}")
        return None
    except Exception as e:
        print(f"Error fetching details for {parsed_paper_id}: {e}")
        return None


def search_papers(
    query: str,
    max_results: int = 10,
    sort_by: str = "relevance",
    download_dir: Path | None = None,
    download_pdf: bool = False,
    download_source: bool = False,
) -> list[dict[str, str | list[str] | None]]:
    """
    Search for papers on arXiv based on a query, with optional download capabilities.

    Args:
        query (str): Search query string (e.g. "quantum computing", "machine learning")
        max_results (int): Maximum number of results to return (default: 10)
        sort_by (str): Sort by "relevance", "last_updated_date", or "submitted_date" (default: "relevance")
        download_pdf (bool): Whether to download PDFs of the papers (default: False)
        download_source (bool): Whether to download LaTeX source of the papers (default: False)

    Returns:
        List[Dict]: List of paper information dictionaries
    """
    # Map sort_by parameter to arXiv SortCriterion
    sort_mapping = {
        "relevance": arxiv.SortCriterion.Relevance,
        "last_updated_date": arxiv.SortCriterion.LastUpdatedDate,
        "submitted_date": arxiv.SortCriterion.SubmittedDate,
    }

    sort_criterion = sort_mapping.get(sort_by.lower(), arxiv.SortCriterion.Relevance)

    search = arxiv.Search(
        query=query, max_results=max_results, sort_by=sort_criterion, sort_order=arxiv.SortOrder.Descending
    )

    client = arxiv.Client(page_size=20, num_retries=2)

    results = []
    try:
        search_results = client.results(search)

        for i, result in enumerate(search_results):
            paper_info = _format_result(result=result)
            results.append(paper_info)

            # Download PDF if requested
            if download_dir and download_pdf:
                try:
                    # Extract paper ID from the result's entry_id
                    paper_id = result.entry_id.split("/")[
                        -1
                    ]  # Handle both arxiv IDs like "1234.56789" and "cs/1234567"
                    pdf_path = download_paper_pdf(paper_id=paper_id, download_dir=download_dir)
                except Exception:
                    # Silently handle download errors to prevent interference with agent
                    pass

            # Download source if requested
            if download_dir and download_source:
                try:
                    # Extract paper ID from the result's entry_id
                    paper_id = result.entry_id.split("/")[
                        -1
                    ]  # Handle both arxiv IDs like "1234.56789" and "cs/1234567"
                    source_path = download_paper_source(paper_id=paper_id, download_dir=download_dir)
                except Exception:
                    # Silently handle download errors to prevent interference with agent
                    pass

            # Stop if we've reached max_results
            if i + 1 >= max_results:
                break

    except Exception:
        # Return empty results instead of raising exception to prevent agent from switching to alternatives
        return []

    return results


def search_papers_with_downloads(
    query: str,
    max_results: int = 10,
    download_dir: Path | None = None,
) -> list[dict]:
    """
    Search papers and automatically trigger download/MD conversion for each.
    Returns a list of dicts where each dict contains metadata + 'pdf_path' + 'md_path'.
    """

    search = arxiv.Search(query=query, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance)
    client = arxiv.Client(num_retries=2)

    results = []
    # Process results one by one (Sequential)
    for result in client.results(search):
        paper_id = result.entry_id.split("/")[-1]

        # Use get_paper_details to handle the actual file heavy-lifting
        # This ensures we get the exact 'pdf_path' and 'md_path' generated
        details = get_paper_details(paper_id=paper_id, download_dir=download_dir, download_pdf=True)

        if details:
            # Combine original metadata with our local file paths
            # You can include title, summary, etc. from result here
            combined_info = {
                "id": paper_id,
                "title": result.title,
                "summary": result.summary,
                "pdf_path": details["pdf_path"],
                "md_path": details["md_path"],
            }
            results.append(combined_info)

        if len(results) >= max_results:
            break

    return results


def main():
    print("reached main")
    # output_path = download_paper_pdf(paper_id="2506.02153", download_dir=Path("./inbox"))
    # print(output_path)
    # paper_detail = get_paper_details(paper_id="2506.02153")
    # print(paper_detail)
    results = search_papers(
        "Small language model challenges", download_dir=Path("./inbox"), download_pdf=True, max_results=5
    )
    print(results)


if __name__ == "__main__":
    main()
