import { useState, useEffect } from 'react';
import { Database, Upload, Search, Trash2 } from 'lucide-react';

interface Collection {
  name: string;
  count: number;
}

export default function RAGManager() {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [selectedCollection, setSelectedCollection] = useState('');
  const [newCollectionName, setNewCollectionName] = useState('');
  const [documentText, setDocumentText] = useState('');
  const [queryText, setQueryText] = useState('');
  const [queryResults, setQueryResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [ragAvailable, setRagAvailable] = useState(true);

  useEffect(() => {
    checkRAGStatus();
  }, []);

  const checkRAGStatus = async () => {
    try {
      const response = await fetch('http://localhost:8078/api/rag/status');
      const data = await response.json();
      setRagAvailable(data.available);
      
      if (data.available) {
        loadCollections();
      }
    } catch (error) {
      console.error('Failed to check RAG status:', error);
      setRagAvailable(false);
    }
  };

  const loadCollections = async () => {
    try {
      const response = await fetch('http://localhost:8078/api/rag/collections');
      const data = await response.json();
      setCollections(data.collections || []);
    } catch (error) {
      console.error('Failed to load collections:', error);
    }
  };

  const createCollection = async () => {
    if (!newCollectionName.trim()) {
      alert('Please enter a collection name');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('http://localhost:8078/api/rag/collections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newCollectionName })
      });

      if (response.ok) {
        setNewCollectionName('');
        loadCollections();
      } else {
        alert('Failed to create collection');
      }
    } catch (error) {
      console.error('Failed to create collection:', error);
      alert('Failed to create collection');
    }
    setLoading(false);
  };

  const addDocument = async () => {
    if (!selectedCollection || !documentText.trim()) {
      alert('Please select a collection and enter document text');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('http://localhost:8078/api/rag/documents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          collection_name: selectedCollection,
          documents: [documentText],
          metadatas: [{ source: 'manual_input' }]
        })
      });

      if (response.ok) {
        setDocumentText('');
        alert('Document added successfully');
        loadCollections();
      } else {
        alert('Failed to add document');
      }
    } catch (error) {
      console.error('Failed to add document:', error);
      alert('Failed to add document');
    }
    setLoading(false);
  };

  const queryCollection = async () => {
    if (!selectedCollection || !queryText.trim()) {
      alert('Please select a collection and enter a query');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('http://localhost:8078/api/rag/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          collection_name: selectedCollection,
          query: queryText,
          n_results: 3
        })
      });

      const data = await response.json();
      setQueryResults(data);
    } catch (error) {
      console.error('Failed to query collection:', error);
      alert('Failed to query collection');
    }
    setLoading(false);
  };

  const deleteCollection = async (name: string) => {
    if (!confirm(`Delete collection "${name}"?`)) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:8078/api/rag/collections/${name}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        loadCollections();
        if (selectedCollection === name) {
          setSelectedCollection('');
        }
      }
    } catch (error) {
      console.error('Failed to delete collection:', error);
    }
  };

  if (!ragAvailable) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">RAG Manager</h1>
          <p className="text-muted-foreground mt-2">
            Retrieval-Augmented Generation with ChromaDB
          </p>
        </div>

        <div className="bg-yellow-50 dark:bg-yellow-900 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6">
          <h3 className="font-semibold text-yellow-800 dark:text-yellow-200 mb-2">
            ⚠️ RAG Not Available
          </h3>
          <p className="text-yellow-700 dark:text-yellow-300">
            ChromaDB is not installed or not compatible with your Python version.
            For full RAG support, use Python 3.10 or 3.11 and install:
          </p>
          <code className="block mt-2 p-2 bg-yellow-100 dark:bg-yellow-800 rounded text-sm">
            pip install chromadb sentence-transformers
          </code>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">RAG Manager</h1>
        <p className="text-muted-foreground mt-2">
          Manage document collections and perform vector search
        </p>
      </div>

      {/* Create Collection */}
      <div className="bg-card border border-border rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Database className="w-5 h-5" />
          Create Collection
        </h3>
        <div className="flex gap-2">
          <input
            type="text"
            value={newCollectionName}
            onChange={(e) => setNewCollectionName(e.target.value)}
            placeholder="Collection name"
            className="flex-1 px-4 py-2 bg-background border border-border rounded-lg"
          />
          <button
            onClick={createCollection}
            disabled={loading}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50"
          >
            Create
          </button>
        </div>
      </div>

      {/* Collections List */}
      <div className="bg-card border border-border rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Collections</h3>
        <div className="space-y-2">
          {collections.map((collection) => (
            <div
              key={collection.name}
              className={`flex items-center justify-between p-3 border rounded-lg ${
                selectedCollection === collection.name
                  ? 'border-primary bg-primary/10'
                  : 'border-border'
              }`}
            >
              <button
                onClick={() => setSelectedCollection(collection.name)}
                className="flex-1 text-left"
              >
                <div className="font-medium">{collection.name}</div>
                <div className="text-sm text-muted-foreground">
                  {collection.count} documents
                </div>
              </button>
              <button
                onClick={() => deleteCollection(collection.name)}
                className="p-2 text-red-600 hover:bg-red-100 dark:hover:bg-red-900 rounded"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
          {collections.length === 0 && (
            <p className="text-center text-muted-foreground py-4">
              No collections yet
            </p>
          )}
        </div>
      </div>

      {/* Add Document */}
      {selectedCollection && (
        <div className="bg-card border border-border rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Upload className="w-5 h-5" />
            Add Document
          </h3>
          <textarea
            value={documentText}
            onChange={(e) => setDocumentText(e.target.value)}
            placeholder="Enter document text..."
            rows={4}
            className="w-full px-4 py-2 bg-background border border-border rounded-lg mb-2"
          />
          <button
            onClick={addDocument}
            disabled={loading}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50"
          >
            Add Document
          </button>
        </div>
      )}

      {/* Query */}
      {selectedCollection && (
        <div className="bg-card border border-border rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Search className="w-5 h-5" />
            Query Collection
          </h3>
          <div className="space-y-4">
            <input
              type="text"
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              placeholder="Enter your query..."
              className="w-full px-4 py-2 bg-background border border-border rounded-lg"
            />
            <button
              onClick={queryCollection}
              disabled={loading}
              className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50"
            >
              {loading ? 'Searching...' : 'Search'}
            </button>

            {queryResults && (
              <div className="mt-4">
                <h4 className="font-semibold mb-2">Results:</h4>
                <pre className="bg-background p-4 rounded-lg overflow-x-auto text-sm">
                  {JSON.stringify(queryResults, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

