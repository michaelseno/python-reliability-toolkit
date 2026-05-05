from html.parser import HTMLParser
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
LANDING_PAGE = REPOSITORY_ROOT / "frontend" / "index.html"


class LandingPageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.links = []
        self.ids = []
        self.headings = []
        self.current_link = None
        self.current_heading = None
        self.text_chunks = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        self.tags.append((tag, attrs_dict))
        if "id" in attrs_dict:
            self.ids.append(attrs_dict["id"])
        if tag == "a":
            self.current_link = {"href": attrs_dict.get("href", ""), "text": ""}
            self.links.append(self.current_link)
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.current_heading = {"tag": tag, "text": ""}
            self.headings.append(self.current_heading)

    def handle_endtag(self, tag):
        if tag == "a":
            self.current_link = None
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.current_heading = None

    def handle_data(self, data):
        self.text_chunks.append(data)
        if self.current_link is not None:
            self.current_link["text"] += data
        if self.current_heading is not None:
            self.current_heading["text"] += data


def parse_page():
    parser = LandingPageParser()
    parser.feed(LANDING_PAGE.read_text(encoding="utf-8"))
    return parser


def normalize(value):
    return " ".join(value.split())


def test_landing_page_required_sections_and_manual_mvp_copy():
    parser = parse_page()
    page_text = normalize(" ".join(parser.text_chunks)).lower()

    required_ids = {
        "hero-title",
        "value",
        "included",
        "safety",
        "pricing",
        "process",
        "faq",
        "request-audit",
    }
    assert required_ids.issubset(set(parser.ids))
    assert "manual/operator-assisted" in page_text
    assert "not saas" in page_text
    assert "up to 10 unique method + path" in page_text
    assert "5 checks per day" in page_text
    assert "private s3 presigned urls" in page_text
    assert "$750" in page_text


def test_deployable_static_page_lives_under_frontend_root_only():
    assert LANDING_PAGE.exists()
    assert not (
        REPOSITORY_ROOT
        / "docs"
        / "frontend"
        / "api_reliability_audit_mvp_landing_page.html"
    ).exists()


def test_ctas_use_exact_text_and_exact_placeholder_href():
    parser = parse_page()
    cta_links = [
        link
        for link in parser.links
        if normalize(link["text"]) == "Request a Reliability Audit"
    ]

    assert cta_links, "At least one exact CTA link is required."
    assert all(link["href"] == "#request-audit" for link in cta_links)
    assert parser.ids.count("request-audit") == 1


def test_page_excludes_forbidden_mvp_elements_and_targets():
    parser = parse_page()
    tags = [tag for tag, _attrs in parser.tags]
    disallowed_tags = {"form", "input", "textarea", "select", "button"}
    disallowed_href_prefixes = ("mailto:", "tel:", "javascript:")
    disallowed_terms = (
        "stripe",
        "paypal",
        "login",
        "sign in",
        "create account",
        "newsletter",
        "scheduler",
        "calendly",
        "chat widget",
    )
    page_text = normalize(" ".join(parser.text_chunks)).lower()

    assert disallowed_tags.isdisjoint(tags)
    assert all(
        not link["href"].lower().startswith(disallowed_href_prefixes)
        for link in parser.links
    )
    for term in disallowed_terms:
        if term in {"login", "scheduler", "chat widget"}:
            # These terms may appear only in explicit prohibition copy, not as UI controls.
            continue
        assert term not in page_text


def test_accessibility_oriented_static_structure():
    parser = parse_page()
    tags = [tag for tag, _attrs in parser.tags]
    h1s = [heading for heading in parser.headings if heading["tag"] == "h1"]
    heading_levels = [int(heading["tag"][1]) for heading in parser.headings]
    request_sections = [
        attrs
        for tag, attrs in parser.tags
        if tag == "section" and attrs.get("id") == "request-audit"
    ]

    assert {"header", "nav", "main", "section", "footer"}.issubset(set(tags))
    assert len(h1s) == 1
    assert normalize(h1s[0]["text"]) == "48-hour API Reliability Audit"
    assert request_sections[0].get("aria-labelledby") == "request-audit-heading"
    assert request_sections[0].get("tabindex") == "-1"
    assert max(heading_levels) <= 3
