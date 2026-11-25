import { useMemo, useState } from 'react';
import { Link as RouterLink, useSearchParams } from 'react-router-dom';
import {
  Alert, Avatar, Box, Button, Card, CardContent, CircularProgress, Dialog, DialogActions,
  DialogContent, DialogContentText, DialogTitle, IconButton, Stack, Typography, useMediaQuery, useTheme,
} from '@mui/material';
import AddRoundedIcon from '@mui/icons-material/AddRounded';
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded';
import DownloadRoundedIcon from '@mui/icons-material/DownloadRounded';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import VisibilityOutlinedIcon from '@mui/icons-material/VisibilityOutlined';
import { MaterialReactTable, useMaterialReactTable, type MRT_ColumnDef } from 'material-react-table';
import { getErrorMessage } from '../api/axios';
import { useContacts, useDeleteContact } from '../hooks/useContacts';
import type { Contact } from '../types/contact';

function exportCsv(contacts: Contact[]) {
  const columns: Array<keyof Contact> = ['first_name', 'last_name', 'email', 'contact_number', 'company_name', 'job_title'];
  const csv = [
    ['First Name', 'Last Name', 'Email', 'Phone', 'Company', 'Designation'],
    ...contacts.map((contact) => columns.map((key) => contact[key] ?? '')),
  ].map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(',')).join('\r\n');
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'contacthub-contacts.csv';
  link.click();
  URL.revokeObjectURL(url);
}

