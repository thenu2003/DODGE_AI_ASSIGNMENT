import React from 'react';
import { Database, Info, ArrowUpRight, ArrowDownLeft } from 'lucide-react';

const NodeDetailsPanel = ({ nodeData, onClose }) => {
    if (!nodeData) return (
        <div style={{ padding: '20px', color: '#7f8c8d' }}>
            <p>Select a node to view its business details.</p>
        </div>
    );

    const { node, incoming, outgoing } = nodeData;

    return (
        <div style={{ padding: '20px', height: '100%', overflowY: 'auto' }}>
            <header style={{ borderBottom: '1px solid #eee', marginBottom: '20px' }}>
                <h3 style={{ display: 'flex', alignItems: 'center' }}>
                    <Info size={18} style={{ marginRight: '8px' }} />
                    Node Details
                </h3>
                <p style={{ fontSize: '12px', fontWeight: 'bold', color: '#3498db' }}>{node.id}</p>
            </header>

            <section style={{ marginBottom: '20px' }}>
                <h4 style={{ display: 'flex', alignItems: 'center', fontSize: '14px' }}>
                    <Database size={16} style={{ marginRight: '8px' }} />
                    Metadata
                </h4>
                <div style={{ backgroundColor: '#f8f9fa', padding: '10px', borderRadius: '4px', fontSize: '12px' }}>
                    {Object.entries(node.data).map(([key, value]) => (
                        <div key={key} style={{ marginBottom: '4px' }}>
                            <span style={{ fontWeight: 600 }}>{key}:</span> {String(value)}
                        </div>
                    ))}
                </div>
            </section>

            <section style={{ marginBottom: '20px' }}>
                <h4 style={{ display: 'flex', alignItems: 'center', fontSize: '14px' }}>
                    <ArrowUpRight size={16} style={{ marginRight: '8px' }} />
                    Outgoing (Source)
                </h4>
                {outgoing.length === 0 ? <p style={{ fontSize: '12px', color: '#95a5a6' }}>None</p> : 
                    outgoing.map((e, idx) => (
                        <div key={idx} style={{ fontSize: '11px', padding: '4px', borderBottom: '1px solid #f1f1f1' }}>
                            <span style={{ color: '#e67e22' }}>[{e.type}]</span> → {e.target}
                        </div>
                    ))
                }
            </section>

            <section>
                <h4 style={{ display: 'flex', alignItems: 'center', fontSize: '14px' }}>
                    <ArrowDownLeft size={16} style={{ marginRight: '8px' }} />
                    Incoming (Target)
                </h4>
                {incoming.length === 0 ? <p style={{ fontSize: '12px', color: '#95a5a6' }}>None</p> : 
                    incoming.map((e, idx) => (
                        <div key={idx} style={{ fontSize: '11px', padding: '4px', borderBottom: '1px solid #f1f1f1' }}>
                            {e.source} → <span style={{ color: '#e67e22' }}>[{e.type}]</span>
                        </div>
                    ))
                }
            </section>
        </div>
    );
};

export default NodeDetailsPanel;
