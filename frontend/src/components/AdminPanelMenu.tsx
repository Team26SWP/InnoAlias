import React, { useState } from 'react';
import {
  HTTP_URL,
  validateToken,
  navigateTo,
  Page,
} from './config';

/*
// In MongoDB shell or MongoDB Compass
db.users.updateOne(
  { "email": "admin@sigma.com" },
  { $set: { "isAdmin": true } }
)
*/

function AdminPanelMenu() {
  const [userEmail, setUserEmail] = useState('');
  const [deckId, setDeckId] = useState('');
  const [tag, setTag] = useState('');
  const [reason, setReason] = useState('');
  const [result, setResult] = useState<string | null>(null);
  const [logs, setLogs] = useState<unknown[] | null>(null);
  const [loading, setLoading] = useState(false);

  const token = localStorage.getItem('access_token');
  function getAuthHeaders(): HeadersInit | undefined {
    if (token) {
      return { Authorization: `Bearer ${token}` };
    }
    return undefined;
  }

  const deleteUser = async () => {
    setLoading(true);
    setResult(null);
    setLogs(null);
    try {
      const valid = await validateToken();
      if (!valid) { navigateTo(Page.Login); }
      const res = await fetch(`${HTTP_URL}/admin/delete/user/${userEmail}?reason=${encodeURIComponent(reason)}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });
      const data = await res.json();
      setResult(res.ok ? data.message : data.detail || JSON.stringify(data));
    } catch (e) {
      setResult('Network error');
    } finally {
      setLoading(false);
    }
  };

  const getLogs = async () => {
    setLoading(true);
    setResult(null);
    setLogs(null);
    try {
      const res = await fetch(`${HTTP_URL}/admin/logs`, {
        headers: getAuthHeaders(),
      });
      const data = await res.json();
      if (res.ok) setLogs(data.logs || []);
      else setResult(data.detail || JSON.stringify(data));
    } catch (e) {
      setResult('Network error');
    } finally {
      setLoading(false);
    }
  };

  const deleteDeck = async () => {
    setLoading(true);
    setResult(null);
    setLogs(null);
    try {
      const res = await fetch(`${HTTP_URL}/admin/delete/deck/${deckId}?reason=${encodeURIComponent(reason)}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });
      const data = await res.json();
      setResult(res.ok ? data.message : data.detail || JSON.stringify(data));
    } catch (e) {
      setResult('Network error');
    } finally {
      setLoading(false);
    }
  };

  const addAdmin = async () => {
    setLoading(true);
    setResult(null);
    setLogs(null);
    try {
      const res = await fetch(`${HTTP_URL}/admin/add/${userEmail}`, {
        method: 'PUT',
        headers: getAuthHeaders(),
      });
      const data = await res.json();
      setResult(res.ok ? data.message : data.detail || JSON.stringify(data));
    } catch (e) {
      setResult('Network error');
    } finally {
      setLoading(false);
    }
  };

  const removeAdmin = async () => {
    setLoading(true);
    setResult(null);
    setLogs(null);
    try {
      const res = await fetch(`${HTTP_URL}/admin/remove/${userEmail}`, {
        method: 'PUT',
        headers: getAuthHeaders(),
      });
      const data = await res.json();
      setResult(res.ok ? data.message : data.detail || JSON.stringify(data));
    } catch (e) {
      setResult('Network error');
    } finally {
      setLoading(false);
    }
  };

  const deleteTag = async () => {
    setLoading(true);
    setResult(null);
    setLogs(null);
    try {
      const res = await fetch(`${HTTP_URL}/admin/delete/tag/${encodeURIComponent(tag)}?reason=${encodeURIComponent(reason)}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });
      const data = await res.json();
      setResult(res.ok ? data.message : data.detail || JSON.stringify(data));
    } catch (e) {
      setResult('Network error');
    } finally {
      setLoading(false);
    }
  };

  const clearLogs = async () => {
    setLoading(true);
    setResult(null);
    setLogs(null);
    try {
      const res = await fetch(`${HTTP_URL}/admin/clear/logs`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });
      const data = await res.json();
      setResult(res.ok ? data.message : data.detail || JSON.stringify(data));
    } catch (e) {
      setResult('Network error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        background: '#000000',
        border: '2px dashed #ff0000',
        padding: 10,
        marginBottom: 20,
      }}
    >
      <h3 style={{ color: '#b00', fontWeight: 'bold', fontSize: 18 }}>Admin Panel</h3>
      <div style={{ marginBottom: 8 }}>
        <input placeholder="user_email" value={userEmail} onChange={(e) => setUserEmail(e.target.value)} />
        <input placeholder="deck_id" value={deckId} onChange={(e) => setDeckId(e.target.value)} />
        <input placeholder="tag" value={tag} onChange={(e) => setTag(e.target.value)} />
        <input placeholder="reason" value={reason} onChange={(e) => setReason(e.target.value)} />
      </div>
      <ul style={{
        color: '#b00',
      }}
      >
        <li><button type="button" onClick={deleteUser} disabled={loading}>DELETE user</button></li>
        <li><button type="button" onClick={deleteDeck} disabled={loading}>DELETE deck</button></li>
        <li><button type="button" onClick={addAdmin} disabled={loading}>ADD admin</button></li>
        <li><button type="button" onClick={removeAdmin} disabled={loading}>REMOVE admin</button></li>
        <li><button type="button" onClick={deleteTag} disabled={loading}>DELETE tag</button></li>
        <li><button type="button" onClick={getLogs} disabled={loading}>GET logs</button></li>
        <li><button type="button" onClick={clearLogs} disabled={loading}>CLEAR logs</button></li>

      </ul>
      {loading && <div style={{ color: '#b00', fontSize: 12 }}>Loading...</div>}
      {result && <div style={{ color: '#b00', fontSize: 12, marginTop: 5 }}>{result}</div>}
      {logs && (
        <div>
          <strong>Logs:</strong>
          <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>{JSON.stringify(logs, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default AdminPanelMenu;
