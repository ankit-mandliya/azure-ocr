import { useNavigate } from 'react-router-dom';
import { Box, Button, Card, CardContent, Typography } from '@mui/material';
import ArrowBackRoundedIcon from '@mui/icons-material/ArrowBackRounded';
import { ContactForm } from '../components/forms/ContactForm';
import { getErrorMessage } from '../api/axios';
import { useCreateContact } from '../hooks/useContacts';
import { emptyContact, type ContactInput } from '../types/contact';

export function CreateContactPage() {
  const navigate = useNavigate();
  const mutation = useCreateContact();
  const submit = (values: ContactInput) => {
    mutation.mutate(values, { onSuccess: (contact) => navigate(`/contacts/${contact.id}`) });
  };
  return (
    <Box className="page-wrap form-page">
      <Button onClick={() => navigate(-1)} startIcon={<ArrowBackRoundedIcon />} color="inherit" sx={{ mb: 2.5 }}>Back</Button>
      <Box className="page-heading"><Box><Typography className="eyebrow">ADDRESS BOOK</Typography><Typography variant="h1">New contact</Typography><Typography className="page-subtitle">Add the details you want to keep at hand.</Typography></Box></Box>
      <Card className="content-card form-card"><CardContent><Typography variant="h2" sx={{ mb: 0.5 }}>Contact details</Typography><Typography className="section-subtitle" sx={{ mb: 3 }}>Add at least a name, email, phone number, or company.</Typography>
        <ContactForm initialValues={emptyContact} submitLabel="Create contact" busy={mutation.isPending} onSubmit={submit} onCancel={() => navigate('/contacts')} error={mutation.error ? getErrorMessage(mutation.error) : null} />
      </CardContent></Card>
    </Box>
  );
}
