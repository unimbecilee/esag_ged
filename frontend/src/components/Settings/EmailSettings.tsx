import React from 'react';
import { Box } from '@chakra-ui/react';
import EmailSettingsOriginal from '../EmailSettings';

interface User {
  id: number;
  email: string;
  nom: string;
  prenom: string;
  role: string;
}

interface EmailSettingsProps {
  currentUser: User | null;
}

const EmailSettings: React.FC<EmailSettingsProps> = ({ currentUser }) => {
  return (
    <Box>
      <EmailSettingsOriginal />
    </Box>
  );
};

export default EmailSettings; 