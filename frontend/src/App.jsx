import React, { useState } from 'react';
import { ApolloProvider } from '@apollo/client/react';
import { client } from './services/GraphAPI';
import GlobeView from './components/GlobeView';
import TacticalHUD from './components/TacticalHUD';
import BriefingPanel from './components/BriefingPanel';

function App() {
  const [entities, setEntities] = useState([]);
  const [selectedEntityName, setSelectedEntityName] = useState(null);

  return (
    <ApolloProvider client={client}>
      <div className="relative w-screen h-screen overflow-hidden bg-black text-white font-sans selection:bg-cyan-500/30">
        <GlobeView entities={entities} onEntityClick={setSelectedEntityName} />
        <TacticalHUD onEntitiesSynced={setEntities} />
        <BriefingPanel 
            selectedEntityName={selectedEntityName} 
            onClose={() => setSelectedEntityName(null)} 
        />
      </div>
    </ApolloProvider>
  );
}

export default App;