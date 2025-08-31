import json, pathlib, requests

GRAPHQL_URL = "http://127.0.0.1:8000/graphql/"
COMMENT_ID  = "16"  # свой id
FILE_PATH   = "/home/dimal11/Pictures/Screenshots/Screenshot From 2025-08-11 21-07-50.png"

ops = {
    "query": """
      mutation($id: ID!, $file: Upload!) {
        uploadAttachment(commentId: $id, file: $file) {
          id url isImage contentType size width height
        }
      }
    """,
    "variables": {"id": COMMENT_ID, "file": None}
}
map_ = {"0": ["variables.file"]}

files = {
    "operations": (None, json.dumps(ops), "application/json"),
    "map":        (None, json.dumps(map_), "application/json"),
    "0":          (pathlib.Path(FILE_PATH).name, open(FILE_PATH, "rb"), "image/png"),
}

r = requests.post(GRAPHQL_URL, files=files)
print(r.status_code, r.text)