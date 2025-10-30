import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { ArrowLeft, AlertCircle } from 'lucide-react';
import PainPointsDisplay from '../components/PainPointsDisplay';
import { api } from '../lib/api';

const AnalysisView = () => {
    const { inputId } = useParams<{ inputId: string }>();
    const navigate = useNavigate();
    const [analysis, setAnalysis] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (inputId) {
            fetchAnalysis();
        }
    }, [inputId]);

    const fetchAnalysis = async () => {
        if (!inputId) return;

        try {
            setLoading(true);
            const response = await api.painPoints.getAnalysisFromDB(inputId);

            if (response.success) {
                setAnalysis(response.analysis);
            } else {
                setError('Analysis not found');
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load analysis');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="responsive-spacing-md pb-8">
                <div className="flex items-center justify-center p-12">
                    <div className="flex flex-col items-center space-y-4">
                        <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
                        <span className="text-lg font-medium text-white">Loading analysis...</span>
                    </div>
                </div>
            </div>
        );
    }

    if (error || !analysis) {
        return (
            <div className="responsive-spacing-md pb-8">
                <div className="text-center p-8">
                    <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-6">
                        <AlertCircle className="mx-auto h-12 w-12 text-red-400 mb-4" />
                        <p className="text-red-300 mb-4">Error: {error || 'Analysis not found'}</p>
                        <Button onClick={() => navigate('/profile')} variant="outline" className="border-red-500/20 text-red-300 hover:bg-red-500/10">
                            Back to Profile
                        </Button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="responsive-spacing-md pb-8">
            {/* Header */}
            <div className="flex items-center gap-4 mb-6">
                <Button
                    variant="ghost"
                    onClick={() => navigate('/profile')}
                    className="text-white hover:bg-white/10"
                >
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back to Profile
                </Button>
            </div>

            {/* Analysis Info */}
            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6 mb-6">
                <h1 className="text-2xl font-bold text-white mb-2">Analysis Results</h1>
                <p className="text-gray-300 mb-4">"{analysis.original_query}"</p>
                <div className="flex items-center gap-6 text-sm text-gray-400">
                    <span>{analysis.pain_points_count} problems found</span>
                    <span>•</span>
                    <span>{analysis.total_clusters} discussion themes</span>
                    <span>•</span>
                    <span>Analyzed {new Date(analysis.created_at).toLocaleDateString()}</span>
                </div>
            </div>

            {/* Pain Points Display */}
            {inputId && <PainPointsDisplay inputId={inputId} />}
        </div>
    );
};

export default AnalysisView;