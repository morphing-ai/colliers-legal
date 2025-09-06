import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Upload, FileText, AlertTriangle, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { useToast } from '@/hooks/useToast';
import { apiClient } from '@/lib/api-client';

interface AnalysisResult {
  analysis_results: Record<string, any>;
  risk_score: {
    score: number;
    level: string;
    color: string;
    high_risks: number;
    medium_risks: number;
    low_risks: number;
  };
  timestamp: string;
  analyzed_by: string;
}

export default function ContractAnalysis() {
  const [contractText, setContractText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const { toast } = useToast();

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (file.type === 'text/plain') {
      const text = await file.text();
      setContractText(text);
      toast({
        title: 'File loaded',
        description: `${file.name} has been loaded successfully.`,
      });
    } else {
      toast({
        title: 'Unsupported file type',
        description: 'Please upload a .txt file for now.',
        variant: 'destructive',
      });
    }
  };

  const analyzeContract = async () => {
    if (!contractText.trim()) {
      toast({
        title: 'No contract text',
        description: 'Please enter or upload a contract to analyze.',
        variant: 'destructive',
      });
      return;
    }

    setIsAnalyzing(true);
    try {
      const response = await apiClient.post('/api/neurobots/analyze-contract', {
        contract_text: contractText,
      });
      
      setAnalysisResult(response.data);
      toast({
        title: 'Analysis complete',
        description: 'Contract has been analyzed successfully.',
      });
    } catch (error) {
      console.error('Analysis failed:', error);
      toast({
        title: 'Analysis failed',
        description: 'An error occurred while analyzing the contract.',
        variant: 'destructive',
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getRiskBadge = (level: string, color: string) => {
    const variants: Record<string, 'destructive' | 'secondary' | 'default'> = {
      red: 'destructive',
      amber: 'secondary',
      green: 'default',
    };
    
    const icons = {
      red: <XCircle className="w-4 h-4" />,
      amber: <AlertTriangle className="w-4 h-4" />,
      green: <CheckCircle className="w-4 h-4" />,
    };

    return (
      <Badge variant={variants[color] || 'default'} className="flex items-center gap-1">
        {icons[color]}
        {level} RISK
      </Badge>
    );
  };

  const renderAnalysisSection = (botName: string, result: any) => {
    if (!result || result.error) {
      return null;
    }

    const formatBotName = (name: string) => {
      return name
        .replace(/_/g, ' ')
        .replace(/\b\w/g, (l) => l.toUpperCase());
    };

    return (
      <Card key={botName} className="mb-4">
        <CardHeader>
          <CardTitle className="text-lg">{formatBotName(botName)}</CardTitle>
        </CardHeader>
        <CardContent>
          {Object.entries(result).map(([key, value]) => {
            if (!value || !Array.isArray(value)) return null;
            
            return (
              <div key={key} className="mb-4">
                <h4 className="font-semibold mb-2 text-sm text-gray-700">
                  {key.replace(/_/g, ' ').toUpperCase()}
                </h4>
                {value.map((item: any, idx: number) => (
                  <Alert key={idx} className="mb-2">
                    <AlertDescription>
                      <div className="space-y-1">
                        {item.type && (
                          <div className="font-semibold">{item.type}</div>
                        )}
                        {item.severity && (
                          <Badge 
                            variant={
                              item.severity === 'high' ? 'destructive' : 
                              item.severity === 'medium' ? 'secondary' : 
                              'default'
                            }
                            className="mb-1"
                          >
                            {item.severity.toUpperCase()}
                          </Badge>
                        )}
                        {item.issue && (
                          <div className="text-sm">{item.issue}</div>
                        )}
                        {item.recommendation && (
                          <div className="text-sm text-blue-600">
                            <strong>Recommendation:</strong> {item.recommendation}
                          </div>
                        )}
                        {item.bot_author && (
                          <div className="text-xs text-gray-500 mt-1">
                            Analysis by: {item.bot_author}
                          </div>
                        )}
                      </div>
                    </AlertDescription>
                  </Alert>
                ))}
              </div>
            );
          })}
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Morphing Digital Paralegal</h1>
        <p className="text-gray-600">AI-powered contract analysis with Neurobot intelligence</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Section */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Contract Input</CardTitle>
              <CardDescription>
                Paste contract text or upload a file for analysis
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label htmlFor="file-upload" className="block mb-2">
                  <Button variant="outline" className="w-full" asChild>
                    <span>
                      <Upload className="w-4 h-4 mr-2" />
                      Upload Contract File
                      <input
                        id="file-upload"
                        type="file"
                        accept=".txt"
                        onChange={handleFileUpload}
                        className="hidden"
                      />
                    </span>
                  </Button>
                </label>
              </div>
              
              <Textarea
                placeholder="Or paste contract text here..."
                value={contractText}
                onChange={(e) => setContractText(e.target.value)}
                className="min-h-[400px] font-mono text-sm"
              />
              
              <Button 
                onClick={analyzeContract} 
                disabled={isAnalyzing || !contractText.trim()}
                className="w-full"
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Analyzing Contract...
                  </>
                ) : (
                  <>
                    <FileText className="w-4 h-4 mr-2" />
                    Analyze Contract
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Results Section */}
        <div>
          {analysisResult ? (
            <div className="space-y-4">
              {/* Risk Score Card */}
              <Card>
                <CardHeader>
                  <CardTitle>Risk Assessment</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <div className="text-3xl font-bold">
                        {analysisResult.risk_score.score}/100
                      </div>
                      <div className="text-sm text-gray-600">Overall Risk Score</div>
                    </div>
                    {getRiskBadge(
                      analysisResult.risk_score.level,
                      analysisResult.risk_score.color
                    )}
                  </div>
                  
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="p-2 bg-red-50 rounded">
                      <div className="text-xl font-semibold text-red-600">
                        {analysisResult.risk_score.high_risks}
                      </div>
                      <div className="text-xs text-gray-600">High Risks</div>
                    </div>
                    <div className="p-2 bg-yellow-50 rounded">
                      <div className="text-xl font-semibold text-yellow-600">
                        {analysisResult.risk_score.medium_risks}
                      </div>
                      <div className="text-xs text-gray-600">Medium Risks</div>
                    </div>
                    <div className="p-2 bg-green-50 rounded">
                      <div className="text-xl font-semibold text-green-600">
                        {analysisResult.risk_score.low_risks}
                      </div>
                      <div className="text-xs text-gray-600">Low Risks</div>
                    </div>
                  </div>
                  
                  <div className="mt-4 text-xs text-gray-500">
                    Analyzed by: {analysisResult.analyzed_by}
                    <br />
                    {new Date(analysisResult.timestamp).toLocaleString()}
                  </div>
                </CardContent>
              </Card>

              {/* Detailed Analysis */}
              <div className="max-h-[600px] overflow-y-auto space-y-2">
                {Object.entries(analysisResult.analysis_results).map(([botName, result]) =>
                  renderAnalysisSection(botName, result)
                )}
              </div>
            </div>
          ) : (
            <Card className="h-full flex items-center justify-center">
              <CardContent className="text-center py-12">
                <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">
                  Analysis results will appear here
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}