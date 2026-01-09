"""Celery tasks for report generation."""

import io
import uuid
from datetime import datetime, timezone
from decimal import Decimal

# Celery Task will be imported from celery_app
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.infra.s3 import s3_service
from app.modules.analytics.repo import AnalyticsRepository
from app.modules.reports.repo import ReportRepository
from app.modules.transactions.repo import TransactionRepository

logger = get_logger(__name__)


def generate_pdf_report_task(job_id: int) -> dict:
    """
    Generate PDF report asynchronously.

    Args:
        job_id: Report job ID

    Returns:
        Task result dictionary
    """
    db = SessionLocal()
    try:
        repo = ReportRepository(db)
        analytics_repo = AnalyticsRepository(db)
        transaction_repo = TransactionRepository(db)
        # Get job
        job = db.get(ReportJob, job_id)
        if not job:
            logger.error("Report job not found", extra={"job_id": job_id})
            return {"status": "failed", "error": "Job not found"}

        # Mark as started
        repo.mark_started(job_id)
        logger.info("Report generation started", extra={"job_id": job_id, "user_id": job.user_id})

        # Parse parameters
        params = job.params_json
        start_date = datetime.strptime(params["start_date"], "%Y-%m-%d")
        end_date = datetime.strptime(params["end_date"], "%Y-%m-%d")
        category_ids = params.get("category_ids")
        transaction_types = params.get("transaction_types")

        # Get transactions for report
        # Handle multiple category IDs - get transactions for each category
        all_transactions = []
        if category_ids:
            for cat_id in category_ids:
                trans_list, _, _, _ = transaction_repo.get_all_by_user(
                    user_id=job.user_id,
                    start_date=start_date,
                    end_date=end_date,
                    category_id=cat_id,
                    type_filter=(
                        transaction_types[0]
                        if transaction_types and len(transaction_types) == 1
                        else None
                    ),
                    limit=10000,
                )
                all_transactions.extend(trans_list)
            # Remove duplicates
            seen_ids = set()
            transactions = []
            for trans in all_transactions:
                if trans.id not in seen_ids:
                    seen_ids.add(trans.id)
                    transactions.append(trans)
        else:
            # No category filter
            type_filter = (
                transaction_types[0] if transaction_types and len(transaction_types) == 1 else None
            )
            transactions, _, _, _ = transaction_repo.get_all_by_user(
                user_id=job.user_id,
                start_date=start_date,
                end_date=end_date,
                type_filter=type_filter,
                limit=10000,
            )

        # Get summary data
        summary = analytics_repo.get_dashboard_summary(
            user_id=job.user_id,
            start_date=start_date,
            end_date=end_date,
        )

        # Generate PDF
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        story = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = styles["Heading1"]
        heading_style = styles["Heading2"]
        normal_style = styles["Normal"]

        # Title
        story.append(Paragraph("Expense Report", title_style))
        story.append(Spacer(1, 0.2 * inch))

        # Report metadata
        story.append(
            Paragraph(f"Period: {params['start_date']} to {params['end_date']}", normal_style)
        )
        story.append(
            Paragraph(
                f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
                normal_style,
            )
        )
        story.append(Spacer(1, 0.3 * inch))

        # Summary section
        story.append(Paragraph("Summary", heading_style))
        summary_data = [
            ["Metric", "Value"],
            ["Total Income", f"${summary.get('total_income', Decimal('0')):.2f}"],
            ["Total Expenses", f"${summary.get('total_expenses', Decimal('0')):.2f}"],
            ["Net", f"${summary.get('net', Decimal('0')):.2f}"],
            ["Transaction Count", str(summary.get("transaction_count", 0))],
        ]
        summary_table = Table(summary_data)
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        story.append(summary_table)
        story.append(Spacer(1, 0.3 * inch))

        # Transactions section
        story.append(Paragraph("Transactions", heading_style))
        if transactions:
            trans_data = [["Date", "Type", "Category", "Amount", "Note"]]
            for trans in transactions[:100]:  # Limit to 100 for PDF size
                trans_data.append(
                    [
                        trans.occurred_at.strftime("%Y-%m-%d") if trans.occurred_at else "",
                        trans.type or "",
                        trans.category.name if trans.category else "Uncategorized",
                        f"${trans.amount:.2f}",
                        trans.note or "",
                    ]
                )

            trans_table = Table(trans_data)
            trans_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ]
                )
            )
            story.append(trans_table)
            if len(transactions) > 100:
                story.append(Spacer(1, 0.1 * inch))
                story.append(
                    Paragraph(
                        f"Note: Showing first 100 of {len(transactions)} transactions", normal_style
                    )
                )
        else:
            story.append(Paragraph("No transactions found in this period.", normal_style))

        # Build PDF
        doc.build(story)
        pdf_content = pdf_buffer.getvalue()
        pdf_buffer.close()

        # Upload to S3
        s3_key = f"reports/{job.user_id}/{job_id}/{uuid.uuid4()}.pdf"
        success = s3_service.upload_file(pdf_content, s3_key, "application/pdf")

        if not success:
            raise Exception("Failed to upload PDF to S3")

        # Mark as completed
        repo.mark_completed(job_id, s3_key)
        logger.info("Report generation completed", extra={"job_id": job_id, "s3_key": s3_key})

        return {"status": "completed", "s3_key": s3_key}

    except Exception as e:
        # Mark as failed
        error_msg = str(e)
        try:
            repo.mark_failed(job_id, error_msg)
        except Exception:
            pass  # If repo is not available, just log
        logger.error(
            "Report generation failed",
            extra={"job_id": job_id, "error": error_msg},
            exc_info=True,
        )
        return {"status": "failed", "error": error_msg}
    finally:
        db.close()


# Import at the end to avoid circular imports
from app.infra.queue import celery_app
from app.models.report_job import ReportJob

# Register task with Celery
generate_pdf_report_task = celery_app.task(
    name="app.modules.reports.tasks.generate_pdf_report_task",
    bind=False,
)(generate_pdf_report_task)
