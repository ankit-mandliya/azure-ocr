import { Link as RouterLink } from 'react-router-dom';
import {
  Alert, Avatar, Box, Button, Card, CardContent, Chip, CircularProgress, Grid, Stack, Typography,
} from '@mui/material';
import AddRoundedIcon from '@mui/icons-material/AddRounded';
import ArrowForwardRoundedIcon from '@mui/icons-material/ArrowForwardRounded';
import BusinessRoundedIcon from '@mui/icons-material/BusinessRounded';
import ContactPageRoundedIcon from '@mui/icons-material/ContactPageRounded';
import DocumentScannerRoundedIcon from '@mui/icons-material/DocumentScannerRounded';
import { useContacts } from '../hooks/useContacts';
import { getErrorMessage } from '../api/axios';

const cards = [
  { title: 'Total contacts', icon: <ContactPageRoundedIcon />, color: 'blue' },
  { title: 'Companies', icon: <BusinessRoundedIcon />, color: 'violet' },
  { title: 'Countries', icon: <BusinessRoundedIcon />, color: 'green' },
  { title: 'Recent scans', icon: <DocumentScannerRoundedIcon />, color: 'amber' },
];

export function DashboardPage() {
  const { data: contacts = [], isLoading, error } = useContacts();
  const companies = new Set(contacts.map((contact) => contact.company_name?.trim()).filter(Boolean));
  const countryCount = new Set(contacts.map((contact) => {
    const phone = contact.contact_number ?? '';
    return phone.startsWith('+') ? phone.match(/^\+\d{1,3}/)?.[0] : null;
  }).filter(Boolean)).size;
  const metrics = [contacts.length, companies.size, countryCount, contacts.filter((contact) => contact.overall_confidence !== null).length];

  return (
    <Box className="page-wrap">
      <Box className="page-heading dashboard-heading">
        <Box>
          <Typography className="eyebrow">YOUR CONTACTS, CONNECTED</Typography>
          <Typography variant="h1">Good to see you.</Typography>
          <Typography className="page-subtitle">A clear view of your business relationships.</Typography>
        </Box>
        <Stack direction="row" spacing={1.2}>
          <Button component={RouterLink} to="/contacts/create" variant="outlined" startIcon={<AddRoundedIcon />}>Add contact</Button>
          <Button component={RouterLink} to="/ocr" variant="contained" startIcon={<DocumentScannerRoundedIcon />}>Scan a card</Button>
        </Stack>
      </Box>
      {error && <Alert severity="error">{getErrorMessage(error)}</Alert>}
      {isLoading ? <Box className="loading-state"><CircularProgress /></Box> : (
        <Grid container spacing={2.25} className="metric-grid">
          {cards.map((card, index) => (
            <Grid key={card.title} size={{ xs: 6, lg: 3 }}>
              <Card className="metric-card">
                <CardContent>
                  <Box className="metric-top">
                    <Typography className="metric-label">{card.title}</Typography>
                    <Avatar className={`metric-icon ${card.color}`}>{card.icon}</Avatar>
                  </Box>
                  <Typography className="metric-value">{metrics[index].toLocaleString()}</Typography>
                  <Typography className="metric-note">{index === 0 ? 'Across your workspace' : index === 1 ? 'Distinct organizations' : index === 2 ? 'Based on phone prefixes' : 'OCR-processed contacts'}</Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
      <Grid container spacing={2.25} sx={{ mt: 0.1 }}>
        <Grid size={{ xs: 12, lg: 8 }}>
          <Card className="content-card">
            <CardContent className="section-card-content">
              <Box className="section-heading">
                <Box><Typography variant="h2">Recently added</Typography><Typography className="section-subtitle">The latest contacts in your address book</Typography></Box>
                <Button component={RouterLink} to="/contacts" endIcon={<ArrowForwardRoundedIcon />}>View all</Button>
              </Box>
              {contacts.length === 0 ? (
                <Box className="empty-state"><ContactPageRoundedIcon /><Typography variant="h3">Your contact list is ready</Typography><Typography>Start by adding a contact or scanning a business card.</Typography></Box>
              ) : (
                <Stack divider={<Box className="list-divider" />} spacing={0}>
                  {[...contacts].sort((a, b) => b.created_at.localeCompare(a.created_at)).slice(0, 5).map((contact) => (
                    <Box key={contact.id} className="recent-row">
                      <Avatar className="contact-avatar">{`${contact.first_name?.[0] ?? ''}${contact.last_name?.[0] ?? contact.company_name?.[0] ?? '?'}`}</Avatar>
                      <Box className="recent-copy">
                        <Typography component={RouterLink} to={`/contacts/${contact.id}`} className="recent-name">{[contact.first_name, contact.last_name].filter(Boolean).join(' ') || contact.company_name || 'Unnamed contact'}</Typography>
                        <Typography className="recent-meta">{contact.job_title || contact.email || 'Contact details available'}</Typography>
                      </Box>
                      {contact.needs_review && <Chip size="small" label="Review" color="warning" variant="outlined" />}
                    </Box>
                  ))}
                </Stack>
              )}
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, lg: 4 }}>
          <Card className="quick-card">
            <CardContent>
              <Avatar className="quick-icon"><DocumentScannerRoundedIcon /></Avatar>
              <Typography variant="h2">A faster way to capture</Typography>
              <Typography className="section-subtitle">Upload a card image and we’ll organize the details. Review the extracted information before it becomes a saved contact.</Typography>
              <Button component={RouterLink} to="/ocr" fullWidth variant="contained" endIcon={<ArrowForwardRoundedIcon />} sx={{ mt: 2.5 }}>Start a scan</Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
