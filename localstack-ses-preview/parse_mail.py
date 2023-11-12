import json
import tempfile
from email import policy
from email.parser import BytesParser
from pathlib import Path

import requests

BASE_PATH = Path(__file__).parents[1]


class SesMailContent:
    def __init__(self, **kwds) -> None:
        self.id = kwds.get("id")
        self.date = kwds.get("date")
        self.to = kwds.get("to")
        self.subject = kwds.get("subject")
        self.body = kwds.get("body")

    def print_as_html(self, fp) -> None:
        fp.write(
            """
<div>
    MailId: {id}<br>
    Date: {date}<br>
    To: {to}<br>
    Subject: {subject}
</div>
""".format(
                id=self.id, date=self.date, to=self.to, subject=self.subject
            )
        )
        fp.write("<div style='border: solid 1px #ccc; padding: 12px'>")
        fp.write(self.body)
        fp.write("</div>\n")
        delete_url = f"http://localhost:4566/_localstack/ses?{self.id}"
        fp.write(f"<p>curl -X DELETE '{delete_url}'</p><br>\n")


def _byteparse(message):
    contents = []
    with tempfile.TemporaryFile() as fp:
        fp.write(message.get("RawData").encode())
        fp.seek(0)
        msg = BytesParser(policy=policy.default).parse(fp)
        simplest = msg.get_body(preferencelist=("plain", "html"))
        contents.append(
            SesMailContent(
                id=message.get("Id"),
                date=msg["Date"],
                to=msg["To"],
                subject=msg["Subject"],
                body="".join(simplest.get_content().splitlines(keepends=True)[:]),
            )
        )

    with open(
        f"{BASE_PATH}/localstack-ses-preview/index.html", "a+", encoding="'utf-8'"
    ) as fp:
        for content in contents:
            content.print_as_html(fp)


def execute():
    res = requests.get("http://localhost:4566/_localstack/ses/")
    res.raise_for_status()

    content = json.loads(res.content)
    for message in content.get("messages"):
        _byteparse(message)

# pipenv run python ./localstack-ses-preview/parse_mail.py
if __name__ == "__main__":
    execute()


"""

https://docs.python.org/ja/3/library/tempfile.html
https://docs.python.org/ja/3.11/library/email.examples.html

- [日本語メールの仕組み](https://sendgrid.kke.co.jp/blog/?p=10958)
- [メールのデコード処理の流れ](https://qiita.com/takey/items/13a3dee5d78d364dd55c)
- [MIMEエンコードされたメールのデコード方法](https://qiita.com/sheepland/items/2065ffcc7ec8c03145cc)
- [E-Mailあれこれ。E-Mailをパースしてみる。](https://emotionexplorer.blog.fc2.com/blog-entry-427.html)

SES API response example.
{
  "messages": [
    {
      "Id": "ilsrgudcubkjgzvr-vufnipdr-yrsm-rhrd-gwyu-kjaqndqjbuiz-oqsmoj",
      "Region": "ap-northeast-1",
      "Source": "localstack-debug@example.com",
      "RawData": "From: localstack-debug@example.com\r\nTo: test@example.com\r\nMessage-ID: <a4757360440849f20a948c2c3ddf660d@example.com>\r\nMIME-Version: 1.0\r\nDate: Sun, 12 Nov 2023 12:19:28 +0900\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Transfer-Encoding: quoted-printable\r\n\r\n",
      "Timestamp": "2023-11-12T03:19:28"
    },
    {
      "Id": "uhwabrnauvfuuxaa-idkimugh-ocql-nxqj-trxs-vupsizfosjkl-qitcgu",
      "Region": "ap-northeast-1",
      "Source": "\"Mock from\" <localstack-debug@example.com>",
      "RawData": "From: Mock from <localstack-debug@example.com>\r\nSubject: =?utf-8?Q?=E3=80=90?=\r\nTo: test@example.com\r\nMessage-ID: <9a6145ffedd18e60a6f73f09cef8b505@example.com>\r\nMIME-Version: 1.0\r\nDate: Sun, 12 Nov 2023 12:37:28 +0900\r\nContent-Type: multipart/alternative; boundary=6Cq5L8nf\r\n\r\n--6Cq5L8nf\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Transfer-Encoding: quoted-printable\r\n\r\n<div>\r\n    <p>\r\n          </p>\r\n    <br>\r\n    <br>\r\n    <a href=3D\"#\">http://localhost:8080</a>\r\n</di=\r\nv>\r\n\r\n--6Cq5L8nf\r\nContent-Type: text/html; charset=utf-8\r\nContent-Transfer-Encoding: quoted-printable\r\n\r\n<div>\r\n    <p>\r\n    </p>\r\n    <br>\r\n    <br>\r\n    <a href=3D\"http://localhost:8080\">http://localhost:8080</a>\r\n</di=\r\nv>\r\n\r\n--6Cq5L8nf--\r\n",
      "Timestamp": "2023-11-12T03:37:28"
    }
  ]
}
"""
