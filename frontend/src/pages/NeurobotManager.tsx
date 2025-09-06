import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Brain, Code, Plus, Edit, Play, User, Activity } from 'lucide-react';
import { useToast } from '@/hooks/useToast';
import { api } from '@/lib/api-client';

interface Neurobot {
  function_name: string;
  description: string;
  type: string;
  author: string;
  usage_count: number;
}

export default function NeurobotManager() {
  const [neurobots, setNeurobots] = useState<Neurobot[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedBot, setSelectedBot] = useState<Neurobot | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [newBot, setNewBot] = useState({
    function_name: '',
    description: '',
    code: '',
    neurobot_type: 'analyze'
  });
  const { toast } = useToast();

  useEffect(() => {
    loadNeurobots();
  }, []);

  const loadNeurobots = async () => {
    try {
      const response = await api.get('/neurobots');
      setNeurobots(response.neurobots || []);
    } catch (error) {
      console.error('Failed to load neurobots:', error);
      toast({
        title: 'Failed to load Neurobots',
        description: 'Could not fetch the list of Neurobots.',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const createNeurobot = async () => {
    if (!newBot.function_name || !newBot.description || !newBot.code) {
      toast({
        title: 'Incomplete form',
        description: 'Please fill in all required fields.',
        variant: 'destructive',
      });
      return;
    }

    setIsCreating(true);
    try {
      await api.post('/neurobots', newBot);
      toast({
        title: 'Neurobot created',
        description: `${newBot.function_name} has been created successfully.`,
      });
      setNewBot({ function_name: '', description: '', code: '', neurobot_type: 'analyze' });
      loadNeurobots();
    } catch (error) {
      toast({
        title: 'Creation failed',
        description: 'Failed to create the Neurobot. Check your code syntax.',
        variant: 'destructive',
      });
    } finally {
      setIsCreating(false);
    }
  };

  const getBotTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      analyze: 'bg-blue-100 text-blue-800',
      compare: 'bg-green-100 text-green-800',
      extract: 'bg-yellow-100 text-yellow-800',
      score: 'bg-red-100 text-red-800',
      learn: 'bg-purple-100 text-purple-800',
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Neurobot Manager</h1>
        <p className="text-gray-600">Manage and create intelligent contract analysis bots</p>
      </div>

      {/* Create New Neurobot */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plus className="w-5 h-5" />
            Create New Neurobot
          </CardTitle>
          <CardDescription>
            Write a new Neurobot to analyze specific contract patterns
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="function_name">Function Name</Label>
              <Input
                id="function_name"
                placeholder="detect_warranty_issues"
                value={newBot.function_name}
                onChange={(e) => setNewBot({ ...newBot, function_name: e.target.value })}
              />
            </div>
            <div>
              <Label htmlFor="type">Type</Label>
              <select
                id="type"
                className="w-full rounded-md border border-input bg-background px-3 py-2"
                value={newBot.neurobot_type}
                onChange={(e) => setNewBot({ ...newBot, neurobot_type: e.target.value })}
              >
                <option value="analyze">Analyze</option>
                <option value="compare">Compare</option>
                <option value="extract">Extract</option>
                <option value="score">Score</option>
                <option value="learn">Learn</option>
              </select>
            </div>
          </div>
          
          <div>
            <Label htmlFor="description">Description</Label>
            <Input
              id="description"
              placeholder="Detects problematic warranty clauses and extended liability periods"
              value={newBot.description}
              onChange={(e) => setNewBot({ ...newBot, description: e.target.value })}
            />
          </div>
          
          <div>
            <Label htmlFor="code">Neurobot Code</Label>
            <Textarea
              id="code"
              placeholder={`async def ${newBot.function_name || 'your_function'}(contract_text, context):
    """
    Your analysis logic here
    """
    issues = []
    
    # Your pattern detection logic
    if 'warranty' in contract_text.lower():
        issues.append({
            'type': 'Extended Warranty',
            'severity': 'medium',
            'recommendation': 'Review warranty period'
        })
    
    return {'issues': issues}`}
              value={newBot.code}
              onChange={(e) => setNewBot({ ...newBot, code: e.target.value })}
              className="min-h-[200px] font-mono text-sm"
            />
          </div>
          
          <Button onClick={createNeurobot} disabled={isCreating}>
            {isCreating ? 'Creating...' : 'Create Neurobot'}
          </Button>
        </CardContent>
      </Card>

      {/* Existing Neurobots */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {isLoading ? (
          <Card className="col-span-full">
            <CardContent className="text-center py-8">
              <Brain className="w-12 h-12 text-gray-400 mx-auto mb-4 animate-pulse" />
              <p className="text-gray-600">Loading Neurobots...</p>
            </CardContent>
          </Card>
        ) : neurobots.length === 0 ? (
          <Card className="col-span-full">
            <CardContent className="text-center py-8">
              <Brain className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No Neurobots found. Create your first one above!</p>
            </CardContent>
          </Card>
        ) : (
          neurobots.map((bot) => (
            <Card key={bot.function_name} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Brain className="w-4 h-4" />
                    {bot.function_name.replace(/_/g, ' ')}
                  </CardTitle>
                  <Badge className={getBotTypeColor(bot.type)}>
                    {bot.type}
                  </Badge>
                </div>
                <CardDescription>{bot.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2 text-gray-600">
                    <User className="w-3 h-3" />
                    <span>By: {bot.author}</span>
                  </div>
                  <div className="flex items-center gap-2 text-gray-600">
                    <Activity className="w-3 h-3" />
                    <span>Used {bot.usage_count} times</span>
                  </div>
                </div>
                
                <div className="mt-4 flex gap-2">
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button variant="outline" size="sm">
                        <Code className="w-3 h-3 mr-1" />
                        View Code
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
                      <DialogHeader>
                        <DialogTitle>{bot.function_name}</DialogTitle>
                        <DialogDescription>
                          Created by {bot.author}
                        </DialogDescription>
                      </DialogHeader>
                      <div className="mt-4">
                        <pre className="bg-gray-100 p-4 rounded-lg overflow-x-auto">
                          <code className="text-sm">
                            {`# Neurobot code would be displayed here
# This would show the actual Python code
# stored in the database for this bot`}
                          </code>
                        </pre>
                      </div>
                    </DialogContent>
                  </Dialog>
                  
                  <Button variant="outline" size="sm">
                    <Edit className="w-3 h-3 mr-1" />
                    Edit
                  </Button>
                  
                  <Button variant="outline" size="sm">
                    <Play className="w-3 h-3 mr-1" />
                    Test
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}