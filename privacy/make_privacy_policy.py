import configparser
import os
from pathlib import Path
import markdown

def get_privacy_settings(inipath):
    parser = configparser.ConfigParser()
    parser.read(inipath)
    inipath = inipath.relative_to(os.getcwd())
    privacy_settings = {
        key: value.strip() for (key, value) in parser["privacy"].items()
    }
    privacy_domain = privacy_settings["privacy_domain"]
    if privacy_domain != "testrun.org" and not privacy_domain.endswith(".testrun.org"):
        for value in privacy_settings.values():
            value = value.lower()
            if "merlinux" in value or "schmieder" in value or "@testrun.org" in value:
                raise SystemExit(f"please set your own privacy contacts/addresses in {inipath}")

def main():
    basedir = Path(__name__).parent.resolve()

    template = basedir.joinpath("privacy-policy.md")
    inipath = template.parent.joinpath(template.stem + ".ini")
    assert os.path.exists(template), template
    assert os.path.exists(inipath), inipath

    privacy_settings = get_privacy_settings(inipath)
    template_content = open(template).read()
    html = markdown.markdown(template_content)

    html_name = template.with_suffix(".html.j2").name
    html_path = basedir.joinpath("../www/default").joinpath(html_name).resolve()

    with open(html_path, "w") as f:
        f.write(html)
    print(f"wrote {html_path}")


if __name__ == "__main__":
    main()
