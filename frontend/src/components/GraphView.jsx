import React, { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
import fcose from 'cytoscape-fcose';

cytoscape.use(fcose);

const NODE_COLORS = {
  Customer: '#3B82F6', 
  Address: '#94A3B8', 
  SalesOrder: '#10B981', 
  SalesOrderItem: '#059669', 
  ScheduleLine: '#0D9488', 
  Delivery: '#F59E0B', 
  DeliveryItem: '#D97706', 
  BillingDocument: '#8B5CF6', 
  BillingDocumentItem: '#7C3AED', 
  JournalEntry: '#EF4444', 
  Payment: '#EAB308', 
  Product: '#14B8A6', 
  Plant: '#64748B'
};

const GraphView = ({ elements, onNodeClick, onBackgroundClick }) => {
    const containerRef = useRef(null);
    const cyRef = useRef(null);

    useEffect(() => {
        if (!containerRef.current || !elements || elements.length === 0) return;

        if (cyRef.current) {
            cyRef.current.destroy();
        }

        cyRef.current = cytoscape({
            container: containerRef.current,
            elements: elements,
            style: [
                {
                    selector: 'node',
                    style: {
                        'label': '',
                        'background-color': 'data(color)',
                        'width': 'mapData(degree, 0, 20, 10, 28)',
                        'height': 'mapData(degree, 0, 20, 10, 28)',
                        'border-width': 1.8,
                        'border-color': '#60a5fa',
                        'transition-property': 'opacity, border-width, border-color',
                        'transition-duration': '0.3s'
                    }
                },
                {
                    selector: 'edge',
                    style: {
                        'width': 1.1,
                        'line-color': '#93c5fd',
                        'target-arrow-color': '#93c5fd',
                        'target-arrow-shape': 'none',
                        'curve-style': 'bezier',
                        'opacity': 0.75,
                        'target-endpoint': 'outside-to-node',
                        'transition-property': 'opacity, line-color, width',
                        'transition-duration': '0.3s'
                    }
                },
                {
                    selector: '.faded',
                    style: {
                        'opacity': 0.05
                    }
                },
                {
                    selector: '.highlighted',
                    style: {
                        'opacity': 1,
                        'line-color': '#3b82f6',
                        'target-arrow-color': '#3b82f6',
                        'width': 2,
                        'z-index': 999
                    }
                },
                {
                    selector: 'node.highlighted',
                    style: {
                        'border-width': 2,
                        'border-color': '#3b82f6',
                        'opacity': 1
                    }
                }
            ],
            layout: {
                name: 'cose',
                randomize: true,
                animate: true,
                animationDuration: 700,
                nodeRepulsion: 450000,
                idealEdgeLength: 120,
                edgeElasticity: 100,
                gravity: 30,
                numIter: 1600,
                fit: true,
                padding: 40,
                componentSpacing: 120
            }
        });

        cyRef.current.on('tap', 'node', (evt) => {
            const node = evt.target;
            const pos = evt.renderedPosition || node.renderedPosition();
            onNodeClick({
                nodeId: node.id(),
                x: pos?.x || 0,
                y: pos?.y || 0
            });

            const neighborhood = node.closedNeighborhood();
            
            cyRef.current.elements().removeClass('highlighted').addClass('faded');
            neighborhood.removeClass('faded').addClass('highlighted');
        });

        cyRef.current.on('tap', (evt) => {
            if (evt.target === cyRef.current) {
                cyRef.current.elements().removeClass('faded highlighted');
                if (onBackgroundClick) onBackgroundClick();
            }
        });

        // Compute degree for scaling
        cyRef.current.nodes().forEach(n => {
            n.data('degree', n.degree());
        });

        return () => {
            if (cyRef.current) cyRef.current.destroy();
        };
    }, [elements]);

    return (
        <div style={{ width: '100%', height: '100%', backgroundColor: '#ffffff' }}>
            <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
        </div>
    );
};

export default GraphView;
