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
    <div className="container mx-auto px-4 py-8">
      <IdeaSubmissionForm onSubmit={handleSubmit} isLoading={ideasLoading} />
    </div>
  );
}
