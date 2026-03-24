import React, { useState } from 'react';
import { Send, Bot, User } from 'lucide-react';

const QueryPanel = ({ onRunQuery }) => {
    const [query, setQuery] = useState('');
    const [messages, setMessages] = useState([]);
    const [isRunning, setIsRunning] = useState(false);

    const submit = async (e) => {
        e.preventDefault();
        if (!query.trim() || !onRunQuery) return;
        const userMessage = query.trim();
        setMessages(prev => [...prev, { role: 'user', text: userMessage }]);
        setQuery('');
        setIsRunning(true);
        try {
            const response = await onRunQuery(userMessage);
            setMessages(prev => [...prev, { role: 'assistant', text: response?.answer_text || 'Query executed.' }]);
        } catch (err) {
            setMessages(prev => [...prev, { role: 'assistant', text: 'Failed to run query. Check backend logs.' }]);
        } finally {
            setIsRunning(false);
        }
    };

    return (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <header style={{ borderBottom: '1px solid #e5e7eb', padding: '12px 14px' }}>
                <div style={{ fontSize: '12px', fontWeight: 700, color: '#111827' }}>Chat with Graph</div>
                <div style={{ fontSize: '10px', color: '#9ca3af', marginTop: '2px' }}>Order to Cash</div>
            </header>

            <div style={{ padding: '14px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '32px', height: '32px', borderRadius: '50%', border: '1px solid #e5e7eb', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Bot size={14} />
                </div>
                <div>
                    <div style={{ fontSize: '13px', fontWeight: 700, color: '#111827' }}>Dodge AI</div>
                    <div style={{ fontSize: '11px', color: '#9ca3af' }}>Graph Agent</div>
                </div>
            </div>

            <div style={{ padding: '0 14px 10px', fontSize: '13px', color: '#111827' }}>
                Hi! I can help you analyze the Order to Cash process.
            </div>

            <div style={{ flex: 1, overflowY: 'auto', padding: '0 14px 10px' }}>
                {messages.map((m, idx) => (
                    <div key={idx} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start', marginBottom: '10px' }}>
                        <div
                            style={{
                                maxWidth: '86%',
                                borderRadius: '8px',
                                padding: '9px 10px',
                                fontSize: '12px',
                                backgroundColor: m.role === 'user' ? '#111827' : '#f3f4f6',
                                color: m.role === 'user' ? '#fff' : '#111827'
                            }}
                        >
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px', opacity: 0.8 }}>
                                {m.role === 'user' ? <User size={11} /> : <Bot size={11} />}
                                <span style={{ fontSize: '10px' }}>{m.role === 'user' ? 'You' : 'Dodge AI'}</span>
                            </div>
                            {m.text}
                        </div>
                    </div>
                ))}
            </div>

            <form onSubmit={submit} style={{ borderTop: '1px solid #e5e7eb', padding: '10px', display: 'flex', gap: '8px' }}>
                <input 
                    type="text" 
                    placeholder="Analyze anything" 
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    style={{ flex: 1, padding: '10px', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '12px' }}
                />
                <button
                    type="submit"
                    style={{ padding: '8px 12px', backgroundColor: '#a3a3a3', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', opacity: isRunning ? 0.7 : 1 }}
                    disabled={isRunning}
                >
                    <Send size={16} />
                </button>
            </form>
        </div>
    );
};

export default QueryPanel;
