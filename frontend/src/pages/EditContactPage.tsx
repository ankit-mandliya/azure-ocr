import { useNavigate, useParams } from 'react-router-dom';
import { Alert, Box, Button, Card, CardContent, CircularProgress, Typography } from '@mui/material';
import ArrowBackRoundedIcon from '@mui/icons-material/ArrowBackRounded';
import { ContactForm } from '../components/forms/ContactForm';
import { getErrorMessage } from '../api/axios';
import { useContact, useUpdateContact } from '../hooks/useContacts';
import type { ContactInput } from '../types/contact';

export function EditContactPage() {
  const { id = '' } = useParams();
  const navigate = useNavigate();
  const { data: contact, isLoading, error } = useContact(id);
  const mutation = useUpdateContact();
  const submit = (values: ContactInput) => {
    mutation.mutate({ id, payload: values }, { onSuccess: () => navigate(`/contacts/${id}`) });
  };
  if (isLoading) return <Box className="loading-state"><CircularProgress /></Box>;
  if (error || !contact) return <Box className="page-wrap"><Alert severity="error">{getErrorMessage(error ?? new Error('Contact not found.'))}</Alert></Box>;
  return (
    <Box className="page-wrap form-page">
      <Button onClick={() => navigate(-1)} startIcon={<ArrowBackRoundedIcon />} color="inherit" sx={{ mb: 2.5 }}>Back</Button>
      <Box className="page-heading"><Box><Typography className="eyebrow">ADDRESS BOOK</Typography><Typography variant="h1">Edit contact</Typography><Typography className="page-subtitle">Update this contact’s information.</Typography></Box></Box>
      <Card className="content-card form-card"><CardContent><Typography variant="h2" sx={{ mb: 2.5 }}>Contact details</Typography>
        <ContactForm initialValues={contact} submitLabel="Save changes" busy={mutation.isPending} onSubmit={submit} onCancel={() => navigate(`/contacts/${id}`)} error={mutation.error ? getErrorMessage(mutation.error) : null} />
      </CardContent></Card>
    </Box>
  );
}
