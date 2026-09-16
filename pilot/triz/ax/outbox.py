"""At-least-once event delivery with fenced leases and per-consumer receipts."""
import json
import time
import uuid
from sqlalchemy import select,update,Column,String
from . import ledger
from .contracts import Conflict,now

receipts=ledger.table('consumer_receipts',Column('consumer',String(64),primary_key=True),
    Column('event_id',String(80),primary_key=True),Column('processed_at',String(40),nullable=False))


def claim(lease_seconds=60):
    with ledger.transaction() as c:
        q=select(ledger.outbox).where(ledger.outbox.c.status!='DELIVERED',
            ledger.outbox.c.lease_until<time.time()).order_by(ledger.outbox.c.event_id).limit(1)
        row=c.execute(q.with_for_update(skip_locked=True)).mappings().first()
        if not row:
            return None
        token=uuid.uuid4().hex
        c.execute(update(ledger.outbox).where(ledger.outbox.c.event_id==row['event_id']).values(
            status='CLAIMED',claim_token=token,lease_until=time.time()+lease_seconds))
        event=c.execute(select(ledger.events).where(ledger.events.c.event_id==row['event_id'])).mappings().one()
        return dict(event,payload=json.loads(event['payload']),claim_token=token)


def deliver(event,consumer,handler):
    """Handler writes through this transaction; no network or paid calls here."""
    with ledger.transaction() as c:
        row=c.execute(select(ledger.outbox).where(ledger.outbox.c.event_id==event['event_id']).with_for_update()).mappings().one()
        if row['status']=='DELIVERED':
            return False
        if row['claim_token']!=event['claim_token'] or row['lease_until']<time.time():
            raise Conflict('Event lease expired or replaced')
        seen=c.execute(select(receipts).where(receipts.c.consumer==consumer,receipts.c.event_id==event['event_id'])).first()
        if not seen:
            handler(c,event)
            c.execute(receipts.insert().values(consumer=consumer,event_id=event['event_id'],processed_at=now()))
        c.execute(update(ledger.outbox).where(ledger.outbox.c.event_id==event['event_id']).values(
            status='DELIVERED',delivered_at=now()))
    return not bool(seen)
