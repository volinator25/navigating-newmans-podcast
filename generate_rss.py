import yaml
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import email.utils
import os

def load_config(config_path='podcast_config.yaml'):
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def format_rfc2822(date_str):
    """Convert ISO 8601 date string to RFC 2822 format required by RSS."""
    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    return email.utils.format_datetime(dt)

def generate_rss(config):
    meta = config['metadata']
    episodes = config.get('episodes', [])

    rss = ET.Element('rss', {
        'version': '2.0',
        'xmlns:itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd',
        'xmlns:content': 'http://purl.org/rss/modules/content/',
        'xmlns:atom': 'http://www.w3.org/2005/Atom'
    })

    channel = ET.SubElement(rss, 'channel')

    # Atom self-reference (required by some validators)
    ET.SubElement(channel, 'atom:link', {
        'href': meta['rss_feed_url'],
        'rel': 'self',
        'type': 'application/rss+xml'
    })

    # Core channel fields
    ET.SubElement(channel, 'title').text = meta['title']
    ET.SubElement(channel, 'link').text = meta['link']
    ET.SubElement(channel, 'description').text = meta['description']
    ET.SubElement(channel, 'language').text = meta.get('language', 'en-us')
    ET.SubElement(channel, 'copyright').text = meta.get('copyright', f'© {datetime.now().year} {meta["author"]}')

    # iTunes channel fields
    ET.SubElement(channel, 'itunes:author').text = meta['author']
    ET.SubElement(channel, 'itunes:subtitle').text = meta.get('subtitle', meta['title'])
    ET.SubElement(channel, 'itunes:summary').text = meta['description']
    ET.SubElement(channel, 'itunes:explicit').text = 'true' if meta.get('explicit') else 'false'
    ET.SubElement(channel, 'itunes:type').text = meta.get('type', 'episodic')

    # iTunes owner block
    owner = ET.SubElement(channel, 'itunes:owner')
    ET.SubElement(owner, 'itunes:name').text = meta['author']
    ET.SubElement(owner, 'itunes:email').text = meta['email']

    # Cover art
    ET.SubElement(channel, 'itunes:image', {'href': meta['image']})
    image_el = ET.SubElement(channel, 'image')
    ET.SubElement(image_el, 'url').text = meta['image']
    ET.SubElement(image_el, 'title').text = meta['title']
    ET.SubElement(image_el, 'link').text = meta['link']

    # iTunes category (primary + optional subcategory)
    category_el = ET.SubElement(channel, 'itunes:category', {'text': meta.get('category', 'Kids & Family')})
    if meta.get('subcategory'):
        ET.SubElement(category_el, 'itunes:category', {'text': meta['subcategory']})

    # Episodes (newest first for RSS readers)
    for ep in reversed(episodes):
        item = ET.SubElement(channel, 'item')

        ET.SubElement(item, 'title').text = ep['title']
        ET.SubElement(item, 'description').text = ep['description']
        ET.SubElement(item, 'content:encoded').text = ep['description']
        ET.SubElement(item, 'itunes:summary').text = ep['description']
        ET.SubElement(item, 'pubDate').text = format_rfc2822(ep['publication_date'])

        # Audio enclosure
        ET.SubElement(item, 'enclosure', {
            'url': ep['asset_url'],
            'length': str(ep.get('file_size', 0)),
            'type': 'audio/mpeg'
        })

        # GUID — unique per episode, use the asset URL
        ET.SubElement(item, 'guid', {'isPermaLink': 'false'}).text = ep['asset_url']

        # iTunes episode fields
        ET.SubElement(item, 'itunes:author').text = meta['author']
        ET.SubElement(item, 'itunes:explicit').text = 'true' if ep.get('explicit') else 'false'
        ET.SubElement(item, 'itunes:duration').text = str(ep.get('duration', ''))
        ET.SubElement(item, 'itunes:episodeType').text = ep.get('episode_type', 'full')

        if ep.get('episode_number'):
            ET.SubElement(item, 'itunes:episode').text = str(ep['episode_number'])
        if ep.get('season_number'):
            ET.SubElement(item, 'itunes:season').text = str(ep['season_number'])
        if ep.get('image'):
            ET.SubElement(item, 'itunes:image', {'href': ep['image']})

    # Serialize with pretty-printing
    xml_str = ET.tostring(rss, encoding='unicode')
    dom = minidom.parseString(xml_str)
    return dom.toprettyxml(indent='  ', encoding='UTF-8')


def main():
    print("Generating podcast RSS feed...")
    config = load_config()
    xml_content = generate_rss(config)

    with open('podcast.xml', 'wb') as f:
        f.write(xml_content)

    print("podcast.xml generated successfully!")
    print(f"  Show: {config['metadata']['title']}")
    print(f"  Episodes: {len(config.get('episodes', []))}")
    print(f"  Feed URL: {config['metadata']['rss_feed_url']}")


if __name__ == '__main__':
    main()
