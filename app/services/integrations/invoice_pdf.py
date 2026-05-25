from uuid import UUID


class InvoicePDFGenerator:
    async def generate(self, order_id: UUID, invoice_number: str) -> str | None:
        # TODO: generate and upload invoice PDF to Supabase Storage.
        return None


invoice_pdf_generator = InvoicePDFGenerator()
