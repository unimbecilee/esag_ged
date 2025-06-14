import React from 'react';
import WorkflowManagement from './Workflow/WorkflowManagement';
import RequireRole from './RequireRole';

const Workflow: React.FC = () => {
  return (
    <RequireRole roles={["admin", "chef_de_service", "directeur"]}>
      <WorkflowManagement />
    </RequireRole>
  );
};

export default Workflow; 