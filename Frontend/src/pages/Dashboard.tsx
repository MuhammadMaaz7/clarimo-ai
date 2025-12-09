import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import {
  Lightbulb,
  Target,
  TrendingUp,
  ArrowRight,
  BarChart3,
  FileText,
  History,
  AlertCircle,
  Activity,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../lib/api';

interface DashboardStats {
  problemDiscovery: {
    total: number;
    totalProblems: number;
    latest?: string | null;
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
  };
}

export default function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [recentActivity, setRecentActivity] = useState<any[]>([]);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);

      // Fetch stats from all modules
      const [problemStats, ideaStats, competitorStats] = await Promise.allSettled([
        api.painPoints.getStats(),
        api.ideas.getAll(),
        api.competitorAnalyses.list(),
      ]);

      console.log('Dashboard Data:', { problemStats, ideaStats, competitorStats });

      const dashboardStats: DashboardStats = {
        problemDiscovery: {
          total: 0,
          totalProblems: 0,
        },
        ideas: {
          total: 0,
          validated: 0,
        },
        competitorAnalysis: {
          total: 0,
          totalCompetitors: 0,
        },
      };

      // Process problem discovery stats
      if (problemStats.status === 'fulfilled') {
        console.log('Problem Stats Value:', problemStats.value);
        if (problemStats.value?.success && problemStats.value?.stats) {
          dashboardStats.problemDiscovery = {
            total: problemStats.value.stats.total_analyses || 0,
            totalProblems: problemStats.value.stats.total_pain_points || 0,
            latest: problemStats.value.stats.latest_analysis,
          };
        }
      } else {
        console.error('Problem stats failed:', problemStats.reason);
      }

      // Process idea stats
      if (ideaStats.status === 'fulfilled') {
        console.log('Idea Stats Value:', ideaStats.value);
        const ideas = Array.isArray(ideaStats.value) ? ideaStats.value : [];
        dashboardStats.ideas = {
          total: ideas.length,
          validated: ideas.filter((idea: any) => idea.latest_validation?.status === 'completed').length,
          latest: ideas.length > 0 ? ideas[0].created_at : undefined,
        };
      } else {
        console.error('Idea stats failed:', ideaStats.reason);
      }

      // Process competitor analysis stats
      if (competitorStats.status === 'fulfilled') {
        console.log('Competitor Stats Value:', competitorStats.value);
        if (competitorStats.value?.success && competitorStats.value?.analyses) {
          const analyses = competitorStats.value.analyses;
          dashboardStats.competitorAnalysis = {
            total: analyses.length,
            totalCompetitors: analyses.reduce((sum: number, a: any) => sum + (a.competitors_found || 0), 0),
            latest: analyses.length > 0 ? analyses[0].created_at : undefined,
          };
        }
      } else {
        console.error('Competitor stats failed:', competitorStats.reason);
      }

      console.log('Final Dashboard Stats:', dashboardStats);
      setStats(dashboardStats);

      // Build recent activity
      const activities: any[] = [];
      
      if (problemStats.status === 'fulfilled' && problemStats.value?.success && problemStats.value?.stats) {
        const count = problemStats.value.stats.total_analyses || 0;
        if (count > 0) {
          activities.push({
            type: 'problem',
            count: count,
            date: problemStats.value.stats.latest_analysis,
          });
        }
      }
      
      if (ideaStats.status === 'fulfilled') {
        const ideas = Array.isArray(ideaStats.value) ? ideaStats.value : [];
        if (ideas.length > 0) {
          activities.push({
            type: 'idea',
            count: ideas.length,
            date: ideas[0].created_at,
          });
        }
      }
      
      if (competitorStats.status === 'fulfilled' && competitorStats.value?.success && competitorStats.value?.analyses) {
        const analyses = competitorStats.value.analyses;
        if (analyses.length > 0) {
          activities.push({
            type: 'competitor',
            count: analyses.length,
            date: analyses[0].created_at,
          });
        }
      }

      setRecentActivity(activities.sort((a, b) => 
        new Date(b.date || 0).getTime() - new Date(a.date || 0).getTime()
      ).slice(0, 3));

    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="space-y-8">
        {/* Welcome Header */}
        <div className="space-y-2">
          <h1 className="text-4xl font-bold">
            {getGreeting()}, {user?.full_name?.split(' ')[0] || 'there'}!
          </h1>
          <p className="text-lg text-muted-foreground">
            Here's what's happening with your startup journey
          </p>
        </div>

        {/* Stats Overview */}
        <div>
          <h2 className="text-2xl font-bold mb-4">Your Progress</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {/* Problem Discovery Stats */}
            <Card className="glass border-border/50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 bg-purple-500/10 rounded-lg">
                    <BarChart3 className="h-5 w-5 text-purple-500" />
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate('/discovered-problems')}
                    className="text-xs"
                  >
                    View All
                  </Button>
                </div>
                <div className="space-y-1">
                  <p className="text-3xl font-bold">{loading ? '...' : stats?.problemDiscovery.total || 0}</p>
                  <p className="text-sm text-muted-foreground">Discoveries</p>
                  <p className="text-xs text-muted-foreground">
                    {loading ? '...' : stats?.problemDiscovery.totalProblems || 0} problems found
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Ideas Stats */}
            <Card className="glass border-border/50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 bg-blue-500/10 rounded-lg">
                    <Lightbulb className="h-5 w-5 text-blue-500" />
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate('/ideas')}
                    className="text-xs"
                  >
                    View All
                  </Button>
                </div>
                <div className="space-y-1">
                  <p className="text-3xl font-bold">{loading ? '...' : stats?.ideas.total || 0}</p>
                  <p className="text-sm text-muted-foreground">Ideas</p>
                  <p className="text-xs text-muted-foreground">
                    {loading ? '...' : stats?.ideas.validated || 0} validated
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Competitor Analysis Stats */}
            <Card className="glass border-border/50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 bg-green-500/10 rounded-lg">
                    <Target className="h-5 w-5 text-green-500" />
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate('/competitor-analysis/history')}
                    className="text-xs"
                  >
                    View All
                  </Button>
                </div>
                <div className="space-y-1">
                  <p className="text-3xl font-bold">{loading ? '...' : stats?.competitorAnalysis.total || 0}</p>
                  <p className="text-sm text-muted-foreground">Analyses</p>
                  <p className="text-xs text-muted-foreground">
                    {loading ? '...' : stats?.competitorAnalysis.totalCompetitors || 0} competitors found
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Activity Stats */}
            <Card className="glass border-border/50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 bg-orange-500/10 rounded-lg">
                    <Activity className="h-5 w-5 text-orange-500" />
                  </div>
                </div>
                <div className="space-y-1">
                  <p className="text-3xl font-bold">
                    {loading ? '...' : (stats?.problemDiscovery.total || 0) + (stats?.ideas.total || 0) + (stats?.competitorAnalysis.total || 0)}
                  </p>
                  <p className="text-sm text-muted-foreground">Total Actions</p>
                  <p className="text-xs text-muted-foreground">
                    All time activity
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Recent Activity & Quick Links */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Recent Activity */}
          <Card className="glass border-border/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="h-5 w-5 text-primary" />
                Recent Activity
              </CardTitle>
              <CardDescription>Your latest actions across all modules</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center py-8 text-muted-foreground">Loading...</div>
              ) : recentActivity.length === 0 ? (
                <div className="text-center py-8">
                  <AlertCircle className="h-12 w-12 mx-auto text-muted-foreground mb-3" />
                  <p className="text-muted-foreground">No activity yet</p>
                  <p className="text-sm text-muted-foreground mt-1">Start by discovering problems or validating ideas</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {recentActivity.map((activity, index) => (
                    <div key={index} className="flex items-center gap-3 p-3 rounded-lg hover:bg-accent/5 transition-colors">
                      <div className={`p-2 rounded-lg ${
                        activity.type === 'problem' ? 'bg-purple-500/10' :
                        activity.type === 'idea' ? 'bg-blue-500/10' :
                        'bg-green-500/10'
                      }`}>
                        {activity.type === 'problem' && <BarChart3 className="h-4 w-4 text-purple-500" />}
                        {activity.type === 'idea' && <Lightbulb className="h-4 w-4 text-blue-500" />}
                        {activity.type === 'competitor' && <Target className="h-4 w-4 text-green-500" />}
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium">
                          {activity.type === 'problem' && 'Problem Discovery'}
                          {activity.type === 'idea' && 'Idea Validation'}
                          {activity.type === 'competitor' && 'Competitor Analysis'}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {activity.count} {activity.count === 1 ? 'item' : 'items'} • {formatDate(activity.date)}
                        </p>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          if (activity.type === 'problem') navigate('/discovered-problems');
                          if (activity.type === 'idea') navigate('/ideas');
                          if (activity.type === 'competitor') navigate('/competitor-analysis/history');
                        }}
                      >
                        <ArrowRight className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Links */}
          <Card className="glass border-border/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-primary" />
                Quick Links
              </CardTitle>
              <CardDescription>Access your work across all modules</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Button
                  variant="outline"
                  className="w-full justify-start glass border-border/50"
                  onClick={() => navigate('/discovered-problems')}
                >
                  <FileText className="mr-2 h-4 w-4" />
                  My Discovered Problems
                  <span className="ml-auto text-xs text-muted-foreground">
                    {stats?.problemDiscovery.total || 0}
                  </span>
                </Button>
                
                <Button
                  variant="outline"
                  className="w-full justify-start glass border-border/50"
                  onClick={() => navigate('/ideas')}
                >
                  <Lightbulb className="mr-2 h-4 w-4" />
                  My Ideas
                  <span className="ml-auto text-xs text-muted-foreground">
                    {stats?.ideas.total || 0}
                  </span>
                </Button>
                
                <Button
                  variant="outline"
                  className="w-full justify-start glass border-border/50"
                  onClick={() => navigate('/competitor-analysis/history')}
                >
                  <Target className="mr-2 h-4 w-4" />
                  My Competitor Analyses
                  <span className="ml-auto text-xs text-muted-foreground">
                    {stats?.competitorAnalysis.total || 0}
                  </span>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
