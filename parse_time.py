from bs4 import BeautifulSoup

with open("page_source_after_day.html", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "lxml")

out = []
time_header = soup.find(string=lambda s: s and "시간선택" in s)
if time_header:
    container = time_header.parent
    for _ in range(3):
        container = container.parent
    out.append(f"container: {container.name} {container.attrs}")
    for tag in container.find_all(["a", "button"]):
        out.append(f"  {tag.name} {tag.attrs} | {tag.get_text(strip=True)!r}")

with open("time_out.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
