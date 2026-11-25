import { Link as RouterLink, useNavigate, useParams } from 'react-router-dom';
import {
  Alert, Avatar, Box, Button, Card, CardContent, CircularProgress, Grid, Stack, Typography,
} from '@mui/material';
import ArrowBackRoundedIcon from '@mui/icons-material/ArrowBackRounded';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import { getErrorMessage } from '../api/axios';
import { useContact } from '../hooks/useContacts';

const detailFields = [
  ['Email', 'email'],
  ['Phone', 'contact_number'],
  ['Company', 'company_name'],
  ['Designation', 'job_title'],
  ['Website', 'website'],
  ['Address', 'address'],
] as const;

export function ContactDetailsPage() {
  const { id = '' } = useParams();
  const navigate = useNavigate();
  const { data: contact, isLoading, error } = useContact(id);
  if (isLoading) return <Box className="loading-state"><CircularProgress /></Box>;
  if (error || !contact) return <Box className="page-wrap"><Alert severity="error">{getErrorMessage(error ?? new Error('Contact not found.'))}</Alert><Button onClick={() => navigate('/contacts')} startIcon={<ArrowBackRoundedIcon />} sx={{ mt: 2 }}>Back to contacts</Button></Box>;
  const fullName = [contact.first_name, contact.last_name].filter(Boolean).join(' ') || 'Unnamed contact';

  return (
    <Box className="page-wrap">
      <Button component={RouterLink} to="/contacts" startIcon={<ArrowBackRoundedIcon />} color="inherit" sx={{ mb: 2.5 }}>All contacts</Button>
      <Card className="content-card detail-hero">
        <CardContent className="detail-hero-content">
          <Avatar className="detail-avatar">{`${contact.first_name?.[0] ?? ''}${contact.last_name?.[0] ?? contact.company_name?.[0] ?? '?'}`}</Avatar>
          <Box className="detail-identity"><Typography className="eyebrow">CONTACT PROFILE</Typography><Typography variant="h1">{fullName}</Typography><Typography className="page-subtitle">{[contact.job_title, contact.company_name].filter(Boolean).join(' · ') || 'Business contact'}</Typography></Box>
          <Button component={RouterLink} to={`/contacts/edit/${contact.id}`} variant="outlined" startIcon={<EditOutlinedIcon />}>Edit contact</Button>
        </CardContent>
      </Card>
      <Card className="content-card detail-card">
        <CardContent><Typography variant="h2" sx={{ mb: 2.5 }}>Contact information</Typography>
          <Grid container spacing={3}>
            {detailFields.map(([label, key]) => (
              <Grid key={key} size={{ xs: 12, sm: 6 }}>
                <Typography className="detail-label">{label}</Typography>
                {key === 'website' && contact[key] ? <Typography component="a" href={contact[key] ?? undefined} target="_blank" rel="noreferrer" className="detail-value">{contact[key]}</Typography> : <Typography className="detail-value">{contact[key] || 'Not provided'}</Typography>}
              </Grid>
            ))}
          </Grid>
          <Stack direction="row" spacing={1} sx={{ mt: 3 }}>
            {contact.needs_review && <Alert severity="warning" sx={{ py: 0 }}>Review recommended</Alert>}
            {contact.overall_confidence !== null && <Typography className="detail-label" sx={{ alignSelf: 'center' }}>OCR confidence: {Math.round(contact.overall_confidence * 100)}%</Typography>}
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
}
