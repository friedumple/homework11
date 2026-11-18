from playwright.sync_api import sync_playwright
from pathlib import Path
import json
P=Path(__file__).parent
results=[]
def check(name,ok):
    results.append({'test':name,'passed':bool(ok)})
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--allow-file-access-from-files'])
    page=b.new_page(viewport={'width':1280,'height':900}); errors=[];page.on('pageerror',lambda e: errors.append(str(e)))
    page.goto((P/'report.html').as_uri()); check('report title', '作業報告' in page.title())
    page.get_by_role('link',name='開啟 Wiki',exact=True).click();check('report to wiki',page.url.endswith('wiki.html'))
    check('10 sources',page.locator('article[id^="S"]').count()==10)
    check('8 entries',page.locator('.entry').count()==8)
    page.locator('#search').fill('東京巨蛋');check('wiki search',page.locator('.entry:visible').count()==1 and page.locator('#K05').is_visible())
    page.locator('#search').fill('不存在的詞');check('empty search',page.locator('#count').inner_text()=='0 筆知識')
    page.locator('#search').fill('');check('clear search',page.locator('.entry:visible').count()==8)
    page.get_by_role('link',name='教學簡報',exact=True).click();check('wiki to slides',page.url.endswith('slides.html'))
    check('11 slides',page.locator('.slide').count()==11)
    check('initial page',page.locator('#page').inner_text()=='1 / 11' and page.locator('#prev').is_disabled())
    page.locator('#next').click();check('next',page.locator('#page').inner_text()=='2 / 11')
    page.keyboard.press('ArrowLeft');check('keyboard left',page.locator('#page').inner_text()=='1 / 11')
    page.locator('#full').click();page.wait_for_timeout(200);check('fullscreen',page.evaluate('!!document.fullscreenElement'));page.evaluate('document.exitFullscreen()')
    for i in range(9):page.keyboard.press('ArrowRight')
    check('keyboard navigation',page.locator('#page').inner_text()=='10 / 11')
    page.get_by_role('button',name='臺北大巨蛋',exact=True).click();check('incorrect quiz feedback','再想想' in page.locator('#feedback').inner_text())
    page.get_by_role('button',name='東京巨蛋',exact=True).click();check('correct quiz feedback','正確' in page.locator('#feedback').inner_text())
    page.locator('#next').click();check('last page', page.locator('#page').inner_text()=='11 / 11' and page.locator('#next').is_disabled())
    page.locator('.slide.active a').first.click();check('slide to source anchor','wiki.html#S01' in page.url and page.locator('#S01').is_visible())
    check('all local html references',all((P/a.split('#')[0]).exists() for f in ['report.html','slides.html','wiki.html'] for a in __import__('re').findall(r'href="([^\"]+)"',(P/f).read_text()) if not a.startswith(('http','#')) and a.split('#')[0] not in ['browser_test.json']))
    page.set_viewport_size({'width':390,'height':844});page.goto((P/'slides.html').as_uri());check('mobile no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
    check('no page JS errors',not errors)
    b.close()
log={'total':len(results),'passed':sum(x['passed'] for x in results),'tests':results,'scope':'Chromium local file:// navigation; external web links not clicked.'}
(P/'browser_test.json').write_text(json.dumps(log,ensure_ascii=False,indent=2));print(json.dumps(log,ensure_ascii=False));assert log['passed']==log['total']
