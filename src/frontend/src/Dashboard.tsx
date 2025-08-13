
import React, { useEffect, useState } from 'react';
import axios from 'axios';

type Email = {
  id: string;
  thread_id: string;
  sender: string;
  subject: string;
  timestamp: string;
  body?: string;
  summary?: string;
  replied?: boolean;
  draft?: string;
};

const Dashboard = () => {
  const [emails, setEmails] = useState<Email[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [csvUrl, setCsvUrl] = useState('');


  const [count, setCount] = useState(5);
  const fetchEmails = async (customCount?: number) => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.get(`/api/unreplied-detect?count=${customCount ?? count}`);
      let emails: Email[] = res.data.emails || [];
      setEmails(emails);
      await axios.post('/api/save-emails', { emails });
    } catch (err) {
      setError('Failed to fetch emails.');
    }
    setLoading(false);
  };


  const exportCSV = () => {
    setCsvUrl('/api/export');
    setTimeout(() => setCsvUrl(''), 1000);
  };

  const generateDraft = async (email: Email) => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post('/api/generate-draft', { email_id: email.id, body: email.body || email.subject });
      const draft = res.data.draft;
      setEmails(prev => prev.map(e => e.id === email.id ? { ...e, draft } : e));
    } catch (err) {
      setError('Failed to generate draft.');
    }
    setLoading(false);
  };


  useEffect(() => {
    fetchEmails();
    // eslint-disable-next-line
  }, [count]);

  return (
    <div style={{ width: '100vw', minHeight: '100vh', margin: 0, padding: 0, fontFamily: 'Arial, sans-serif', background: '#f8f8f8', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <h2>Smart Email Assistant Dashboard</h2>
      <div style={{ display: 'flex', gap: 16, marginBottom: 8, alignItems: 'center' }}>
        <label style={{ fontWeight: 600 }}>
          Number of emails:
          <input
            type="number"
            min={1}
            max={50}
            value={count}
            onChange={e => setCount(Number(e.target.value))}
            style={{ marginLeft: 8, width: 60, padding: 4 }}
            disabled={loading}
          />
        </label>
        <button
          onClick={() => fetchEmails()}
          disabled={loading}
          style={{
            background: '#1976d2',
            color: '#fff',
            border: 'none',
            borderRadius: 4,
            padding: '8px 20px',
            fontWeight: 600,
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.7 : 1
          }}
        >
          {loading ? 'Loading...' : 'Refresh'}
        </button>
        <button
          onClick={exportCSV}
          disabled={emails.length === 0}
          style={{
            background: '#43a047',
            color: '#fff',
            border: 'none',
            borderRadius: 4,
            padding: '8px 20px',
            fontWeight: 600,
            cursor: emails.length === 0 ? 'not-allowed' : 'pointer',
            opacity: emails.length === 0 ? 0.7 : 1
          }}
        >
          Export CSV
        </button>
      </div>
      {csvUrl && <iframe src={csvUrl} style={{ display: 'none' }} title="csv-export" />}
      <div style={{ marginTop: 30 }}>
        {error && <div style={{ color: 'red' }}>{error}</div>}
        {emails.length === 0 && !loading && <div>No emails found.</div>}
        {emails.length > 0 && (
          <table style={{ width: '90%', maxWidth: 1200, minWidth: 900, borderCollapse: 'collapse', background: '#fff', margin: '0 auto', boxShadow: '0 2px 12px rgba(0,0,0,0.07)' }}>
            <thead>
              <tr style={{ background: '#f0f0f0' }}>
                <th style={{ border: '1px solid #ccc', padding: 8 }}>From</th>
                <th style={{ border: '1px solid #ccc', padding: 8 }}>Subject</th>
                <th style={{ border: '1px solid #ccc', padding: 8 }}>Summary</th>
                <th style={{ border: '1px solid #ccc', padding: 8 }}>Replied</th>
                <th style={{ border: '1px solid #ccc', padding: 8 }}>Draft</th>
                <th style={{ border: '1px solid #ccc', padding: 8 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {emails.map(email => (
                <tr key={email.id}>
                  <td style={{ border: '1px solid #ccc', padding: 8 }}>{email.sender}</td>
                  <td style={{ border: '1px solid #ccc', padding: 8 }}>{email.subject}</td>
                  <td style={{ border: '1px solid #ccc', padding: 8, whiteSpace: 'pre-wrap' }}>{email.summary || <span style={{color:'#aaa'}}>No summary</span>}</td>
                  <td style={{ border: '1px solid #ccc', padding: 8 }}>{email.replied ? 'Yes' : 'No'}</td>
                  <td style={{ border: '1px solid #ccc', padding: 8, whiteSpace: 'pre-wrap' }}>{email.draft ? email.draft : <span style={{color:'#aaa'}}>No draft</span>}</td>
                  <td style={{ border: '1px solid #ccc', padding: 8 }}>
                    {email.replied ? (
                      <button onClick={() => generateDraft(email)} disabled={loading || !!email.draft}>
                        {email.draft ? 'Draft Ready' : 'Generate Draft'}
                      </button>
                    ) : (
                      <span style={{ color: '#aaa' }}>Auto</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
