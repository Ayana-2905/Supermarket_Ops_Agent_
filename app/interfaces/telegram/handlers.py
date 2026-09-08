from telegram import Update
from telegram.ext import ContextTypes

from agents import Runner

from app.agent.agent import kirana_pilot

from app.agent.tools import (
    _confirm_pending_bill,
    is_confirmation,
    is_cancellation,
    current_chat_id
)

from app.domain.billing.confirmation_instance import (
    confirmation_manager
)

from app.interfaces.telegram.formatter import (
    format_response
)
from app.agent.tools import _confirm_pending_bill

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

        token = current_chat_id.set(chat_id)

        try:
            result = await Runner.run(
                kirana_pilot,
                user_input
            )
        finally:
            current_chat_id.reset(token)
        response = format_response(
            result.final_output
        )

        await update.message.reply_text(
            response
        )

    except Exception as e:

        print(
            f"Telegram handler error: {e}"
        )

        await update.message.reply_text(
            "⚠️ Something went wrong while "
            "processing your request."
        )
from telegram import Update
from telegram.ext import ContextTypes
from agents import Runner

from app.agent.agent import kirana_pilot

from app.agent.tools import (
    _confirm_pending_bill,
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

        result = await Runner.run(
            kirana_pilot,
            user_input
        )

        response = format_response(
            result.final_output
        )

        await update.message.reply_text(
            response
        )

    except Exception as e:

        print(
            f"Telegram handler error: {e}"
        )

        await update.message.reply_text(
            "⚠️ Something went wrong while "
            "processing your request."
        )

