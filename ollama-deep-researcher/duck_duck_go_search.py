from typing import Dict, List
from duckduckgo_search import DDGS


def execute(
    query: str, max_results: int = 3, fetch_full_page: bool = False
) -> Dict[str, List[Dict[str, str]]]:
    try:
        with DDGS() as ddgs:
            results = []
            search_results = list(ddgs.text(query, max_results=max_results))
            for r in search_results:
                url = r.get("href")
                title = r.get("title")
                content = r.get("body")

                if not all([url, title, content]):
                    print(f"Warning: Incomplete result from DuckDuckGo: {r}")
                    continue

                raw_content = content
                if fetch_full_page:
                    try:
                        import urllib.request
                        from bs4 import BeautifulSoup

                        response = urllib.request.urlopen(url)
                        html = response.read()
                        soup = BeautifulSoup(html, "html.parser")
                        raw_content = soup.get_text()

                    except Exception as e:
                        print(
                            f"Warning: Failed to fetch full page content for {url}: {str(e)}"
                        )

                result = {
                    "title": title,
                    "url": url,
                    "content": content,
                    "raw_content": raw_content,
                }
                results.append(result)

            return {"results": results}
    except Exception as e:
        print(f"Error in DuckDuckGo search: {str(e)}")
        print(f"Full error details: {type(e).__name__}")
        return {"results": []}
