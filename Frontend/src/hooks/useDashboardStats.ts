import { useState, useCallback, useEffect } from 'react';
import { api } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';

interface DashboardStats {
  problemDiscovery: {
    total: number;
    totalProblems: number;
    latest?: string | null;
    latestTitle?: string | null;
  };
  ideas: {
    total: number;
    validated: number;
    latest?: string | null;
  };
  competitorAnalysis: {
    total: number;
    totalCompetitors: number;
    latest?: string | null;
    latestTitle?: string | null;
  };
  launchPlanning: {
    total: number;
    latest?: string | null;
    latestTitle?: string | null;
  };
  gtm: {
    total: number;
    latest?: string | null;
    latestTitle?: string | null;
  };
}

interface Activity {
  type: 'problem' | 'idea' | 'competitor' | 'launch' | 'gtm';
  count: number;
  date?: string | null;
}

export function useDashboardStats() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recentActivity, setRecentActivity] = useState<Activity[]>([]);

  const fetchStats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch stats from all modules using settled promises to ensure partial success works
      const [problemStats, ideaStats, competitorStats, launchStats, gtmStats] = await Promise.allSettled([
        api.painPoints.getStats(),
        api.ideas.getAll(),
        api.competitorAnalyses.list(),
        api.launchPlanning.getHistory(user?.id || ''),
        api.gtm.getHistory(user?.id || ''),
      ]);

      const dashboardStats: DashboardStats = {
        problemDiscovery: { total: 0, totalProblems: 0 },
        ideas: { total: 0, validated: 0 },
        competitorAnalysis: { total: 0, totalCompetitors: 0 },
        launchPlanning: { total: 0 },
        gtm: { total: 0 },
      };

      const activities: Activity[] = [];

      // Process problem discovery stats
      if (problemStats.status === 'fulfilled' && problemStats.value?.success && problemStats.value?.stats) {
        const s = problemStats.value.stats;
        dashboardStats.problemDiscovery = {
          total: s.total_analyses || 0,
          totalProblems: s.total_pain_points || 0,
          latest: s.latest_analysis,
        };
        if (s.total_analyses > 0) activities.push({ type: 'problem', count: s.total_analyses, date: s.latest_analysis });
      }

      // Process idea stats
      if (ideaStats.status === 'fulfilled') {
        const ideas = Array.isArray(ideaStats.value) ? ideaStats.value : [];
        dashboardStats.ideas = {
          total: ideas.length,
          validated: ideas.filter((idea: any) => idea.latest_validation?.status === 'completed').length,
          latest: ideas.length > 0 ? ideas[0].created_at : undefined,
        };
        if (ideas.length > 0) activities.push({ type: 'idea', count: ideas.length, date: ideas[0].created_at });
      }

      // Process competitor analysis stats
      if (competitorStats.status === 'fulfilled' && competitorStats.value?.success && competitorStats.value?.analyses) {
        const analyses = competitorStats.value.analyses;
        dashboardStats.competitorAnalysis = {
          total: analyses.length,
          totalCompetitors: analyses.reduce((sum: number, a: any) => sum + (a.competitors_found || 0), 0),
          latest: analyses.length > 0 ? analyses[0].created_at : undefined,
        };
        if (analyses.length > 0) activities.push({ type: 'competitor', count: analyses.length, date: analyses[0].created_at });
      }

      // Process launch planning stats
      if (launchStats.status === 'fulfilled') {
        const plans = Array.isArray(launchStats.value) ? launchStats.value : [];
        dashboardStats.launchPlanning = {
          total: plans.length,
          latest: plans.length > 0 ? plans[0].created_at : undefined,
          latestTitle: plans.length > 0 ? (plans[0].inputs?.startup_name || plans[0].inputs?.target_audience) : undefined,
        };
        if (plans.length > 0) activities.push({ type: 'launch', count: plans.length, date: plans[0].created_at });
      }

      // Process GTM stats
      if (gtmStats.status === 'fulfilled') {
        const strategies = Array.isArray(gtmStats.value) ? gtmStats.value : [];
        dashboardStats.gtm = {
          total: strategies.length,
          latest: strategies.length > 0 ? strategies[0].created_at : undefined,
          latestTitle: strategies.length > 0 ? (strategies[0].inputs?.startup_description.slice(0, 30) + '...') : undefined,
        };
        if (strategies.length > 0) activities.push({ type: 'gtm', count: strategies.length, date: strategies[0].created_at });
      }

      setStats(dashboardStats);
      setRecentActivity(
        activities
          .sort((a, b) => new Date(b.date || 0).getTime() - new Date(a.date || 0).getTime())
          .slice(0, 3)
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, [user?.id]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return {
    stats,
    loading,
    error,
    recentActivity,
    refresh: fetchStats,
    totalActions: (stats?.problemDiscovery.total || 0) + 
                  (stats?.ideas.total || 0) + 
                  (stats?.competitorAnalysis.total || 0) + 
                  (stats?.launchPlanning.total || 0) +
                  (stats?.gtm.total || 0),
  };
}
