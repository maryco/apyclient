
## VsCode Settings

Extentions
- [Black Formatter (Id: ms-python.black-formatter)](https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter)
- [isort (Id: ms-python.isort)](https://marketplace.visualstudio.com/items?itemName=ms-python.isort)

settings.json
```json
{
    "python.pipenvPath": "/Users/unknown/.local/share/virtualenvs/apyclient-g6OG163o/bin/python",
    "python.analysis.extraPaths": [
        "/Users/unknown/.local/share/virtualenvs/apyclient-g6OG163o/lib/python3.11/site-packages"
    ],
    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        },
    },
    "isort.args":["--profile", "black"]
}
```


