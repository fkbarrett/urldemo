"""
URL shortener API

A production application would bootstrap with a config file.
"""
import json
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, FileResponse

from pydantic import BaseModel

from .memory_key_value_store import MemoryKeyValueStore
from .url_map_store import URLMapStore

# Initial the URL store with a key/value store instance.
str_cache = MemoryKeyValueStore()
url_map_store = URLMapStore(str_cache)

app = FastAPI()


@app.get("/")
def get_homepage():
   """
   Default endpoint displays the home page for the shortener app.
   """
   return FileResponse("static/index.html")


@app.get("/status")
def get_status():
    """
    Displays status.
    Can be used for an API health check.
    """
    return {"status": "OK"}


# form for the /url endpoint
class URLMapping(BaseModel):
    url: str
    key: Optional[str] = None
    expiration_min: Optional[int] = None


@app.post("/url")
async def post_new_mapping(url_map: URLMapping):
    """
    Handles POST of data for URL/shortname mapping
    """
    exp_sec = None
    if url_map.expiration_min:
        exp_sec = 60 * url_map.expiration_min

    try:
        shortname = await url_map_store.store(url_map.url,
                                              user_shortname=url_map.key,
                                              expiration_time=exp_sec)
    except Exception as e:
        print("Caught error %s" % e)
        raise HTTPException(status_code=400, detail=str(e))

    return { "url": url_map.url, "shortname": shortname }


@app.get("/{shortname}")
async def get_redirect_shortname(request: Request, shortname: str):
    """
    When there is a GET on the shortname, redirect to the original URL.
    If the URL is not found, show the "not found" page.
    """
    url = await url_map_store.lookup(shortname)
    if not url:
        return FileResponse("static/shortname_not_found.html")

    return RedirectResponse(url)
