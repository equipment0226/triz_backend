"""Isolated no-network PDF reader. No JavaScript, files or embedded media execute."""
import sys,json
from io import BytesIO


def main():
    if sys.platform!='win32':
        import resource
        resource.setrlimit(resource.RLIMIT_AS,(384*1024*1024,384*1024*1024))
        resource.setrlimit(resource.RLIMIT_CPU,(10,10))
    from pypdf import PdfReader
    content=sys.stdin.buffer.read(20_000_001)
    if len(content)>20_000_000 or not content.startswith(b'%PDF-'):raise ValueError('input')
    reader=PdfReader(BytesIO(content))
    if reader.is_encrypted:raise ValueError('encrypted')
    pages=[];remaining=100_000;partial=len(reader.pages)>30
    for i,page in enumerate(reader.pages[:30]):
        text=(page.extract_text() or '').replace('\x00','')
        partial=partial or len(text)>remaining
        kept=text[:remaining];remaining-=len(kept)
        pages.append({'number':i+1,'text':kept})
        if remaining<=0:break
    partial=partial or len(pages)<len(reader.pages)
    result={'parse_status':'PARTIAL' if partial else 'TEXT_EXTRACTED' if any(p['text'].strip() for p in pages) else 'TEXT_UNAVAILABLE',
            'pages':pages,'total_pages':len(reader.pages),'processed_pages':len(pages),
            'limitation':'텍스트 추출만 수행했습니다. 이미지·수식 배치의 시각 검토와 측정 결과 진위 확인은 별도입니다.'}
    sys.stdout.buffer.write(json.dumps(result,ensure_ascii=False).encode())


if __name__=='__main__':main()
