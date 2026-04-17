import IdeaSubmissionForm from '../components/IdeaSubmissionForm';
import { useValidation } from '../contexts/ValidationContext';
import { IdeaFormData } from '../types/validation';
import { useNavigate } from 'react-router-dom';

import { ModuleHeader } from '../components/ui/ModuleHeader';
import { Lightbulb } from 'lucide-react';

export default function IdeaNew() {
  const navigate = useNavigate();
  const { createIdea, ideasLoading } = useValidation();

  const handleSubmit = async (data: IdeaFormData) => {
    try {
      const newIdea = await createIdea(data);
      navigate(`/ideas/${newIdea.id}`);
    } catch (error) {
      console.error('Error creating idea:', error);
    }
  };

  return (
    <div className="responsive-container-dashboard">
      <div className="max-w-3xl mx-auto space-y-8">
        <ModuleHeader
          icon={Lightbulb}
          title="Submit Your Idea"
          description="Provide details about your startup idea for comprehensive validation and architectural mapping."
        />

        <div className="w-full">
          <IdeaSubmissionForm onSubmit={handleSubmit} isLoading={ideasLoading} />
        </div>
      </div>
    </div>
  );
}
