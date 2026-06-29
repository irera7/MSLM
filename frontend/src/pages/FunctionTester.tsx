import { useState } from 'react';
import { Calculator, Clock, Search } from 'lucide-react';

interface FunctionCall {
  name: string;
  arguments: Record<string, any>;
  result?: any;
}

export default function FunctionTester() {
  const [selectedFunction, setSelectedFunction] = useState('calculator');
  const [expression, setExpression] = useState('2 + 2');
  const [searchQuery, setSearchQuery] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const executeFunction = async () => {
    setLoading(true);
    setResult(null);

    try {
      let functionCall: FunctionCall;

      switch (selectedFunction) {
        case 'calculator':
          functionCall = {
            name: 'calculator',
            arguments: { expression }
          };
          break;
        case 'get_current_time':
          functionCall = {
            name: 'get_current_time',
            arguments: {}
          };
          break;
        case 'search_web':
          functionCall = {
            name: 'search_web',
            arguments: { query: searchQuery }
          };
          break;
        default:
          return;
      }

      const response = await fetch('http://localhost:8078/api/functions/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(functionCall)
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Failed to execute function:', error);
      setResult({ error: 'Failed to execute function' });
    }

    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Function Calling Tester</h1>
        <p className="text-muted-foreground mt-2">
          Test built-in functions
        </p>
      </div>

      {/* Function Selection */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button
          onClick={() => setSelectedFunction('calculator')}
          className={`p-4 border rounded-lg transition-colors ${
            selectedFunction === 'calculator'
              ? 'border-primary bg-primary/10'
              : 'border-border hover:bg-secondary'
          }`}
        >
          <Calculator className="w-8 h-8 mb-2" />
          <div className="font-semibold">Calculator</div>
          <div className="text-sm text-muted-foreground">
            Evaluate math expressions
          </div>
        </button>

        <button
          onClick={() => setSelectedFunction('get_current_time')}
          className={`p-4 border rounded-lg transition-colors ${
            selectedFunction === 'get_current_time'
              ? 'border-primary bg-primary/10'
              : 'border-border hover:bg-secondary'
          }`}
        >
          <Clock className="w-8 h-8 mb-2" />
          <div className="font-semibold">Current Time</div>
          <div className="text-sm text-muted-foreground">
            Get current date and time
          </div>
        </button>

        <button
          onClick={() => setSelectedFunction('search_web')}
          className={`p-4 border rounded-lg transition-colors ${
            selectedFunction === 'search_web'
              ? 'border-primary bg-primary/10'
              : 'border-border hover:bg-secondary'
          }`}
        >
          <Search className="w-8 h-8 mb-2" />
          <div className="font-semibold">Web Search</div>
          <div className="text-sm text-muted-foreground">
            Search the web (mock)
          </div>
        </button>
      </div>

      {/* Function Input */}
      <div className="bg-card border border-border rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Function Parameters</h3>

        {selectedFunction === 'calculator' && (
          <div>
            <label className="block text-sm font-medium mb-2">
              Expression
            </label>
            <input
              type="text"
              value={expression}
              onChange={(e) => setExpression(e.target.value)}
              placeholder="2 + 2"
              className="w-full px-4 py-2 bg-background border border-border rounded-lg"
            />
            <p className="text-sm text-muted-foreground mt-1">
              Examples: 2 + 2, 10 * 5, sqrt(16), sin(3.14)
            </p>
          </div>
        )}

        {selectedFunction === 'get_current_time' && (
          <p className="text-muted-foreground">
            This function doesn't require any parameters.
          </p>
        )}

        {selectedFunction === 'search_web' && (
          <div>
            <label className="block text-sm font-medium mb-2">
              Search Query
            </label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Python programming"
              className="w-full px-4 py-2 bg-background border border-border rounded-lg"
            />
          </div>
        )}

        <button
          onClick={executeFunction}
          disabled={loading}
          className="mt-4 px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50"
        >
          {loading ? 'Executing...' : 'Execute Function'}
        </button>
      </div>

      {/* Result */}
      {result && (
        <div className="bg-card border border-border rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Result</h3>
          <pre className="bg-background p-4 rounded-lg overflow-x-auto text-sm">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

