/**
 * IdeaVersionComparison Page
 * 
 * Compares two validation versions for an idea.
 * Shows score deltas and identifies improvements/declines.
 * 
 * Requirements: 13.3, 13.4
 */

import { useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { ArrowLeft } from 'lucide-react';
import VersionComparisonView from '../components/VersionComparisonView';
import { useValidation } from '../contexts/ValidationContext';

export default function IdeaVersionComparison() {
  const { ideaId } = useParams<{ ideaId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { fetchIdeaById } = useValidation();
  
  const validationId1 = searchParams.get('v1');
  const validationId2 = searchParams.get('v2');

  useEffect(() => {
    if (ideaId) {
      fetchIdeaById(ideaId);
    }
  }, [ideaId, fetchIdeaById]);

  if (!validationId1 || !validationId2) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="glass border-border/50">
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <p className="text-muted-foreground mb-4">Missing validation IDs for comparison</p>
              <Button onClick={() => navigate(`/ideas/${ideaId}/history`)}>
                Back to History
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <Button
            variant="ghost"
            onClick={() => navigate(`/ideas/${ideaId}/history`)}
            className="mb-4"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to History
          </Button>
        </div>

        {/* Version Comparison */}
        <VersionComparisonView
          validationId1={validationId1}
          validationId2={validationId2}
          onBack={() => navigate(`/ideas/${ideaId}/history`)}
        />
      </div>
    </div>
  );
}
