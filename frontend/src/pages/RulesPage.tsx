import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, ArrowRight, FolderOpen } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const RulesPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Legacy Rules Page</h1>
        <p className="text-muted-foreground mt-2">
          This page has been replaced with the new Rule Sets management system
        </p>
      </div>

      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <div className="flex items-center gap-2 text-amber-600">
            <AlertCircle className="h-5 w-5" />
            <CardTitle>Page Moved</CardTitle>
          </div>
          <CardDescription>
            The rules management functionality has been upgraded
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-4 bg-muted rounded-lg">
            <h3 className="font-semibold mb-2">What's New?</h3>
            <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
              <li>Create and manage multiple rule sets</li>
              <li>Upload rules from JSON files</li>
              <li>Add rules manually with a form</li>
              <li>Optional GPT-4o preprocessing for rule transformation</li>
              <li>Organize rules by categories</li>
            </ul>
          </div>
          
          <div className="flex items-center justify-center pt-4">
            <Button 
              onClick={() => navigate('/rule-sets')}
              size="lg"
              className="gap-2"
            >
              <FolderOpen className="h-4 w-4" />
              Go to Rule Sets
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default RulesPage;