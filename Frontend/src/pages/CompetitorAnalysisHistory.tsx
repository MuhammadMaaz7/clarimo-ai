/**
 * Competitor Analysis History Page
 * Shows all previous analyses for the user
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { History, Plus, TrendingUp, Search, Trash2 } from 'lucide-react';
import ConfirmationModal from '../components/ConfirmationModal';
import { unifiedToast } from '../lib/toast-utils';
import api from '../lib/api';

export default function CompetitorAnalysisHistory() {
  const navigate = useNavigate();
  const [analyses, setAnalyses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean;
    analysisId: string;
    productName: string;
  }>({ isOpen: false, analysisId: '', productName: '' });

  useEffect(() => {
    loadAnalyses();
  }, []);

  const loadAnalyses = async () => {
    try {
      setLoading(true);
      const result = await api.competitorAnalyses.list();
      setAnalyses(result.analyses);
    } catch (error: any) {
      console.error('Failed to load analyses:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const openDeleteConfirmation = (analysisId: string, productName: string) => {
    setConfirmModal({ isOpen: true, analysisId, productName });
  };

  const closeDeleteConfirmation = () => {
    setConfirmModal({ isOpen: false, analysisId: '', productName: '' });
  };

  const handleDeleteConfirm = async () => {
    try {
      await api.competitorAnalyses.delete(confirmModal.analysisId);
      
      unifiedToast.success({
        description: 'Analysis deleted successfully!',
      });
      
      closeDeleteConfirmation();
      await loadAnalyses();
    } catch (error) {
      console.error('Error deleting analysis:', error);
      
      unifiedToast.error({
        description: 'Failed to delete analysis. Please try again later.',
      });
    }
  };

  // Filter analyses based on search query
  const filteredAnalyses = analyses.filter((analysis) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return analysis.product_name.toLowerCase().includes(query);
  });

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="glass border-border/50">
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <History className="h-12 w-12 animate-spin mx-auto text-primary mb-4" />
              <p className="text-muted-foreground">Loading analyses...</p>
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
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <History className="h-8 w-8 text-primary" />
              My Competitor Analyses
            </h1>
            <p className="text-muted-foreground mt-2">
              View and manage your previous competitor analyses
            </p>
          </div>
          <Button
            onClick={() => navigate('/competitor-analysis/new')}
            size="lg"
            className="bg-gradient-to-r from-accent to-primary text-white glow hover:glow-sm hover:scale-[1.02] transition-all duration-300"
          >
            <Plus className="mr-2 h-5 w-5" />
            New Analysis
          </Button>
        </div>

        {/* Search Bar */}
        {analyses.length > 0 && (
          <Card className="glass border-border/50">
            <CardContent className="pt-6">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search analyses by product name..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 glass border-border/50"
                />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Analyses List */}
        {filteredAnalyses.length === 0 && analyses.length === 0 ? (
          <Card className="glass border-border/50">
            <CardContent className="pt-6">
              <div className="text-center py-12">
                <History className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-xl font-semibold mb-2">No Analyses Yet</h3>
                <p className="text-muted-foreground mb-6">
                  Start by creating your first competitor analysis to discover market opportunities
                </p>
                <Button
                  onClick={() => navigate('/competitor-analysis/new')}
                  className="bg-gradient-to-r from-accent to-primary text-white"
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Create First Analysis
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : filteredAnalyses.length === 0 ? (
          <Card className="glass border-border/50">
            <CardContent className="pt-6">
              <div className="text-center py-12">
                <Search className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-xl font-semibold mb-2">No Results Found</h3>
                <p className="text-muted-foreground mb-6">
                  Try adjusting your search query
                </p>
                <Button
                  variant="outline"
                  onClick={() => setSearchQuery('')}
                  className="glass border-border/50"
                >
                  Clear Search
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-6">
            {filteredAnalyses.map((analysis) => (
              <Card
                key={analysis.analysis_id}
                className="glass border-border/50 hover:border-primary/50 transition-all duration-300 cursor-pointer"
                onClick={() => navigate(`/competitor-analysis/new?id=${analysis.analysis_id}`)}
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-xl mb-2">{analysis.product_name}</CardTitle>
                      <CardDescription>
                        {analysis.competitors_found} competitors found
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <p className="text-xs text-muted-foreground">
                        Created: {formatDate(analysis.created_at)}
                      </p>
                      <p className="text-xs text-green-500 font-medium">
                        {analysis.status === 'completed' ? 'Completed' : analysis.status}
                      </p>
                    </div>
                  </div>
                  <div className="mt-4 flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="glass border-border/50"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/competitor-analysis/new?id=${analysis.analysis_id}`);
                      }}
                    >
                      <TrendingUp className="mr-2 h-4 w-4" />
                      View Analysis
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="glass border-border/50 text-red-500 hover:text-red-600"
                      onClick={(e) => {
                        e.stopPropagation();
                        openDeleteConfirmation(analysis.analysis_id, analysis.product_name);
                      }}
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Results Count */}
        {!loading && filteredAnalyses.length > 0 && (
          <div className="text-center text-sm text-muted-foreground">
            Showing {filteredAnalyses.length} of {analyses.length} analysis(es)
          </div>
        )}
      </div>

      {/* Confirmation Modal */}
      <ConfirmationModal
        isOpen={confirmModal.isOpen}
        onClose={closeDeleteConfirmation}
        onConfirm={handleDeleteConfirm}
        title="Delete Analysis?"
        message={`Are you sure you want to delete the analysis for "${confirmModal.productName}"?`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
}
