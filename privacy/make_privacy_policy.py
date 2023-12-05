import configparser
import os
import markdown

def main():
    basename = "privacy-policy"
    template = basename + ".md"
    inipath = basename + ".ini"
    assert os.path.exists(template), template
    assert os.path.exists(inipath), inipath

    parser = configparser.ConfigParser()
    parser.read(inipath)
    privacy_settings = {key: value.strip() for (key, value) in parser["privacy"].items()}
    template_content = open(template).read()
    content = template_content.format(**privacy_settings)
    html = markdown.markdown(content)

    html_path = basename + ".html"
    with open(html_path, "w") as f:
        f.write(html)
        print(f"wrote {html_path}")

if __name__ == "__main__":
    main()
