"""The references image lists every source from the README."""

import re

from PIL import Image

from budget_compare import OUTPUT_DIR, PROJECT_ROOT
from budget_compare.references import parse_sources, wrap_url


def test_every_readme_source_is_parsed() -> None:
    """All numbered source links in the README make it into the image, in order."""
    section = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8").split("## Sources", 1)[1].split("\n## ", 1)[0]
    readme_urls = re.findall(r"<(https?://\S+)>", section)
    parsed = [item for _, items in parse_sources() for item in items]
    assert [url for _, _, url in parsed] == readme_urls
    assert [int(num) for num, _, _ in parsed] == list(range(1, len(readme_urls) + 1))


def test_wrapped_urls_rejoin_exactly() -> None:
    """Wrapping a URL never drops or alters characters."""
    for _, items in parse_sources():
        for _, _, url in items:
            assert "".join(wrap_url(url)) == url


def test_reference_images_exist() -> None:
    """White and transparent reference PNGs are written at 300 DPI."""
    for name, alpha in (("references.png", 255), ("references_transparent.png", 0)):
        with Image.open(OUTPUT_DIR / name) as im:
            assert round(im.info["dpi"][0]) >= 300
            assert im.convert("RGBA").getpixel((2, 2))[3] == alpha
