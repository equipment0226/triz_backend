"""Read-only bounded keyset scan of the stored public patent abstracts."""
from datetime import datetime,timezone

from sqlalchemy import select,func

from . import patent_corpus as corpus


def harvest_page(cursor='',upper_bound='',limit=400):
    cursor=str(cursor or '');upper_bound=str(upper_bound or '');limit=int(limit)
    if not 1<=limit<=1000 or len(cursor)>64 or len(upper_bound)>64:raise ValueError('Invalid page request')
    with corpus.engine().connect() as connection:
        if not upper_bound:
            upper_bound=connection.execute(select(func.max(corpus.patents.c.publication_number))).scalar() or ''
        rows=connection.execute(select(corpus.patents.c.publication_number,corpus.patents.c.content_hash,corpus.patents.c.document)
            .where(corpus.patents.c.publication_number>cursor,corpus.patents.c.publication_number<=upper_bound)
            .order_by(corpus.patents.c.publication_number).limit(limit)).all()
    documents=[]
    for number,content_hash,blob in rows:
        doc=corpus.decode(blob)
        documents.append(dict(identifier=number,publication_number=number,source_type='PATENT',
            title=doc.get('title',''),abstract=doc.get('abstract',''),url='https://patents.google.com/patent/'+number.replace('-','')+'/en',
            year=doc.get('year',''),cpc=doc.get('cpc',[]),family_id=doc.get('family_id'),content_hash=content_hash.hex(),
            abstract_truncated=bool(doc.get('abstract_truncated')),retrieval_scope='stored_patent_abstract',
            origins=['exhaustive_primary_key_sweep']))
    return dict(inventory=dict(created_at=datetime.now(timezone.utc).isoformat(),cursor=cursor,
        next_cursor=rows[-1][0] if rows else cursor,upper_bound=upper_bound,exported_records=len(rows),
        complete=not rows or rows[-1][0]==upper_bound,
        coverage='Bounded sequential scan of stored abstracts, not claims/full text. New or changed records need a subsequent sweep.'),documents=documents)
