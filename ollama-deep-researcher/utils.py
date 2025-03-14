from typing import Dict, List


def remove_duplicates(data: Dict) -> List:
    return list({item["url"] for item in data.get("results", [])})


def get_content_from(data: Dict, using: List) -> str:
    result = []
    filtered_data = list(filter(lambda x: x["url"] in using, data["results"]))
    for data in filtered_data:
        result.append(
            f"Title: {data['title']} - Url: {data['url']} - Content: {data['content']}"
        )
    return "".join(result)
