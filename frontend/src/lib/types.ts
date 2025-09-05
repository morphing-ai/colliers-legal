// frontend/src/lib/types.ts

// Define ticket-related types
export interface Ticket {
  id: number;
  title: string;
  description: string;
  status: string;
  priority: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  responses: TicketResponse[];
}

export interface TicketResponse {
  id: number;
  ticket_id: number;
  content: string;
  created_by: string;
  created_at: string;
}


export interface TicketCreateInput {
  title: string;
  description: string;
  priority?: string;
  status?: string;
}

export interface TicketUpdateInput {
  title?: string;
  description?: string;
  priority?: string;
  status?: string;
}

export interface TicketResponseInput {
  content: string;
}
