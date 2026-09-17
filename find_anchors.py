from bs4 import BeautifulSoup

with open("page_source.html", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "lxml")

with open("anchors_out.txt", "w", encoding="utf-8") as out:
    for tag in soup.find_all("a", class_="btn_pop"):
        out.write(f"{tag.attrs} | {tag.get_text(strip=True)}\n")
        parent = tag.parent
        out.write(f"  parent: {parent.name} {parent.attrs}\n")

