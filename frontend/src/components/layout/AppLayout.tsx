import { useState } from 'react';
import { Link as RouterLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  AppBar, Avatar, Box, Button, Divider, Drawer, IconButton, InputAdornment, List,
  ListItemButton, ListItemIcon, ListItemText, TextField, Toolbar, Tooltip, Typography,
  useMediaQuery, useTheme,
} from '@mui/material';
import DashboardRoundedIcon from '@mui/icons-material/DashboardRounded';
import ContactPageRoundedIcon from '@mui/icons-material/ContactPageRounded';
import DocumentScannerRoundedIcon from '@mui/icons-material/DocumentScannerRounded';
import MenuRoundedIcon from '@mui/icons-material/MenuRounded';
import SearchRoundedIcon from '@mui/icons-material/SearchRounded';
import PersonAddAlt1RoundedIcon from '@mui/icons-material/PersonAddAlt1Rounded';
import { useContacts } from '../../hooks/useContacts';

const drawerWidth = 248;
const navItems = [
  { label: 'Overview', path: '/', icon: <DashboardRoundedIcon /> },
  { label: 'OCR Scanner', path: '/ocr', icon: <DocumentScannerRoundedIcon /> },
  { label: 'Azure OCR', path: '/azure-ocr', icon: <DocumentScannerRoundedIcon /> },
  { label: 'Contacts', path: '/contacts', icon: <ContactPageRoundedIcon /> },
  { label: 'VCF Reader', path: '/vcf', icon: <DocumentScannerRoundedIcon /> },
];

export function AppLayout() {
  const theme = useTheme();
  const desktop = useMediaQuery(theme.breakpoints.up('md'));
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { data: contacts = [] } = useContacts();
  const [searchQuery, setSearchQuery] = useState('');
  const selectedContact = location.pathname.startsWith('/contacts');

  const drawer = (
    <Box className="sidebar-content">
      <Box className="brand-lockup">
        <Box className="brand-mark">C</Box>
        <Box>
          <Typography className="brand-name">ContactHub</Typography>
          <Typography className="brand-caption">CONTACT MANAGEMENT</Typography>
        </Box>
      </Box>
      {/* <Typography className="nav-caption">WORKSPACE</Typography> */}
      <List className="nav-list" disablePadding>
        {navItems.map((item) => {
          const active = item.path === '/contacts' ? selectedContact :
            item.path === '/' ? location.pathname === '/' || location.pathname === '/dashboard' :
              location.pathname === item.path;
          return (
            <ListItemButton
              key={item.path}
              component={RouterLink}
              to={item.path}
              selected={active}
              onClick={() => setMobileOpen(false)}
              className="nav-item"
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          );
        })}
      </List>
      <Box className="sidebar-spacer" />
      <Box className="sidebar-tip">
        <DocumentScannerRoundedIcon />
        <Typography variant="subtitle2">Turn cards into contacts</Typography>
        <Typography variant="body2">Scan a business card and review every detail before saving.</Typography>
        <Button component={RouterLink} to="/ocr" variant="contained" size="small">Scan a card</Button>
      </Box>
      <Divider className="sidebar-divider" />
      <Box className="sidebar-user">
        <Avatar className="user-avatar">AM</Avatar>
        <Box><Typography variant="subtitle2">Ankit</Typography><Typography variant="caption">Contact manager</Typography></Box>
      </Box>
    </Box>
  );

  return (
    <Box className="app-shell">
      <AppBar position="fixed" elevation={0} className="topbar" sx={{ ml: { md: `${drawerWidth}px` }, width: { md: `calc(100% - ${drawerWidth}px)` } }}>
        <Toolbar className="topbar-toolbar">
          {!desktop && <IconButton aria-label="Open navigation" onClick={() => setMobileOpen(true)} edge="start"><MenuRoundedIcon /></IconButton>}
          <Typography className="topbar-title">{location.pathname === '/' || location.pathname === '/dashboard' ? 'Overview' : location.pathname.startsWith('/ocr') ? 'OCR Scanner' : location.pathname === '/azure-ocr' ? 'Azure OCR' : 'Contacts'}</Typography>
          <TextField
            size="small"
            placeholder="Search contacts..."
            className="topbar-search"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                const search = searchQuery.trim();
                navigate(search ? `/contacts?search=${encodeURIComponent(search)}` : '/contacts');
              }
            }}
            slotProps={{
              input: { startAdornment: <InputAdornment position="start"><SearchRoundedIcon fontSize="small" /></InputAdornment> },
              htmlInput: { 'aria-label': 'Search contacts' },
            }}
          />
          <Tooltip title={`${contacts.length} saved contacts`}>
            <Avatar className="topbar-avatar">AM</Avatar>
          </Tooltip>
        </Toolbar>
      </AppBar>
      <Box component="nav" className="navigation">
        {desktop ? <Drawer variant="permanent" open className="desktop-drawer" sx={{ '& .MuiDrawer-paper': { width: drawerWidth } }}>{drawer}</Drawer> :
          <Drawer variant="temporary" open={mobileOpen} onClose={() => setMobileOpen(false)} className="mobile-drawer" sx={{ '& .MuiDrawer-paper': { width: drawerWidth } }}>{drawer}</Drawer>}
      </Box>
      <Box component="main" className="main-content" sx={{ ml: { md: `${drawerWidth}px` } }}>
        <Outlet />
        <Box className="mobile-bottom-nav">
          {navItems.map((item) => (
            <IconButton key={item.path} aria-label={item.label} onClick={() => navigate(item.path)} color={(item.path === '/contacts' ? selectedContact : location.pathname === item.path) ? 'primary' : 'default'}>
              {item.icon}
            </IconButton>
          ))}
          <IconButton aria-label="Create contact" onClick={() => navigate('/contacts/create')}><PersonAddAlt1RoundedIcon /></IconButton>
        </Box>
      </Box>
    </Box>
  );
}
