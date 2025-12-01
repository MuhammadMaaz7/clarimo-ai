import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from './ui/alert-dialog';
import {
  Lightbulb,
  ArrowLeft,
  Edit,
  Trash2,
  Link as LinkIcon,
  Calendar,
  Target,
  Briefcase,
  Users,
  CheckCircle2,
  Clock,
  XCircle,
  Loader2,
} from 'lucide-react';
import { useValidation } from '../contexts/ValidationContext';
import { formatScore, getScoreColor, getScoreLabel } from '../types/validation';
import IdeaSubmissionForm from './IdeaSubmissionForm';
import { IdeaFormData } from '../types/validation';
import { ValidationTrigger } from './ValidationTrigger';

export default function IdeaDetailView() {
  const { ideaId } = useParams<{ ideaId: string }>();
  const navigate = useNavigate();
  const {
    currentIdea,
    ideasLoading,
    ideasError,
    fetchIdeaById,
    updateIdea,
    deleteIdea,
  } = useValidation();

  const [isEditing, setIsEditing] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (ideaId) {
      fetchIdeaById(ideaId);
    }
  }, [ideaId, fetchIdeaById]);

  const handleUpdate = async (data: IdeaFormData) => {
    if (!ideaId) return;
    try {
      await updateIdea(ideaId, data);
      setIsEditing(false);
    } catch (error) {
      console.error('Error updating idea:', error);
    }
  };

  const handleDelete = async () => {
    if (!ideaId) return;
    setIsDeleting(true);
    try {
      await deleteIdea(ideaId);
      navigate('/ideas');
    } catch (error) {
      console.error('Error deleting idea:', error);
      setIsDeleting(false);
    }
  };

  const handleValidationStarted = () => {
    // Navigate to validation dashboard
    navigate(`/ideas/${ideaId}/validate`);
  };

  const getStatusBadge = () => {
    if (!currentIdea?.latest_validation) {
      return (
        <Badge variant="outline" className="flex items-center gap-1">
          <Clock className="h-3 w-3" />
          Not Validated
        </Badge>
      );
    }

    const status = currentIdea.latest_validation.status;
    if (status === 'completed') {
      return (
        <Badge variant="default" className="flex items-center gap-1 bg-green-500">
          <CheckCircle2 className="h-3 w-3" />
          Validated
        </Badge>
      );
    } else if (status === 'in_progress' || status === 'pending') {
      return (
        <Badge variant="default" className="flex items-center gap-1 bg-blue-500">
          <Loader2 className="h-3 w-3 animate-spin" />
          In Progress
        </Badge>
      );
    } else if (status === 'failed') {
      return (
        <Badge variant="destructive" className="flex items-center gap-1">
          <XCircle className="h-3 w-3" />
          Failed
        </Badge>
      );
    }
  };

  if (ideasLoading) {
    return (
      <Card className="glass border-border/50">
        <CardContent className="pt-6">
          <div className="text-center py-12">
            <Loader2 className="h-12 w-12 animate-spin mx-auto text-primary mb-4" />
            <p className="text-muted-foreground">Loading idea details...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (ideasError || !currentIdea) {
    return (
      <Card className="glass border-border/50">
        <CardContent className="pt-6">
          <div className="text-center text-red-500">
            <XCircle className="h-12 w-12 mx-auto mb-4" />
            <p className="text-lg font-semibold">Error loading idea</p>
            <p className="text-sm text-muted-foreground mt-2">
              {ideasError || 'Idea not found'}
            </p>
            <Button onClick={() => navigate('/ideas')} className="mt-4">
              Back to Ideas
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isEditing) {
    return (
      <div className="space-y-6">
        <Button
          variant="ghost"
          onClick={() => setIsEditing(false)}
          className="mb-4"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Cancel Editing
        </Button>
        <IdeaSubmissionForm
          onSubmit={handleUpdate}
          initialData={{
            title: currentIdea.title,
            description: currentIdea.description,
            problemStatement: currentIdea.problem_statement,
            solutionDescription: currentIdea.solution_description,
            targetMarket: currentIdea.target_market,
            businessModel: currentIdea.business_model,
            teamCapabilities: currentIdea.team_capabilities,
            linkedPainPointIds: currentIdea.linked_pain_points,
          }}
          isLoading={ideasLoading}
          isEdit={true}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button
          variant="ghost"
          onClick={() => navigate('/ideas')}
          className="mb-4"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Ideas
        </Button>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => setIsEditing(true)}
            className="glass border-border/50"
          >
            <Edit className="mr-2 h-4 w-4" />
            Edit
          </Button>
          <Button
            variant="outline"
            onClick={() => setShowDeleteDialog(true)}
            className="glass border-border/50 text-red-500 hover:text-red-600"
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <Card className="glass border-border/50">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="text-3xl mb-2 flex items-center gap-3">
                <Lightbulb className="h-8 w-8 text-primary" />
                {currentIdea.title}
              </CardTitle>
              <div className="flex items-center gap-4 mt-4">
                {getStatusBadge()}
                {currentIdea.latest_validation?.overall_score && (
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">Score:</span>
                    <span
                      className="text-xl font-bold"
                      style={{
                        color: getScoreColor(currentIdea.latest_validation.overall_score),
                      }}
                    >
                      {formatScore(currentIdea.latest_validation.overall_score)}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      ({getScoreLabel(currentIdea.latest_validation.overall_score)})
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Description */}
          <div>
            <h3 className="text-lg font-semibold mb-2">Description</h3>
            <p className="text-muted-foreground whitespace-pre-wrap">
              {currentIdea.description}
            </p>
          </div>

          {/* Problem Statement */}
          <div>
            <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
              <Target className="h-5 w-5 text-primary" />
              Problem Statement
            </h3>
            <p className="text-muted-foreground whitespace-pre-wrap">
              {currentIdea.problem_statement}
            </p>
          </div>

          {/* Solution Description */}
          <div>
            <h3 className="text-lg font-semibold mb-2">Solution</h3>
            <p className="text-muted-foreground whitespace-pre-wrap">
              {currentIdea.solution_description}
            </p>
          </div>

          {/* Target Market */}
          <div>
            <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
              <Users className="h-5 w-5 text-primary" />
              Target Market
            </h3>
            <p className="text-muted-foreground">{currentIdea.target_market}</p>
          </div>

          {/* Business Model (if provided) */}
          {currentIdea.business_model && (
            <div>
              <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
                <Briefcase className="h-5 w-5 text-primary" />
                Business Model
              </h3>
              <p className="text-muted-foreground whitespace-pre-wrap">
                {currentIdea.business_model}
              </p>
            </div>
          )}

          {/* Team Capabilities (if provided) */}
          {currentIdea.team_capabilities && (
            <div>
              <h3 className="text-lg font-semibold mb-2">Team Capabilities</h3>
              <p className="text-muted-foreground whitespace-pre-wrap">
                {currentIdea.team_capabilities}
              </p>
            </div>
          )}

          {/* Linked Pain Points */}
          <div>
            <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
              <LinkIcon className="h-5 w-5 text-primary" />
              Linked Pain Points
            </h3>
            {currentIdea.linked_pain_points.length > 0 ? (
              <div className="space-y-2">
                <p className="text-muted-foreground">
                  {currentIdea.linked_pain_points.length} pain point(s) linked
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(`/ideas/${ideaId}/pain-points`)}
                  className="glass border-border/50"
                >
                  <LinkIcon className="mr-2 h-4 w-4" />
                  Manage Pain Points
                </Button>
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-muted-foreground">No pain points linked yet</p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(`/ideas/${ideaId}/pain-points`)}
                  className="glass border-border/50"
                >
                  <LinkIcon className="mr-2 h-4 w-4" />
                  Link Pain Points
                </Button>
              </div>
            )}
          </div>

          {/* Metadata */}
          <div className="pt-4 border-t border-border/50">
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Created: {new Date(currentIdea.created_at).toLocaleDateString()}
              </div>
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Updated: {new Date(currentIdea.updated_at).toLocaleDateString()}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Validation Actions */}
      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle>Validation</CardTitle>
          <CardDescription>
            Run a comprehensive validation to assess your idea's viability
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {currentIdea.latest_validation ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">
                    Last validated:{' '}
                    {new Date(currentIdea.latest_validation.created_at).toLocaleDateString()}
                  </p>
                  {currentIdea.latest_validation.overall_score && (
                    <p className="text-sm text-muted-foreground">
                      Overall Score:{' '}
                      <span
                        className="font-semibold"
                        style={{
                          color: getScoreColor(currentIdea.latest_validation.overall_score),
                        }}
                      >
                        {formatScore(currentIdea.latest_validation.overall_score)}/5.0
                      </span>
                    </p>
                  )}
                </div>
                <Button
                  onClick={() =>
                    navigate(`/ideas/${ideaId}/validate`)
                  }
                  variant="outline"
                  className="glass border-border/50"
                >
                  View Report
                </Button>
              </div>
              <div className="w-full">
                <ValidationTrigger
                  ideaId={ideaId!}
                  ideaTitle={currentIdea.title}
                  onValidationStarted={handleValidationStarted}
                  variant="default"
                  size="lg"
                  showConfigOptions={true}
                />
              </div>
            </div>
          ) : (
            <div className="w-full">
              <ValidationTrigger
                ideaId={ideaId!}
                ideaTitle={currentIdea.title}
                onValidationStarted={handleValidationStarted}
                variant="default"
                size="lg"
                showConfigOptions={true}
              />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete "{currentIdea.title}" and all associated validation
              data. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={isDeleting}
              className="bg-red-500 hover:bg-red-600"
            >
              {isDeleting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Deleting...
                </>
              ) : (
                'Delete'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
