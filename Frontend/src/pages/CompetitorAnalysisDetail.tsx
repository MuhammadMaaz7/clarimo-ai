/**
 * CompetitorAnalysisDetail Page
 * 
 * Shows product details and allows starting competitor analysis
 */

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useCompetitor } from '../contexts/CompetitorContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { ArrowLeft, Edit, Trash2, Play, Loader2, CheckCircle } from 'lucide-react';
import { UnifiedLoadingSpinner } from '../components/shared';
import { unifiedToast } from '../lib/toast-utils';

export default function CompetitorAnalysisDetail() {
  const { productId } = useParams<{ productId: string }>();
  const navigate = useNavigate();
  const {
    currentProduct,
    fetchProductById,
    deleteProduct,
    startAnalysis,
    productsLoading,
    analysisLoading,
  } = useCompetitor();

  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (productId) {
      fetchProductById(productId);
    }
  }, [productId, fetchProductById]);

  const handleDelete = async () => {
    if (!productId) return;

    const confirmed = window.confirm(
      'Are you sure you want to delete this product? This action cannot be undone.'
    );

    if (!confirmed) return;

    setIsDeleting(true);
    try {
      await deleteProduct(productId);
      unifiedToast.success({
        description: 'Product has been successfully deleted.',
      });
      navigate('/competitor-analysis');
    } catch (error: any) {
      unifiedToast.error({
        description: error.message || 'Failed to delete product',
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const handleStartAnalysis = async () => {
    if (!productId) return;

    try {
      await startAnalysis(productId);
      unifiedToast.success({
        description: 'Competitor analysis has been initiated. This may take a few minutes.',
      });
      navigate(`/competitor-analysis/${productId}/analysis`);
    } catch (error: any) {
      unifiedToast.error({
        description: error.message || 'Failed to start analysis',
      });
    }
  };

  if (productsLoading || !currentProduct) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="glass border-border/50">
          <CardContent className="pt-6">
            <UnifiedLoadingSpinner text="Loading product..." />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Back Button */}
        <Button variant="ghost" onClick={() => navigate('/competitor-analysis')}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Products
        </Button>

        {/* Product Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">{currentProduct.product_name}</h1>
            <p className="text-muted-foreground">
              Created {new Date(currentProduct.created_at).toLocaleDateString()}
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => navigate(`/competitor-analysis/${productId}/edit`)}>
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </Button>
            <Button variant="outline" size="sm" onClick={handleDelete} disabled={isDeleting}>
              {isDeleting ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Trash2 className="mr-2 h-4 w-4" />
              )}
              Delete
            </Button>
          </div>
        </div>

        {/* Product Details */}
        <Card className="glass border-border/50">
          <CardHeader>
            <CardTitle>Product Description</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground whitespace-pre-wrap">
              {currentProduct.product_description}
            </p>
          </CardContent>
        </Card>

        {/* Key Features */}
        <Card className="glass border-border/50">
          <CardHeader>
            <CardTitle>Key Features</CardTitle>
            <CardDescription>
              {currentProduct.key_features.length} feature{currentProduct.key_features.length !== 1 ? 's' : ''}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-2">
              {currentProduct.key_features.map((feature, index) => (
                <div
                  key={index}
                  className="flex items-start gap-2 p-3 rounded-lg bg-muted/30 border border-border/30"
                >
                  <CheckCircle className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                  <span className="text-sm">{feature}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Analysis Section */}
        <Card className="glass border-border/50">
          <CardHeader>
            <CardTitle>Competitor Analysis</CardTitle>
            <CardDescription>
              Analyze your product against competitors in the market
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {currentProduct.latest_analysis ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 rounded-lg bg-primary/10 border border-primary/30">
                  <div>
                    <p className="font-medium">Latest Analysis</p>
                    <p className="text-sm text-muted-foreground">
                      {currentProduct.latest_analysis.competitors_found} competitors found •{' '}
                      {new Date(currentProduct.latest_analysis.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <Badge variant="outline" className="border-primary text-primary">
                    {currentProduct.latest_analysis.status}
                  </Badge>
                </div>
                <div className="flex gap-3">
                  <Button
                    onClick={() => navigate(`/competitor-analysis/${productId}/analysis`)}
                    className="flex-1"
                  >
                    View Analysis Report
                  </Button>
                  <Button
                    variant="outline"
                    onClick={handleStartAnalysis}
                    disabled={analysisLoading}
                  >
                    {analysisLoading ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Play className="mr-2 h-4 w-4" />
                    )}
                    Run New Analysis
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-muted-foreground mb-4">
                  No analysis has been run for this product yet
                </p>
                <Button onClick={handleStartAnalysis} disabled={analysisLoading}>
                  {analysisLoading ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Play className="mr-2 h-4 w-4" />
                  )}
                  Start Competitor Analysis
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