export function ContactsPage() {
  const { data: contacts = [], isLoading, error } = useContacts();
  const deletion = useDeleteContact();
  const [selected, setSelected] = useState<Contact | null>(null);
  const [params, setParams] = useSearchParams();
  const theme = useTheme();
  const mobile = useMediaQuery(theme.breakpoints.down('sm'));
  const search = params.get('search') ?? '';
  const columns = useMemo<MRT_ColumnDef<Contact>[]>(() => [
    { accessorKey: 'first_name', header: 'First name', Cell: ({ row }) => row.original.first_name || '—' },
    { accessorKey: 'last_name', header: 'Last name', Cell: ({ row }) => row.original.last_name || '—' },
    { accessorKey: 'email', header: 'Email', Cell: ({ row }) => row.original.email || '—' },
    { accessorKey: 'contact_number', header: 'Phone', Cell: ({ row }) => row.original.contact_number || '—' },
    { accessorKey: 'company_name', header: 'Company', Cell: ({ row }) => row.original.company_name || '—' },
    { accessorKey: 'job_title', header: 'Designation', Cell: ({ row }) => row.original.job_title || '—' },
  ], []);
  const table = useMaterialReactTable({
    columns,
    data: contacts,
    enableRowSelection: true,
    enableColumnFilters: true,
    enableGlobalFilter: true,
    enableSorting: true,
    enablePagination: true,
    filterFns: {
      contactSearch: (row, _columnId, filterValue) => Object.values(row.original)
        .map((value) => String(value ?? ''))
        .join(' ')
        .toLowerCase()
        .includes(String(filterValue ?? '').toLowerCase()),
    },
    globalFilterFn: 'contactSearch',
    initialState: { showGlobalFilter: true, pagination: { pageIndex: 0, pageSize: 10 } },
    state: { globalFilter: search },
    onGlobalFilterChange: (value) => {
      const next = typeof value === 'string' ? value : '';
      setParams(next ? { search: next } : {}, { replace: true });
    },
    renderRowActions: ({ row }) => (
      <Stack direction="row" spacing={0.25}>
        <IconButton component={RouterLink} to={`/contacts/${row.original.id}`} aria-label="View contact" size="small"><VisibilityOutlinedIcon fontSize="small" /></IconButton>
        <IconButton component={RouterLink} to={`/contacts/edit/${row.original.id}`} aria-label="Edit contact" size="small"><EditOutlinedIcon fontSize="small" /></IconButton>
        <IconButton aria-label="Delete contact" size="small" color="error" onClick={() => setSelected(row.original)}><DeleteOutlineRoundedIcon fontSize="small" /></IconButton>
      </Stack>
    ),
    positionActionsColumn: 'last',
    muiTablePaperProps: { elevation: 0, sx: { border: '1px solid #e8edf3', borderRadius: '16px', overflow: 'hidden' } },
    muiTableHeadCellProps: { sx: { backgroundColor: '#f8fafc', color: '#667085', fontWeight: 700 } },
    muiTableBodyCellProps: { sx: { py: 1.5 } },
  });

  const confirmDelete = () => {
    if (!selected) return;
    deletion.mutate(selected.id, { onSuccess: () => setSelected(null) });
  };

  return (
    <Box className="page-wrap">
      <Box className="page-heading">
        <Box><Typography className="eyebrow">ADDRESS BOOK</Typography><Typography variant="h1">Contacts</Typography><Typography className="page-subtitle">Search, organize, and manage your business connections.</Typography></Box>
        <Stack direction="row" spacing={1}>
          <Button variant="outlined" startIcon={<DownloadRoundedIcon />} onClick={() => exportCsv(contacts)} disabled={!contacts.length}>Export CSV</Button>
          <Button component={RouterLink} to="/contacts/create" variant="contained" startIcon={<AddRoundedIcon />}>New contact</Button>
        </Stack>
      </Box>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{getErrorMessage(error)}</Alert>}
      {deletion.error && <Alert severity="error" sx={{ mb: 2 }}>{getErrorMessage(deletion.error)}</Alert>}
      {isLoading ? <Box className="loading-state"><CircularProgress /></Box> : mobile ? (
        <Stack spacing={1.2}>
          {contacts.filter((contact) => JSON.stringify(contact).toLowerCase().includes(search.toLowerCase())).map((contact) => (
            <Card key={contact.id} className="mobile-contact-card"><CardContent className="mobile-contact-content">
              <Avatar className="contact-avatar">{`${contact.first_name?.[0] ?? ''}${contact.last_name?.[0] ?? contact.company_name?.[0] ?? '?'}`}</Avatar>
              <Box className="mobile-contact-copy"><Typography variant="h3">{[contact.first_name, contact.last_name].filter(Boolean).join(' ') || contact.company_name || 'Unnamed contact'}</Typography><Typography>{contact.company_name || contact.job_title || '—'}</Typography><Typography>{contact.email || contact.contact_number || 'No contact details'}</Typography></Box>
              <Stack><IconButton component={RouterLink} to={`/contacts/${contact.id}`} aria-label="View contact"><VisibilityOutlinedIcon /></IconButton><IconButton component={RouterLink} to={`/contacts/edit/${contact.id}`} aria-label="Edit contact"><EditOutlinedIcon /></IconButton><IconButton color="error" onClick={() => setSelected(contact)} aria-label="Delete contact"><DeleteOutlineRoundedIcon /></IconButton></Stack>
            </CardContent></Card>
          ))}
          {!contacts.length && <Card className="content-card"><CardContent><Typography>No contacts yet. Create one or scan a business card.</Typography></CardContent></Card>}
        </Stack>
      ) : <MaterialReactTable table={table} />}
      <Dialog open={!!selected} onClose={() => !deletion.isPending && setSelected(null)}>
        <DialogTitle>Delete contact?</DialogTitle>
        <DialogContent><DialogContentText>This will permanently remove {selected?.first_name || selected?.company_name || 'this contact'} from your address book.</DialogContentText></DialogContent>
        <DialogActions><Button onClick={() => setSelected(null)} disabled={deletion.isPending} color="inherit">Cancel</Button><Button onClick={confirmDelete} color="error" variant="contained" disabled={deletion.isPending}>{deletion.isPending ? 'Deleting…' : 'Delete'}</Button></DialogActions>
      </Dialog>
    </Box>
  );
}
