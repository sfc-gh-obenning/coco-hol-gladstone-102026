import concurrent.futures, html, re, sys, urllib.request

urls = [l.strip() for l in open(sys.argv[1]) if l.strip() and not l.startswith('#')]

def check(u):
    try:
        req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 (link-check)'})
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read(400000).decode('utf-8', 'ignore')
            m = re.search(r'<title[^>]*>(.*?)</title>', body, re.S | re.I)
            title = html.unescape(m.group(1)).strip() if m else ''
            notfound = bool(re.search(r'page not found|404|does not exist', title, re.I))
            return u, r.status, r.geturl(), title[:100], notfound
    except Exception as e:
        return u, getattr(e, 'code', 'ERR'), '', str(e)[:60], True

with concurrent.futures.ThreadPoolExecutor(8) as ex:
    for u, st, final, title, bad in ex.map(check, urls):
        flag = 'BAD ' if bad or st != 200 else 'OK  '
        print(f"{flag}{st} {u}\n      -> {final if final != u else ''} | {title}")
