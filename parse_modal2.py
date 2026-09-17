from bs4 import BeautifulSoup

with open("page_source_modal.html", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "lxml")

out = []
import re
for tag in soup.find_all(string=re.compile(r"서울")):
    el = tag.parent
    out.append(f"text={tag.strip()!r} tag={el.name} attrs={el.attrs} parent={el.parent.name} parentattrs={el.parent.attrs}")

with open("modal_out2.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
