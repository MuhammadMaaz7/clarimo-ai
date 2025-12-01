/**
 * IdeaValidationHistory Page
 * 
 * Displays the validation history for a specific idea.
 * Allows users to view past validations and compare versions.
 * 
 * Requirements: 13.1, 13.2
 */

import { useNavigate, useParams } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { ArrowLeft } from 'lucide-react';
import ValidationHistoryView from '../components/ValidationHistoryView';
import { useValidation } from '../contexts/ValidationContext';
import { useEffect } from 'react';

export default function IdeaValidationHistory() {
  const { ideaId } = useParams<{ ideaId: string }>();
  const navigate = useNavigate();
  const { currentIdea, fetchIdeaById } = useValidation();

  useEffect(() => {
    if (ideaId) {
      fetchIdeaById(ideaId);
    }
  }, [ideaId, fetchIdeaById]);

  const handleCompareVersions = (validationId1: string, validationId2: string) => {
    // Navigate to version comparison view
    navigate(`/ideas/${ideaId}/history/compare?v1=${validationId1}&v2=${validationId2}`);
  };

  if (!ideaId) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center py-12">
          <p className="text-muted-foreground">Invalid idea ID</p>
          <Button onClick={() => navigate('/ideas')} className="mt-4">
            Back to Ideas
          </Button>
        </div>
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
            onClick={() => navigate(`/ideas/${ideaId}`)}
            className="mb-4"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Idea
          </Button>
        </div>

        {/* Validation History */}
        <ValidationHistoryView
          ideaId={ideaId}
          ideaTitle={currentIdea?.title}
          onCompareVersions={handleCompareVersions}
        />
      </div>
    </div>
  );
}