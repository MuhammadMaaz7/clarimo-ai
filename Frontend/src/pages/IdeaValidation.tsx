/**
 * IdeaValidation Page
 * Production-ready with Premium UI and decoupled logic
 */

import { useParams, useNavigate } from 'react-router-dom';
import { useIdeaValidation } from '../hooks/useIdeaValidation';
import { ValidationProgress } from '../components/ValidationProgress';
import ValidationReportView from '../components/ValidationReportView';
import { PremiumCard } from '../components/ui/premium/PremiumCard';
import { PremiumButton } from '../components/ui/premium/PremiumButton';
import { Target, ArrowLeft, RefreshCw, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { ModuleHeader } from '../components/ui/ModuleHeader';

export default function IdeaValidation() {
  const { ideaId } = useParams<{ ideaId: string }>();
  const navigate = useNavigate();
  const {
    idea,
    validation,
    status,
    loading,
    isActionRunning,
    startValidation,
    exportReport
  } = useIdeaValidation(ideaId);

  const containerVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
  };

  if (loading && !validation) {
    return (
      <div className="container mx-auto px-4 py-20 flex flex-col items-center justify-center min-h-[60vh]">
        <motion.div 
          animate={{ rotate: 360 }} 
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="rounded-full h-12 w-12 border-t-2 border-primary mb-6"
        />
        <p className="text-muted-foreground animate-pulse font-bold tracking-widest uppercase text-xs">Synchronizing Intel...</p>
      </div>
    );
  }

  if (!idea) {
    return (
      <div className="container mx-auto px-4 py-20 max-w-xl">
        <PremiumCard variant="default" className="text-center space-y-6">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto" />
          <div className="space-y-2">
            <h2 className="text-2xl font-bold">Concept Not Found</h2>
            <p className="text-muted-foreground">The specified idea does not exist or has been archived.</p>
          </div>
          <PremiumButton variant="outlined" onClick={() => navigate('/ideas')} className="w-full">
             <ArrowLeft className="mr-2 h-4 w-4" />
             Back to Pipeline
          </PremiumButton>
        </PremiumCard>
      </div>
    );
  }

  return (
    <div className="responsive-container-dashboard">
      <div className="max-w-6xl mx-auto space-y-8">
        <motion.div 
          initial="hidden"
          animate="visible"
          variants={containerVariants}
          className="space-y-8"
        >
          {/* Header Section */}
          <ModuleHeader
            icon={Target}
            title={idea.title}
            description={`Algorithmically mapping market viability and technical feasibility for your startup concept. Current Status: ${status?.status || 'Initial Assessment'}`}
            actions={
              <div className="flex items-center gap-3">
                <PremiumButton variant="ghost" onClick={() => navigate(`/ideas/${ideaId}`)}>
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Back
                </PremiumButton>
                {validation?.status === 'completed' && (
                  <PremiumButton onClick={() => startValidation()} loading={isActionRunning}>
                      <RefreshCw className="mr-2 h-4 w-4" />
                      Relaunch Scan
                  </PremiumButton>
                )}
              </div>
            }
          />

          {/* Content Section */}
          <AnimatePresence mode="wait">
            {status?.status === 'pending' || status?.status === 'processing' ? (
              <motion.div
                key="progress"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="max-w-4xl mx-auto w-full"
              >
                <ValidationProgress
                  validationId={validation?.validation_id || ''}
                  ideaTitle={idea.title}
                  onComplete={() => {}}
                  onError={() => {}}
                  onRetry={() => startValidation()}
                />
              </motion.div>
            ) : validation?.status === 'completed' && validation.report_data ? (
              <motion.div
                key="report"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <ValidationReportView
                  report={validation.report_data}
                  onExportJson={() => exportReport('json')}
                  onExportPdf={() => exportReport('pdf')}
                  onShare={() => {}}
                  isExporting={isActionRunning}
                />
              </motion.div>
            ) : (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="py-12"
              >
                <div className="max-w-4xl mx-auto">
                  <PremiumCard variant="default" className="text-center py-24 border-dashed border-white/10">
                    <div className="max-w-md mx-auto space-y-8">
                      <div className="bg-primary/10 w-20 h-20 rounded-full flex items-center justify-center mx-auto border border-primary/20">
                         <AlertCircle className="h-10 w-10 text-primary" />
                      </div>
                      <div className="space-y-3">
                        <h2 className="text-3xl font-black">Scan Required</h2>
                        <p className="text-muted-foreground text-lg">
                          {validation?.status === 'failed' 
                            ? 'The prior scan encountered a structural failure. Algorithm recalibration required.' 
                            : 'Deploy the validation engine to map market viability and technical feasibility.'}
                        </p>
                      </div>
                      <PremiumButton 
                        size="lg" 
                        className="w-full h-16 text-xl font-black" 
                        onClick={() => startValidation()}
                        loading={isActionRunning}
                      >
                        {isActionRunning ? 'Initializing...' : 'Deploy Validation Scan'}
                      </PremiumButton>
                    </div>
                  </PremiumCard>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </div>
  );
}
