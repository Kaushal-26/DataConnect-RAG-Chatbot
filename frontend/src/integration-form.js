import { useState } from 'react';
import {
    Box,
    Autocomplete,
    TextField,
    Typography,
    Divider,
} from '@mui/material';
import { AirtableIntegration } from './integrations/airtable';
import { NotionIntegration } from './integrations/notion';
import { HubspotIntegration } from './integrations/hubspot';
import { DataForm } from './data-form';

const integrationMapping = {
    'Notion': NotionIntegration,
    'Airtable': AirtableIntegration,
    'HubSpot': HubspotIntegration,
};

export const IntegrationForm = () => {
    const [integrationParams, setIntegrationParams] = useState({});
    const [user, setUser] = useState('TestUser');
    const [org, setOrg] = useState('TestOrg');
    const [currType, setCurrType] = useState(null);
    const CurrIntegration = integrationMapping[currType];

    const handleIntegrationTypeChange = (e, value) => {
        // Reset integrationParams when integration type changes
        setIntegrationParams({});
        setCurrType(value);
    };

  return (
    <Box display='flex' justifyContent='center' alignItems='center' flexDirection='column' sx={{ width: '100%' }}>
        <Typography variant="h4" gutterBottom sx={{mt: 4}}>
            Integration Form
            <Divider sx={{width: '100%', mt: 2}} />
        </Typography>
        <Box display='flex' flexDirection='column'>
        <TextField
            label="User"
            value={user}
            onChange={(e) => setUser(e.target.value)}
            sx={{mt: 2}}
        />
        <TextField
            label="Organization"
            value={org}
            onChange={(e) => setOrg(e.target.value)}
            sx={{mt: 2}}
        />
        <Autocomplete
            id="integration-type"
            options={Object.keys(integrationMapping)}
            sx={{ width: 300, mt: 2 }}
            renderInput={(params) => <TextField {...params} label="Integration Type" />}
            onChange={handleIntegrationTypeChange}
            value={currType}
        />
        </Box>
        {currType &&
        <Box>
            <CurrIntegration user={user} org={org} integrationParams={integrationParams} setIntegrationParams={setIntegrationParams} />
        </Box>
        }
        {integrationParams?.credentials &&
        <Box sx={{mt: 2}}>
            <DataForm integrationType={integrationParams?.type} credentials={integrationParams?.credentials} />
        </Box>
        }
    </Box>
  );
}
