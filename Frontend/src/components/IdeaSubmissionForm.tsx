import { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Lightbulb, AlertCircle, Loader2 } from 'lucide-react';
import { IdeaFormData } from '../types/validation';

interface IdeaSubmissionFormProps {
  onSubmit: (data: IdeaFormData) => Promise<void>;
  initialData?: Partial<IdeaFormData>;
  isLoading?: boolean;
  isEdit?: boolean;
}

export default function IdeaSubmissionForm({
  onSubmit,
  initialData,
  isLoading = false,
  isEdit = false,
}: IdeaSubmissionFormProps) {
  const [formData, setFormData] = useState<IdeaFormData>({
    title: initialData?.title || '',
    description: initialData?.description || '',
    problemStatement: initialData?.problemStatement || '',
    solutionDescription: initialData?.solutionDescription || '',
    targetMarket: initialData?.targetMarket || '',
    businessModel: initialData?.businessModel || '',
    teamCapabilities: initialData?.teamCapabilities || '',
  });

  const [showValidation, setShowValidation] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Update form when initialData changes
  useEffect(() => {
    if (initialData) {
      setFormData({
        title: initialData.title || '',
        description: initialData.description || '',
        problemStatement: initialData.problemStatement || '',
        solutionDescription: initialData.solutionDescription || '',
        targetMarket: initialData.targetMarket || '',
        businessModel: initialData.businessModel || '',
        teamCapabilities: initialData.teamCapabilities || '',
      });
    }
  }, [initialData]);

  // Validation functions
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (formData.title.trim().length < 5) {
      newErrors.title = 'Title must be at least 5 characters';
    }
    if (formData.title.trim().length > 200) {
      newErrors.title = 'Title must be less than 200 characters';
    }

    if (formData.description.trim().length < 50) {
      newErrors.description = 'Description must be at least 50 characters';
    }

    if (formData.problemStatement.trim().length < 20) {
      newErrors.problemStatement = 'Problem statement must be at least 20 characters';
    }

    if (formData.solutionDescription.trim().length < 50) {
      newErrors.solutionDescription = 'Solution description must be at least 50 characters';
    }

    if (formData.targetMarket.trim().length < 5) {
      newErrors.targetMarket = 'Target market must be at least 5 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setShowValidation(true);

    if (!validateForm()) {
      return;
    }

    try {
      await onSubmit(formData);
    } catch (error) {
      console.error('Error submitting idea:', error);
    }
  };

  const handleChange = (field: keyof IdeaFormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setShowValidation(false);
    // Clear error for this field
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const getFieldError = (field: string): string | undefined => {
    return showValidation ? errors[field] : undefined;
  };

  return (
    <Card className="glass border-border/50">
      {isEdit && (
        <CardHeader>
          <CardTitle className="text-xl">Edit Idea</CardTitle>
          <CardDescription>
            Update your idea details to refine your validation
          </CardDescription>
        </CardHeader>
      )}
      <CardContent className={isEdit ? '' : 'pt-6'}>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="title" className="text-base">
              Idea Title *
            </Label>
            <Input
              id="title"
              value={formData.title}
              onChange={(e) => handleChange('title', e.target.value)}
              placeholder="e.g., AI-Powered Customer Support Platform"
              className={`glass border-border/50 focus:border-primary transition-all duration-300 ${
                getFieldError('title') ? 'border-red-500' : ''
              }`}
              maxLength={200}
              required
            />
            {getFieldError('title') && (
              <div className="flex items-center gap-2 text-red-500 text-sm">
                <AlertCircle className="h-4 w-4" />
                {getFieldError('title')}
              </div>
            )}
            <p className="text-xs text-muted-foreground">
              {formData.title.length}/200 characters • Minimum 5 characters
            </p>
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description" className="text-base">
              Idea Description *
            </Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => handleChange('description', e.target.value)}
              placeholder="Provide a comprehensive description of your startup idea, including what it does and who it serves..."
              className={`min-h-[120px] resize-none glass border-border/50 focus:border-primary transition-all duration-300 ${
                getFieldError('description') ? 'border-red-500' : ''
              }`}
              required
            />
            {getFieldError('description') && (
              <div className="flex items-center gap-2 text-red-500 text-sm">
                <AlertCircle className="h-4 w-4" />
                {getFieldError('description')}
              </div>
            )}
            <p className="text-xs text-muted-foreground">
              {formData.description.length} characters • Minimum 50 characters
            </p>
          </div>

          {/* Problem Statement */}
          <div className="space-y-2">
            <Label htmlFor="problemStatement" className="text-base">
              Problem Statement *
            </Label>
            <Textarea
              id="problemStatement"
              value={formData.problemStatement}
              onChange={(e) => handleChange('problemStatement', e.target.value)}
              placeholder="Clearly define the problem your idea solves. Be specific about user pain points..."
              className={`min-h-[100px] resize-none glass border-border/50 focus:border-primary transition-all duration-300 ${
                getFieldError('problemStatement') ? 'border-red-500' : ''
              }`}
              required
            />
            {getFieldError('problemStatement') && (
              <div className="flex items-center gap-2 text-red-500 text-sm">
                <AlertCircle className="h-4 w-4" />
                {getFieldError('problemStatement')}
              </div>
            )}
            <p className="text-xs text-muted-foreground">
              {formData.problemStatement.length} characters • Minimum 20 characters
            </p>
          </div>

          {/* Solution Description */}
          <div className="space-y-2">
            <Label htmlFor="solutionDescription" className="text-base">
              Solution Description *
            </Label>
            <Textarea
              id="solutionDescription"
              value={formData.solutionDescription}
              onChange={(e) => handleChange('solutionDescription', e.target.value)}
              placeholder="Describe your proposed solution and how it addresses the problem..."
              className={`min-h-[100px] resize-none glass border-border/50 focus:border-primary transition-all duration-300 ${
                getFieldError('solutionDescription') ? 'border-red-500' : ''
              }`}
              required
            />
            {getFieldError('solutionDescription') && (
              <div className="flex items-center gap-2 text-red-500 text-sm">
                <AlertCircle className="h-4 w-4" />
                {getFieldError('solutionDescription')}
              </div>
            )}
            <p className="text-xs text-muted-foreground">
              {formData.solutionDescription.length} characters • Minimum 50 characters
            </p>
          </div>

          {/* Target Market */}
          <div className="space-y-2">
            <Label htmlFor="targetMarket" className="text-base">
              Target Market *
            </Label>
            <Input
              id="targetMarket"
              value={formData.targetMarket}
              onChange={(e) => handleChange('targetMarket', e.target.value)}
              placeholder="e.g., Small to medium-sized e-commerce businesses in North America"
              className={`glass border-border/50 focus:border-primary transition-all duration-300 ${
                getFieldError('targetMarket') ? 'border-red-500' : ''
              }`}
              required
            />
            {getFieldError('targetMarket') && (
              <div className="flex items-center gap-2 text-red-500 text-sm">
                <AlertCircle className="h-4 w-4" />
                {getFieldError('targetMarket')}
              </div>
            )}
            <p className="text-xs text-muted-foreground">
              {formData.targetMarket.length} characters • Minimum 5 characters
            </p>
          </div>

          {/* Optional Fields Section */}
          <div className="space-y-4 pt-4 border-t border-border/50">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
              Optional Information
            </h3>

            {/* Business Model */}
            <div className="space-y-2">
              <Label htmlFor="businessModel">Business Model (Optional)</Label>
              <Textarea
                id="businessModel"
                value={formData.businessModel}
                onChange={(e) => handleChange('businessModel', e.target.value)}
                placeholder="Describe your revenue model (e.g., SaaS subscription, freemium, marketplace commission)..."
                className="min-h-[80px] resize-none glass border-border/50 focus:border-primary transition-all duration-300"
              />
              <p className="text-xs text-muted-foreground">
                How you plan to generate revenue
              </p>
            </div>

            {/* Team Capabilities */}
            <div className="space-y-2">
              <Label htmlFor="teamCapabilities">Team Capabilities (Optional)</Label>
              <Textarea
                id="teamCapabilities"
                value={formData.teamCapabilities}
                onChange={(e) => handleChange('teamCapabilities', e.target.value)}
                placeholder="Describe your team's skills and experience (e.g., 10 years in SaaS, expertise in AI/ML, strong sales background)..."
                className="min-h-[80px] resize-none glass border-border/50 focus:border-primary transition-all duration-300"
              />
              <p className="text-xs text-muted-foreground">
                Your team's relevant skills and experience
              </p>
            </div>
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            size="lg"
            className="w-full bg-gradient-to-r from-accent to-primary text-white glow hover:glow-sm hover:scale-[1.02] transition-all duration-300 font-semibold text-lg shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                {isEdit ? 'Updating Idea...' : 'Submitting Idea...'}
              </>
            ) : (
              <>
                <Lightbulb className="mr-2 h-5 w-5" />
                {isEdit ? 'Update Idea' : 'Submit Idea'}
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
