/**
 * CompetitorAnalysis Page
 * 
 * Main landing page for competitor analysis module
 * Shows list of products and option to create new
 */

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCompetitor } from '../contexts/CompetitorContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Plus, Search, TrendingUp, Loader2 } from 'lucide-react';
import LoadingSpinner from '../components/LoadingSpinner';

export default function CompetitorAnalysis() {
  const navigate = useNavigate();
  const { products, productsLoading, fetchProducts } = useCompetitor();

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  if (productsLoading && products.length === 0) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="glass border-border/50">
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <LoadingSpinner />
              <p className="text-muted-foreground mt-4">Loading products...</p>
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
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Competitor Analysis</h1>
            <p className="text-muted-foreground">
              Analyze your product against competitors in the market
            </p>
          </div>
          <Button onClick={() => navigate('/competitor-analysis/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Product
          </Button>
        </div>

        {/* Products List or Empty State */}
        {products.length === 0 ? (
          <Card className="glass border-border/50">
            <CardContent className="pt-6">
              <div className="text-center py-12">
                <div className="mx-auto w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                  <Search className="h-8 w-8 text-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-2">No Products Yet</h3>
                <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                  Start by adding your product to analyze competitors and discover market opportunities
                </p>
                <Button onClick={() => navigate('/competitor-analysis/new')}>
                  <Plus className="mr-2 h-4 w-4" />
                  Add Your First Product
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {products.map((product) => (
              <Card
                key={product.id}
                className="glass border-border/50 hover:border-primary/50 transition-all cursor-pointer"
                onClick={() => navigate(`/competitor-analysis/${product.id}`)}
              >
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    {product.product_name}
                  </CardTitle>
                  <CardDescription className="line-clamp-2">
                    {product.product_description}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Features</span>
                      <span className="font-medium">{product.key_features.length}</span>
                    </div>
                    {product.latest_analysis && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Competitors Found</span>
                        <span className="font-medium">{product.latest_analysis.competitors_found}</span>
                      </div>
                    )}
                    <div className="pt-2">
                      <Button variant="outline" size="sm" className="w-full">
                        <TrendingUp className="mr-2 h-4 w-4" />
                        {product.latest_analysis ? 'View Analysis' : 'Start Analysis'}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
