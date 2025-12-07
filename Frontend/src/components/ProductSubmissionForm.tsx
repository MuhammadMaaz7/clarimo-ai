/**
 * ProductSubmissionForm Component
 * 
 * Form for creating/editing products for competitor analysis
 */

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Label } from './ui/label';
import { Plus, X, Loader2 } from 'lucide-react';
import { ProductFormData } from '../types/competitor';
import { useToast } from '../hooks/use-toast';

interface ProductSubmissionFormProps {
  initialData?: Partial<ProductFormData>;
  onSubmit: (data: ProductFormData) => Promise<void>;
  isLoading?: boolean;
  submitButtonText?: string;
}

export default function ProductSubmissionForm({
  initialData,
  onSubmit,
  isLoading = false,
  submitButtonText = 'Create Product',
}: ProductSubmissionFormProps) {
  const { toast } = useToast();
  const [formData, setFormData] = useState<ProductFormData>({
    productName: initialData?.productName || '',
    productDescription: initialData?.productDescription || '',
    keyFeatures: initialData?.keyFeatures || [''],
  });

  const [errors, setErrors] = useState<Partial<Record<keyof ProductFormData, string>>>({});

  const handleChange = (field: keyof ProductFormData, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  const handleFeatureChange = (index: number, value: string) => {
    const newFeatures = [...formData.keyFeatures];
    newFeatures[index] = value;
    handleChange('keyFeatures', newFeatures);
  };

  const addFeature = () => {
    handleChange('keyFeatures', [...formData.keyFeatures, '']);
  };

  const removeFeature = (index: number) => {
    if (formData.keyFeatures.length > 1) {
      const newFeatures = formData.keyFeatures.filter((_, i) => i !== index);
      handleChange('keyFeatures', newFeatures);
    }
  };

  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof ProductFormData, string>> = {};

    if (!formData.productName.trim()) {
      newErrors.productName = 'Product name is required';
    }

    if (!formData.productDescription.trim()) {
      newErrors.productDescription = 'Product description is required';
    } else if (formData.productDescription.trim().length < 20) {
      newErrors.productDescription = 'Description should be at least 20 characters';
    }

    const validFeatures = formData.keyFeatures.filter((f) => f.trim());
    if (validFeatures.length === 0) {
      newErrors.keyFeatures = 'At least one key feature is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      toast({
        title: 'Validation Error',
        description: 'Please fill in all required fields correctly.',
        variant: 'destructive',
      });
      return;
    }

    try {
      // Filter out empty features
      const cleanedData = {
        ...formData,
        keyFeatures: formData.keyFeatures.filter((f) => f.trim()),
      };

      await onSubmit(cleanedData);

      toast({
        title: 'Success',
        description: 'Product saved successfully!',
      });
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to save product',
        variant: 'destructive',
      });
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle>Product Information</CardTitle>
          <CardDescription>
            Provide details about your product for competitor analysis
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Product Name */}
          <div className="space-y-2">
            <Label htmlFor="productName">
              Product Name <span className="text-destructive">*</span>
            </Label>
            <Input
              id="productName"
              value={formData.productName}
              onChange={(e) => handleChange('productName', e.target.value)}
              placeholder="e.g., TaskMaster Pro"
              className={errors.productName ? 'border-destructive' : ''}
              disabled={isLoading}
            />
            {errors.productName && (
              <p className="text-sm text-destructive">{errors.productName}</p>
            )}
          </div>

          {/* Product Description */}
          <div className="space-y-2">
            <Label htmlFor="productDescription">
              Product Description <span className="text-destructive">*</span>
            </Label>
            <Textarea
              id="productDescription"
              value={formData.productDescription}
              onChange={(e) => handleChange('productDescription', e.target.value)}
              placeholder="Describe what your product does, who it's for, and what problem it solves..."
              className={`min-h-[120px] resize-none ${errors.productDescription ? 'border-destructive' : ''}`}
              disabled={isLoading}
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{errors.productDescription || 'Minimum 20 characters'}</span>
              <span>{formData.productDescription.length} characters</span>
            </div>
          </div>

          {/* Key Features */}
          <div className="space-y-2">
            <Label>
              Key Features <span className="text-destructive">*</span>
            </Label>
            <p className="text-sm text-muted-foreground mb-3">
              List the main features that make your product unique
            </p>
            <div className="space-y-3">
              {formData.keyFeatures.map((feature, index) => (
                <div key={index} className="flex gap-2">
                  <Input
                    value={feature}
                    onChange={(e) => handleFeatureChange(index, e.target.value)}
                    placeholder={`Feature ${index + 1}`}
                    className="flex-1"
                    disabled={isLoading}
                  />
                  {formData.keyFeatures.length > 1 && (
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      onClick={() => removeFeature(index)}
                      disabled={isLoading}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              ))}
            </div>
            {errors.keyFeatures && (
              <p className="text-sm text-destructive">{errors.keyFeatures}</p>
            )}
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={addFeature}
              disabled={isLoading}
              className="mt-2"
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Feature
            </Button>
          </div>

          {/* Submit Button */}
          <div className="flex gap-3 pt-4">
            <Button type="submit" disabled={isLoading} className="flex-1">
              {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {submitButtonText}
            </Button>
          </div>
        </CardContent>
      </Card>
    </form>
  );
}
