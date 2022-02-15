# coding=utf-8
import json
import os
from typing import List, Dict, Union

from requests import get
from lxml import etree
import html

REPLACE_DIR = "assets"
DOC_HOST = "https://hex-rays.com/wp-content/static/products/ida/support/idapython_docs"
ROOT_PATH = r"idapython_docs\html"


def format_uri(name: str):
    return "{host}/{path}".format(host=DOC_HOST, path=name)


def get_all_href(_elements: List[etree.ElementBase]):
    return [element.get("href") for element in _elements]


def get_utool_preload_doc(_all_page_info, folder_path=""):
    all_in_one = []
    for page_info in _all_page_info:
        name = page_info["path"]
        tmp = [{"t": t["name"], "p": os.path.join(folder_path, name + t["href"]), "d": ""} for t in
               page_info["globals"]]
        all_in_one.extend(tmp)

    return all_in_one


def get_all_page_globals(_paths: List[str]):
    all_page_info = []
    for p in _paths:
        url = format_uri(p)
        content = get(url=url).text
        parser = etree.HTML(content)
        li_arr = parser.xpath('/html/body/main/nav/ul/li[position()]')
        pageInfo = {"path": p, "globals": []}
        for li in li_arr:
            pageInfo["globals"].extend([{"name": co.text, "href": co.get("href")} for co in li.xpath("ul/li//a")])
        all_page_info.append(pageInfo)

    return all_page_info


def delete_attr(_l):
    remove_proc = ["crossorigin", "integrity"]
    procs = _l.keys()
    for remove in remove_proc:
        if remove in procs:
            del _l.attrib[remove]


def remove_tag(_tags):
    if len(_tags) > 0:
        for i in _tags:
            i.getparent().remove(i)


def replace_path(_l, _attr: str):
    _l.set(_attr, REPLACE_DIR + "/" + _l.get(_attr).split("/")[-1])


def get_indexes(save_dir: str):
    info = get_all_page_globals(page_arr)
    rest = get_utool_preload_doc(info, folder_path="html")
    open(os.path.join(save_dir, "indexes.json"), "w").write(json.dumps(rest))


def get_html_alias(save_dir: str):
    # generate html
    abs_replace_dir = os.path.join(save_dir, REPLACE_DIR)
    try:
        os.makedirs(abs_replace_dir)
    except FileExistsError:
        pass

    # get all static assets
    static_assets = set()

    for page in page_arr:
        url = format_uri(page)
        content = get(url=url).content.decode("utf-8")
        parser = etree.HTML(content)

        # remove <nav> tag 'Search'
        nav = parser.xpath("/html/body/main/nav")
        remove_tag(nav)

        # remove <a> tag 'Module index'
        nav = parser.xpath("/html/body/main/article/a")
        remove_tag(nav)

        for _l in parser.xpath("//link"):
            href = _l.get("href")
            if href is not None:
                static_assets.add(href)
                replace_path(_l, "href")
            delete_attr(_l)

        for _l in parser.xpath("//script"):
            src = _l.get("src")
            if src is not None:
                static_assets.add(src)
                replace_path(_l, "src")
            delete_attr(_l)

        # TODO: I cannot have better way to transfer '\2002'
        source = etree.tostring(parser.page).decode("utf-8")
        source = source.replace(r"li:after{content:',&#128;2'}", r"li:after{content: ',\2002'}")

        open(os.path.join(save_dir, page), "w").write(html.escape(source))
        print("save file {}".format(page))

    for url in static_assets:
        content = get(url=url).text
        open(os.path.join(abs_replace_dir, url.split("/")[-1]), "w", encoding="utf-8").write(content)

    print("all ok!")


res = get(url=format_uri("index.html"))
elements = etree.HTML(res.text).xpath("/html/body/main/article/ul/li//a")
page_arr = get_all_href(elements)
print(page_arr)

get_html_alias(ROOT_PATH)
get_indexes(ROOT_PATH)

