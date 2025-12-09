/**
 * IdeaValidation Page
 * 
 * Shows validation progress and results for an idea.
 * Displays real-time progress during validation and the report when complete.
 * 
 * Requirements: 11.1, 13.1
 */

import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';

import { useValidation } from '../contexts/ValidationContext';
import { ValidationProgress } from '../components/ValidationProgress';
import ValidationReportView from '../components/ValidationReportView';
import { UnifiedLoadingSpinner } from '../components/shared';
import { unifiedToast } from '../lib/toast-utils';

export default function IdeaValidation() {
  const { ideaId } = useParams<{ ideaId: string }>();
  const navigate = useNavigate();
  const {
    currentIdea,
    currentValidation,
    currentReport,
    fetchIdeaById,
    ideasLoading,
    startValidation,
    clearCurrentValidation,
    exportToJson,
    exportToPdf,
    fetchValidationResult,
  } = useValidation();

  const [showProgress, setShowProgress] = useState(true);
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    if (ideaId) {
      fetchIdeaById(ideaId);
    }
  }, [ideaId, fetchIdeaById]);

  // Fetch validation result if idea has a latest validation
  useEffect(() => {
    if (currentIdea?.latest_validation?.validation_id) {
      console.log('Fetching validation result:', currentIdea.latest_validation.validation_id);
      fetchValidationResult(currentIdea.latest_validation.validation_id);
    }
  }, [currentIdea?.latest_validation?.validation_id, fetchValidationResult]);

  useEffect(() => {
    // If there's no validation in progress, check if we should show results
    if (currentValidation) {
      if (currentValidation.status === 'completed') {
        setShowProgress(false);
      } else if (currentValidation.status === 'failed') {
        setShowProgress(false);
      }
    }
  }, [currentValidation]);

  const handleValidationComplete = () => {
    unifiedToast.success({
      description: 'Your validation report is ready to view.',
    });
    setShowProgress(false);
  };

  const handleValidationError = (error: string) => {
    unifiedToast.error({
      title: 'Validation Failed',
      description: error,
    });
    setShowProgress(false);
  };

  const handleRetry = async () => {
    if (!ideaId) return;
    
    try {
      clearCurrentValidation();
      setShowProgress(true);
      await startValidation(ideaId);
      
      unifiedToast.success({
        description: 'Starting a new validation for your idea.',
      });
    } catch (error: any) {
      unifiedToast.error({
        title: 'Failed to Restart Validation',
        description: error.message || 'Please try again later.',
      });
    }
  };

  const handleExportJson = async () => {
    if (!currentValidation?.validation_id) return;
    
    setIsExporting(true);
    try {
      const data = await exportToJson(currentValidation.validation_id);
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `validation-${currentValidation.validation_id}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      unifiedToast.success({
        description: 'Validation report exported as JSON.',
      });
    } catch (error: any) {
      unifiedToast.error({
        description: error.message || 'Failed to export report.',
      });
    } finally {
      setIsExporting(false);
    }
  };

  const handleExportPdf = async () => {
    if (!currentValidation?.validation_id) return;
    
    setIsExporting(true);
    try {
      const blob = await exportToPdf(currentValidation.validation_id);
      
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `validation-${currentValidation.validation_id}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      unifiedToast.success({
        description: 'Validation report exported as PDF.',
      });
    } catch (error: any) {
      unifiedToast.error({
        description: error.message || 'Failed to export report.',
      });
    } finally {
      setIsExporting(false);
    }
  };

  const handleShare = () => {
    unifiedToast.info({
      title: 'Coming Soon',
      description: 'Share functionality will be available in the next update.',
    });
  };

  if (ideasLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="glass border-border/50">
          <CardContent className="pt-6">
            <UnifiedLoadingSpinner text="Loading validation..." />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!currentIdea) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="glass border-border/50">
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <p className="text-muted-foreground">Idea not found</p>
              <Button onClick={() => navigate('/ideas')} className="mt-4">
                Back to Ideas
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
        {/* Validation Progress or Results */}
        {showProgress && currentValidation && currentValidation.status !== 'completed' ? (
          <ValidationProgress
            validationId={currentValidation.validation_id}
            ideaTitle={currentIdea.title}
            onComplete={handleValidationComplete}
            onError={handleValidationError}
            onRetry={handleRetry}
          />
        ) : currentReport && currentValidation?.status === 'completed' ? (
          <ValidationReportView
            report={currentReport}
            onExportJson={handleExportJson}
            onExportPdf={handleExportPdf}
            onShare={handleShare}
            isExporting={isExporting}
          />
        ) : (
          <Card className="glass border-border/50">
            <CardContent className="pt-6">
              <div className="text-center py-12">
                <p className="text-muted-foreground mb-4">
                  {currentValidation?.status === 'failed'
                    ? 'Validation failed. Please try again.'
                    : 'No validation results available.'}
                </p>
                <div className="flex gap-4 justify-center">
                  <Button onClick={() => navigate(`/ideas/${ideaId}`)}>
                    Back to Idea
                  </Button>
                  {currentValidation?.status === 'failed' && (
                    <Button
                      variant="outline"
                      onClick={handleRetry}
                    >
                      Retry Validation
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
