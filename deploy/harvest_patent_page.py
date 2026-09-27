"""Read a bounded page of public patent abstracts, ordered by primary key."""
import json
from datetime import datetime,timezone
from sqlalchemy import select,func
from triz import patent_corpus as corpus

config=globals().get('TASK_CONFIG',{})
cursor=str(config.get('cursor') or '')
upper=str(config.get('upper_bound') or '')
limit=int(config.get('limit',400))
if not 1<=limit<=1000 or len(cursor)>64 or len(upper)>64:raise ValueError('Invalid page request')
with corpus.engine().connect() as connection:
    if not upper:
        upper=connection.execute(select(func.max(corpus.patents.c.publication_number))).scalar() or ''
    rows=connection.execute(select(corpus.patents.c.publication_number,corpus.patents.c.content_hash,corpus.patents.c.document)
        .where(corpus.patents.c.publication_number>cursor,corpus.patents.c.publication_number<=upper)
        .order_by(corpus.patents.c.publication_number).limit(limit)).all()
documents=[]
for number,content_hash,blob in rows:
    doc=corpus.decode(blob)
    documents.append(dict(identifier=number,publication_number=number,source_type='PATENT',
        title=doc.get('title',''),abstract=doc.get('abstract',''),url='https://patents.google.com/patent/'+number,
        year=str(doc.get('publication_date',''))[:4] or doc.get('year',''),
        publication_date=doc.get('publication_date',''),country_code=doc.get('country_code',''),
        cpc=doc.get('cpc',[]),ipc=doc.get('ipc',[]),family_id=doc.get('family_id'),content_hash=content_hash.hex(),
        abstract_truncated=bool(doc.get('abstract_truncated')),retrieval_scope='stored_patent_abstract',
        origins=['exhaustive_primary_key_sweep']))
print(json.dumps(dict(inventory=dict(created_at=datetime.now(timezone.utc).isoformat(),cursor=cursor,
    next_cursor=rows[-1][0] if rows else cursor,upper_bound=upper,exported_records=len(rows),
    complete=not rows or rows[-1][0]==upper,
    coverage='Sequential corpus scan of stored abstracts, not claims/full text. New or changed records are detected on a subsequent sweep.'),documents=documents),ensure_ascii=False))
