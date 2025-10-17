import { useState } from 'react';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Search, Filter } from 'lucide-react';

interface ProblemFormProps {
  onSubmit: (data: FormData) => void;
  isLoading: boolean;
}

export interface FormData {
  problemDescription: string;
  industry?: string;
  region?: string;
  targetAudience?: string;
  budget?: string;
}

const ProblemForm = ({ onSubmit, isLoading }: ProblemFormProps) => {
  const [formData, setFormData] = useState<FormData>({
    problemDescription: '',
    industry: '',
    region: '',
    targetAudience: '',
    budget: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const handleChange = (field: keyof FormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <Card className="glass border-border/50">
      <CardHeader>
        <CardTitle className="text-2xl">Search Parameters</CardTitle>
        <CardDescription className="text-base">
          Describe the problem space you want to explore and set optional filters
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Problem Description */}
          <div className="space-y-2">
            <Label htmlFor="problem" className="text-base">Problem Description *</Label>
            <Textarea
              id="problem"
              name="problemDescription"
              value={formData.problemDescription}
              onChange={(e) => handleChange('problemDescription', e.target.value)}
              placeholder="Describe the problems you want to discover (e.g., 'Small businesses struggling with customer management')"
              className="min-h-[120px] resize-none glass border-border/50 focus:border-primary transition-all duration-300"
              required
            />
          </div>

          {/* Optional Filters */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-primary" />
              <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Optional Filters</h3>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {/* Industry */}
              <div className="space-y-2">
                <Label htmlFor="industry">Industry</Label>
                <Select
                  value={formData.industry}
                  onValueChange={(value) => handleChange('industry', value)}
                >
                  <SelectTrigger id="industry" className="glass border-border/50">
                    <SelectValue placeholder="Select industry" />
                  </SelectTrigger>
                  <SelectContent className="glass">
                    <SelectItem value="all">All Industries</SelectItem>
                    <SelectItem value="saas">SaaS</SelectItem>
                    <SelectItem value="ecommerce">E-commerce</SelectItem>
                    <SelectItem value="fintech">Fintech</SelectItem>
                    <SelectItem value="healthcare">Healthcare</SelectItem>
                    <SelectItem value="education">Education</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Region */}
              <div className="space-y-2">
                <Label htmlFor="region">Region</Label>
                <Select
                  value={formData.region}
                  onValueChange={(value) => handleChange('region', value)}
                >
                  <SelectTrigger id="region" className="glass border-border/50">
                    <SelectValue placeholder="Select region" />
                  </SelectTrigger>
                  <SelectContent className="glass">
                    <SelectItem value="global">Global</SelectItem>
                    <SelectItem value="north-america">North America</SelectItem>
                    <SelectItem value="europe">Europe</SelectItem>
                    <SelectItem value="asia">Asia</SelectItem>
                    <SelectItem value="latam">Latin America</SelectItem>
                    <SelectItem value="africa">Africa</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Target Audience */}
              <div className="space-y-2">
                <Label htmlFor="audience">Target Audience</Label>
                <Select
                  value={formData.targetAudience}
                  onValueChange={(value) => handleChange('targetAudience', value)}
                >
                  <SelectTrigger id="audience" className="glass border-border/50">
                    <SelectValue placeholder="Select audience" />
                  </SelectTrigger>
                  <SelectContent className="glass">
                    <SelectItem value="all">All Audiences</SelectItem>
                    <SelectItem value="b2b">B2B</SelectItem>
                    <SelectItem value="b2c">B2C</SelectItem>
                    <SelectItem value="enterprise">Enterprise</SelectItem>
                    <SelectItem value="smb">Small/Medium Business</SelectItem>
                    <SelectItem value="individual">Individual</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Budget */}
              <div className="space-y-2">
                <Label htmlFor="budget">Startup Budget</Label>
                <Select
                  value={formData.budget}
                  onValueChange={(value) => handleChange('budget', value)}
                >
                  <SelectTrigger id="budget" className="glass border-border/50">
                    <SelectValue placeholder="Select budget" />
                  </SelectTrigger>
                  <SelectContent className="glass">
                    <SelectItem value="all">Any Budget</SelectItem>
                    <SelectItem value="low">Low (&lt; $10K)</SelectItem>
                    <SelectItem value="medium">Medium ($10K - $50K)</SelectItem>
                    <SelectItem value="high">High (&gt; $50K)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            size="lg"
            className="w-full bg-gradient-to-r from-primary to-accent text-white glow hover:glow-sm hover:scale-[1.02] transition-all duration-300 font-semibold text-lg"
            disabled={isLoading || !formData.problemDescription.trim()}
          >
            <Search className="mr-2 h-5 w-5" />
            {isLoading ? 'Discovering Problems...' : 'Discover Problems'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};

export default ProblemForm;
