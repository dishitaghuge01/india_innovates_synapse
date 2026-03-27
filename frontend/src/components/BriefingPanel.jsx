import React from 'react';
import { useQuery } from '@apollo/client/react';
import { X, Activity, Link as LinkIcon, FileText } from 'lucide-react';
import { GET_ENTITY_DETAILS } from '../services/GraphAPI';

const BriefingPanel = ({ selectedEntityName, onClose }) => {
    const { data, loading, error } = useQuery(GET_ENTITY_DETAILS, {
        variables: { name: selectedEntityName || '' },
        skip: !selectedEntityName,
        fetchPolicy: 'network-only'
    });

    return (
        <div className={`fixed right-0 top-0 h-full w-96 bg-black/80 backdrop-blur-xl border-l border-cyan-500/50 z-20 transition-transform duration-300 ease-in-out ${selectedEntityName ? 'translate-x-0' : 'translate-x-full'} flex flex-col pointer-events-auto shadow-[-10px_0_30px_rgba(0,255,255,0.1)]`}>
            {/* Header */}
            <div className="flex items-center justify-between p-5 border-b border-cyan-500/30 bg-cyan-950/30">
                <h2 className="text-cyan-400 font-mono text-lg font-bold tracking-widest truncate flex-1 flex items-center gap-3">
                    <Activity className="w-5 h-5 text-cyan-400 drop-shadow-[0_0_8px_rgba(0,255,255,0.8)]" />
                    DOSSIER
                </h2>
                <button onClick={onClose} className="text-cyan-600 hover:text-cyan-300 transition-colors">
                    <X className="w-6 h-6" />
                </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-5">
                {selectedEntityName && (
                    <div className="mb-6">
                        <p className="text-[10px] text-gray-500 uppercase tracking-[0.2em] mb-1">Target Identity</p>
                        <h1 className="text-2xl font-bold text-white tracking-wide">{selectedEntityName.toUpperCase()}</h1>
                    </div>
                )}

                {loading && (
                    <div className="flex flex-col items-center justify-center h-40 space-y-4">
                        <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
                        <p className="text-cyan-500/60 font-mono text-xs tracking-widest animate-pulse">DECRYPTING INTEL...</p>
                    </div>
                )}

                {error && (
                    <div className="text-red-400 text-sm font-mono p-4 border border-red-500/30 bg-red-950/20 rounded">
                        ERROR: SECURE DATA RETRIEVAL FAILED
                    </div>
                )}

                {data && data.entity && (
                    <div className="space-y-6">
                        <div>
                            <h3 className="text-[11px] text-cyan-500 font-mono uppercase tracking-[0.2em] mb-4 flex items-center gap-2 border-b border-cyan-500/20 pb-2">
                                <LinkIcon className="w-3.5 h-3.5" />
                                Intelligence Leads
                            </h3>
                            {data.entity.relations && data.entity.relations.length > 0 ? (
                                <ul className="space-y-4">
                                    {data.entity.relations.map((rel, idx) => (
                                        <li key={idx} className="bg-black/60 border border-cyan-900/50 rounded p-3 text-sm font-mono hover:border-cyan-500/50 transition-colors">
                                            <div className="flex flex-wrap items-center gap-2 text-cyan-300 mb-2">
                                                <span className="px-2 py-0.5 bg-cyan-950 rounded text-[10px] tracking-wider border border-cyan-800/80">
                                                    {rel.relation.toUpperCase()}
                                                </span>
                                                <span className="text-gray-600">→</span>
                                                <span className="font-bold text-white">{rel.target.toUpperCase()}</span>
                                            </div>
                                            {rel.context && (
                                                <div className="text-gray-400 text-xs mt-2 pl-3 border-l-2 border-cyan-800/50 flex items-start gap-2">
                                                    <FileText className="w-3.5 h-3.5 flex-shrink-0 mt-0.5 text-cyan-700" />
                                                    <span className="italic leading-relaxed">"{rel.context}"</span>
                                                </div>
                                            )}
                                        </li>
                                    ))}
                                </ul>
                            ) : (
                                <div className="bg-black/40 border border-white/5 p-4 rounded text-center">
                                    <p className="text-gray-500 text-xs font-mono tracking-wider">NO DIRECT CONNECTIONS FOUND</p>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
            
            {/* Footer */}
            <div className="p-3 border-t border-cyan-500/20 bg-black/40">
                <p className="text-[9px] text-cyan-600 font-mono tracking-widest text-center">
                    CONFIDENTIAL / EYES ONLY
                </p>
            </div>
        </div>
    );
};

export default BriefingPanel;