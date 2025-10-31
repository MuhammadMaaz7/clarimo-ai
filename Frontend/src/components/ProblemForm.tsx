import { useState, useImperativeHandle, forwardRef } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Search, Filter, AlertCircle } from 'lucide-react';

interface ProblemFormProps {
  onSubmit: (data: FormData) => void;
  isLoading: boolean;
  compact?: boolean;
  onReset?: () => void;
}

export interface ProblemFormRef {
  resetForm: () => void;
}

export interface FormData {
  problemDescription: string;
  domain?: string;
  region?: string;
  targetAudience?: string;
}

const ProblemForm = forwardRef<ProblemFormRef, ProblemFormProps>(({ onSubmit, isLoading, compact = false, onReset }, ref) => {
  const [formData, setFormData] = useState<FormData>({
    problemDescription: '',
    domain: '',
    region: '',
    targetAudience: '',
  });
  const [showValidation, setShowValidation] = useState(false);

  // Validation functions
  const validateText = (text: string): string => {
    return text.replaceAll(/[<>{}[\]\\`~|@#$%^&*()+=]/g, '');
  };

  const validateTextForSubmit = (text: string): string => {
    return validateText(text).trim();
  };

  const isFormValid = formData.problemDescription.trim().length >= 10;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setShowValidation(true);
    
    if (!isFormValid) {
      return;
    }
    
    // Validate and clean the form data
    const cleanedData: FormData = {
      problemDescription: validateTextForSubmit(formData.problemDescription),
      domain: formData.domain ? validateTextForSubmit(formData.domain) : undefined,
      region: formData.region ? validateTextForSubmit(formData.region) : undefined,
      targetAudience: formData.targetAudience ? validateTextForSubmit(formData.targetAudience) : undefined,
    };

    onSubmit(cleanedData);
  };

  const handleChange = (field: keyof FormData, value: string) => {
    const cleanedValue = validateText(value);
    setFormData((prev) => ({ ...prev, [field]: cleanedValue }));
    setShowValidation(false); // Reset validation on change
  };

  const resetForm = () => {
    setFormData({
      problemDescription: '',
      domain: '',
      region: '',
      targetAudience: '',
    });
    setShowValidation(false);
    onReset?.();
  };

  useImperativeHandle(ref, () => ({
    resetForm
  }));

  return (
    <Card className={`glass border-border/50 ${compact ? 'bg-white/3' : ''}`}>
      {!compact && (
        <CardHeader>
          <CardTitle className="text-2xl">Search Parameters</CardTitle>
          <CardDescription className="text-base">
            Describe the problem space you want to explore and set optional filters
          </CardDescription>
        </CardHeader>
      )}
      <CardContent className={compact ? 'pt-6' : ''}>
        <form onSubmit={handleSubmit} className={compact ? "space-y-4" : "space-y-6"}>
          {/* Problem Description */}
          <div className="space-y-2">
            <Label htmlFor="problem" className="text-base">Problem Description *</Label>
            <Textarea
              id="problem"
              name="problemDescription"
              value={formData.problemDescription}
              onChange={(e) => handleChange('problemDescription', e.target.value)}
              placeholder="Describe the problems you want to discover (e.g., 'Small businesses struggling with customer management')"
              className={`${compact ? 'min-h-[80px]' : 'min-h-[120px]'} resize-none glass border-border/50 focus:border-primary transition-all duration-300 ${
                showValidation && !isFormValid ? 'border-red-500' : ''
              }`}
              required
            />
            {showValidation && !isFormValid && (
              <div className="flex items-center gap-2 text-red-500 text-sm">
                <AlertCircle className="h-4 w-4" />
                Please provide at least 10 characters for the problem description
              </div>
            )}
            <p className="text-xs text-muted-foreground">
              {formData.problemDescription.length}/1000 characters • Minimum 10 characters required
            </p>
          </div>

          {/* Optional Context Fields */}
          {!compact && (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-primary" />
                <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Optional Context</h3>
              </div>

              <div className="grid gap-4 sm:grid-cols-1 lg:grid-cols-3">
                {/* Domain */}
                <div className="space-y-2">
                  <Label htmlFor="domain">Domain (Optional)</Label>
                  <Input
                    id="domain"
                    type="text"
                    value={formData.domain || ''}
                    onChange={(e) => handleChange('domain', e.target.value)}
                    placeholder="e.g., Healthcare, SaaS, E-commerce"
                    className="glass border-border/50 focus:border-primary transition-all duration-300"
                    maxLength={100}
                  />
                  <p className="text-xs text-muted-foreground">Industry or domain context</p>
                </div>

                {/* Target Audience */}
                <div className="space-y-2">
                  <Label htmlFor="audience">Target Audience (Optional)</Label>
                  <Input
                    id="audience"
                    type="text"
                    value={formData.targetAudience || ''}
                    onChange={(e) => handleChange('targetAudience', e.target.value)}
                    placeholder="e.g., Small businesses, Students, Developers"
                    className="glass border-border/50 focus:border-primary transition-all duration-300"
                    maxLength={100}
                  />
                  <p className="text-xs text-muted-foreground">Who faces these problems</p>
                </div>

                {/* Region */}
                <div className="space-y-2">
                  <Label htmlFor="region">Region (Optional)</Label>
                  <Input
                    id="region"
                    type="text"
                    value={formData.region || ''}
                    onChange={(e) => handleChange('region', e.target.value)}
                    placeholder="e.g., North America, Europe, Global"
                    className="glass border-border/50 focus:border-primary transition-all duration-300"
                    maxLength={100}
                  />
                  <p className="text-xs text-muted-foreground">Geographic context</p>
                </div>
              </div>
            </div>
          )}

          {/* Submit Button */}
          <Button
            type="submit"
            size="lg"
            className="w-full bg-gradient-to-r from-accent to-primary text-white glow hover:glow-sm hover:scale-[1.02] transition-all duration-300 font-semibold text-lg shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={isLoading || !isFormValid}
          >
            <Search className="mr-2 h-5 w-5" />
            {isLoading ? 'Discovering Problems...' : 'Discover Problems'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
});

ProblemForm.displayName = 'ProblemForm';

export default ProblemForm;