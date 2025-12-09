import IdeaSubmissionForm from '../components/IdeaSubmissionForm';
import { useValidation } from '../contexts/ValidationContext';
import { IdeaFormData } from '../types/validation';
import { useNavigate } from 'react-router-dom';

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
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <div className="space-y-6">
        {/* Header */}
        <div className="text-center space-y-2 mb-8">
          <h1 className="text-3xl font-bold">Submit Your Idea</h1>
          <p className="text-muted-foreground">
            Provide details about your startup idea for comprehensive validation
          </p>
        </div>

        {/* Form */}
        <IdeaSubmissionForm onSubmit={handleSubmit} isLoading={ideasLoading} />
      </div>
    </div>
  );
}
