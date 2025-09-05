# backend/app/services/ticket_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any

from app.db.models import Ticket, TicketResponse, TicketStatus, TicketPriority

class TicketService:
    """Service for handling ticket operations."""
    
    @staticmethod
    async def create_ticket(
        session: AsyncSession,
        title: str,
        description: str,
        created_by: str,
        priority: TicketPriority = TicketPriority.MEDIUM,
        status: TicketStatus = TicketStatus.OPEN
    ) -> Ticket:
        """Create a new ticket."""
        # Create ticket record
        ticket = Ticket(
            title=title,
            description=description,
            created_by=created_by,
            priority=priority,
            status=status
        )
        
        # Add to session and commit
        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)
        
        return ticket
    
    @staticmethod
    async def get_tickets(
        session: AsyncSession,
        status: Optional[str] = None,
        created_by: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Ticket]:
        """Get tickets with optional filtering."""
        # Build query
        query = select(Ticket).options(selectinload(Ticket.responses))
        
        # Apply filters if provided
        if status:
            # IMPORTANT: Handle case-insensitivity for status enums
            # Convert status to uppercase and ensure it's a valid TicketStatus enum value
            try:
                # This normalizes the case to match the enum's definition
                # It handles both "in_progress" and "IN_PROGRESS" correctly
                status_upper = status.upper()
                enum_status = TicketStatus[status_upper]
                query = query.filter(Ticket.status == enum_status)
            except KeyError:
                # If the status is not a valid enum value, simply log and don't apply the filter
                print(f"Warning: Invalid status filter '{status}'. Valid values: {[s.name for s in TicketStatus]}")
        
        if created_by:
            query = query.filter(Ticket.created_by == created_by)
        
        # Add pagination
        query = query.order_by(desc(Ticket.created_at)).offset(skip).limit(limit)
        
        # Execute query
        result = await session.execute(query)
        tickets = result.scalars().all()
        
        return list(tickets)
    
    @staticmethod
    async def get_ticket(
        session: AsyncSession,
        ticket_id: int
    ) -> Optional[Ticket]:
        """Get a ticket by ID."""
        query = select(Ticket).options(selectinload(Ticket.responses)).filter(Ticket.id == ticket_id)
        result = await session.execute(query)
        ticket = result.scalars().first()
        
        return ticket
    
    @staticmethod
    async def update_ticket(
        session: AsyncSession,
        ticket_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> Optional[Ticket]:
        """Update a ticket."""
        # Get current ticket
        ticket = await TicketService.get_ticket(session, ticket_id)
        if not ticket:
            return None
        
        # Prepare update data
        update_data = {}
        if title is not None:
            update_data["title"] = title
        if description is not None:
            update_data["description"] = description
            
        # Handle enum values with case normalization
        if status is not None:
            try:
                # Convert status string to enum
                status_upper = status.upper()
                enum_status = TicketStatus[status_upper]
                update_data["status"] = enum_status
            except (KeyError, AttributeError):
                # Skip invalid status
                print(f"Warning: Invalid status '{status}'. Using existing value.")
                
        if priority is not None:
            try:
                # Convert priority string to enum
                priority_upper = priority.upper()
                enum_priority = TicketPriority[priority_upper]
                update_data["priority"] = enum_priority
            except (KeyError, AttributeError):
                # Skip invalid priority
                print(f"Warning: Invalid priority '{priority}'. Using existing value.")
        
        # Update ticket if there's data to update
        if update_data:
            stmt = update(Ticket).where(Ticket.id == ticket_id).values(**update_data)
            await session.execute(stmt)
            await session.commit()
            
            # Refresh ticket to get updated data
            await session.refresh(ticket)
        
        return ticket
    
    @staticmethod
    async def add_response(
        session: AsyncSession,
        ticket_id: int,
        content: str,
        created_by: str
    ) -> TicketResponse:
        """Add a response to a ticket."""
        # Create response
        response = TicketResponse(
            ticket_id=ticket_id,
            content=content,
            created_by=created_by
        )
        
        # Add to session and commit
        session.add(response)
        await session.commit()
        await session.refresh(response)
        
        # Update ticket status to in_progress if it's open
        ticket = await TicketService.get_ticket(session, ticket_id)
        if ticket and ticket.status == TicketStatus.OPEN:
            await TicketService.update_ticket(
                session=session,
                ticket_id=ticket_id,
                status="IN_PROGRESS"  # Use uppercase to match enum
            )
        
        return response
    
    @staticmethod
    async def delete_ticket(
        session: AsyncSession,
        ticket_id: int
    ) -> bool:
        """Delete a ticket."""
        stmt = delete(Ticket).where(Ticket.id == ticket_id)
        result = await session.execute(stmt)
        await session.commit()
        
        # Check if any rows were deleted
        return result.rowcount > 0