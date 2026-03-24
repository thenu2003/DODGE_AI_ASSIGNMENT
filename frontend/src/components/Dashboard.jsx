import React, { useEffect, useState } from 'react';
import GraphView from './GraphView';
import QueryPanel from './QueryPanel';
import NodePopupCard from './NodePopupCard';
import { useGraphController } from './GraphController';
import { RefreshCw, Search, Loader2, Minimize2 } from 'lucide-react';

const Dashboard = () => {
    const { 
        elements, 
        selectedNode, 
        isLoading, 
        loadInitialGraph,
        expandNode,
        setFocusedTrace,
        runQuery,
        setSelectedNode
    } = useGraphController();

    const [searchInput, setSearchInput] = useState("");
    const [popupPosition, setPopupPosition] = useState(null);

    useEffect(() => {
        loadInitialGraph();
    }, [loadInitialGraph]);

    const handleNodeClick = async ({ nodeId, x, y }) => {
        setPopupPosition({ x, y });
        await expandNode(nodeId);
    };

    const handleSearch = async (e) => {
        e.preventDefault();
        if (searchInput.trim()) {
            await setFocusedTrace(searchInput.trim());
        }
    };

    return (
        <div style={{ height: '100vh', width: '100vw', display: 'flex', flexDirection: 'column', backgroundColor: '#f8fafc' }}>
            <header style={{ 
                height: '52px', borderBottom: '1px solid #e5e7eb',
                display: 'flex', alignItems: 'center', padding: '0 14px',
                backgroundColor: 'white', zIndex: 10
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#9ca3af', fontSize: '14px' }}>
                    <span>Mapping</span>
                    <span>/</span>
                    <span style={{ color: '#111827', fontWeight: 600 }}>Order to Cash</span>
                </div>

                <form onSubmit={handleSearch} style={{ marginLeft: '28px', width: '420px', position: 'relative' }}>
                    <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
                    <input 
                        type="text" 
                        value={searchInput}
                        onChange={(e) => setSearchInput(e.target.value)}
                        placeholder="Trace billing document 90012345"
                        style={{ width: '100%', padding: '8px 12px 8px 40px', borderRadius: '8px', border: '1px solid #e5e7eb', fontSize: '13px', backgroundColor: '#f9fafb' }}
                    />
                </form>

                <div style={{ flex: 1 }} />
                
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                    {isLoading && <Loader2 size={16} className="animate-spin" style={{ color: '#3B82F6' }} />}
                    <button 
                        onClick={loadInitialGraph} 
                        style={{ padding: '7px 12px', fontSize: '12px', backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px', color: '#4b5563', fontWeight: 500 }}>
                        <RefreshCw size={14} /> Reset Workflow
                    </button>
                </div>
            </header>

            <main style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
                <div style={{ flex: '7.4', backgroundColor: '#ffffff', position: 'relative' }}>
                    <div style={{ position: 'absolute', left: '14px', top: '12px', zIndex: 12, display: 'flex', gap: '8px' }}>
                        <button style={{ border: '1px solid #e5e7eb', backgroundColor: '#fff', borderRadius: '6px', fontSize: '11px', padding: '5px 10px', display: 'flex', gap: '5px', alignItems: 'center' }}>
                            <Minimize2 size={12} /> Minimize
                        </button>
                        <button style={{ border: '1px solid #111827', color: '#fff', backgroundColor: '#111827', borderRadius: '6px', fontSize: '11px', padding: '5px 10px' }}>
                            Hide Granular Overlay
                        </button>
                    </div>

                    <GraphView
                        elements={elements}
                        onNodeClick={handleNodeClick}
                        onBackgroundClick={() => {
                            setPopupPosition(null);
                            setSelectedNode(null);
                        }}
                    />

                    {selectedNode && popupPosition && (
                        <NodePopupCard nodeData={selectedNode} position={popupPosition} />
                    )}
                    
                    {elements.length < 15 && (
                        <div style={{ position: 'absolute', bottom: '18px', left: '18px', backgroundColor: '#ffffff', padding: '10px 12px', borderRadius: '8px', border: '1px solid #e5e7eb', boxShadow: '0 3px 10px rgba(0,0,0,0.04)', fontSize: '12px', maxWidth: '300px', color: '#475569' }}>
                            Click a major business node to expand instances. Click any instance to view details and neighborhood.
                        </div>
                    )}
                </div>

                <aside style={{ flex: '2.6', display: 'flex', flexDirection: 'column', borderLeft: '1px solid #e5e7eb', backgroundColor: 'white' }}>
                    <QueryPanel onRunQuery={runQuery} />
                </aside>
            </main>
        </div>
    );
};

export default Dashboard;
