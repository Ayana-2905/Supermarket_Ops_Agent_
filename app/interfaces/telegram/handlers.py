import os
import re

from telegram import Update
from telegram.ext import ContextTypes

from agents import Runner

from app.agent.agent import kirana_pilot
from app.agent.tools import (
    TelegramContext,
    _confirm_pending_bill,
    _generate_invoice,
    is_confirmation,
    is_cancellation
)

from app.domain.billing.confirmation_instance import (
    confirmation_manager
)

from app.interfaces.telegram.formatter import (
    format_response
)


async def start_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "👋 Welcome to KiranaPilot.\n\n"
        "I can help you with:\n"
        "• Inventory\n"
        "• Stock levels\n"
        "• Low-stock checks\n"
        "• Draft bills\n"
        "• Sale confirmation\n"
        "• Khata\n"
        "• Sales analysis\n\n"
        "Try:\n"
        "\"How much Maggi do I have?\""
    )


async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.message:
        return

    user_input = update.message.text.strip()

    if not user_input:
        return

    chat_id = str(update.message.chat_id)

    # ---------------------------------------------------------
    # EXPLICIT CONFIRMATION
    # ---------------------------------------------------------

    if is_confirmation(user_input):

        result = _confirm_pending_bill(
            chat_id=chat_id,
            payment_mode="CASH",
            payment_reference=""
        )

        if "error" in result:

            await update.message.reply_text(
                f"Cannot confirm sale: {result['error']}"
            )

            return

        response = (
            "✅ Sale completed successfully.\n\n"
            f"Bill Number: {result['bill_number']}\n"
            f"Status: {result['status']}\n"
            f"Payment: {result['payment_mode']}\n"
            f"Total: ₹{result['total']}"
        )

        await update.message.reply_text(response)

        # -----------------------------------------------------
        # AUTOMATIC INVOICE GENERATION
        # -----------------------------------------------------

        invoice_result = _generate_invoice(
            result["bill_number"]
        )

        if "error" in invoice_result:

            print(
                f"[INVOICE] Generation failed: "
                f"{invoice_result['error']}"
            )

            await update.message.reply_text(
                "⚠️ Sale completed, but the invoice "
                "could not be generated."
            )

        else:

            invoice_path = invoice_result["invoice_path"]

            print(
                f"[INVOICE] Generated: {invoice_path}"
            )

            try:

                with open(
                    invoice_path,
                    "rb"
                ) as pdf_file:

                    await update.message.reply_document(
                        document=pdf_file,
                        filename=os.path.basename(
                            invoice_path
                        ),
                        caption="📄 GST Invoice"
                    )

                print(
                    "[INVOICE] PDF sent to Telegram"
                )

            except Exception as e:

                print(
                    f"[INVOICE] Sending failed: {e}"
                )

                await update.message.reply_text(
                    "⚠️ Sale completed, but the "
                    "invoice could not be sent."
                )

        return

    # ---------------------------------------------------------
    # CANCELLATION
    # ---------------------------------------------------------

    if is_cancellation(user_input):

        pending = confirmation_manager.get_pending(
            chat_id
        )

        if not pending:

            await update.message.reply_text(
                "There is no bill waiting "
                "for confirmation."
            )

            return

        bill_number = pending.bill_number

        confirmation_manager.clear(
            chat_id
        )

        await update.message.reply_text(
            f"❌ Bill {bill_number} cancelled.\n\n"
            "No stock was deducted."
        )

        return

    # ---------------------------------------------------------
    # NORMAL AGENT REQUEST
    # ---------------------------------------------------------

    try:

        telegram_context = TelegramContext(
            chat_id=chat_id
        )

        result = await Runner.run(
            kirana_pilot,
            user_input,
            context=telegram_context
        )

        response = format_response(
            result.final_output
        )

        await update.message.reply_text(
            response
        )

                # -----------------------------------------------------
        # SEND GENERATED FILES TO TELEGRAM
        # -----------------------------------------------------

        output_text = str(result.final_output)

        print("[AGENT OUTPUT]")
        print(output_text)

        # -----------------------------------------------------
        # PDF
        # -----------------------------------------------------

        if ".pdf" in output_text.lower():

            invoice_path = find_generated_file(
                output_text,
                ".pdf"
            )

            if invoice_path:

                try:

                    with open(
                        invoice_path,
                        "rb"
                    ) as pdf_file:

                        await update.message.reply_document(
                            document=pdf_file,
                            filename=os.path.basename(
                                invoice_path
                            ),
                            caption="📄 GST Invoice"
                        )

                    print(
                        f"[FILE] PDF sent successfully: "
                        f"{invoice_path}"
                    )

                except Exception as e:

                    print(
                        f"[FILE] PDF sending failed: {e}"
                    )

                    await update.message.reply_text(
                        f"⚠️ Invoice was generated but "
                        f"could not be sent: {e}"
                    )

            else:

                print(
                    "[FILE] PDF path found in response "
                    "but file does not exist."
                )

        # -----------------------------------------------------
        # PPTX
        # -----------------------------------------------------

        if ".pptx" in output_text.lower():

            ppt_path = find_generated_file(
                output_text,
                ".pptx"
            )

            if ppt_path:

                try:

                    with open(
                        ppt_path,
                        "rb"
                    ) as ppt_file:

                        await update.message.reply_document(
                            document=ppt_file,
                            filename=os.path.basename(
                                ppt_path
                            ),
                            caption="📊 Sales Analysis"
                        )

                    print(
                        f"[FILE] PPTX sent successfully: "
                        f"{ppt_path}"
                    )

                except Exception as e:

                    print(
                        f"[FILE] PPTX sending failed: {e}"
                    )

            else:

                print(
                    "[FILE] PPTX path found in response "
                    "but file does not exist."
                )

    except Exception as e:

        print(
            f"Telegram handler error: {e}"
        )

        await update.message.reply_text(
            "⚠️ Something went wrong while "
            "processing your request."
        )


# -------------------------------------------------------------
# FILE PATH EXTRACTION
# -------------------------------------------------------------

def extract_file_path(
    text: str,
    extension: str
):
    """
    Extract a generated file path from the agent output.
    """

    for line in text.splitlines():

        line = line.strip()

        if extension.lower() in line.lower():

            # Try common formats such as:
            # invoice_path: invoices/file.pdf
            # file_path: reports/file.pptx

            if ":" in line:

                path = line.split(
                    ":",
                    1
                )[1].strip()

            else:

                path = line.strip()

            # Remove markdown/code formatting
            path = path.strip(
                "`\"'"
            )

            if extension.lower() in path.lower():

                return path

    return None
def find_generated_file(text: str, extension: str):

    import os
    import re

    if extension.lower() == ".pdf":

        match = re.search(
            r'(BILL-[A-Za-z0-9_-]+\.pdf)',
            text,
            re.IGNORECASE
        )

        if not match:
            return None

        filename = match.group(1)

        project_root = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                ".."
            )
        )

        file_path = os.path.join(
            project_root,
            "data",
            "invoices",
            filename
        )

    elif extension.lower() == ".pptx":

        match = re.search(
            r'(sales_analysis_[A-Za-z0-9_-]+\.pptx)',
            text,
            re.IGNORECASE
        )

        if not match:
            return None

        filename = match.group(1)

        project_root = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                ".."
            )
        )

        file_path = os.path.join(
            project_root,
            "data",
            "reports",
            filename
        )

    else:
        return None

    file_path = os.path.abspath(file_path)

    print(f"[FILE] Checking: {file_path}")
    print(f"[FILE] Exists: {os.path.exists(file_path)}")

    if os.path.exists(file_path):
        return file_path

    return None