import React from 'react';

const EXCLUDE_FIELDS = new Set(['node_type']);

const NodePopupCard = ({ nodeData, position }) => {
    if (!nodeData || !nodeData.node) return null;

    const metadata = nodeData.node.data || {};
    const entries = Object.entries(metadata).filter(([k]) => !EXCLUDE_FIELDS.has(k));
    const incomingCount = Array.isArray(nodeData.incoming) ? nodeData.incoming.length : 0;
    const outgoingCount = Array.isArray(nodeData.outgoing) ? nodeData.outgoing.length : 0;

    return (
        <div
            style={{
                position: 'absolute',
                left: `${position.x}px`,
                top: `${position.y}px`,
                transform: 'translate(16px, -12px)',
                width: '260px',
                maxHeight: '360px',
                overflowY: 'auto',
                backgroundColor: '#ffffff',
                border: '1px solid #d1d5db',
                borderRadius: '10px',
                boxShadow: '0 8px 24px rgba(15,23,42,0.18)',
                zIndex: 20,
                padding: '12px'
            }}
        >
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#111827', marginBottom: '8px' }}>
                {metadata.node_type || 'Entity'}
            </div>

            <div style={{ fontSize: '12px', color: '#374151', marginBottom: '8px' }}>
                <strong>ID:</strong> {nodeData.node.id}
            </div>

            {entries.slice(0, 14).map(([key, value]) => (
                <div key={key} style={{ fontSize: '11px', color: '#4b5563', marginBottom: '4px', lineHeight: 1.4 }}>
                    <strong>{key}:</strong> {String(value)}
                </div>
            ))}

            <div style={{ marginTop: '10px', paddingTop: '8px', borderTop: '1px solid #e5e7eb', fontSize: '11px', color: '#475569' }}>
                <div><strong>Connections:</strong> {incomingCount + outgoingCount}</div>
                <div>Incoming: {incomingCount}</div>
                <div>Outgoing: {outgoingCount}</div>
            </div>
        </div>
    );
};

export default NodePopupCard;
