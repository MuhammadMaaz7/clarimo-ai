import { useNavigate } from 'react-router-dom';
import { useProfile } from '../hooks/useProfile';
import { useAuth } from '../contexts/AuthContext';
import { PremiumCard } from '../components/ui/premium/PremiumCard';
import { PremiumButton } from '../components/ui/premium/PremiumButton';
import { Label } from '../components/ui/label';
import { Input } from '../components/ui/input';
import { User, Mail, Settings, History, CheckCircle, Target, LogOut, ShieldCheck } from 'lucide-react';
import { motion, Variants } from 'framer-motion';

const Profile = () => {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const {
    user,
    formData,
    setFormData,
    isEditing,
    isSaving,
    updateProfile,
    cancelEdit,
    startEditing
  } = useProfile();

  const containerVariants: Variants = {
    hidden: { opacity: 0, y: 30 },
    visible: { 
      opacity: 1, 
      y: 0, 
      transition: { 
        duration: 0.6, 
        ease: "easeOut" 
      } 
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, x: -10 },
    visible: { opacity: 1, x: 0 }
  };

  return (
    <div className="container mx-auto px-6 py-12 max-w-7xl">
      <motion.div 
        initial="hidden" 
        animate="visible" 
        variants={containerVariants}
        className="space-y-10"
      >
        {/* Profile Header Dashboard */}
        <PremiumCard variant="glass" className="relative group overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000" />
          
          <div className="flex flex-col md:flex-row items-center gap-8 relative z-20">
            <div className="relative">
              <div className="rounded-[2rem] gradient-primary p-5 shadow-2xl shadow-primary/30 glow-sm">
                <User className="h-16 w-16 text-white" />
              </div>
              <div className="absolute -bottom-2 -right-2 bg-green-500 border-4 border-[#0a0a0a] h-6 w-6 rounded-full" title="Core System Active" />
            </div>

            <div className="flex-1 text-center md:text-left space-y-2">
              <div className="flex items-center justify-center md:justify-start gap-3">
                <h1 className="text-4xl font-black tracking-tighter text-white">{user?.full_name}</h1>
                <div className="bg-white/5 border border-white/10 px-3 py-1 rounded-full flex items-center gap-2">
                  <ShieldCheck className="h-3 w-3 text-blue-400" />
                  <span className="text-[10px] uppercase font-black tracking-widest text-blue-400">Verified Operator</span>
                </div>
              </div>
              
              <div className="flex flex-col md:flex-row md:items-center gap-4 text-muted-foreground/80">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Mail className="h-4 w-4 text-primary" />
                  {user?.email}
                </div>
              </div>
            </div>

            <PremiumButton 
              variant={isEditing ? "outlined" : "primary"}
              onClick={isEditing ? cancelEdit : startEditing}
              className="min-w-[160px]"
            >
              {isEditing ? <ArrowLeft className="mr-2 h-4 w-4" /> : <Settings className="mr-2 h-4 w-4" />}
              {isEditing ? 'Discard' : 'Edit Identity'}
            </PremiumButton>
          </div>
        </PremiumCard>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
          {/* Main Core Settings */}
          <div className="lg:col-span-2 space-y-6">
            <PremiumCard className="relative h-full">
               <div className="flex items-center gap-4 mb-8">
                  <div className="h-1 w-12 bg-primary rounded-full" />
                  <h2 className="text-xl font-bold tracking-tight uppercase text-xs tracking-widest text-muted-foreground">Biometric Data</h2>
               </div>

               <div className="space-y-8">
                {isEditing ? (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
                    <div className="space-y-2">
                      <Label className="text-xs font-black uppercase tracking-widest text-blue-400 ml-1">Full Legal Name</Label>
                      <Input
                        value={formData.fullName}
                        onChange={(e) => setFormData(p => ({ ...p, fullName: e.target.value }))}
                        className="h-14 bg-white/5 border-white/10 rounded-2xl focus:border-primary/50 transition-all text-lg"
                        placeholder="Operator Name"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-xs font-black uppercase tracking-widest text-blue-400 ml-1">Secure Email Communication</Label>
                      <Input
                        type="email"
                        value={formData.email}
                        readOnly
                        className="h-14 bg-white/5 border-white/10 rounded-2xl opacity-60 cursor-not-allowed text-lg"
                      />
                    </div>
                    <div className="flex gap-4 pt-4">
                      <PremiumButton 
                        onClick={updateProfile} 
                        loading={isSaving}
                        className="flex-1 shadow-primary/20"
                      >
                        Override Settings
                      </PremiumButton>
                      <PremiumButton 
                        variant="outlined" 
                        onClick={cancelEdit}
                        disabled={isSaving}
                        className="flex-1"
                      >
                        Cancel
                      </PremiumButton>
                    </div>
                  </motion.div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <motion.div variants={itemVariants} className="p-6 rounded-3xl bg-white/[0.02] border border-white/5">
                      <Label className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground mb-2 block">Operator</Label>
                      <p className="text-xl font-bold text-white">{user?.full_name}</p>
                    </motion.div>
                    
                    <motion.div variants={itemVariants} className="p-6 rounded-3xl bg-white/[0.02] border border-white/5">
                      <Label className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground mb-2 block">Encryption Channel</Label>
                      <p className="text-xl font-bold text-white truncate">{user?.email}</p>
                    </motion.div>

                    <motion.div variants={itemVariants} className="p-6 rounded-3xl bg-white/[0.02] border border-white/5">
                      <Label className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground mb-2 block">Clearance Level</Label>
                      <p className="text-xl font-bold text-green-400 flex items-center gap-2">
                        <ShieldCheck className="h-5 w-5" />
                        Active Alpha
                      </p>
                    </motion.div>

                    <motion.div variants={itemVariants} className="p-6 rounded-3xl bg-white/[0.02] border border-white/5">
                      <Label className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground mb-2 block">Data Centers</Label>
                      <p className="text-xl font-bold text-white italic">Multi-Regional</p>
                    </motion.div>
                  </div>
                )}
               </div>
            </PremiumCard>
          </div>

          {/* Intelligence Modules */}
          <div className="space-y-6">
            <PremiumCard variant="default">
               <h3 className="text-xs font-black uppercase tracking-widest text-muted-foreground mb-6">Archive Access</h3>
               <div className="space-y-3">
                  {[
                    { label: 'Intelligence Pipeline', icon: Target, path: '/ideas', color: 'text-blue-400' },
                    { label: 'Market Disruptions', icon: History, path: '/discovered-problems', color: 'text-green-400' },
                    { label: 'Entity Analysis', icon: CheckCircle, path: '/competitor-analysis/history', color: 'text-purple-400' }
                  ].map((action, i) => (
                    <motion.button
                      key={i}
                      whileHover={{ scale: 1.02, x: 5 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => navigate(action.path)}
                      className="w-full flex items-center gap-4 p-4 rounded-2xl bg-white/[0.03] border border-white/5 hover:border-white/10 hover:bg-white/5 transition-all text-left"
                    >
                      <action.icon className={`h-5 w-5 ${action.color}`} />
                      <span className="text-sm font-bold text-white/90">{action.label}</span>
                    </motion.button>
                  ))}
               </div>
            </PremiumCard>

            <PremiumCard variant="default" className="border-red-500/20 bg-red-500/[0.02]">
               <h3 className="text-xs font-black uppercase tracking-widest text-muted-foreground mb-6">Termination</h3>
               <div className="space-y-3">
                  <PremiumButton 
                    variant="outlined" 
                    onClick={logout}
                    className="w-full border-red-500/20 text-red-400 hover:bg-red-500/10"
                  >
                    <LogOut className="mr-2 h-4 w-4" />
                    Sever Connection
                  </PremiumButton>
               </div>
            </PremiumCard>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default Profile;

// Internal utility icons
const ArrowLeft = ({ className }: { className?: string }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></svg>
);