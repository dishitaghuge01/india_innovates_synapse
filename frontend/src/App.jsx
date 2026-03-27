import React, { useState } from 'react';
import { ApolloProvider } from '@apollo/client/react';
import { client } from './services/GraphAPI';
import GlobeView from './components/GlobeView';
import TacticalHUD from './components/TacticalHUD';

function App() {
  const [entities, setEntities] = useState([]);

  return (
    <ApolloProvider client={client}>
      <div className="relative w-screen h-screen overflow-hidden bg-black text-white font-sans selection:bg-cyan-500/30">
        <GlobeView entities={entities} />
        <TacticalHUD onEntitiesSynced={setEntities} />
      </div>
    </ApolloProvider>
  );
}

export default App;