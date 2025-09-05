// frontend/src/pages/ComplianceAnalyzer.tsx
import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '@clerk/clerk-react';
import { useParams, useNavigate } from 'react-router-dom';
import { AlertCircle, FileText, CheckCircle, XCircle, AlertTriangle, Info, Loader2, Send, ChevronDown, ChevronUp, Clock, Trash2, History, Eye, EyeOff, Edit, Upload, Calendar, Download } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { useToast } from '../hooks/useToast';
import { cn } from '../lib/utils';
import ComplianceResults from '../components/compliance/ComplianceResults';
import { formatDistanceToNow } from 'date-fns';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../components/ui/tooltip';
// Temporary API client until we fix the main one
const api = {
  async get(url: string) {
    try {
      // Get Clerk token
      let token = null;
      if (window.Clerk && window.Clerk.session) {
        token = await window.Clerk.session.getToken();
      }
      
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${url}`, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  },
};

interface RuleSet {
  id: number;
  name: string;
  description?: string;
  rule_count: number;
}

// Simple Clickable Rule Badge Component - shows details in modal on click
const RuleBadge: React.FC<{ 
  ruleNumber: string; 
  type: 'compliant' | 'violation';
  issue?: any;
  colorScheme: 'green' | 'red' | 'yellow' | 'blue';
}> = ({ ruleNumber, type, issue, colorScheme }) => {
  const [showModal, setShowModal] = useState(false);
  const [ruleDetails, setRuleDetails] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  
  const colorSchemes = {
    green: {
      badge: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 border-green-300 dark:border-green-700 hover:bg-green-200 dark:hover:bg-green-900/50',
      icon: <CheckCircle className="h-3 w-3" />
    },
    red: {
      badge: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 border-red-300 dark:border-red-700 hover:bg-red-200 dark:hover:bg-red-900/50',
      icon: <XCircle className="h-3 w-3" />
    },
    yellow: {
      badge: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 border-yellow-300 dark:border-yellow-700 hover:bg-yellow-200 dark:hover:bg-yellow-900/50',
      icon: <AlertTriangle className="h-3 w-3" />
    },
    blue: {
      badge: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-blue-300 dark:border-blue-700 hover:bg-blue-200 dark:hover:bg-blue-900/50',
      icon: <Info className="h-3 w-3" />
    }
  };
  
  const scheme = colorSchemes[colorScheme];
  
  const handleClick = async () => {
    setShowModal(true);
    
    if (!ruleDetails && !loading) {
      setLoading(true);
      try {
        const selectedRuleSetId = localStorage.getItem('selectedRuleSetId');
        if (selectedRuleSetId) {
          // Try exact match first, then broader search
          // First try exact match
          let response = await api.get(`/rules/rule-sets/${selectedRuleSetId}/rules?rule_number=${ruleNumber}`);
          let rules = await response;
          
          // We should get exactly one rule or none
          if (rules && rules.length > 0) {
            setRuleDetails(rules[0]);
          } else {
            // If exact match failed, try search as fallback
            response = await api.get(`/rules/rule-sets/${selectedRuleSetId}/rules?search_text=${ruleNumber}&limit=1`);
            rules = await response;
            if (rules && rules.length > 0) {
              setRuleDetails(rules[0]);
            }
          }
        }
      } catch (error) {
        console.error('Error fetching rule details:', error);
      } finally {
        setLoading(false);
      }
    }
  };
  
  return (
    <>
      {/* Clickable Badge */}
      <button
        className={`inline-flex items-center gap-1 px-2 py-1 text-xs rounded border transition-colors cursor-pointer ${scheme.badge}`}
        onClick={handleClick}
      >
        {scheme.icon}
        <span className="font-semibold">Rule {ruleNumber}</span>
      </button>
      
      {/* Modal with Rule Details and Violation Info */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/50" onClick={() => setShowModal(false)} />
          <div className="relative bg-white dark:bg-slate-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="sticky top-0 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {scheme.icon}
                  <h3 className="font-semibold text-lg">
                    Rule {ruleNumber}
                  </h3>
                </div>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
                  title="Close (Esc)"
                >
                  <XCircle className="h-5 w-5" />
                </button>
              </div>
            </div>
            
            <div className="p-4 space-y-4">
              {/* Violation Info (if applicable) */}
              {type === 'violation' && issue && (
                <div className={`p-3 rounded-lg border ${
                  colorScheme === 'red' ? 'bg-red-50 dark:bg-red-900/20 border-red-300 dark:border-red-700' :
                  colorScheme === 'yellow' ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-300 dark:border-yellow-700' :
                  'bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700'
                }`}>
                  <h4 className="font-semibold text-sm mb-2">Why this rule is {
                    colorScheme === 'red' ? 'missing/critical' : 
                    colorScheme === 'yellow' ? 'inadequate' : 
                    'flagged'
                  }:</h4>
                  <p className="text-sm">{issue.description}</p>
                  {issue.issue_type && (
                    <div className="mt-2">
                      <span className="text-xs px-2 py-0.5 rounded-full bg-white/50 dark:bg-black/20">
                        {issue.issue_type}
                      </span>
                    </div>
                  )}
                </div>
              )}
              
              {/* Compliant Info */}
              {type === 'compliant' && (
                <div className="p-3 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-300 dark:border-green-700">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" />
                    <span className="font-semibold text-sm text-green-700 dark:text-green-300">
                      This paragraph is compliant with this rule
                    </span>
                  </div>
                </div>
              )}
              
              {/* Rule Details */}
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-slate-500" />
                  <span className="ml-2">Loading rule details...</span>
                </div>
              ) : ruleDetails ? (
                <div className="space-y-3">
                  <div>
                    <h4 className="font-semibold text-sm text-slate-900 dark:text-white">
                      {ruleDetails.rule_title}
                    </h4>
                    {ruleDetails.rulebook_hierarchy && (
                      <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                        {ruleDetails.rulebook_hierarchy}
                      </p>
                    )}
                  </div>
                  
                  {ruleDetails.effective_start_date && (
                    <div className="text-xs text-slate-600 dark:text-slate-400">
                      <span className="font-medium">Effective:</span> {new Date(ruleDetails.effective_start_date).toLocaleDateString()}
                      {ruleDetails.effective_end_date && (
                        <span> - {new Date(ruleDetails.effective_end_date).toLocaleDateString()}</span>
                      )}
                    </div>
                  )}

                  {ruleDetails.summary && (
                    <div>
                      <h5 className="font-medium text-sm mb-1">Summary</h5>
                      <p className="text-sm text-slate-700 dark:text-slate-300">
                        {ruleDetails.summary}
                      </p>
                    </div>
                  )}

                  <div>
                    <h5 className="font-medium text-sm mb-1">Full Rule Text</h5>
                    <div className="p-3 bg-slate-50 dark:bg-slate-900/50 rounded-lg">
                      <p className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap">
                        {ruleDetails.rule_text}
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-sm text-slate-500">
                  Rule details could not be loaded.
                </div>
              )}
              
              {/* Close Button at Bottom */}
              <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
                <Button
                  onClick={() => setShowModal(false)}
                  className="w-full"
                  variant="outline"
                >
                  Close
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

// Wrapper for violation badges
const ViolationBadge: React.FC<{ issue: any; colorScheme: 'red' | 'yellow' | 'blue' }> = ({ issue, colorScheme }) => {
  return <RuleBadge ruleNumber={issue.rule_number} type="violation" issue={issue} colorScheme={colorScheme} />;
};

// Compliance Issue Card Component with color coding
const ComplianceIssueCard: React.FC<{ issue: any; colorScheme: 'red' | 'yellow' | 'blue'; paragraphIndex: number; issueIndex: number }> = ({ issue, colorScheme, paragraphIndex, issueIndex }) => {
  const [showExplanation, setShowExplanation] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [showRecommendation, setShowRecommendation] = useState(false);
  
  const colorSchemes = {
    red: {
      container: 'bg-red-50 border-red-300 dark:bg-red-900/20 dark:border-red-700',
      text: 'text-red-700 dark:text-red-300',
      icon: <XCircle className="h-4 w-4 text-red-600 dark:text-red-400" />,
      ruleColor: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 border-red-300 dark:border-red-700'
    },
    yellow: {
      container: 'bg-yellow-50 border-yellow-300 dark:bg-yellow-900/20 dark:border-yellow-700',
      text: 'text-yellow-700 dark:text-yellow-300',
      icon: <AlertTriangle className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />,
      ruleColor: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 border-yellow-300 dark:border-yellow-700'
    },
    blue: {
      container: 'bg-blue-50 border-blue-300 dark:bg-blue-900/20 dark:border-blue-700',
      text: 'text-blue-700 dark:text-blue-300',
      icon: <Info className="h-4 w-4 text-blue-600 dark:text-blue-400" />,
      ruleColor: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-blue-300 dark:border-blue-700'
    }
  };

  const scheme = colorSchemes[colorScheme];

  return (
    <div className="space-y-2">
      {/* Violation Card - Clickable */}
      <div className={`rounded-lg border ${scheme.container}`}>
        <button
          onClick={() => setShowExplanation(!showExplanation)}
          className="w-full p-3 text-left hover:bg-black/5 dark:hover:bg-white/5 transition-colors rounded-lg"
        >
          <div className="flex items-start gap-2">
            <div className="mt-0.5 flex-shrink-0">
              {scheme.icon}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`text-xs font-semibold px-2 py-1 rounded border ${scheme.ruleColor}`}>
                  Rule {issue.rule_number}
                </span>
                {issue.rule_title && (
                  <span className={`text-xs ${scheme.text}`}>
                    {issue.rule_title}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs opacity-60">
                  {issue.issue_type}
                </span>
                <span className="text-xs opacity-50 flex items-center gap-1">
                  {showExplanation ? (
                    <>Hide details <ChevronUp className="h-3 w-3" /></>
                  ) : (
                    <>Show details <ChevronDown className="h-3 w-3" /></>
                  )}
                </span>
              </div>
            </div>
          </div>
        </button>
        
        {/* Explanation - Only shown when expanded */}
        {showExplanation && (
          <div className="px-3 pb-3 -mt-1">
            <div className={`text-xs leading-relaxed p-2 rounded bg-white/50 dark:bg-black/20 ${scheme.text}`}>
              {issue.description}
            </div>
          </div>
        )}
      </div>
      
      {/* Document Preview with Fixes - Collapsible */}
      {issue.current_text && (
        <div className="ml-6">
          <button
            onClick={() => setShowPreview(!showPreview)}
            className="flex items-center gap-2 text-xs font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 transition-colors mb-2"
          >
            {showPreview ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
            {showPreview ? 'Hide' : 'Show'} Document Preview with Fixes
          </button>
          {showPreview && (
            <div className="grid md:grid-cols-2 gap-2 mb-2">
              <div className="p-2 bg-red-50 dark:bg-red-900/20 rounded border border-red-300 dark:border-red-700">
                <div className="text-xs font-semibold text-red-700 dark:text-red-400 mb-1">Current Text:</div>
                <div className="text-xs text-red-600 dark:text-red-300">{issue.current_text}</div>
              </div>
              {issue.required_text && (
                <div className="p-2 bg-green-50 dark:bg-green-900/20 rounded border border-green-300 dark:border-green-700">
                  <div className="text-xs font-semibold text-green-700 dark:text-green-400 mb-1">Required Text:</div>
                  <div className="text-xs text-green-600 dark:text-green-300">{issue.required_text}</div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
      
      {/* Suggested Fix - Toggleable */}
      {issue.suggested_fix && (
        <div className="ml-6">
          <button
            onClick={() => setShowRecommendation(!showRecommendation)}
            className="flex items-center gap-2 text-xs font-medium text-blue-700 dark:text-blue-300 hover:text-blue-900 dark:hover:text-blue-100 transition-colors mb-2"
          >
            {showRecommendation ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
            {showRecommendation ? 'Hide' : 'Show'} Recommended Actions
          </button>
          {showRecommendation && (
            <div className="p-2 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-300 dark:border-green-700">
              <div className="flex items-start gap-1.5">
                <CheckCircle className="h-3.5 w-3.5 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
                <div className="flex-1">
                  <div className="text-xs text-green-600 dark:text-green-400 leading-relaxed">
                    {issue.suggested_fix}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Keep the old IssueCard for backward compatibility
const IssueCard: React.FC<{ issue: any }> = ({ issue }) => {
  const colorMap = {
    critical: 'red' as const,
    high: 'red' as const,
    medium: 'yellow' as const,
    low: 'blue' as const,
  };
  
  return <ComplianceIssueCard issue={issue} colorScheme={colorMap[issue.severity as keyof typeof colorMap] || 'blue'} />;
};

// Rule Tooltip Component
const RuleTooltip: React.FC<{ 
  ruleNumber: string; 
  showTitle?: boolean;
  ruleTitle?: string;
  className?: string;
  showIcon?: boolean;
}> = ({ ruleNumber, showTitle = false, ruleTitle, className, showIcon = false }) => {
  const [ruleDetails, setRuleDetails] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchRuleDetails = async () => {
    if (loading || ruleDetails) return;
    
    setLoading(true);
    try {
      // Get the current rule set from localStorage or state
      const selectedRuleSetId = localStorage.getItem('selectedRuleSetId');
      if (selectedRuleSetId) {
        const response = await api.get(`/rules/rule-sets/${selectedRuleSetId}/rules?search_text=${ruleNumber}&limit=1`);
        const rules = await response;
        if (rules && rules.length > 0) {
          setRuleDetails(rules[0]);
        }
      }
    } catch (error) {
      console.error('Error fetching rule details:', error);
    } finally {
      setLoading(false);
    }
  };

  const defaultClassName = "inline-flex items-center px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs rounded hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors cursor-pointer";

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            className={className || defaultClassName}
            onMouseEnter={fetchRuleDetails}
          >
            {showIcon && <CheckCircle className="h-3 w-3" />}
            <span className="font-semibold">Rule {ruleNumber}</span>
            {showTitle && ruleTitle && (
              <span className="ml-1">: {ruleTitle}</span>
            )}
          </button>
        </TooltipTrigger>
        <TooltipContent 
          side="top" 
          className="max-w-xl p-4 max-h-96 overflow-y-auto"
        >
          {loading ? (
            <div className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Loading rule details...</span>
            </div>
          ) : ruleDetails ? (
            <div className="space-y-3">
              <div>
                <h4 className="font-semibold text-sm">
                  Rule {ruleDetails.rule_number}: {ruleDetails.rule_title}
                </h4>
                {ruleDetails.rulebook_hierarchy && (
                  <p className="text-xs text-muted-foreground mt-1">
                    {ruleDetails.rulebook_hierarchy}
                  </p>
                )}
              </div>
              
              {ruleDetails.effective_start_date && (
                <div className="text-xs text-muted-foreground">
                  Effective: {new Date(ruleDetails.effective_start_date).toLocaleDateString()}
                  {ruleDetails.effective_end_date && (
                    <span> - {new Date(ruleDetails.effective_end_date).toLocaleDateString()}</span>
                  )}
                </div>
              )}

              {ruleDetails.summary && (
                <div>
                  <h5 className="font-medium text-xs mb-1">Summary</h5>
                  <p className="text-xs text-muted-foreground">
                    {ruleDetails.summary}
                  </p>
                </div>
              )}

              <div>
                <h5 className="font-medium text-xs mb-1">Full Text</h5>
                <p className="text-xs text-muted-foreground whitespace-pre-wrap">
                  {ruleDetails.rule_text}
                </p>
              </div>
            </div>
          ) : (
            <div className="text-xs text-muted-foreground">
              Hover to load rule details
            </div>
          )}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

// Recommendations Section Component with toggles
const RecommendationsSection: React.FC<{ 
  suggestedFixes: any[]; 
  paragraphIndex: number;
  violatedRules: any[];
  showRecommendations: boolean;
}> = ({ suggestedFixes, paragraphIndex, violatedRules, showRecommendations }) => {
  const [showPreviews, setShowPreviews] = useState<Set<string>>(new Set());

  const togglePreview = (issueIdx: number) => {
    const key = `${paragraphIndex}-${issueIdx}`;
    const newShowPreviews = new Set(showPreviews);
    if (newShowPreviews.has(key)) {
      newShowPreviews.delete(key);
    } else {
      newShowPreviews.add(key);
    }
    setShowPreviews(newShowPreviews);
  };

  if (!showRecommendations) return null;

  return (
    <>
      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">
        <AlertCircle className="h-3.5 w-3.5" />
        Recommended Actions
      </div>
      
      {suggestedFixes.map((issue: any, idx: number) => {
        const isHighSeverity = ['critical', 'high'].includes(issue.severity);
        const isMediumSeverity = issue.severity === 'medium';
        
        const severityStyles = isHighSeverity 
          ? 'bg-red-50/80 dark:bg-red-900/30 border-red-300/50 dark:border-red-700/50 text-red-700 dark:text-red-300'
          : isMediumSeverity
          ? 'bg-yellow-50/80 dark:bg-yellow-900/30 border-yellow-300/50 dark:border-yellow-700/50 text-yellow-700 dark:text-yellow-300'
          : 'bg-blue-50/80 dark:bg-blue-900/30 border-blue-300/50 dark:border-blue-700/50 text-blue-700 dark:text-blue-300';
        
        const icon = isHighSeverity 
          ? <XCircle className="h-3 w-3" />
          : isMediumSeverity 
          ? <AlertTriangle className="h-3 w-3" />
          : <Info className="h-3 w-3" />;
        
        const fullIssue = violatedRules.find((v: any) => 
          v.rule_number === issue.rule_number && v.suggested_fix === issue.suggested_fix
        );
        
        return (
          <div key={idx} className="ml-5 space-y-2">
            {/* Document Preview Toggle */}
            {fullIssue?.current_text && (
              <button
                onClick={() => togglePreview(idx)}
                className="flex items-center gap-1.5 text-xs font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 transition-colors"
              >
                {showPreviews.has(`${paragraphIndex}-${idx}`) ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                {showPreviews.has(`${paragraphIndex}-${idx}`) ? 'Hide' : 'Show'} Document Preview
              </button>
            )}
            
            {/* Document Preview */}
            {showPreviews.has(`${paragraphIndex}-${idx}`) && fullIssue?.current_text && (
              <div className="grid md:grid-cols-2 gap-2 ml-5">
                <div className="p-2 bg-red-50 dark:bg-red-900/20 rounded text-xs border border-red-300 dark:border-red-700">
                  <div className="font-semibold text-red-700 dark:text-red-400 mb-1">Current:</div>
                  <div className="text-red-600 dark:text-red-300">{fullIssue.current_text}</div>
                </div>
                {fullIssue.required_text && (
                  <div className="p-2 bg-green-50 dark:bg-green-900/20 rounded text-xs border border-green-300 dark:border-green-700">
                    <div className="font-semibold text-green-700 dark:text-green-400 mb-1">Required:</div>
                    <div className="text-green-600 dark:text-green-300">{fullIssue.required_text}</div>
                  </div>
                )}
              </div>
            )}
            
            {/* Recommendation */}
            <div className={`p-2 rounded border ${severityStyles}`}>
              <div className="flex items-start gap-1.5">
                <div className="mt-0.5">{icon}</div>
                <div className="flex-1">
                  <div className="text-xs mb-1 font-medium">
                    For Rule {issue.rule_number}:
                  </div>
                  <div className="text-xs leading-relaxed">
                    {issue.suggested_fix}
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </>
  );
};

const ComplianceAnalyzer: React.FC = () => {
  const { getToken } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const { sessionId: urlSessionId } = useParams<{ sessionId?: string }>();
  
  const [documentText, setDocumentText] = useState('');
  const [showMarkdownPreview, setShowMarkdownPreview] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [results, setResults] = useState<any>(null);
  const [ruleSets, setRuleSets] = useState<RuleSet[]>([]);
  const [selectedRuleSetId, setSelectedRuleSetId] = useState<string>('');
  const [effectiveDate, setEffectiveDate] = useState<string>('');
  const [forceNewAnalysis, setForceNewAnalysis] = useState(false);
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [historyItems, setHistoryItems] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [showAllRecommendations, setShowAllRecommendations] = useState(false);
  const [progress, setProgress] = useState<{
    percentage: number;
    processed: number;
    total: number;
    startTime?: Date;
    estimatedEndTime?: Date;
    averageTimePerParagraph?: number;
    etaString?: string;
  }>({
    percentage: 0,
    processed: 0,
    total: 0
  });

  // Fetch available rule sets
  useEffect(() => {
    fetchRuleSets();
  }, []);

  // Store selected rule set ID in localStorage for tooltip access and persistence
  useEffect(() => {
    if (selectedRuleSetId) {
      localStorage.setItem('selectedRuleSetId', selectedRuleSetId);  // For tooltip access
      localStorage.setItem('lastSelectedRuleSetId', selectedRuleSetId);  // For persistence across sessions
    }
  }, [selectedRuleSetId]);

  // Load analysis from URL if present
  useEffect(() => {
    if (urlSessionId) {
      // Always load if URL has a session ID and we don't have results
      // or if the session ID is different
      if (!results || urlSessionId !== sessionId) {
        loadAnalysis(urlSessionId);
      }
    }
  }, [urlSessionId]);

  // Handle escape key for modals
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (showHistoryModal) {
          setShowHistoryModal(false);
        }
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [showHistoryModal]);

  const fetchHistory = async () => {
    setLoadingHistory(true);
    try {
      const token = await getToken();
      const response = await fetch(`${import.meta.env.VITE_API_URL}/compliance/history?limit=50`, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setHistoryItems(data.analyses || []);
      }
    } catch (error) {
      console.error('Error fetching history:', error);
      toast({
        title: 'Error',
        description: 'Failed to fetch analysis history',
        variant: 'destructive',
      });
    } finally {
      setLoadingHistory(false);
    }
  };

  const deleteAnalysis = async (analysisSessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this analysis?')) {
      return;
    }

    try {
      const token = await getToken();
      const response = await fetch(`${import.meta.env.VITE_API_URL}/compliance/history/${analysisSessionId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        },
      });
      
      if (response.ok) {
        setHistoryItems(prev => prev.filter(h => h.session_id !== analysisSessionId));
        toast({
          title: 'Success',
          description: 'Analysis deleted successfully',
        });
      }
    } catch (error) {
      console.error('Error deleting analysis:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete analysis',
        variant: 'destructive',
      });
    }
  };

  const fetchRuleSets = async () => {
    try {
      const response = await api.get('/rules/rule-sets?include_all=true');
      const ruleSetsData = response || [];
      setRuleSets(ruleSetsData);
      
      // Try to restore last selected rule set from localStorage
      const lastSelectedId = localStorage.getItem('lastSelectedRuleSetId');
      
      if (lastSelectedId && ruleSetsData.some(rs => rs.id.toString() === lastSelectedId)) {
        // Use the last selected if it still exists
        setSelectedRuleSetId(lastSelectedId);
      } else if (ruleSetsData.length > 0) {
        // Otherwise, select the first one
        setSelectedRuleSetId(ruleSetsData[0].id.toString());
      }
    } catch (error) {
      console.error('Error fetching rule sets:', error);
      toast({
        title: 'Error',
        description: 'Failed to fetch rule sets',
        variant: 'destructive',
      });
    }
  };

  const loadAnalysis = async (analysisSessionId: string) => {
    setResults(null);
    setSessionId(analysisSessionId);
    
    try {
      const token = await getToken();
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/compliance/results/${analysisSessionId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        
        // Check if analysis is still processing
        if (data.status === 'processing') {
          setIsAnalyzing(true);
          // Set initial progress
          setProgress({
            percentage: data.progress_percentage || 0,
            processed: data.paragraphs_processed || 0,
            total: data.total_paragraphs || 0,
            startTime: new Date(),
            etaString: 'Calculating...'
          });
          // Start polling for updates
          pollForResults(analysisSessionId);
        } else {
          setIsAnalyzing(false);
          setResults(data);
        }
        
        // Set the document text if available
        if (data.document_text) {
          setDocumentText(data.document_text);
        }
        
        // Set the rule set if available
        if (data.rule_set_id) {
          setSelectedRuleSetId(data.rule_set_id.toString());
        }
        
        // Update URL if not already set
        if (!urlSessionId || urlSessionId !== analysisSessionId) {
          navigate(`/compliance/analysis/${analysisSessionId}`, { replace: true });
        }
        
        toast({
          title: 'Analysis Loaded',
          description: 'Previous analysis has been loaded successfully.',
        });
      } else {
        throw new Error('Failed to load analysis');
      }
    } catch (error) {
      console.error('Error loading analysis:', error);
      toast({
        title: 'Error',
        description: 'Failed to load analysis. Please try again.',
        variant: 'destructive',
      });
    }
  };

  const handleSelectAnalysis = (analysisSessionId: string) => {
    // Force reload even if it's the same session
    if (analysisSessionId === sessionId) {
      // Clear current state to force reload
      setResults(null);
      setSessionId(null);
    }
    navigate(`/compliance/analysis/${analysisSessionId}`);
  };

  const handleNewAnalysis = () => {
    setResults(null);
    setDocumentText('');
    setSessionId(null);
    setProgress({ percentage: 0, processed: 0, total: 0 });
    navigate('/compliance');
  };

  const handleFileRead = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      setDocumentText(text);
      toast({
        title: 'File Loaded',
        description: `Successfully loaded ${file.name}`,
      });
    };
    reader.onerror = () => {
      toast({
        title: 'Error',
        description: 'Failed to read file',
        variant: 'destructive',
      });
    };
    reader.readAsText(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    const textFile = files.find(file => 
      file.type === 'text/plain' || 
      file.type === 'text/markdown' ||
      file.name.endsWith('.md') ||
      file.name.endsWith('.txt')
    );

    if (textFile) {
      handleFileRead(textFile);
    } else if (files.length > 0) {
      // Try to read the first file anyway
      handleFileRead(files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileRead(file);
    }
  };

  const analyzeDocument = async () => {
    if (!documentText.trim() || documentText.length < 100) {
      toast({
        title: 'Invalid Input',
        description: 'Please enter at least 100 characters of document text.',
        variant: 'destructive',
      });
      return;
    }

    if (!selectedRuleSetId) {
      toast({
        title: 'No Rule Set Selected',
        description: 'Please select a rule set for analysis.',
        variant: 'destructive',
      });
      return;
    }

    setIsAnalyzing(true);
    setResults(null);
    setProgress({ percentage: 0, processed: 0, total: 0 });

    try {
      const token = await getToken();
      const response = await fetch(`${import.meta.env.VITE_API_URL}/compliance/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ 
          document_text: documentText,
          rule_set_id: parseInt(selectedRuleSetId),
          effective_date: effectiveDate || undefined,
          force_new: forceNewAnalysis
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to analyze document');
      }

      const data = await response.json();
      setSessionId(data.session_id);
      
      // Update URL with new session ID
      navigate(`/compliance/analysis/${data.session_id}`, { replace: true });
      
      // Poll for results
      pollForResults(data.session_id);
      
    } catch (error) {
      console.error('Analysis error:', error);
      toast({
        title: 'Analysis Failed',
        description: 'An error occurred while analyzing the document.',
        variant: 'destructive',
      });
      setIsAnalyzing(false);
    }
  };

  const pollForResults = async (sessionId: string) => {
    const maxAttempts = 3000; // 50 minutes for large docs
    let attempts = 0;
    const startTime = new Date();
    let lastProcessed = 0;
    let lastUpdateTime = new Date();
    let processingRates: number[] = [];

    const poll = async () => {
      try {
        const token = await getToken();
        const response = await fetch(
          `${import.meta.env.VITE_API_URL}/compliance/results/${sessionId}`,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error('Failed to fetch results');
        }

        const data = await response.json();

        // Update progress with ETA calculation
        if (data.total_paragraphs > 0) {
          const currentProcessed = data.paragraphs_processed || 0;
          const total = data.total_paragraphs;
          
          // Calculate processing rate and ETA based on average time per paragraph
          let etaString = 'Calculating...';
          let estimatedEndTime: Date | undefined;
          let averageTimePerParagraph: number | undefined;
          
          if (currentProcessed > 0 && startTime) {
            const currentTime = new Date();
            const elapsedSeconds = (currentTime.getTime() - startTime.getTime()) / 1000;
            
            // Calculate overall average time per paragraph
            averageTimePerParagraph = elapsedSeconds / currentProcessed;
            
            // Track processing rate changes when progress actually updates
            if (currentProcessed > lastProcessed) {
              // Calculate ACTUAL time since last update (not assumed 2 seconds)
              const actualTimeSinceUpdate = (currentTime.getTime() - lastUpdateTime.getTime()) / 1000;
              const paragraphsProcessed = currentProcessed - lastProcessed;
              
              // Only record rate if time difference is reasonable (avoid divide by zero)
              if (actualTimeSinceUpdate > 0.1) {
                const recentRate = paragraphsProcessed / actualTimeSinceUpdate; // paragraphs per second
                processingRates.push(recentRate);
                
                // Keep only last 5 measurements (fewer for batch processing)
                if (processingRates.length > 5) {
                  processingRates.shift();
                }
              }
              
              lastProcessed = currentProcessed;
              lastUpdateTime = currentTime;
            }
            
            // Calculate ETA more conservatively for batch processing
            let estimatedSecondsRemaining: number;
            const remainingParas = total - currentProcessed;
            
            // For batch processing, use overall average as it's more reliable
            // Only use recent rates if we have enough samples and they're consistent
            if (processingRates.length >= 3) {
              // Check if rates are consistent (not varying wildly due to batching)
              const rateVariance = Math.max(...processingRates) / Math.min(...processingRates);
              
              if (rateVariance < 2) {
                // Rates are consistent, use weighted average
                const recentAvg = processingRates.reduce((a, b) => a + b, 0) / processingRates.length;
                const overallRate = currentProcessed / elapsedSeconds;
                const effectiveRate = (recentAvg * 0.3 + overallRate * 0.7); // 30% recent, 70% overall for stability
                estimatedSecondsRemaining = remainingParas / effectiveRate;
              } else {
                // Rates vary too much (batch processing), use overall average
                estimatedSecondsRemaining = remainingParas * averageTimePerParagraph;
              }
            } else {
              // Not enough data, use simple average
              estimatedSecondsRemaining = remainingParas * averageTimePerParagraph;
            }
            
            // Add 20% buffer for batch processing overhead
            estimatedSecondsRemaining *= 1.2;
            
            // Debug logging for ETA calculation
            console.log('ETA Debug:', {
              currentProcessed,
              total,
              elapsedSeconds: Math.round(elapsedSeconds),
              averageTimePerParagraph: averageTimePerParagraph.toFixed(2),
              remainingParas,
              estimatedSecondsRemaining: Math.round(estimatedSecondsRemaining),
              processingRatesCount: processingRates.length,
              recentRates: processingRates.map(r => r.toFixed(2))
            });
            
            if (estimatedSecondsRemaining > 0) {
              estimatedEndTime = new Date(Date.now() + estimatedSecondsRemaining * 1000);
              
              // Format ETA string
              if (estimatedSecondsRemaining < 60) {
                etaString = `~${Math.ceil(estimatedSecondsRemaining)}s`;
              } else if (estimatedSecondsRemaining < 3600) {
                const minutes = Math.ceil(estimatedSecondsRemaining / 60);
                etaString = `~${minutes} min`;
              } else {
                const hours = Math.floor(estimatedSecondsRemaining / 3600);
                const minutes = Math.ceil((estimatedSecondsRemaining % 3600) / 60);
                etaString = `~${hours}h ${minutes}m`;
              }
            }
          }
          
          setProgress({
            percentage: data.progress_percentage || 0,
            processed: currentProcessed,
            total: total,
            startTime: startTime,
            estimatedEndTime: estimatedEndTime,
            averageTimePerParagraph: averageTimePerParagraph,
            etaString: etaString
          });
        }

        // Always update results with latest data (including partial)
        setResults(data);

        if (data.status === 'completed') {
          setIsAnalyzing(false);
          const totalIssues = data.paragraphs?.reduce((acc: number, p: any) => acc + (p.issues?.length || 0), 0) || 0;
          toast({
            title: 'Analysis Complete',
            description: `Analyzed ${data.total_paragraphs} paragraphs and found ${totalIssues} compliance issues.`,
          });
        } else if (data.status === 'failed') {
          throw new Error('Analysis failed');
        } else if (attempts < maxAttempts) {
          attempts++;
          // Poll faster initially, then slow down
          const delay = attempts < 30 ? 1000 : 2000;
          setTimeout(poll, delay);
        } else {
          throw new Error('Analysis timeout');
        }
      } catch (error) {
        console.error('Polling error:', error);
        setIsAnalyzing(false);
        toast({
          title: 'Error',
          description: 'Failed to retrieve analysis results.',
          variant: 'destructive',
        });
      }
    };

    poll();
  };

  const handleAnalyze = () => {
    analyzeDocument();
  };

  const handleExportToWord = async () => {
    if (!sessionId) return;
    
    try {
      const token = await getToken();
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/compliance/results/${sessionId}/export/docx`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to export document');
      }

      // Get the blob from response
      const blob = await response.blob();
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `compliance_analysis_${sessionId.substring(0, 8)}_${new Date().toISOString().split('T')[0]}.docx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast({
        title: 'Export Successful',
        description: 'Your compliance analysis has been exported to Word.',
        variant: 'default',
      });
    } catch (error) {
      console.error('Error exporting to Word:', error);
      toast({
        title: 'Export Failed',
        description: 'Failed to export the analysis to Word.',
        variant: 'destructive',
      });
    }
  };

  const handleStopAnalysis = async () => {
    if (!sessionId) return;
    
    try {
      const token = await getToken();
      const response = await fetch(`${import.meta.env.VITE_API_URL}/compliance/analysis/${sessionId}/stop`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        toast({
          title: 'Analysis Stopped',
          description: 'The analysis has been stopped.',
          variant: 'default',
        });
        setIsAnalyzing(false);
        setSessionId(null);
        setProgress({ percentage: 0, processed: 0, total: 0 });
      } else {
        toast({
          title: 'Error',
          description: 'Failed to stop analysis.',
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Error stopping analysis:', error);
      toast({
        title: 'Error',
        description: 'Failed to stop analysis.',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-8">
        {/* Header with History Button */}
        <div className="mb-8 flex items-start justify-between">
          <div>
            <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-2">
              Compliance Analyzer
            </h1>
            <p className="text-lg text-slate-600 dark:text-slate-300">
              Analyze your documents against selected rule sets
            </p>
          </div>
          <Button
            onClick={() => {
              fetchHistory();
              setShowHistoryModal(true);
            }}
            variant="outline"
            className="flex items-center gap-2"
          >
            <History className="h-4 w-4" />
            Analysis History
          </Button>
        </div>

        {/* Input Section */}
        {!results && (
          <Card className="mb-8 p-6 bg-white dark:bg-slate-800 shadow-xl">
            {/* Rule Set Selector */}
            <div className="mb-4">
              <Label htmlFor="ruleSet" className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-2">
                Select Rule Set
              </Label>
              <Select value={selectedRuleSetId} onValueChange={setSelectedRuleSetId}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select a rule set for analysis" />
                </SelectTrigger>
                <SelectContent>
                  {ruleSets.length === 0 ? (
                    <SelectItem value="no-sets" disabled>
                      No rule sets available
                    </SelectItem>
                  ) : (
                    ruleSets.map((ruleSet) => (
                      <SelectItem key={ruleSet.id} value={ruleSet.id.toString()}>
                        {ruleSet.name} ({ruleSet.rule_count} rules)
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
              {selectedRuleSetId && ruleSets.find(rs => rs.id.toString() === selectedRuleSetId)?.description && (
                <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                  {ruleSets.find(rs => rs.id.toString() === selectedRuleSetId)?.description}
                </p>
              )}
            </div>

            <div className="mb-4">
              <Label htmlFor="effective-date" className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-2">
                <Calendar className="inline-block h-4 w-4 mr-1" />
                Analyze rules as of date (optional)
              </Label>
              <input
                type="date"
                id="effective-date"
                value={effectiveDate}
                onChange={(e) => setEffectiveDate(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isAnalyzing}
              />
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                {effectiveDate ? 
                  `Will analyze using rules effective on ${new Date(effectiveDate).toLocaleDateString()}` :
                  'Leave blank to use all current rules'
                }
              </p>
            </div>

            <div className="mb-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={forceNewAnalysis}
                  onChange={(e) => setForceNewAnalysis(e.target.checked)}
                  className="h-4 w-4 rounded border-slate-300 dark:border-slate-600 text-blue-600 focus:ring-blue-500"
                  disabled={isAnalyzing}
                />
                <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
                  Force new analysis (bypass cache)
                </span>
              </label>
              <p className="mt-1 ml-6 text-xs text-slate-500 dark:text-slate-400">
                Check this to ignore cached results and perform a fresh analysis
              </p>
            </div>

            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <Label htmlFor="document" className="block text-sm font-medium text-slate-700 dark:text-slate-200">
                  Paste or drop your document below
                </Label>
                <div className="flex gap-1">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".txt,.md,text/plain,text/markdown"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => fileInputRef.current?.click()}
                    className="px-3 py-1"
                  >
                    <Upload className="h-3.5 w-3.5 mr-1" />
                    Upload
                  </Button>
                  <div className="w-px bg-slate-300 dark:bg-slate-600" />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowMarkdownPreview(false)}
                    className={cn(
                      "px-3 py-1",
                      !showMarkdownPreview && "bg-slate-100 dark:bg-slate-800"
                    )}
                  >
                    <Edit className="h-3.5 w-3.5 mr-1" />
                    Edit
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowMarkdownPreview(true)}
                    className={cn(
                      "px-3 py-1",
                      showMarkdownPreview && "bg-slate-100 dark:bg-slate-800"
                    )}
                  >
                    <Eye className="h-3.5 w-3.5 mr-1" />
                    Preview
                  </Button>
                </div>
              </div>
              
              {!showMarkdownPreview ? (
                <div
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  className="relative"
                >
                  {isDragging && (
                    <div className="absolute inset-0 z-10 flex items-center justify-center bg-blue-50 dark:bg-blue-900/20 border-2 border-dashed border-blue-400 dark:border-blue-600 rounded-md">
                      <div className="text-center">
                        <Upload className="h-12 w-12 mx-auto mb-2 text-blue-600 dark:text-blue-400" />
                        <p className="text-blue-600 dark:text-blue-400 font-medium">Drop your file here</p>
                        <p className="text-sm text-blue-500 dark:text-blue-300">Supports .txt and .md files</p>
                      </div>
                    </div>
                  )}
                  <Textarea
                    id="document"
                    placeholder="Enter your Written Supervisory Procedures document text here. Supports markdown formatting...\n\nOr drag and drop a .txt or .md file here!"
                    className={cn(
                      "min-h-[400px] font-mono text-sm bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-700",
                      isDragging && "opacity-50"
                    )}
                    value={documentText}
                    onChange={(e) => setDocumentText(e.target.value)}
                    disabled={isAnalyzing}
                  />
                  <div className="mt-2 flex items-center justify-between text-sm text-slate-500 dark:text-slate-400">
                    <span>{documentText.length} characters • {documentText.split(/\n\n+/).filter(p => p.trim()).length} paragraphs</span>
                    <span className="text-xs">Markdown supported • Drag & drop enabled</span>
                  </div>
                </div>
              ) : (
                <div 
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  className="min-h-[400px] p-4 bg-slate-50 dark:bg-slate-900 border rounded-md border-slate-200 dark:border-slate-700 overflow-auto relative"
                >
                  {isDragging && (
                    <div className="absolute inset-0 z-10 flex items-center justify-center bg-blue-50 dark:bg-blue-900/20 border-2 border-dashed border-blue-400 dark:border-blue-600 rounded-md">
                      <div className="text-center">
                        <Upload className="h-12 w-12 mx-auto mb-2 text-blue-600 dark:text-blue-400" />
                        <p className="text-blue-600 dark:text-blue-400 font-medium">Drop your file here</p>
                        <p className="text-sm text-blue-500 dark:text-blue-300">Supports .txt and .md files</p>
                      </div>
                    </div>
                  )}
                  {documentText.trim() ? (
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          h1: ({children}) => <h1 className="text-xl font-bold mb-3 mt-4">{children}</h1>,
                          h2: ({children}) => <h2 className="text-lg font-bold mb-2 mt-3">{children}</h2>,
                          h3: ({children}) => <h3 className="text-base font-semibold mb-2 mt-3">{children}</h3>,
                          p: ({children}) => <p className="mb-3">{children}</p>,
                          ul: ({children}) => <ul className="list-disc list-inside mb-3 space-y-1">{children}</ul>,
                          ol: ({children}) => <ol className="list-decimal list-inside mb-3 space-y-1">{children}</ol>,
                          li: ({children}) => <li className="ml-2">{children}</li>,
                          blockquote: ({children}) => <blockquote className="border-l-4 border-slate-300 dark:border-slate-600 pl-4 italic my-3">{children}</blockquote>,
                          code: ({inline, children}) => inline ? 
                            <code className="px-1.5 py-0.5 bg-slate-200 dark:bg-slate-700 rounded text-xs font-mono">{children}</code> :
                            <pre className="bg-slate-200 dark:bg-slate-700 rounded p-3 overflow-x-auto my-3"><code className="text-xs font-mono">{children}</code></pre>,
                          table: ({children}) => <table className="border-collapse border border-slate-300 dark:border-slate-600 my-3 w-full">{children}</table>,
                          thead: ({children}) => <thead className="bg-slate-100 dark:bg-slate-800">{children}</thead>,
                          tbody: ({children}) => <tbody>{children}</tbody>,
                          tr: ({children}) => <tr className="border-b border-slate-300 dark:border-slate-600">{children}</tr>,
                          th: ({children}) => <th className="px-3 py-2 text-left font-semibold border-r border-slate-300 dark:border-slate-600 last:border-r-0">{children}</th>,
                          td: ({children}) => <td className="px-3 py-2 border-r border-slate-300 dark:border-slate-600 last:border-r-0">{children}</td>,
                          hr: () => <hr className="my-4 border-slate-300 dark:border-slate-600" />,
                          strong: ({children}) => <strong className="font-semibold">{children}</strong>,
                          em: ({children}) => <em className="italic">{children}</em>,
                          a: ({href, children}) => <a href={href} className="text-blue-600 dark:text-blue-400 underline hover:opacity-75" target="_blank" rel="noopener noreferrer">{children}</a>,
                        }}
                      >
                        {documentText}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <div className="text-slate-400 dark:text-slate-500 text-sm italic">
                      Enter text in the editor to see a markdown preview...
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="flex gap-2">
              <Button
                onClick={handleAnalyze}
                disabled={!documentText.trim() || isAnalyzing}
                size="lg"
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Analyzing Document...
                  </>
                ) : (
                  'Analyze for Compliance'
                )}
              </Button>
              {isAnalyzing && sessionId && (
                <Button
                  onClick={handleStopAnalysis}
                  size="lg"
                  variant="destructive"
                  className="px-4"
                  title="Stop Analysis"
                >
                  <XCircle className="h-4 w-4" />
                  Stop
                </Button>
              )}
            </div>
          </Card>
        )}

        {/* Enhanced Progress Bar with ETA - Always visible when analyzing */}
        {isAnalyzing && progress.total > 0 && (
          <Card className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
            <div className="flex justify-between items-center text-sm mb-2">
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-blue-600 dark:text-blue-400" />
                <span className="font-medium text-blue-900 dark:text-blue-100">Analyzing document...</span>
              </div>
              <div className="flex items-center gap-3 text-blue-700 dark:text-blue-300">
                {progress.etaString && (
                  <span className="flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" />
                    ETA: {progress.etaString}
                  </span>
                )}
                <span className="font-medium">
                  {progress.processed} / {progress.total}
                </span>
              </div>
            </div>
            
            <div className="relative">
              <div className="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-3 overflow-hidden">
                <div 
                  className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-500 ease-out relative"
                  style={{ width: `${progress.percentage}%` }}
                >
                  {/* Animated stripe pattern */}
                  <div className="absolute inset-0 bg-stripes opacity-20" />
                </div>
              </div>
              <span className="absolute left-1/2 -translate-x-1/2 text-xs font-bold text-white drop-shadow-lg"
                    style={{ top: '1px' }}>
                {progress.percentage}%
              </span>
            </div>
            
            <div className="flex justify-between items-center mt-2">
              <p className="text-xs text-blue-600 dark:text-blue-400">
                {progress.processed > 0 && progress.averageTimePerParagraph && (
                  <span>Processing ~{(1 / progress.averageTimePerParagraph).toFixed(1)} paragraphs/sec ({progress.averageTimePerParagraph.toFixed(1)}s per paragraph)</span>
                )}
              </p>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                Results updating in real-time below ↓
              </p>
            </div>
          </Card>
        )}

        {/* Back Button */}
        {results && (
          <Button
            variant="outline"
            onClick={handleNewAnalysis}
            className="mb-4"
          >
            ← New Analysis
          </Button>
        )}

        {/* Results Section - Show partial results during analysis */}
        {(results || (isAnalyzing && progress.processed > 0)) && (
          <div className="space-y-6">
            {/* Summary Card with Live Updates */}
            <Card className="p-6 bg-white dark:bg-slate-800 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-6">
                  <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
                    Analysis Results {isAnalyzing && '(Live Updates)'}
                  </h2>
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <Label htmlFor="recommendations-toggle" className="text-sm text-slate-600 dark:text-slate-400 cursor-pointer">
                        Show Recommendations
                      </Label>
                      <Switch
                        id="recommendations-toggle"
                        checked={showAllRecommendations}
                        onCheckedChange={setShowAllRecommendations}
                      />
                    </div>
                    {results && !isAnalyzing && (
                      <Button
                        onClick={handleExportToWord}
                        variant="outline"
                        size="sm"
                        className="flex items-center gap-2"
                      >
                        <Download className="h-4 w-4" />
                        Export to Word
                      </Button>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  {isAnalyzing && progress.total > 0 && (
                    <div className="flex items-center text-sm text-slate-600 dark:text-slate-400">
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Processing... {progress.percentage}% complete ({progress.processed}/{progress.total})
                    </div>
                  )}
                  {isAnalyzing && sessionId && (
                    <Button
                      onClick={handleStopAnalysis}
                      size="sm"
                      variant="destructive"
                      className="flex items-center gap-2"
                      title="Stop Analysis"
                    >
                      <XCircle className="h-4 w-4" />
                      Stop
                    </Button>
                  )}
                </div>
              </div>

              {/* Quick Stats */}
              {results && results.paragraphs && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <div className="bg-slate-50 dark:bg-slate-900 p-3 rounded-lg">
                    <div className="text-2xl font-bold text-slate-900 dark:text-white">
                      {results.paragraphs.length}
                    </div>
                    <div className="text-sm text-slate-600 dark:text-slate-400">
                      Paragraphs Analyzed
                    </div>
                  </div>
                  <div className="bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
                    <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                      {results.paragraphs.reduce((acc: number, p: any) => 
                        acc + p.issues.filter((i: any) => ['critical', 'high'].includes(i.severity)).length, 0
                      )}
                    </div>
                    <div className="text-sm text-slate-600 dark:text-slate-400">
                      Critical/High Issues
                    </div>
                  </div>
                  <div className="bg-yellow-50 dark:bg-yellow-900/20 p-3 rounded-lg">
                    <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                      {results.paragraphs.reduce((acc: number, p: any) => 
                        acc + p.issues.filter((i: any) => i.severity === 'medium').length, 0
                      )}
                    </div>
                    <div className="text-sm text-slate-600 dark:text-slate-400">
                      Medium Issues
                    </div>
                  </div>
                  <div className="bg-green-50 dark:bg-green-900/20 p-3 rounded-lg">
                    <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                      {results.paragraphs.reduce((acc: number, p: any) => 
                        acc + p.issues.filter((i: any) => i.severity === 'success').length, 0
                      )}
                    </div>
                    <div className="text-sm text-slate-600 dark:text-slate-400">
                      Compliant Items
                    </div>
                  </div>
                </div>
              )}
            </Card>

            {/* Document with Side Comments Layout */}
            <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl">
              {results?.paragraphs?.length === 0 && isAnalyzing && (
                <Card className="p-8 bg-white dark:bg-slate-800 text-center">
                  <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
                  <p className="text-slate-600 dark:text-slate-400">
                    Analyzing paragraphs... Results will appear here as they're processed.
                  </p>
                  <p className="text-sm text-slate-500 dark:text-slate-500 mt-2">
                    This may take a few minutes depending on document length.
                  </p>
                </Card>
              )}
              
              {results?.paragraphs?.map((paragraph: any, idx: number) => {
                // Categorize rules by their compliance status
                const satisfiedRules = paragraph.applicable_rules?.filter((rule: string) => 
                  !paragraph.issues?.some((issue: any) => issue.rule_number === rule)
                ) || [];
                
                const violatedRules = paragraph.issues || [];
                const criticalViolations = violatedRules.filter((i: any) => ['critical', 'high'].includes(i.severity));
                const mediumViolations = violatedRules.filter((i: any) => i.severity === 'medium');
                const lowViolations = violatedRules.filter((i: any) => i.severity === 'low');
                
                const hasRulesOrIssues = (paragraph.applicable_rules?.length > 0 || paragraph.issues?.length > 0);
                
                // Get all suggested fixes for this paragraph
                const suggestedFixes = violatedRules.filter((v: any) => v.suggested_fix);
                
                return (
                  <div key={idx} className="relative group">
                    <div className="flex">
                      {/* Left side: Document paragraph + Recommendations */}
                      <div className="flex-1 border-b border-slate-200 dark:border-slate-700">
                        {/* Paragraph content */}
                        <div className="p-6">
                          <div className="flex items-start gap-4">
                            <div className="text-xs text-slate-400 dark:text-slate-500 mt-1 font-mono">
                              {paragraph.index + 1}
                            </div>
                            <div className="flex-1">
                              <p className={`text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed ${
                                hasRulesOrIssues ? 'pr-4' : ''
                              }`}>
                                {paragraph.content}
                              </p>
                            </div>
                          </div>
                        </div>
                        
                        {/* Recommendations under the paragraph - Toggleable */}
                        {suggestedFixes.length > 0 && (
                          <div className="px-6 pb-4 bg-slate-50/50 dark:bg-slate-900/30 border-t border-slate-200 dark:border-slate-700">
                            <div className="pt-3 space-y-2">
                              <RecommendationsSection
                                suggestedFixes={suggestedFixes}
                                paragraphIndex={paragraph.index}
                                violatedRules={violatedRules}
                                showRecommendations={showAllRecommendations}
                              />
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Right side: All Rules organized by status */}
                      <div className={`w-96 border-l border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 ${
                        hasRulesOrIssues ? '' : 'opacity-0'
                      }`}>
                        {hasRulesOrIssues && (
                          <div className="p-4 space-y-4 relative">
                            {/* Arrow pointing to paragraph */}
                            <div className="absolute -left-3 top-8 w-6 h-6 bg-slate-50 dark:bg-slate-900/50 border-l border-t border-slate-200 dark:border-slate-700 transform rotate-45" />
                            
                            {/* Compliant (Green) */}
                            {satisfiedRules.length > 0 && (
                              <div className="space-y-2">
                                <div className="text-xs font-semibold text-green-700 dark:text-green-300 flex items-center gap-1">
                                  <CheckCircle className="h-3.5 w-3.5" />
                                  Compliant
                                </div>
                                <div className="flex flex-wrap gap-1">
                                  {satisfiedRules.map((rule: string) => (
                                    <RuleBadge 
                                      key={rule} 
                                      ruleNumber={rule}
                                      type="compliant"
                                      colorScheme="green"
                                    />
                                  ))}
                                </div>
                              </div>
                            )}
                            
                            {/* Missing/Critical Rules (Red) */}
                            {criticalViolations.length > 0 && (
                              <div className="space-y-2">
                                <div className="text-xs font-semibold text-red-700 dark:text-red-300 flex items-center gap-1">
                                  <XCircle className="h-3.5 w-3.5" />
                                  Missing/Critical
                                </div>
                                <div className="flex flex-wrap gap-1">
                                  {criticalViolations.map((issue: any, idx: number) => (
                                    <ViolationBadge 
                                      key={`critical-${idx}`}
                                      issue={issue}
                                      colorScheme="red"
                                    />
                                  ))}
                                </div>
                              </div>
                            )}
                            
                            {/* Inadequate Rules (Yellow) */}
                            {mediumViolations.length > 0 && (
                              <div className="space-y-2">
                                <div className="text-xs font-semibold text-yellow-700 dark:text-yellow-300 flex items-center gap-1">
                                  <AlertTriangle className="h-3.5 w-3.5" />
                                  Inadequate
                                </div>
                                <div className="flex flex-wrap gap-1">
                                  {mediumViolations.map((issue: any, idx: number) => (
                                    <ViolationBadge 
                                      key={`medium-${idx}`}
                                      issue={issue}
                                      colorScheme="yellow"
                                    />
                                  ))}
                                </div>
                              </div>
                            )}
                            
                            {/* Minor Issues (Blue) */}
                            {lowViolations.length > 0 && (
                              <div className="space-y-2">
                                <div className="text-xs font-semibold text-blue-700 dark:text-blue-300 flex items-center gap-1">
                                  <Info className="h-3.5 w-3.5" />
                                  Minor Issues
                                </div>
                                <div className="flex flex-wrap gap-1">
                                  {lowViolations.map((issue: any, idx: number) => (
                                    <ViolationBadge 
                                      key={`low-${idx}`}
                                      issue={issue}
                                      colorScheme="blue"
                                    />
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* History Modal */}
      {showHistoryModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/50" onClick={() => setShowHistoryModal(false)} />
          <div className="relative bg-white dark:bg-slate-800 rounded-lg shadow-xl max-w-3xl w-full max-h-[80vh] overflow-hidden flex flex-col">
            <div className="sticky top-0 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Clock className="h-5 w-5" />
                  <h3 className="font-semibold text-lg">Analysis History</h3>
                </div>
                <button
                  onClick={() => setShowHistoryModal(false)}
                  className="text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
                  title="Close (Esc)"
                >
                  <XCircle className="h-5 w-5" />
                </button>
              </div>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4">
              {loadingHistory ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-slate-500" />
                  <span className="ml-2">Loading history...</span>
                </div>
              ) : historyItems.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  No previous analyses found
                </div>
              ) : (
                <div className="space-y-3">
                  {historyItems.map((item) => (
                    <div
                      key={item.session_id}
                      onClick={() => {
                        handleSelectAnalysis(item.session_id);
                        setShowHistoryModal(false);
                      }}
                      className={cn(
                        "p-4 rounded-lg border cursor-pointer transition-all hover:shadow-md",
                        sessionId === item.session_id
                          ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                          : "border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600"
                      )}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          {item.status === 'processing' ? (
                            <div className="h-2 w-2 bg-blue-500 rounded-full animate-pulse" />
                          ) : item.status === 'failed' ? (
                            <div className="h-2 w-2 bg-red-500 rounded-full" />
                          ) : item.issues_count > 0 ? (
                            <AlertCircle className="h-4 w-4 text-yellow-500" />
                          ) : (
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          )}
                          <span className="text-xs text-slate-500">
                            {formatDistanceToNow(new Date(item.created_at), { addSuffix: true })}
                          </span>
                        </div>
                        <button
                          onClick={(e) => deleteAnalysis(item.session_id, e)}
                          className="text-slate-400 hover:text-red-500 transition-colors"
                        >
                          <Trash2 className="h-3 w-3" />
                        </button>
                      </div>
                      
                      <div className="space-y-1">
                        <div className="font-medium text-sm line-clamp-2">
                          {item.title || 'Untitled Analysis'}
                        </div>
                        <div className="text-xs text-slate-600 dark:text-slate-400">
                          {item.rule_set_name}
                        </div>
                        <div className="flex items-center gap-3 text-xs text-slate-500">
                          <span className="flex items-center gap-1">
                            <FileText className="h-3 w-3" />
                            {item.total_paragraphs} paragraphs
                          </span>
                          {item.issues_count > 0 && (
                            <span className="flex items-center gap-1 text-yellow-600 dark:text-yellow-400">
                              <AlertCircle className="h-3 w-3" />
                              {item.issues_count} issues
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            <div className="sticky bottom-0 bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700 p-4">
              <Button
                onClick={() => setShowHistoryModal(false)}
                className="w-full"
                variant="outline"
              >
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ComplianceAnalyzer;