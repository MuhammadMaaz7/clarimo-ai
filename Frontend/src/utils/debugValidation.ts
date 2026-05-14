/**
 * Debug utilities for validation display issues
 * 
 * Usage in browser console:
 * import { debugValidation } from './utils/debugValidation';
 * debugValidation.checkIdeasData();
 */

import api from '../lib/api';

export const debugValidation = {
  /**
   * Check if ideas are being fetched correctly
   */
  async checkIdeasData() {
    console.group('🔍 Debug: Ideas Data');
    
    try {
      const ideas = await api.ideas.getAll();
      console.log(`✓ Fetched ${ideas.length} ideas`);
      
      ideas.forEach((idea: any, index: number) => {
        console.group(`Idea ${index + 1}: ${idea.title}`);
        console.log('ID:', idea.id);
        console.log('Validation Count:', idea.validation_count);
        console.log('Latest Validation ID:', idea.latest_validation_id);
        
        if (idea.latest_validation) {
          console.log('✓ Latest Validation:', {
            validation_id: idea.latest_validation.validation_id,
            overall_score: idea.latest_validation.overall_score,
            status: idea.latest_validation.status,
            created_at: idea.latest_validation.created_at,
          });
        } else {
          console.warn('✗ No latest_validation populated');
          
          if (idea.latest_validation_id) {
            console.warn('  → latest_validation_id exists but latest_validation is null');
            console.warn('  → This indicates a backend population issue');
          } else {
            console.log('  → No latest_validation_id (idea not validated yet)');
          }
        }
        
        console.groupEnd();
      });
      
      // Summary
      const validatedIdeas = ideas.filter((i: any) => i.latest_validation);
      const ideasWithValidationId = ideas.filter((i: any) => i.latest_validation_id);
      
      console.log('\n📊 Summary:');
      console.log(`Total ideas: ${ideas.length}`);
      console.log(`Ideas with latest_validation_id: ${ideasWithValidationId.length}`);
      console.log(`Ideas with latest_validation populated: ${validatedIdeas.length}`);
      
      if (ideasWithValidationId.length > validatedIdeas.length) {
        console.error(
          `⚠️ ISSUE DETECTED: ${ideasWithValidationId.length - validatedIdeas.length} ` +
          `ideas have latest_validation_id but latest_validation is not populated`
        );
        console.log('This indicates a backend issue with _populate_latest_validation()');
      } else {
        console.log('✓ All ideas with validations are properly populated');
      }
      
    } catch (error) {
      console.error('✗ Failed to fetch ideas:', error);
    }
    
    console.groupEnd();
  },

  /**
   * Check a specific idea's validation
   */
  async checkIdeaValidation(ideaId: string) {
    console.group(`🔍 Debug: Idea ${ideaId}`);
    
    try {
      const idea = await api.ideas.getById(ideaId);
      console.log('Idea:', idea);
      
      if (idea.latest_validation_id) {
        console.log(`\nFetching validation ${idea.latest_validation_id}...`);
        
        try {
          const validation = await api.validations.getResult(idea.latest_validation_id);
          console.log('✓ Validation:', validation);
          
          if (idea.latest_validation) {
            console.log('✓ latest_validation is populated in idea response');
          } else {
            console.error('✗ latest_validation is NOT populated in idea response');
            console.log('Backend should populate this field');
          }
        } catch (error) {
          console.error('✗ Failed to fetch validation:', error);
        }
      } else {
        console.log('No latest_validation_id (idea not validated yet)');
      }
      
    } catch (error) {
      console.error('✗ Failed to fetch idea:', error);
    }
    
    console.groupEnd();
  },

  /**
   * Check backend debug endpoint
   */
  async checkBackendLinkage(ideaId: string) {
    console.group(`🔍 Debug: Backend Linkage for ${ideaId}`);
    
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(
        `http://localhost:8000/api/debug/validation-linkage/${ideaId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Backend Debug Response:', data);
      
      if (data.is_healthy) {
        console.log('✓ Validation linkage is healthy');
      } else {
        console.error('✗ Issues detected:', data.issues);
      }
      
    } catch (error) {
      console.error('✗ Failed to check backend linkage:', error);
    }
    
    console.groupEnd();
  },

  /**
   * Check all ideas linkage health
   */
  async checkAllIdeasLinkage() {
    console.group('🔍 Debug: All Ideas Linkage Health');
    
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(
        'http://localhost:8000/api/debug/all-ideas-linkage',
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Backend Debug Response:', data);
      
      console.log(`\n📊 Summary:`);
      console.log(`Total ideas: ${data.total_ideas}`);
      console.log(`Ideas with validations: ${data.ideas_with_validations}`);
      console.log(`Ideas with issues: ${data.ideas_with_issues}`);
      
      if (data.is_healthy) {
        console.log('✓ All ideas are healthy');
      } else {
        console.error('✗ Issues detected:');
        data.issues.forEach((issue: any) => {
          console.error(`  - ${issue.title}:`, issue.issues);
        });
      }
      
    } catch (error) {
      console.error('✗ Failed to check backend linkage:', error);
    }
    
    console.groupEnd();
  },

  /**
   * Run all checks
   */
  async runAllChecks(ideaId?: string) {
    console.log('🚀 Running all validation debug checks...\n');
    
    await this.checkIdeasData();
    console.log('\n');
    
    if (ideaId) {
      await this.checkIdeaValidation(ideaId);
      console.log('\n');
      await this.checkBackendLinkage(ideaId);
    } else {
      await this.checkAllIdeasLinkage();
    }
    
    console.log('\n✅ All checks complete');
  },
};

// Make it available globally for easy console access
if (typeof window !== 'undefined') {
  (window as any).debugValidation = debugValidation;
}

export default debugValidation;
