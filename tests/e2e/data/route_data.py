SMOKE_ROUTES = [
    "/",
    "/contact",
    "/auth/login",
    "/auth/register",
    "/auth/forgot-password",
    "/category/hand-tools",
    "/category/power-tools",
    "/category/other",
    "/category/special-tools",
    "/category/rentals",
]

HEADER_HREF_CASES = [
    ("[data-test='nav-home']", "/"),
    ("[data-test='nav-contact']", "/contact"),
    ("[data-test='nav-sign-in']", "/auth/login"),
    ("[data-test='nav-hand-tools']", "/category/hand-tools"),
    ("[data-test='nav-power-tools']", "/category/power-tools"),
    ("[data-test='nav-rentals']", "/rentals"),
]

HOME_CORE_SELECTORS = [
    "[data-test='language-select']",
    "[data-test='search-query']",
    "[data-test='search-submit']",
    "[data-test='sort']",
    "[data-test='nav-home']",
    "[data-test='nav-sign-in']",
]
