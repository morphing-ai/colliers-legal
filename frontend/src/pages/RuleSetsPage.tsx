// frontend/src/pages/RuleSetsPage.tsx
import { useState, useEffect, useCallback, useRef } from 'react';
import { Plus, Upload, Edit2, Trash2, FileText, Settings, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { useAuth } from '@clerk/clerk-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { useToast } from '../hooks/useToast';
import { Badge } from '../components/ui/badge';
import { Checkbox } from '../components/ui/checkbox';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '../components/ui/alert-dialog';
import { cn } from '../lib/utils';
import { useDropzone } from 'react-dropzone';

interface RuleSet {
  id: number;
  name: string;
  description?: string;
  created_by: string;
  is_active: boolean;
  preprocessing_prompt?: string;
  metadata: Record<string, any>;
  rule_count: number;
  created_at: string;
  updated_at?: string;
}

interface Rule {
  id: number;
  rule_set_id: number;
  rule_number: string;
  rule_title: string;
  rule_text: string;
  effective_start_date?: string;
  effective_end_date?: string;
  rulebook_hierarchy?: string;
  category?: string;
  summary?: string;
  is_current: boolean;
  rule_metadata?: any;
  created_at: string;
}

export default function RuleSetsPage() {
  const { getToken } = useAuth();
  const [ruleSets, setRuleSets] = useState<RuleSet[]>([]);
  const [selectedRuleSet, setSelectedRuleSet] = useState<RuleSet | null>(null);
  const [rules, setRules] = useState<Rule[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [manualRuleDialogOpen, setManualRuleDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [ruleSetToDelete, setRuleSetToDelete] = useState<RuleSet | null>(null);
  const [searchText, setSearchText] = useState('');
  const [filterDate, setFilterDate] = useState('');
  const [expandedRules, setExpandedRules] = useState<Set<number>>(new Set());
  const [includeSuperseded, setIncludeSuperseded] = useState(false);
  const [rulesLoading, setRulesLoading] = useState(false);
  const [hasMoreRules, setHasMoreRules] = useState(true);
  const [totalRules, setTotalRules] = useState(0);
  const loadMoreRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  // Form states
  const [newRuleSetName, setNewRuleSetName] = useState('');
  const [newRuleSetDescription, setNewRuleSetDescription] = useState('');
  const [preprocessingPrompt, setPreprocessingPrompt] = useState('');
  const [manualRule, setManualRule] = useState({
    rule_number: '',
    rule_title: '',
    rule_text: '',
    category: ''
  });

  // API helper functions using useAuth hook
  const apiGet = useCallback(async (url: string) => {
    try {
      const token = await getToken();
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${url}`, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API GET request failed:', error);
      throw error;
    }
  }, [getToken]);

  const apiPost = useCallback(async (url: string, data?: any) => {
    try {
      const token = await getToken();
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${url}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : '',
        },
        body: data ? JSON.stringify(data) : undefined,
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API POST request failed:', error);
      throw error;
    }
  }, [getToken]);

  const apiDelete = useCallback(async (url: string) => {
    try {
      const token = await getToken();
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${url}`, {
        method: 'DELETE',
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API DELETE request failed:', error);
      throw error;
    }
  }, [getToken]);

  const apiUpload = useCallback(async (url: string, formData: FormData) => {
    try {
      const token = await getToken();
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${url}`, {
        method: 'POST',
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        },
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API Upload request failed:', error);
      throw error;
    }
  }, [getToken]);

  // Fetch rule sets
  const fetchRuleSets = useCallback(async () => {
    try {
      console.log('Fetching rule sets...');
      const response = await apiGet('/rules/rule-sets?include_all=true');
      console.log('Rule sets response:', response);
      // API returns array directly, not wrapped in data
      setRuleSets(response || []);
    } catch (error) {
      console.error('Error fetching rule sets - full error:', error);
      toast({
        title: 'Error',
        description: 'Failed to fetch rule sets',
        variant: 'destructive',
      });
      setRuleSets([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  }, [apiGet, toast]);

  // Fetch rules for a specific rule set with pagination
  const fetchRules = useCallback(async (
    ruleSetId: number, 
    search?: string, 
    date?: string,
    offset: number = 0,
    limit: number = 50,
    append: boolean = false,
    includeSup: boolean = false
  ) => {
    try {
      setRulesLoading(true);
      let url = `/rules/rule-sets/${ruleSetId}/rules?limit=${limit}&offset=${offset}`;
      
      // Add filters if present
      if (search) {
        url += `&search_text=${encodeURIComponent(search)}`;
      }
      if (date) {
        url += `&filter_date=${date}`;
      }
      if (includeSup) {
        url += `&include_superseded=true`;
      }
      
      const response = await apiGet(url);
      const fetchedRules = response || [];
      
      if (append) {
        // Append to existing rules for infinite scroll
        setRules(prev => [...prev, ...fetchedRules]);
      } else {
        // Replace rules for new search
        setRules(fetchedRules);
      }
      
      // Check if there are more rules to load
      setHasMoreRules(fetchedRules.length === limit);
      
      // Update total count (you might want to get this from API)
      if (!append) {
        setTotalRules(fetchedRules.length);
      } else {
        setTotalRules(prev => prev + fetchedRules.length);
      }
    } catch (error) {
      console.error('Error fetching rules:', error);
      toast({
        title: 'Error',
        description: 'Failed to fetch rules',
        variant: 'destructive',
      });
    } finally {
      setRulesLoading(false);
    }
  }, [apiGet, toast]);

  // Create a new rule set
  const createRuleSet = async () => {
    if (!newRuleSetName.trim()) {
      toast({
        title: 'Error',
        description: 'Rule set name is required',
        variant: 'destructive',
      });
      return;
    }

    try {
      const newRuleSet = await apiPost('/rules/rule-sets', {
        name: newRuleSetName,
        description: newRuleSetDescription,
        preprocessing_prompt: preprocessingPrompt || null,
        rule_set_metadata: {}
      });

      toast({
        title: 'Success',
        description: 'Rule set created successfully',
      });
      
      // Refresh rule sets
      await fetchRuleSets();
      
      // Reset form and close dialog
      setNewRuleSetName('');
      setNewRuleSetDescription('');
      setPreprocessingPrompt('');
      setCreateDialogOpen(false);
    } catch (error) {
      console.error('Error creating rule set:', error);
      toast({
        title: 'Error',
        description: 'Failed to create rule set',
        variant: 'destructive',
      });
    }
  };

  // Delete a rule set
  const deleteRuleSet = async (id: number) => {
    try {
      await apiDelete(`/rules/rule-sets/${id}`);
      
      toast({
        title: 'Success',
        description: 'Rule set deleted successfully',
      });
      
      // Refresh rule sets
      await fetchRuleSets();
      
      // Clear selection if deleted rule set was selected
      if (selectedRuleSet?.id === id) {
        setSelectedRuleSet(null);
        setRules([]);
      }
    } catch (error) {
      console.error('Error deleting rule set:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete rule set',
        variant: 'destructive',
      });
    }
  };

  // Upload rules to a rule set
  const uploadRules = async (ruleSetId: number, files: File[]) => {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    try {
      const result = await apiUpload(`/rules/rule-sets/${ruleSetId}/rules/upload`, formData);
      
      toast({
        title: 'Success',
        description: result.message || 'Rules uploaded successfully',
      });
      
      // Refresh rules
      await fetchRules(ruleSetId, '', '', 0, 50, false, false);
      
      // Refresh rule sets to update rule count
      await fetchRuleSets();
      
      setUploadDialogOpen(false);
    } catch (error) {
      console.error('Error uploading rules:', error);
      toast({
        title: 'Error',
        description: 'Failed to upload rules',
        variant: 'destructive',
      });
    }
  };

  // Add a rule manually
  const addRuleManually = async () => {
    if (!selectedRuleSet) return;
    
    if (!manualRule.rule_number || !manualRule.rule_title || !manualRule.rule_text) {
      toast({
        title: 'Error',
        description: 'Rule number, title, and text are required',
        variant: 'destructive',
      });
      return;
    }

    try {
      const response = await apiPost(`/rules/rule-sets/${selectedRuleSet.id}/rules`, manualRule);
      
      toast({
        title: 'Success',
        description: 'Rule added successfully',
      });
      
      // Refresh rules
      await fetchRules(selectedRuleSet.id, '', '', 0, 50, false, false);
      
      // Refresh rule sets to update rule count
      await fetchRuleSets();
      
      // Reset form and close dialog
      setManualRule({
        rule_number: '',
        rule_title: '',
        rule_text: '',
        category: ''
      });
      setManualRuleDialogOpen(false);
    } catch (error) {
      console.error('Error adding rule:', error);
      toast({
        title: 'Error',
        description: 'Failed to add rule',
        variant: 'destructive',
      });
    }
  };

  // Dropzone configuration
  const { getRootProps, getInputProps, isDragActive, acceptedFiles } = useDropzone({
    accept: {
      'application/json': ['.json']
    },
    onDrop: (files) => {
      // Files are automatically stored in acceptedFiles
      console.log('Files dropped:', files);
    }
  });

  // Load rule sets on mount
  useEffect(() => {
    fetchRuleSets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty dependency array - only run on mount

  // Load rules when a rule set is selected
  useEffect(() => {
    if (selectedRuleSet) {
      fetchRules(selectedRuleSet.id, '', '', 0, 50, false, false);
    } else {
      setRules([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedRuleSet?.id]); // Only depend on the ID, not the whole object or function

  return (
    <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Rule Sets Management</h2>
        <Button onClick={() => setCreateDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New Rule Set
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {loading ? (
          <Card className="col-span-full">
            <CardContent className="flex items-center justify-center p-6">
              <div className="text-muted-foreground">Loading rule sets...</div>
            </CardContent>
          </Card>
        ) : ruleSets.length === 0 ? (
          <Card className="col-span-full">
            <CardContent className="flex flex-col items-center justify-center p-6">
              <FileText className="h-12 w-12 text-muted-foreground mb-4" />
              <div className="text-muted-foreground">No rule sets found</div>
              <Button 
                onClick={() => setCreateDialogOpen(true)} 
                className="mt-4"
                variant="outline"
              >
                Create your first rule set
              </Button>
            </CardContent>
          </Card>
        ) : (
          ruleSets.map((ruleSet) => (
            <Card 
              key={ruleSet.id} 
              className={cn(
                "cursor-pointer transition-colors hover:bg-accent",
                selectedRuleSet?.id === ruleSet.id && "border-primary"
              )}
              onClick={() => setSelectedRuleSet(ruleSet)}
            >
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {ruleSet.name}
                </CardTitle>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedRuleSet(ruleSet);
                      setUploadDialogOpen(true);
                    }}
                  >
                    <Upload className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={(e) => {
                      e.stopPropagation();
                      setRuleSetToDelete(ruleSet);
                      setDeleteDialogOpen(true);
                    }}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-xs text-muted-foreground mb-2">
                  {ruleSet.description || 'No description'}
                </div>
                <div className="flex items-center justify-between">
                  <Badge variant={ruleSet.is_active ? "default" : "secondary"}>
                    {ruleSet.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {ruleSet.rule_count || 0} rules
                  </span>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {selectedRuleSet && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>{selectedRuleSet.name} - Rules</CardTitle>
              <Button
                size="sm"
                onClick={() => setManualRuleDialogOpen(true)}
              >
                <Plus className="mr-2 h-4 w-4" />
                Add Rule
              </Button>
            </div>
            <CardDescription>
              {selectedRuleSet.description || 'No description'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {rules.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No rules in this rule set
              </div>
            ) : (
              <div className="space-y-4">
                {/* Add filter controls */}
                <div className="flex gap-4 pb-4 border-b">
                  <Input
                    placeholder="Search rules..."
                    value={searchText}
                    onChange={(e) => setSearchText(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && selectedRuleSet) {
                        const target = e.target as HTMLInputElement;
                        fetchRules(selectedRuleSet.id, target.value, filterDate, 0, 50, false, includeSuperseded);
                      }
                    }}
                    className="max-w-sm"
                  />
                  <Input
                    type="date"
                    placeholder="Filter by date"
                    value={filterDate}
                    onChange={(e) => setFilterDate(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && selectedRuleSet) {
                        const target = e.target as HTMLInputElement;
                        fetchRules(selectedRuleSet.id, searchText, target.value, 0, 50, false, includeSuperseded);
                      }
                    }}
                    className="max-w-sm"
                  />
                  <Button
                    variant="outline"
                    onClick={() => {
                      if (selectedRuleSet) {
                        fetchRules(selectedRuleSet.id, searchText, filterDate, 0, 50, false, includeSuperseded);
                      }
                    }}
                  >
                    Apply Filters
                  </Button>
                  <div className="flex items-center space-x-2">
                    <Checkbox 
                      id="superseded" 
                      checked={includeSuperseded}
                      onCheckedChange={(checked) => {
                        setIncludeSuperseded(checked as boolean);
                        if (selectedRuleSet) {
                          fetchRules(selectedRuleSet.id, searchText, filterDate, 0, 50, false, checked as boolean);
                        }
                      }}
                    />
                    <Label 
                      htmlFor="superseded" 
                      className="text-sm font-normal cursor-pointer"
                    >
                      Include superseded rules
                    </Label>
                  </div>
                  {(searchText || filterDate) && (
                    <Button
                      variant="ghost"
                      onClick={() => {
                        setSearchText('');
                        setFilterDate('');
                        if (selectedRuleSet) {
                          fetchRules(selectedRuleSet.id, '', '', 0, 50, false, includeSuperseded);
                        }
                      }}
                    >
                      Clear
                    </Button>
                  )}
                </div>
                
                <div className="max-h-[600px] overflow-y-auto">
                  {rules.map((rule) => {
                    const isExpanded = expandedRules.has(rule.id);
                    return (
                    <div key={rule.id} className="border rounded-lg p-4 transition-all">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <h4 className="font-semibold">
                              {rule.rule_number}: {rule.rule_title}
                            </h4>
                          </div>
                          {rule.rulebook_hierarchy && (
                            <p className="text-xs text-muted-foreground mt-1">
                              {rule.rulebook_hierarchy}
                            </p>
                          )}
                          <div className="flex gap-2 mt-2">
                            {rule.category && (
                              <Badge variant="outline" className="text-xs">
                                {rule.category}
                              </Badge>
                            )}
                            {rule.effective_start_date && (
                              <Badge variant="secondary" className="text-xs">
                                From: {new Date(rule.effective_start_date).toLocaleDateString()}
                              </Badge>
                            )}
                            {rule.effective_end_date && (
                              <Badge variant="destructive" className="text-xs">
                                Until: {new Date(rule.effective_end_date).toLocaleDateString()}
                              </Badge>
                            )}
                            {!rule.effective_end_date && rule.is_current && (
                              <Badge variant="default" className="text-xs">
                                Current
                              </Badge>
                            )}
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            const newExpanded = new Set(expandedRules);
                            if (isExpanded) {
                              newExpanded.delete(rule.id);
                            } else {
                              newExpanded.add(rule.id);
                            }
                            setExpandedRules(newExpanded);
                          }}
                        >
                          {isExpanded ? (
                            <>
                              <ChevronUp className="h-4 w-4 mr-1" />
                              Collapse
                            </>
                          ) : (
                            <>
                              <ChevronDown className="h-4 w-4 mr-1" />
                              Expand
                            </>
                          )}
                        </Button>
                      </div>
                      
                      {isExpanded && (
                        <div className="mt-4 space-y-3 border-t pt-4">
                          {rule.summary && (
                            <div>
                              <h5 className="font-medium text-sm mb-1">Summary</h5>
                              <p className="text-sm text-muted-foreground">
                                {rule.summary}
                              </p>
                            </div>
                          )}
                          <div>
                            <h5 className="font-medium text-sm mb-1">Full Text</h5>
                            <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                              {rule.rule_text}
                            </p>
                          </div>
                          {rule.rule_metadata && Object.keys(rule.rule_metadata).length > 0 && (
                            <div>
                              <h5 className="font-medium text-sm mb-1">Additional Information</h5>
                              <div className="text-xs text-muted-foreground">
                                {rule.rule_metadata.detailedTopics && (
                                  <p>Topics: {rule.rule_metadata.detailedTopics}</p>
                                )}
                                {rule.rule_metadata.hasHtmlVersion && (
                                  <p>HTML version available</p>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                  })}
                  
                  {/* Load More Trigger */}
                  {hasMoreRules && !rulesLoading && rules.length > 0 && (
                    <div 
                      ref={loadMoreRef}
                      className="py-4 text-center"
                    >
                      <Button
                        variant="outline"
                        onClick={() => {
                          if (selectedRuleSet) {
                            fetchRules(
                              selectedRuleSet.id, 
                              searchText, 
                              filterDate, 
                              rules.length, 
                              50, 
                              true,
                              includeSuperseded
                            );
                          }
                        }}
                      >
                        Load More Rules
                      </Button>
                    </div>
                  )}
                  
                  {rulesLoading && (
                    <div className="py-4 text-center">
                      <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                      <p className="text-sm text-muted-foreground mt-2">Loading rules...</p>
                    </div>
                  )}
                  
                  {!hasMoreRules && rules.length > 0 && (
                    <div className="py-4 text-center text-sm text-muted-foreground">
                      All {rules.length} rules loaded
                    </div>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Create Rule Set Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Rule Set</DialogTitle>
            <DialogDescription>
              Create a new rule set to organize your compliance rules
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={newRuleSetName}
                onChange={(e) => setNewRuleSetName(e.target.value)}
                placeholder="e.g., FINRA Rules 2024"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={newRuleSetDescription}
                onChange={(e) => setNewRuleSetDescription(e.target.value)}
                placeholder="Describe the purpose of this rule set"
                rows={3}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="preprocessing">
                Preprocessing Prompt (Optional)
              </Label>
              <Textarea
                id="preprocessing"
                value={preprocessingPrompt}
                onChange={(e) => setPreprocessingPrompt(e.target.value)}
                placeholder="Enter a GPT-4o prompt to preprocess rules before importing"
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={createRuleSet}>Create</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Upload Rules Dialog */}
      <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Upload Rules</DialogTitle>
            <DialogDescription>
              Upload JSON files containing rules to {selectedRuleSet?.name}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div
              {...getRootProps()}
              className={cn(
                "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
                isDragActive ? "border-primary bg-primary/10" : "border-muted-foreground/25"
              )}
            >
              <input {...getInputProps()} />
              <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              {isDragActive ? (
                <p>Drop the JSON files here...</p>
              ) : (
                <div>
                  <p className="mb-2">Drag & drop JSON files here, or click to select</p>
                  <p className="text-xs text-muted-foreground">
                    You can upload multiple JSON files at once
                  </p>
                </div>
              )}
            </div>
            {acceptedFiles.length > 0 && (
              <div className="space-y-2">
                <Label>Selected Files:</Label>
                <div className="space-y-1">
                  {acceptedFiles.map((file, index) => (
                    <div key={index} className="text-sm text-muted-foreground">
                      • {file.name}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setUploadDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={() => selectedRuleSet && uploadRules(selectedRuleSet.id, acceptedFiles)}
              disabled={acceptedFiles.length === 0}
            >
              Upload {acceptedFiles.length} file(s)
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Rule Manually Dialog */}
      <Dialog open={manualRuleDialogOpen} onOpenChange={setManualRuleDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Rule Manually</DialogTitle>
            <DialogDescription>
              Add a new rule to {selectedRuleSet?.name}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="rule_number">Rule Number</Label>
              <Input
                id="rule_number"
                value={manualRule.rule_number}
                onChange={(e) => setManualRule({...manualRule, rule_number: e.target.value})}
                placeholder="e.g., 2210"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="rule_title">Rule Title</Label>
              <Input
                id="rule_title"
                value={manualRule.rule_title}
                onChange={(e) => setManualRule({...manualRule, rule_title: e.target.value})}
                placeholder="Enter rule title"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="rule_text">Rule Text</Label>
              <Textarea
                id="rule_text"
                value={manualRule.rule_text}
                onChange={(e) => setManualRule({...manualRule, rule_text: e.target.value})}
                placeholder="Enter the full rule text"
                rows={5}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="category">Category (Optional)</Label>
              <Input
                id="category"
                value={manualRule.category}
                onChange={(e) => setManualRule({...manualRule, category: e.target.value})}
                placeholder="e.g., Communications, Trading"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setManualRuleDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={addRuleManually}>Add Rule</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete the rule set "{ruleSetToDelete?.name}" and all its rules.
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (ruleSetToDelete) {
                  deleteRuleSet(ruleSetToDelete.id);
                  setDeleteDialogOpen(false);
                  setRuleSetToDelete(null);
                }
              }}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}