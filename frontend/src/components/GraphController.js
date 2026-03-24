import { useState, useCallback, useEffect } from 'react';
import { fetchBusinessFlowGraph, fetchNodeDetails, fetchNodeNeighbors, fetchExpandNode, traceBusinessFlow, runChatQuery } from '../api/graphApi';

const NODE_COLORS = {
  Customer: '#3B82F6', Address: '#94A3B8', SalesOrder: '#10B981', 
  SalesOrderItem: '#059669', ScheduleLine: '#0D9488', Delivery: '#F59E0B', 
  DeliveryItem: '#D97706', BillingDocument: '#8B5CF6', BillingDocumentItem: '#7C3AED', 
  JournalEntry: '#EF4444', Payment: '#EAB308', Product: '#14B8A6', Plant: '#64748B'
};

const MAX_NODES = 500; // Browser safety limit

export const useGraphController = () => {
    const [currentElements, setCurrentElements] = useState([]);
    const [selectedNode, setSelectedNode] = useState(null);
    const [isLoading, setIsLoading] = useState(false);

    const transformToCytoscape = (data) => {
        const nodes = data.nodes.map(n => ({
            group: 'nodes',
            data: { 
                id: n.id, 
                label: n.type === n.id ? n.type : n.id,
                type: n.type,
                color: NODE_COLORS[n.type] || '#bdc3c7',
                metadata: n.metadata
            }
        }));

        const edges = data.edges.map((e, idx) => ({
            group: 'edges',
            data: { id: `e_${e.source}_${e.target}_${e.relationship}`, source: e.source, target: e.target, label: e.relationship }
        }));

        return [...nodes, ...edges];
    };

    const loadInitialGraph = useCallback(async () => {
        setIsLoading(true);
        try {
            const data = await fetchBusinessFlowGraph();
            setCurrentElements(transformToCytoscape(data));
            setSelectedNode(null);
        } catch (err) {
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    }, []);

    const mergeElements = (prev, incoming) => {
        const existingNodeIds = new Set(prev.filter(e => e.group === 'nodes').map(e => e.data.id));
        const existingEdgeIds = new Set(prev.filter(e => e.group === 'edges').map(e => e.data.id));
        const filtered = incoming.filter(e => {
            if (e.group === 'nodes') return !existingNodeIds.has(e.data.id);
            return !existingEdgeIds.has(e.data.id);
        });
        return [...prev, ...filtered];
    };

    const expandNode = async (nodeId) => {
        // Guard: Check if we are already over the node limit
        const nodeCount = currentElements.filter(e => e.group === 'nodes').length;
        if (nodeCount >= MAX_NODES) {
            alert(`Node limit of ${MAX_NODES} reached for performance.`);
            return;
        }

        setIsLoading(true);
        try {
            const isAbstract = ['Customer', 'SalesOrder', 'Delivery', 'BillingDocument', 'Payment'].includes(nodeId);
            if (isAbstract) {
                const expandedData = await fetchExpandNode(nodeId, 20);
                const newElements = transformToCytoscape(expandedData);
                setCurrentElements(prev => mergeElements(prev, newElements));
                setSelectedNode({
                    node: { id: nodeId, data: { node_type: nodeId, is_abstract: true } },
                    incoming: [],
                    outgoing: []
                });
            } else {
                const [details, neighborsData] = await Promise.all([
                    fetchNodeDetails(nodeId),
                    fetchNodeNeighbors(nodeId)
                ]);
                setSelectedNode(details);
                let aggregateElements = transformToCytoscape(neighborsData);
                const clickedType = details?.node?.data?.node_type;

                // Add peer context (same business entity type) so layout forms clusters,
                // not only a linear document chain.
                if (clickedType && ['Customer', 'SalesOrder', 'Delivery', 'BillingDocument', 'Payment'].includes(clickedType)) {
                    try {
                        const peerContext = await fetchExpandNode(clickedType, 12);
                        aggregateElements = mergeElements(aggregateElements, transformToCytoscape(peerContext));
                    } catch (e) {
                        // Continue with local neighborhood if peer-context expansion fails.
                    }
                }

                // Pull a limited 2-hop neighborhood to avoid single-line chains
                // and give a denser cluster around the clicked business node.
                const firstHopIds = (neighborsData.nodes || [])
                    .map(n => n.id)
                    .filter(id => id !== nodeId)
                    .slice(0, 8);

                for (const neighborId of firstHopIds) {
                    try {
                        const secondHop = await fetchNodeNeighbors(neighborId);
                        aggregateElements = mergeElements(aggregateElements, transformToCytoscape(secondHop));
                    } catch (e) {
                        // Keep partial neighborhood if one second-hop fetch fails.
                    }
                }

                setCurrentElements(prev => mergeElements(prev, aggregateElements));
            }
        } catch (err) {
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    const setFocusedTrace = async (documentId) => {
        setIsLoading(true);
        try {
            const data = await traceBusinessFlow(documentId);
            const normalized = {
                nodes: (data.nodes || []).map(n => ({ id: n.id, type: n.type, metadata: {} })),
                edges: (data.edges || []).map(e => ({ source: e.source, target: e.target, relationship: e.type || 'RELATED_TO' }))
            };
            setCurrentElements(transformToCytoscape(normalized));
            setSelectedNode(null);
        } catch (err) {
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    const runQuery = async (question) => {
        setIsLoading(true);
        try {
            const response = await runChatQuery(question, { topK: 20, useLlm: true });
            const { detected_intent: intent, data_result: result, highlight_nodes: highlightNodes = [] } = response;

            if (intent === 'trace_flow' && result?.records?.nodes) {
                const normalized = {
                    nodes: result.records.nodes.map(n => ({ id: n.id, type: n.type, metadata: {} })),
                    edges: result.records.edges.map(e => ({ source: e.source, target: e.target, relationship: e.type || 'RELATED_TO' }))
                };
                setCurrentElements(transformToCytoscape(normalized));
                setSelectedNode(null);
                return response;
            }

            if (intent === 'broken_flow' && Array.isArray(result?.records)) {
                const soIds = result.records.slice(0, 8).map(r => `SO_${r.sales_order}`);
                let aggregate = transformToCytoscape(await fetchBusinessFlowGraph());
                for (const so of soIds) {
                    try {
                        const neighbors = await fetchNodeNeighbors(so);
                        aggregate = mergeElements(aggregate, transformToCytoscape(neighbors));
                    } catch (e) {
                        // Continue partial graph rendering even if one ID fails.
                    }
                }
                setCurrentElements(aggregate);
                setSelectedNode(null);
                return response;
            }

            if (highlightNodes.length > 0) {
                let aggregate = transformToCytoscape(await fetchBusinessFlowGraph());
                for (const nodeId of highlightNodes.slice(0, 8)) {
                    try {
                        const neighbors = await fetchNodeNeighbors(nodeId);
                        aggregate = mergeElements(aggregate, transformToCytoscape(neighbors));
                    } catch (e) {
                        // Continue partial graph rendering even if one ID fails.
                    }
                }
                setCurrentElements(aggregate);
            }

            return response;
        } catch (err) {
            console.error(err);
            throw err;
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        loadInitialGraph();
    }, [loadInitialGraph]);

    return {
        elements: currentElements,
        selectedNode, 
        isLoading, 
        expandNode,
        setSelectedNode,
        loadInitialGraph,
        setFocusedTrace,
        runQuery
    };
};
