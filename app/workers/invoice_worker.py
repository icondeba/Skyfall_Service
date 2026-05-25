from uuid import UUID

from app.core.database import SessionLocal
from app.services.integrations.invoice_pdf import invoice_pdf_generator


async def generate_invoice_pdf(order_id: UUID, invoice_number: str) -> str | None:
    with SessionLocal():
        return await invoice_pdf_generator.generate(order_id, invoice_number)
