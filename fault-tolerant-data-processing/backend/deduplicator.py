import hashlib
import json

class Deduplicator:
    """
    Prevents duplicate processing through content-based hashing
    Key insight: If the exact same raw payload is received, it's the same event
    """
    
    @staticmethod
    def compute_hash(raw_event):
        """
        Compute deterministic hash of event content
        This is the deduplication key - if hash exists, event was already processed
        """
        # Use the raw payload as the dedup key
        canonical_json = json.dumps(raw_event, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical_json.encode()).hexdigest()
    
    @staticmethod
    def is_duplicate(session, content_hash):
        """Check if we've seen this exact event before"""
        from models import RawEvent
        existing = session.query(RawEvent).filter_by(content_hash=content_hash).first()
        return existing is not None
    
    @staticmethod
    def get_previous_result(session, content_hash):
        """If event is duplicate, return its previous processing result"""
        from models import RawEvent, NormalizedEvent
        raw_event = session.query(RawEvent).filter_by(content_hash=content_hash).first()
        if not raw_event:
            return None
        
        if raw_event.processing_status == 'processed':
            normalized = session.query(NormalizedEvent).filter_by(raw_event_id=raw_event.id).first()
            return {'status': 'processed', 'data': normalized}
        elif raw_event.processing_status == 'failed':
            return {'status': 'failed', 'error': raw_event.error_message}
        
        return None