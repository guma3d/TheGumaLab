import json
import urllib.request

url = "http://localhost:6337/collections/gumaphoto_hybrid_kr/points/query"
headers = {"Content-Type": "application/json"}
# We need to query using a vector, or if we use string query, we query a point ID.
# The code does `query=tid, using=fb_type`.
# Let's see if we can do this through REST API, or just write a small py script using Qdrant client directly.
