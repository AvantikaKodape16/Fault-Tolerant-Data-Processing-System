const API_BASE = 'http://localhost:5000/api';

let lastSubmittedEvent = null;

function showMessage(elementId, text, type) {
    const el = document.getElementById(elementId);
    el.textContent = text;
    el.className = `status-message status-${type}`;
    el.style.display = 'block';
}

async function submitEvent() {
    const client = document.getElementById('clientSelect').value;
    const shouldFail = document.getElementById('simulateFailure').checked;
    
    try {
        const payload = JSON.parse(document.getElementById('eventPayload').value);
        const event = { source: client, payload };
        
        lastSubmittedEvent = event;
        
        if (shouldFail) {
            showMessage('submitMessage', '❌ Simulated DB failure - request would fail', 'error');
            return;
        }
        
        const response = await fetch(`${API_BASE}/events`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(event)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('submitMessage', `✅ Success (ID: ${data.event_id})`, 'success');
        } else if (data.status === 'duplicate_idempotent') {
            showMessage('submitMessage', '⚠️ Duplicate detected - returning previous result', 'info');
        } else {
            showMessage('submitMessage', `❌ ${data.message}: ${data.errors?.join(', ') || 'Unknown error'}`, 'error');
        }
    } catch (e) {
        showMessage('submitMessage', `❌ ${e.message}`, 'error');
    }
}

async function submitDuplicate() {
    if (!lastSubmittedEvent) {
        showMessage('submitMessage', '⚠️ No previous event submitted', 'info');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/events`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(lastSubmittedEvent)
        });
        
        const data = await response.json();
        if (data.status === 'duplicate_idempotent') {
            showMessage('submitMessage', '✅ Duplicate correctly detected - no double processing!', 'success');
        } else {
            showMessage('submitMessage', '✅ Submitted again (not a duplicate)', 'success');
        }
    } catch (e) {
        showMessage('submitMessage', `❌ ${e.message}`, 'error');
    }
}

async function getAggregates() {
    try {
        const client = document.getElementById('filterClient').value;
        const metric = document.getElementById('filterMetric').value;
        const days = document.getElementById('filterDays').value;
        
        let url = `${API_BASE}/aggregates?days=${days}`;
        if (client) url += `&client_id=${client}`;
        if (metric) url += `&metric=${metric}`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        document.getElementById('aggregateJson').textContent = JSON.stringify(data, null, 2);
        document.getElementById('aggregateResults').style.display = 'block';
    } catch (e) {
        showMessage('submitMessage', `❌ ${e.message}`, 'error');
    }
}

async function getEventStatus() {
    try {
        const response = await fetch(`${API_BASE}/events/status`);
        const data = await response.json();
        
        document.getElementById('statusJson').textContent = JSON.stringify(data, null, 2);
        document.getElementById('statusResults').style.display = 'block';
    } catch (e) {
        console.error(e);
    }
}

async function getProcessedEvents() {
    try {
        const response = await fetch(`${API_BASE}/events/status?status=processed`);
        const data = await response.json();
        
        document.getElementById('statusJson').textContent = JSON.stringify(data, null, 2);
        document.getElementById('statusResults').style.display = 'block';
    } catch (e) {
        console.error(e);
    }
}

async function getFailedEvents() {
    try {
        const response = await fetch(`${API_BASE}/events/status?status=failed`);
        const data = await response.json();
        
        document.getElementById('statusJson').textContent = JSON.stringify(data, null, 2);
        document.getElementById('statusResults').style.display = 'block';
    } catch (e) {
        console.error(e);
    }
}