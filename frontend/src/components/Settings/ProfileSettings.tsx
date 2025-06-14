import React from 'react';
import { Box, Text } from '@chakra-ui/react';

interface User {
  id: number;
  email: string;
  nom: string;
  prenom: string;
  role: string;
}

interface ProfileSettingsProps {
  currentUser: User | null;
}

const ProfileSettings: React.FC<ProfileSettingsProps> = ({ currentUser }) => {
  return (
    <Box>
      <Text color="white">Paramètres du profil</Text>
    </Box>
  );
};

export default ProfileSettings; 