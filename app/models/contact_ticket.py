from datetime import datetime, timezone
from app.extensions import db


class ContactTicket(db.Model):
    """Customer support ticket created via the contact form."""
    __tablename__ = 'contact_tickets'

    STATUS_NEW      = 'new'
    STATUS_ACTIVE   = 'active'
    STATUS_WORKING  = 'working'
    STATUS_CLOSED   = 'closed'
    STATUS_ARCHIVED = 'archived'

    STATUS_CHOICES = [STATUS_NEW, STATUS_ACTIVE, STATUS_WORKING, STATUS_CLOSED, STATUS_ARCHIVED]
    # Statuses that indicate an open / unresolved ticket
    OPEN_STATUSES  = [STATUS_NEW, STATUS_ACTIVE, STATUS_WORKING]

    id         = db.Column(db.Integer, primary_key=True)
    ticket_ref = db.Column(db.String(32), unique=True, nullable=False)
    name       = db.Column(db.String(200), nullable=False)
    email      = db.Column(db.String(200), nullable=False)
    subject    = db.Column(db.String(300), nullable=True)
    message    = db.Column(db.Text, nullable=False)
    status     = db.Column(db.String(20), default=STATUS_NEW, nullable=False)
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    @property
    def is_open(self):
        return self.status in self.OPEN_STATUSES

    def __repr__(self):
        return f'<ContactTicket {self.ticket_ref} status={self.status}>'

    def __str__(self):
        return f'{self.ticket_ref} — {self.name}'
