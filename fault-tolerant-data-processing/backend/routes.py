@api.route('/events', methods=['POST'])
def ingest_event(session, schema_config):
    """
    Core ingestion endpoint with idempotency
    Now uses schema_config for normalization
    """
    try:
        raw_event = request.json
        
        # Step 1: Compute hash for deduplication
        content_hash = Deduplicator.compute_hash(raw_event)
        
        # Step 2: Check if duplicate
        if Deduplicator.is_duplicate(session, content_hash):
            previous_result = Deduplicator.get_previous_result(session, content_hash)
            return jsonify({
                'status': 'duplicate_idempotent',
                'previous_result': previous_result,
                'message': 'This event was already processed'
            }), 200
        
        # Step 3: Store raw event
        raw_db_event = RawEvent(
            client_id=raw_event.get('source', 'unknown'),
            raw_payload=json.dumps(raw_event),
            content_hash=content_hash,
            processing_status='pending'
        )
        session.add(raw_db_event)
        session.flush()
        
        # Step 4: Normalize using schema config
        normalizer = EnhancedNormalizer(schema_config)
        normalized, errors = normalizer.normalize(raw_event)
        
        if errors:
            failed_event = FailedEvent(
                raw_event_id=raw_db_event.id,
                client_id=raw_event.get('source', 'unknown'),
                reason='; '.join(errors),
                raw_payload=json.dumps(raw_event)
            )
            session.add(failed_event)
            raw_db_event.processing_status = 'failed'
            raw_db_event.error_message = '; '.join(errors)
            session.commit()
            return jsonify({'status': 'validation_failed', 'errors': errors}), 400
        
        # Step 5: Store normalized event
        normalized_db_event = NormalizedEvent(
            raw_event_id=raw_db_event.id,
            client_id=normalized['client_id'],
            metric=normalized['metric'],
            amount=normalized['amount'],
            timestamp=datetime.fromisoformat(normalized['timestamp'].replace('Z', '+00:00'))
        )
        session.add(normalized_db_event)
        raw_db_event.processing_status = 'processed'
        
        session.commit()
        
        return jsonify({
            'status': 'success',
            'event_id': raw_db_event.id,
            'message': 'Event processed successfully'
        }), 201
        
    except Exception as e:
        session.rollback()
        return jsonify({
            'status': 'error',
            'error': str(e),
            'message': 'Database or processing error occurred'
        }), 500