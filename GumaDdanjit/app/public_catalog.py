"""Public, read-only selection of explicitly registered and published products."""
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.config import STORAGE_DIR
from app.core import versions

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / 'templates'))


def public_products():
    registry = STORAGE_DIR / 'public_catalog.json'
    if not registry.is_file():
        return []
    items = json.loads(registry.read_text(encoding='utf-8'))['items']
    visible = []
    for item in items:
        if item.get('approved') is not True:
            continue
        try:
            idea = versions.read(item['idea_id'])
            upload = json.loads((versions.version_dir(item['idea_id'], 'Video', item['version']) / 'upload.json').read_text(encoding='utf-8'))
        except (FileNotFoundError, ValueError, KeyError):
            continue
        if idea.get('archived') or upload.get('state') != 'public' or upload.get('privacy') != 'public':
            continue
        if not re.fullmatch(r'https://www.youtube.com/watch\?v=[A-Za-z0-9_-]{11}', upload.get('url', '')):
            continue
        purchase = item['purchase_url']
        parsed = urlparse(purchase)
        if parsed.scheme != 'https' or parsed.netloc != 'link.coupang.com':
            continue
        thumbnail = item.get('thumbnail_url', '')
        thumbnail_parts = urlparse(thumbnail)
        video_id = upload['url'].split('=')[-1]
        if thumbnail_parts.scheme != 'https' or thumbnail_parts.netloc != 'i.ytimg.com' or not thumbnail_parts.path.startswith(f'/vi/{video_id}/'):
            thumbnail = ''
        product_image = item.get('product_image_url', '')
        image_parts = urlparse(product_image)
        if image_parts.scheme != 'https' or image_parts.netloc != 'thumbnail.coupangcdn.com':
            product_image = ''
        # Explicit fields only: never expose production metadata or local paths.
        visible.append(dict(number=item['number'], name=item['name'], category=item['category'],
                            summary=item['summary'], details=item['details'], purchase_url=purchase,
                            video_url=upload['url'], thumbnail_url=product_image or thumbnail,
                            is_product_photo=bool(product_image)))
    return sorted(visible, key=lambda item: item['number'])


@router.get('/products', include_in_schema=False)
def catalog(request: Request):
    return templates.TemplateResponse(request=request, name='public_catalog.html',
        context={'products': public_products()},
        headers={'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
                 'Referrer-Policy': 'strict-origin-when-cross-origin'})
