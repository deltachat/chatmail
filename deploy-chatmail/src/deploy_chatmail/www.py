import importlib.resources
import webbrowser
import hashlib
import time

import markdown
from jinja2 import Template
from .genqr import gen_qr_png_data
from deploy_chatmail import get_ini_settings


def snapshot_dir_stats(somedir):
    d = {}
    for path in somedir.iterdir():
        if path.is_file() and path.name[0] != "." and path.suffix != ".swp":
            mtime = path.stat().st_mtime
            hash = hashlib.md5(path.read_bytes()).hexdigest()
            d[path] = (mtime, hash)
    return d


def prepare_template(source):
    assert source.exists(), source
    render_vars = {}
    render_vars["pagename"] = "home" if source.stem == "index" else source.stem
    render_vars["markdown_html"] = markdown.markdown(source.read_text())
    page_layout = source.with_name("page-layout.html").read_text()
    return render_vars, page_layout


def build_webpages(src_dir, build_dir, config):
    mail_domain = config["mail_domain"]
    assert src_dir.exists(), src_dir
    if not build_dir.exists():
        build_dir.mkdir()

    qr_path = build_dir.joinpath(f"qr-chatmail-invite-{mail_domain}.png")
    qr_path.write_bytes(gen_qr_png_data(mail_domain).read())

    for path in src_dir.iterdir():
        if path.suffix == ".md":
            render_vars, content = prepare_template(path)
            target = build_dir.joinpath(path.stem + ".html")

            # recursive jinja2 rendering
            while 1:
                new = Template(content).render(config=config, **render_vars)
                if new == content:
                    break
                content = new

            with target.open("w") as f:
                f.write(content)
        elif path.name != "page-layout.html":
            target = build_dir.joinpath(path.name)
            target.write_bytes(path.read_bytes())
    return build_dir


def main():
    path = importlib.resources.files(__package__)
    reporoot = path.joinpath("../../../").resolve()
    inipath = reporoot.joinpath("chatmail.ini")
    config = get_ini_settings("example.testrun.org", inipath)
    www_path = reporoot.joinpath("www")
    src_path = www_path.joinpath("src")
    stats = snapshot_dir_stats(src_path)
    build_dir = www_path.joinpath("build")
    src_dir = www_path.joinpath("src")
    build_webpages(src_dir, build_dir, config)
    index_path = build_dir.joinpath("index.html")
    webbrowser.open(str(index_path))
    print(f"started webbrowser-window for f{index_path}")

    print(f"watching {src_path} directory for changes")
    count = 0
    while 1:
        newstats = snapshot_dir_stats(src_path)
        if newstats == stats and count < 60:
            count += 1
            time.sleep(1.0)
            continue
        for key in newstats:
            if stats[key] != newstats[key]:
                print(f"*** CHANGED: {key}")

        stats = newstats
        build_webpages(src_dir, build_dir, config)
        print(f"regenerated web pages at: {index_path}")
        count = 0


if __name__ == "__main__":
    main()
