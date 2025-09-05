// frontend/src/components/compliance/ComplianceResults.tsx
import React, { useState } from 'react';
import { CheckCircle, XCircle, AlertTriangle, Info, ChevronDown, ChevronUp, FileText, Calendar, RefreshCw, Eye, EyeOff } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';

interface ComplianceResultsProps {
  results: any;
  onReset: () => void;
}

const ComplianceResults: React.FC<ComplianceResultsProps> = ({ results, onReset }) => {
  const [expandedParagraphs, setExpandedParagraphs] = useState<Set<number>>(new Set());
  const [showPreview, setShowPreview] = useState<Set<string>>(new Set());
  const [showRecommendations, setShowRecommendations] = useState<Set<string>>(new Set());

  const toggleParagraph = (index: number) => {
    const newExpanded = new Set(expandedParagraphs);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedParagraphs(newExpanded);
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <XCircle className="h-5 w-5 text-red-600" />;
      case 'high':
        return <AlertTriangle className="h-5 w-5 text-orange-600" />;
      case 'medium':
        return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
      case 'low':
        return <Info className="h-5 w-5 text-blue-600" />;
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      default:
        return <Info className="h-5 w-5 text-gray-600" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'success':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getIssueTypeLabel = (type: string) => {
    switch (type) {
      case 'compliant':
        return 'Compliant';
      case 'missing':
        return 'Missing Requirement';
      case 'inadequate':
        return 'Inadequate Coverage';
      case 'outdated':
        return 'Outdated Reference';
      case 'violation':
        return 'Violation';
      default:
        return type;
    }
  };

  // Calculate summary statistics
  const stats = {
    total: 0,
    compliant: 0,
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
  };

  results.paragraphs?.forEach((para: any) => {
    para.issues?.forEach((issue: any) => {
      stats.total++;
      if (issue.issue_type === 'compliant') {
        stats.compliant++;
      } else {
        switch (issue.severity) {
          case 'critical':
            stats.critical++;
            break;
          case 'high':
            stats.high++;
            break;
          case 'medium':
            stats.medium++;
            break;
          case 'low':
            stats.low++;
            break;
        }
      }
    });
  });

  return (
    <div className="space-y-6">
      {/* Summary Card */}
      <Card className="p-6 bg-white dark:bg-slate-800 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
            Compliance Analysis Results
          </h2>
          <Button onClick={onReset} variant="outline" className="flex items-center gap-2">
            <RefreshCw className="h-4 w-4" />
            New Analysis
          </Button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mt-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600">{stats.compliant}</div>
            <div className="text-sm text-slate-600 dark:text-slate-400">Compliant</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-red-600">{stats.critical}</div>
            <div className="text-sm text-slate-600 dark:text-slate-400">Critical</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-orange-600">{stats.high}</div>
            <div className="text-sm text-slate-600 dark:text-slate-400">High</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-yellow-600">{stats.medium}</div>
            <div className="text-sm text-slate-600 dark:text-slate-400">Medium</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">{stats.low}</div>
            <div className="text-sm text-slate-600 dark:text-slate-400">Low</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-slate-900 dark:text-white">{stats.total}</div>
            <div className="text-sm text-slate-600 dark:text-slate-400">Total Findings</div>
          </div>
        </div>
      </Card>

      {/* Paragraph Analysis */}
      <div className="space-y-4">
        {results.paragraphs?.map((paragraph: any, index: number) => {
          const hasIssues = paragraph.issues && paragraph.issues.length > 0;
          const isExpanded = expandedParagraphs.has(index);

          return (
            <Card
              key={index}
              className={`p-6 bg-white dark:bg-slate-800 shadow-lg transition-all ${
                hasIssues ? 'border-l-4 ' + (
                  paragraph.issues.some((i: any) => i.severity === 'critical') ? 'border-l-red-500' :
                  paragraph.issues.some((i: any) => i.severity === 'high') ? 'border-l-orange-500' :
                  paragraph.issues.some((i: any) => i.severity === 'medium') ? 'border-l-yellow-500' :
                  paragraph.issues.every((i: any) => i.issue_type === 'compliant') ? 'border-l-green-500' :
                  'border-l-blue-500'
                ) : 'border-l-4 border-l-gray-300'
              }`}
            >
              {/* Paragraph Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                      Paragraph {index + 1}
                    </h3>
                    {paragraph.applicable_rules && paragraph.applicable_rules.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {paragraph.applicable_rules.map((rule: string) => (
                          <Badge key={rule} variant="outline" className="text-xs">
                            Rule {rule}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                  
                  {/* Paragraph Content Preview */}
                  <div className="text-sm text-slate-600 dark:text-slate-300 line-clamp-2">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        p: ({children}) => <span>{children}</span>,
                        h1: ({children}) => <span className="font-bold">{children}</span>,
                        h2: ({children}) => <span className="font-bold">{children}</span>,
                        h3: ({children}) => <span className="font-semibold">{children}</span>,
                        ul: ({children}) => <span>{children}</span>,
                        ol: ({children}) => <span>{children}</span>,
                        li: ({children}) => <span> • {children}</span>,
                        code: ({children}) => <code className="px-1 py-0.5 bg-slate-200 dark:bg-slate-700 rounded text-xs">{children}</code>,
                      }}
                    >
                      {paragraph.content}
                    </ReactMarkdown>
                  </div>
                </div>

                <button
                  onClick={() => toggleParagraph(index)}
                  className="ml-4 p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                >
                  {isExpanded ? (
                    <ChevronUp className="h-5 w-5 text-slate-600 dark:text-slate-400" />
                  ) : (
                    <ChevronDown className="h-5 w-5 text-slate-600 dark:text-slate-400" />
                  )}
                </button>
              </div>

              {/* Expanded Content */}
              {isExpanded && (
                <div className="mt-4 space-y-4">
                  {/* Full Paragraph Text */}
                  <div className="p-4 bg-slate-50 dark:bg-slate-900 rounded-lg">
                    <div className="prose prose-sm dark:prose-invert max-w-none text-slate-700 dark:text-slate-200">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          h1: ({children}) => <h1 className="text-lg font-bold mb-2 mt-3">{children}</h1>,
                          h2: ({children}) => <h2 className="text-base font-bold mb-2 mt-3">{children}</h2>,
                          h3: ({children}) => <h3 className="text-sm font-semibold mb-1 mt-2">{children}</h3>,
                          p: ({children}) => <p className="mb-2">{children}</p>,
                          ul: ({children}) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                          ol: ({children}) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                          li: ({children}) => <li className="ml-2">{children}</li>,
                          blockquote: ({children}) => <blockquote className="border-l-4 border-slate-300 dark:border-slate-600 pl-4 italic my-2">{children}</blockquote>,
                          code: ({inline, children}) => inline ? 
                            <code className="px-1.5 py-0.5 bg-slate-200 dark:bg-slate-700 rounded text-xs font-mono">{children}</code> :
                            <pre className="bg-slate-200 dark:bg-slate-700 rounded p-3 overflow-x-auto my-2"><code className="text-xs font-mono">{children}</code></pre>,
                          table: ({children}) => <table className="border-collapse border border-slate-300 dark:border-slate-600 my-2">{children}</table>,
                          thead: ({children}) => <thead className="bg-slate-100 dark:bg-slate-800">{children}</thead>,
                          tbody: ({children}) => <tbody>{children}</tbody>,
                          tr: ({children}) => <tr className="border-b border-slate-300 dark:border-slate-600">{children}</tr>,
                          th: ({children}) => <th className="px-3 py-2 text-left font-semibold">{children}</th>,
                          td: ({children}) => <td className="px-3 py-2">{children}</td>,
                          hr: () => <hr className="my-3 border-slate-300 dark:border-slate-600" />,
                          strong: ({children}) => <strong className="font-semibold">{children}</strong>,
                          em: ({children}) => <em className="italic">{children}</em>,
                          a: ({href, children}) => <a href={href} className="text-blue-600 dark:text-blue-400 underline hover:opacity-75" target="_blank" rel="noopener noreferrer">{children}</a>,
                        }}
                      >
                        {paragraph.content}
                      </ReactMarkdown>
                    </div>
                  </div>

                  {/* Issues/Findings */}
                  {hasIssues && (
                    <div className="space-y-3">
                      <h4 className="font-semibold text-slate-900 dark:text-white">
                        Compliance Findings:
                      </h4>
                      {paragraph.issues.map((issue: any, issueIndex: number) => (
                        <div
                          key={issueIndex}
                          className={`p-4 rounded-lg border ${getSeverityColor(issue.severity)}`}
                        >
                          <div className="flex items-start gap-3">
                            {getSeverityIcon(issue.severity)}
                            <div className="flex-1">
                              {/* Issue Header */}
                              <div className="flex items-center gap-2 mb-2">
                                <span className="font-semibold text-sm">
                                  Rule {issue.rule_number}: {issue.rule_title}
                                </span>
                                <Badge variant="outline" className="text-xs">
                                  {getIssueTypeLabel(issue.issue_type)}
                                </Badge>
                                {issue.rule_date && (
                                  <div className="flex items-center gap-1 text-xs text-slate-500">
                                    <Calendar className="h-3 w-3" />
                                    {issue.rule_date}
                                  </div>
                                )}
                              </div>

                              {/* Issue Description */}
                              <p className="text-sm mb-3">{issue.description}</p>

                              {/* Current vs Required - Collapsible */}
                              {issue.current_text && (
                                <div className="mb-3">
                                  <button
                                    onClick={() => {
                                      const key = `${paragraph.index}-${issueIndex}`;
                                      const newShowPreview = new Set(showPreview);
                                      if (newShowPreview.has(key)) {
                                        newShowPreview.delete(key);
                                      } else {
                                        newShowPreview.add(key);
                                      }
                                      setShowPreview(newShowPreview);
                                    }}
                                    className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 transition-colors mb-2"
                                  >
                                    {showPreview.has(`${paragraph.index}-${issueIndex}`) ? (
                                      <EyeOff className="h-4 w-4" />
                                    ) : (
                                      <Eye className="h-4 w-4" />
                                    )}
                                    {showPreview.has(`${paragraph.index}-${issueIndex}`) ? 'Hide' : 'Show'} Document Preview with Fixes
                                  </button>
                                  
                                  {showPreview.has(`${paragraph.index}-${issueIndex}`) && (
                                    <div className="grid md:grid-cols-2 gap-3">
                                      <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded">
                                        <div className="text-xs font-semibold text-red-700 dark:text-red-400 mb-1">
                                          Current Text:
                                        </div>
                                        <p className="text-xs text-red-600 dark:text-red-300">
                                          {issue.current_text}
                                        </p>
                                      </div>
                                      {issue.required_text && (
                                        <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded">
                                          <div className="text-xs font-semibold text-green-700 dark:text-green-400 mb-1">
                                            Required Text:
                                          </div>
                                          <p className="text-xs text-green-600 dark:text-green-300">
                                            {issue.required_text}
                                          </p>
                                        </div>
                                      )}
                                    </div>
                                  )}
                                </div>
                              )}

                              {/* Suggested Fix - Toggleable */}
                              {issue.suggested_fix && (
                                <div>
                                  <button
                                    onClick={() => {
                                      const key = `${paragraph.index}-${issueIndex}`;
                                      const newShowRecs = new Set(showRecommendations);
                                      if (newShowRecs.has(key)) {
                                        newShowRecs.delete(key);
                                      } else {
                                        newShowRecs.add(key);
                                      }
                                      setShowRecommendations(newShowRecs);
                                    }}
                                    className="flex items-center gap-2 text-sm font-medium text-blue-700 dark:text-blue-300 hover:text-blue-900 dark:hover:text-blue-100 transition-colors mb-2"
                                  >
                                    {showRecommendations.has(`${paragraph.index}-${issueIndex}`) ? (
                                      <ChevronUp className="h-4 w-4" />
                                    ) : (
                                      <ChevronDown className="h-4 w-4" />
                                    )}
                                    {showRecommendations.has(`${paragraph.index}-${issueIndex}`) ? 'Hide' : 'Show'} Recommended Actions
                                  </button>
                                  
                                  {showRecommendations.has(`${paragraph.index}-${issueIndex}`) && (
                                    <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded">
                                      <p className="text-xs text-blue-600 dark:text-blue-300">
                                        {issue.suggested_fix}
                                      </p>
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {!hasIssues && (
                    <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="h-5 w-5 text-green-600" />
                        <span className="text-sm text-green-700 dark:text-green-300">
                          No compliance issues found in this paragraph
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </Card>
          );
        })}
      </div>
    </div>
  );
};

export default ComplianceResults;