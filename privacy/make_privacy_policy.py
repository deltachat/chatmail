import configparser
import os
from pathlib import Path
import markdown


def main():
    basedir = Path(__name__).parent.resolve()

    template = basedir.joinpath("privacy-policy.md")
    inipath = template.parent.joinpath(template.stem + ".ini")
    assert os.path.exists(template), template
    assert os.path.exists(inipath), inipath

    parser = configparser.ConfigParser()
    parser.read(inipath)
    privacy_settings = {
        key: value.strip() for (key, value) in parser["privacy"].items()
    }
    template_content = open(template).read()
    html = markdown.markdown(template_content)

    html_name = template.with_suffix(".html.j2").name
    html_path = basedir.joinpath("../www/default").joinpath(html_name).resolve()

    with open(html_path, "w") as f:
        f.write(html)
    print(f"wrote {html_path}")


if __name__ == "__main__":
    main()
